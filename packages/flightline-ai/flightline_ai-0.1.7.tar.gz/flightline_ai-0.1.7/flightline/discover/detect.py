"""AI call detection for Python and JavaScript/TypeScript.

Uses Python's built-in ast module for Python files and regex for JS/TS.
Focus is on high precision - we want few false positives.
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from flightline.discover.schema import CallType, Location, Provider

# =============================================================================
# DETECTION RESULT
# =============================================================================


@dataclass
class DetectedCall:
    """A detected AI API call."""

    location: Location
    provider: Provider
    call_type: CallType

    # Raw info for tracing
    client_variable: Optional[str] = None  # e.g., "client", "openai"
    method_chain: Optional[str] = None  # e.g., "chat.completions.create"
    raw_args: Optional[str] = None  # Raw argument string for tracing

    # For generating unique IDs
    function_context: Optional[str] = None

    def make_id(self, file_path: Path) -> str:
        """Generate a unique ID for this call."""
        import hashlib

        stem = file_path.stem.replace("-", "_").replace(".", "_")
        func = self.function_context or "module"

        # Create a stable signature for this call site
        # We use provider, type, and the method chain
        sig = f"{self.provider}_{self.call_type}_{self.method_chain}_{self.location.line}"
        sig_hash = hashlib.md5(sig.encode()).hexdigest()[:6]

        return f"{stem}_{func}_{sig_hash}"


# =============================================================================
# PYTHON DETECTION (using ast)
# =============================================================================


class PythonAIDetector(ast.NodeVisitor):
    """AST visitor that detects AI SDK calls in Python code."""

    # Import patterns to track
    OPENAI_IMPORTS = {
        "openai": {"OpenAI", "AsyncOpenAI", "AzureOpenAI"},
        "from openai": {"OpenAI", "AsyncOpenAI", "AzureOpenAI"},
    }

    ANTHROPIC_IMPORTS = {
        "anthropic": {"Anthropic", "AsyncAnthropic"},
        "from anthropic": {"Anthropic", "AsyncAnthropic"},
    }

    GOOGLE_IMPORTS = {
        "google.generativeai": {"GenerativeModel"},
        "from google.generativeai": {"GenerativeModel"},
    }

    MISTRAL_IMPORTS = {
        "mistralai": {"MistralClient"},
        "from mistralai.client": {"MistralClient"},
    }

    # Method patterns that indicate AI calls
    OPENAI_METHODS = {
        "chat.completions.create": CallType.CHAT,
        "completions.create": CallType.COMPLETION,
        "embeddings.create": CallType.EMBEDDING,
    }

    ANTHROPIC_METHODS = {
        "messages.create": CallType.CHAT,
    }

    GOOGLE_METHODS = {
        "generate_content": CallType.CHAT,
        "generate_content_async": CallType.CHAT,
    }

    MISTRAL_METHODS = {
        "chat": CallType.CHAT,
        "embeddings": CallType.EMBEDDING,
    }

    def __init__(self, file_path: Path, source: str):
        self.file_path = file_path
        self.source = source
        self.lines = source.splitlines()

        # Track imports
        self.openai_client_vars: set[str] = set()
        self.anthropic_client_vars: set[str] = set()
        self.google_client_vars: set[str] = set()
        self.mistral_client_vars: set[str] = set()

        # Track detected calls
        self.detected_calls: list[DetectedCall] = []

        # Current context
        self._current_function: Optional[str] = None
        self._current_class: Optional[str] = None

    def _get_location(self, node: ast.AST) -> Location:
        """Create a Location from an AST node."""
        return Location(
            file=str(self.file_path),
            line=node.lineno,
            column=node.col_offset,
            function=self._current_function,
            class_name=self._current_class,
        )

    def visit_Import(self, node: ast.Import) -> None:
        """Track 'import openai' style imports."""
        for alias in node.names:
            if alias.name == "openai":
                var_name = alias.asname or "openai"
                self.openai_client_vars.add(var_name)
            elif alias.name == "anthropic":
                var_name = alias.asname or "anthropic"
                self.anthropic_client_vars.add(var_name)
            elif alias.name == "google.generativeai":
                var_name = alias.asname or "genai"
                self.google_client_vars.add(var_name)
            elif alias.name == "mistralai":
                var_name = alias.asname or "mistralai"
                self.mistral_client_vars.add(var_name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track 'from openai import OpenAI' style imports."""
        if node.module == "openai":
            for alias in node.names:
                if alias.name in {"OpenAI", "AsyncOpenAI", "AzureOpenAI"}:
                    self.openai_client_vars.add("__openai_imported__")
        elif node.module == "anthropic":
            for alias in node.names:
                if alias.name in {"Anthropic", "AsyncAnthropic"}:
                    self.anthropic_client_vars.add("__anthropic_imported__")
        elif node.module == "google.generativeai":
            for alias in node.names:
                if alias.name == "GenerativeModel":
                    self.google_client_vars.add("__google_imported__")
        elif node.module == "mistralai.client":
            for alias in node.names:
                if alias.name == "MistralClient":
                    self.mistral_client_vars.add("__mistral_imported__")
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Track client variable assignments like 'client = OpenAI()'."""
        if isinstance(node.value, ast.Call):
            func = node.value.func
            func_name = self._get_call_name(func)

            # Check if this is an OpenAI client instantiation
            if func_name in {"OpenAI", "AsyncOpenAI", "AzureOpenAI"}:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.openai_client_vars.add(target.id)
                        # Check for OpenRouter base_url
                        if self._is_openrouter_url(node.value):
                            self.openai_client_vars.add(f"{target.id}_openrouter")

            # Check if this is an Anthropic client instantiation
            elif func_name in {"Anthropic", "AsyncAnthropic"}:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.anthropic_client_vars.add(target.id)

            # Check if this is a Mistral client instantiation
            elif func_name == "MistralClient":
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.mistral_client_vars.add(target.id)

            # Check for Google GenerativeModel
            elif func_name == "GenerativeModel":
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.google_client_vars.add(target.id)

        self.generic_visit(node)

    def _is_openrouter_url(self, node: ast.Call) -> bool:
        """Check if call has OpenRouter base_url."""
        for kw in node.keywords:
            if kw.arg == "base_url":
                if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    if "openrouter.ai" in kw.value.value:
                        return True
        return False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track function context."""
        old_function = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track async function context."""
        old_function = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_function

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track class context."""
        old_class = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = old_class

    def visit_Call(self, node: ast.Call) -> None:
        """Detect AI API calls."""
        method_chain = self._get_method_chain(node.func)

        if method_chain:
            # Check for OpenAI patterns
            call_type = self._match_openai_call(method_chain, node)
            if call_type:
                provider = Provider.OPENAI
                # If we detected OpenRouter url earlier, mark it
                client_var = self._get_client_var(node.func)
                if client_var and f"{client_var}_openrouter" in self.openai_client_vars:
                    provider = Provider.OPENROUTER

                self.detected_calls.append(
                    DetectedCall(
                        location=self._get_location(node),
                        provider=provider,
                        call_type=call_type,
                        client_variable=client_var,
                        method_chain=method_chain,
                        raw_args=self._extract_raw_args(node),
                        function_context=self._current_function,
                    )
                )
            else:
                # Check for Anthropic patterns
                call_type = self._match_anthropic_call(method_chain, node)
                if call_type:
                    self.detected_calls.append(
                        DetectedCall(
                            location=self._get_location(node),
                            provider=Provider.ANTHROPIC,
                            call_type=call_type,
                            client_variable=self._get_client_var(node.func),
                            method_chain=method_chain,
                            raw_args=self._extract_raw_args(node),
                            function_context=self._current_function,
                        )
                    )
                else:
                    # Check for Google patterns
                    call_type = self._match_google_call(method_chain, node)
                    if call_type:
                        self.detected_calls.append(
                            DetectedCall(
                                location=self._get_location(node),
                                provider=Provider.GOOGLE,
                                call_type=call_type,
                                client_variable=self._get_client_var(node.func),
                                method_chain=method_chain,
                                raw_args=self._extract_raw_args(node),
                                function_context=self._current_function,
                            )
                        )
                    else:
                        # Check for Mistral patterns
                        call_type = self._match_mistral_call(method_chain, node)
                        if call_type:
                            self.detected_calls.append(
                                DetectedCall(
                                    location=self._get_location(node),
                                    provider=Provider.MISTRAL,
                                    call_type=call_type,
                                    client_variable=self._get_client_var(node.func),
                                    method_chain=method_chain,
                                    raw_args=self._extract_raw_args(node),
                                    function_context=self._current_function,
                                )
                            )

        self.generic_visit(node)

    def _match_google_call(self, method_chain: str, node: ast.Call) -> Optional[CallType]:
        """Check if method chain matches Google patterns."""
        if not self.google_client_vars:
            return None

        client_var = self._get_client_var(node.func)
        if client_var and client_var not in self.google_client_vars:
            if "__google_imported__" not in self.google_client_vars:
                return None

        for pattern, call_type in self.GOOGLE_METHODS.items():
            if method_chain.endswith(pattern):
                return call_type
        return None

    def _match_mistral_call(self, method_chain: str, node: ast.Call) -> Optional[CallType]:
        """Check if method chain matches Mistral patterns."""
        if not self.mistral_client_vars:
            return None

        client_var = self._get_client_var(node.func)
        if client_var and client_var not in self.mistral_client_vars:
            if "__mistral_imported__" not in self.mistral_client_vars:
                return None

        for pattern, call_type in self.MISTRAL_METHODS.items():
            if method_chain.endswith(pattern):
                return call_type
        return None

    def _get_call_name(self, node: ast.expr) -> Optional[str]:
        """Get the name of a call target."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None

    def _get_method_chain(self, node: ast.expr) -> Optional[str]:
        """Extract method chain like 'client.chat.completions.create'."""
        parts = []
        current = node

        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            parts.append(current.id)

        if not parts:
            return None

        parts.reverse()
        return ".".join(parts)

    def _get_client_var(self, node: ast.expr) -> Optional[str]:
        """Get the client variable name from a method call."""
        current = node
        while isinstance(current, ast.Attribute):
            current = current.value

        if isinstance(current, ast.Name):
            return current.id
        return None

    def _match_openai_call(self, method_chain: str, node: ast.Call) -> Optional[CallType]:
        """Check if method chain matches OpenAI patterns."""
        # Check if we've seen OpenAI imports
        if not self.openai_client_vars:
            return None

        # Get client variable
        client_var = self._get_client_var(node.func)

        # Must be from a known client variable or the module itself
        if client_var and client_var not in self.openai_client_vars:
            # Check if it might be a generic 'client' that we should flag
            if client_var not in {"client", "openai_client", "ai_client"}:
                if "__openai_imported__" not in self.openai_client_vars:
                    return None

        # Check method patterns
        for pattern, call_type in self.OPENAI_METHODS.items():
            if method_chain.endswith(pattern):
                return call_type

        return None

    def _match_anthropic_call(self, method_chain: str, node: ast.Call) -> Optional[CallType]:
        """Check if method chain matches Anthropic patterns."""
        if not self.anthropic_client_vars:
            return None

        client_var = self._get_client_var(node.func)

        if client_var and client_var not in self.anthropic_client_vars:
            if client_var not in {"client", "anthropic_client", "ai_client"}:
                if "__anthropic_imported__" not in self.anthropic_client_vars:
                    return None

        for pattern, call_type in self.ANTHROPIC_METHODS.items():
            if method_chain.endswith(pattern):
                return call_type

        return None

    def _extract_raw_args(self, node: ast.Call) -> Optional[str]:
        """Extract raw argument string for later tracing."""
        try:
            # Get the line range
            start_line = node.lineno - 1
            end_line = node.end_lineno or node.lineno

            if start_line < len(self.lines):
                lines = self.lines[start_line:end_line]
                return "\n".join(lines)
        except (AttributeError, IndexError):
            pass
        return None


def detect_python_ai_calls(file_path: Path) -> list[DetectedCall]:
    """
    Detect AI calls in a Python file.

    Args:
        file_path: Path to Python file

    Returns:
        List of detected AI calls
    """
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, OSError):
        # Skip files that can't be parsed
        return []

    detector = PythonAIDetector(file_path, source)
    detector.visit(tree)

    return detector.detected_calls


# =============================================================================
# JAVASCRIPT/TYPESCRIPT DETECTION (using regex)
# =============================================================================


# Import patterns
JS_OPENAI_IMPORT = re.compile(
    r"""(?:import\s+(?:(\w+)|{[^}]*})\s+from\s+['"]openai['"]|"""
    r"""const\s+(\w+)\s*=\s*require\s*\(\s*['"]openai['"]\s*\))""",
    re.MULTILINE,
)

JS_ANTHROPIC_IMPORT = re.compile(
    r"""(?:import\s+(?:(\w+)|{[^}]*})\s+from\s+['"]@anthropic-ai/sdk['"]|"""
    r"""const\s+(\w+)\s*=\s*require\s*\(\s*['"]@anthropic-ai/sdk['"]\s*\))""",
    re.MULTILINE,
)

JS_GOOGLE_IMPORT = re.compile(
    r"""(?:import\s+{[^}]*GoogleGenerativeAI[^}]*}\s+from\s+['"]@google/generative-ai['"]|"""
    r"""const\s+{[^}]*GoogleGenerativeAI[^}]*}\s*=\s*require\s*\(\s*['"]@google/generative-ai['"]\s*\))""",
    re.MULTILINE,
)

JS_MISTRAL_IMPORT = re.compile(
    r"""(?:import\s+(\w+)\s+from\s+['"]@mistralai/mistralai['"]|"""
    r"""const\s+(\w+)\s*=\s*require\s*\(\s*['"]@mistralai/mistralai['"]\s*\))""",
    re.MULTILINE,
)

# Client instantiation patterns
JS_OPENAI_CLIENT = re.compile(r"""(?:const|let|var)\s+(\w+)\s*=\s*new\s+OpenAI\s*\(\s*({[^}]*})?\s*\)""", re.MULTILINE)

JS_ANTHROPIC_CLIENT = re.compile(r"""(?:const|let|var)\s+(\w+)\s*=\s*new\s+Anthropic\s*\(""", re.MULTILINE)

JS_GOOGLE_CLIENT = re.compile(r"""(?:const|let|var)\s+(\w+)\s*=\s*new\s+GoogleGenerativeAI\s*\(""", re.MULTILINE)

JS_MISTRAL_CLIENT = re.compile(r"""(?:const|let|var)\s+(\w+)\s*=\s*new\s+MistralClient\s*\(""", re.MULTILINE)

# Call patterns
JS_OPENAI_CHAT_CALL = re.compile(r"""(\w+)\.chat\.completions\.create\s*\(""", re.MULTILINE)

JS_OPENAI_EMBEDDING_CALL = re.compile(r"""(\w+)\.embeddings\.create\s*\(""", re.MULTILINE)

JS_ANTHROPIC_CALL = re.compile(r"""(\w+)\.messages\.create\s*\(""", re.MULTILINE)

JS_GOOGLE_CALL = re.compile(r"""(\w+)\.generateContent(?:Async)?\s*\(""", re.MULTILINE)

JS_MISTRAL_CALL = re.compile(r"""(\w+)\.chat\s*\(""", re.MULTILINE)

# Function context pattern
JS_FUNCTION_PATTERN = re.compile(
    r"""(?:async\s+)?(?:function\s+(\w+)|(\w+)\s*[=:]\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>|\w+\s*=>))""",
    re.MULTILINE,
)


@dataclass
class JSDetectionContext:
    """Context for JS/TS detection."""

    file_path: Path
    source: str
    lines: list[str]

    # Track client variables
    openai_clients: set[str] = field(default_factory=set)
    anthropic_clients: set[str] = field(default_factory=set)
    google_clients: set[str] = field(default_factory=set)
    mistral_clients: set[str] = field(default_factory=set)
    openrouter_clients: set[str] = field(default_factory=set)

    # Track if imports are present
    has_openai_import: bool = False
    has_anthropic_import: bool = False
    has_google_import: bool = False
    has_mistral_import: bool = False


def _get_line_number(source: str, pos: int) -> int:
    """Get 1-indexed line number from character position."""
    return source[:pos].count("\n") + 1


def _get_function_at_line(source: str, line_num: int) -> Optional[str]:
    """Find the function name containing a line."""
    lines = source.splitlines()

    # Search backwards for function definition
    for i in range(line_num - 1, -1, -1):
        if i >= len(lines):
            continue

        line = lines[i]
        match = JS_FUNCTION_PATTERN.search(line)
        if match:
            return match.group(1) or match.group(2)

    return None


def detect_js_ai_calls(file_path: Path) -> list[DetectedCall]:
    """
    Detect AI calls in a JavaScript/TypeScript file.

    Args:
        file_path: Path to JS/TS file

    Returns:
        List of detected AI calls
    """
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    ctx = JSDetectionContext(
        file_path=file_path,
        source=source,
        lines=source.splitlines(),
    )

    detected_calls: list[DetectedCall] = []

    # Find imports
    for match in JS_OPENAI_IMPORT.finditer(source):
        ctx.has_openai_import = True
        var_name = match.group(1) or match.group(2)
        if var_name:
            ctx.openai_clients.add(var_name)

    for match in JS_ANTHROPIC_IMPORT.finditer(source):
        ctx.has_anthropic_import = True
        var_name = match.group(1) or match.group(2)
        if var_name:
            ctx.anthropic_clients.add(var_name)

    for match in JS_GOOGLE_IMPORT.finditer(source):
        ctx.has_google_import = True

    for match in JS_MISTRAL_IMPORT.finditer(source):
        ctx.has_mistral_import = True
        var_name = match.group(1) or match.group(2)
        if var_name:
            ctx.mistral_clients.add(var_name)

    # Find client instantiations and model gets
    for match in JS_OPENAI_CLIENT.finditer(source):
        var_name = match.group(1)
        ctx.openai_clients.add(var_name)
        # Check for OpenRouter base_url
        if match.group(2) and "openrouter.ai" in match.group(2):
            ctx.openrouter_clients.add(var_name)

    for match in JS_ANTHROPIC_CLIENT.finditer(source):
        ctx.anthropic_clients.add(match.group(1))

    for match in JS_GOOGLE_CLIENT.finditer(source):
        ctx.google_clients.add(match.group(1))

    # Google model.getGenerativeModel pattern
    google_model_pattern = re.compile(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:\w+)\.getGenerativeModel\s*\(")
    for match in google_model_pattern.finditer(source):
        ctx.google_clients.add(match.group(1))

    for match in JS_MISTRAL_CLIENT.finditer(source):
        ctx.mistral_clients.add(match.group(1))

    # If no imports found, skip call detection (unless we saw client instantiations)
    if not any([ctx.has_openai_import, ctx.has_anthropic_import, ctx.has_google_import, ctx.has_mistral_import]):
        if not any([ctx.openai_clients, ctx.anthropic_clients, ctx.google_clients, ctx.mistral_clients]):
            return []

    # Find OpenAI chat calls
    for match in JS_OPENAI_CHAT_CALL.finditer(source):
        client_var = match.group(1)
        # Verify this is from an OpenAI client
        if client_var in ctx.openai_clients or client_var in {"client", "openai", "openaiClient"}:
            provider = Provider.OPENROUTER if client_var in ctx.openrouter_clients else Provider.OPENAI
            line_num = _get_line_number(source, match.start())
            detected_calls.append(
                DetectedCall(
                    location=Location(
                        file=str(file_path),
                        line=line_num,
                        function=_get_function_at_line(source, line_num),
                    ),
                    provider=provider,
                    call_type=CallType.CHAT,
                    client_variable=client_var,
                    method_chain="chat.completions.create",
                    function_context=_get_function_at_line(source, line_num),
                )
            )

    for match in JS_OPENAI_EMBEDDING_CALL.finditer(source):
        client_var = match.group(1)
        if client_var in ctx.openai_clients or client_var in {"client", "openai", "openaiClient"}:
            line_num = _get_line_number(source, match.start())
            detected_calls.append(
                DetectedCall(
                    location=Location(
                        file=str(file_path),
                        line=line_num,
                        function=_get_function_at_line(source, line_num),
                    ),
                    provider=Provider.OPENAI,
                    call_type=CallType.EMBEDDING,
                    client_variable=client_var,
                    method_chain="embeddings.create",
                    function_context=_get_function_at_line(source, line_num),
                )
            )

    # Find Anthropic calls
    for match in JS_ANTHROPIC_CALL.finditer(source):
        client_var = match.group(1)
        if client_var in ctx.anthropic_clients or client_var in {"client", "anthropic", "anthropicClient"}:
            line_num = _get_line_number(source, match.start())
            detected_calls.append(
                DetectedCall(
                    location=Location(
                        file=str(file_path),
                        line=line_num,
                        function=_get_function_at_line(source, line_num),
                    ),
                    provider=Provider.ANTHROPIC,
                    call_type=CallType.CHAT,
                    client_variable=client_var,
                    method_chain="messages.create",
                    function_context=_get_function_at_line(source, line_num),
                )
            )

    # Find Google calls
    for match in JS_GOOGLE_CALL.finditer(source):
        client_var = match.group(1)
        if client_var in ctx.google_clients or client_var in {"genai", "model"}:
            line_num = _get_line_number(source, match.start())
            detected_calls.append(
                DetectedCall(
                    location=Location(
                        file=str(file_path),
                        line=line_num,
                        function=_get_function_at_line(source, line_num),
                    ),
                    provider=Provider.GOOGLE,
                    call_type=CallType.CHAT,
                    client_variable=client_var,
                    method_chain="generateContent",
                    function_context=_get_function_at_line(source, line_num),
                )
            )

    # Find Mistral calls
    for match in JS_MISTRAL_CALL.finditer(source):
        client_var = match.group(1)
        if client_var in ctx.mistral_clients or client_var in {"mistral", "client"}:
            line_num = _get_line_number(source, match.start())
            detected_calls.append(
                DetectedCall(
                    location=Location(
                        file=str(file_path),
                        line=line_num,
                        function=_get_function_at_line(source, line_num),
                    ),
                    provider=Provider.MISTRAL,
                    call_type=CallType.CHAT,
                    client_variable=client_var,
                    method_chain="chat",
                    function_context=_get_function_at_line(source, line_num),
                )
            )

    return detected_calls


# =============================================================================
# UNIFIED DETECTION
# =============================================================================


def detect_ai_calls(file_path: Path) -> list[DetectedCall]:
    """
    Detect AI calls in a file based on its extension.

    Args:
        file_path: Path to source file

    Returns:
        List of detected AI calls
    """
    suffix = file_path.suffix.lower()

    if suffix == ".py":
        return detect_python_ai_calls(file_path)
    elif suffix in {".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs"}:
        return detect_js_ai_calls(file_path)

    return []
