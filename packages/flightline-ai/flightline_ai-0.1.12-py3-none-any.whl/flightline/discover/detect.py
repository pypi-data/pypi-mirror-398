"""AI call detection for Python and JavaScript/TypeScript.

Uses Python's built-in ast module for Python files and regex for JS/TS.
Focus is on high precision - we want few false positives.
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set

from flightline.discover.schema import CallType, Location, Provider

# =============================================================================
# DETECTION RESULT
# =============================================================================


@dataclass
class DetectedCall:
    """A potential AI call site found in code."""

    location: Location
    provider: Provider
    call_type: CallType
    method_chain: str
    raw_args: str
    function_context: Optional[str] = None


# =============================================================================
# PYTHON DETECTION (AST-based)
# =============================================================================


class PythonAiCallVisitor(ast.NodeVisitor):
    """AST visitor to find AI SDK calls in Python files."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.openai_client_vars: Set[str] = set()
        self.anthropic_client_vars: Set[str] = set()
        self.google_client_vars: Set[str] = set()
        self.mistral_client_vars: Set[str] = set()
        self.openrouter_client_vars: Set[str] = set()

        # Track detected calls
        self.detected_calls: List[DetectedCall] = []

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
        """Track top-level imports."""
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Track from X import Y."""
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track class context."""
        old_class = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track function context."""
        old_func = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track async function context."""
        old_func = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_func

    def visit_Assign(self, node: ast.Assign) -> None:
        """Track client assignments like client = OpenAI()."""
        if isinstance(node.value, ast.Call):
            # client = OpenAI(...)
            if isinstance(node.value.func, ast.Name):
                class_name = node.value.func.id
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        if class_name == "OpenAI":
                            # Check for OpenRouter base_url
                            is_openrouter = False
                            for kw in node.value.keywords:
                                if kw.arg == "base_url" and isinstance(kw.value, ast.Constant):
                                    if "openrouter.ai" in str(kw.value.value):
                                        is_openrouter = True
                                        break
                            if is_openrouter:
                                self.openrouter_client_vars.add(var_name)
                            else:
                                self.openai_client_vars.add(var_name)
                        elif class_name == "Anthropic":
                            self.anthropic_client_vars.add(var_name)
                        elif class_name == "MistralClient":
                            self.mistral_client_vars.add(var_name)

            # client = google.generativeai.GenerativeModel(...)
            elif isinstance(node.value.func, ast.Attribute):
                try:
                    chain = self._get_attr_chain(node.value.func)
                    if "GenerativeModel" in chain:
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                self.google_client_vars.add(target.id)
                except Exception:
                    pass

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Detect AI call sites."""
        if isinstance(node.func, ast.Attribute):
            try:
                chain = self._get_attr_chain(node.func)
                method_name = node.func.attr

                # 1. OpenAI Chat Completions or OpenRouter
                # client.chat.completions.create(...)
                if "chat" in chain and "completions" in chain and method_name == "create":
                    # Check if the root variable is a known OpenAI or OpenRouter client
                    root = self._get_attr_root(node.func)
                    if root in self.openrouter_client_vars:
                        self._add_call(node, Provider.OPENROUTER, CallType.CHAT, chain)
                    elif root in self.openai_client_vars or root == "client":
                        # Also check for inline base_url override
                        is_openrouter = False
                        for kw in node.keywords:
                            if kw.arg == "base_url" and isinstance(kw.value, ast.Constant):
                                if "openrouter.ai" in str(kw.value.value):
                                    is_openrouter = True
                                    break
                        if is_openrouter:
                            self._add_call(node, Provider.OPENROUTER, CallType.CHAT, chain)
                        else:
                            self._add_call(node, Provider.OPENAI, CallType.CHAT, chain)

                # 2. Anthropic Messages
                # client.messages.create(...)
                elif "messages" in chain and method_name == "create":
                    root = self._get_attr_root(node.func)
                    if root in self.anthropic_client_vars or root == "client":
                        self._add_call(node, Provider.ANTHROPIC, CallType.CHAT, chain)

                # 3. Google Gemini
                # model.generate_content(...)
                elif method_name == "generate_content":
                    root = self._get_attr_root(node.func)
                    if root in self.google_client_vars or "model" in root:
                        self._add_call(node, Provider.GOOGLE, CallType.CHAT, chain)

            except Exception:
                pass

        self.generic_visit(node)

    def _get_attr_chain(self, node: ast.Attribute) -> List[str]:
        """Convert a nested attribute (a.b.c) to a list of strings."""
        parts = [node.attr]
        curr = node.value
        while isinstance(curr, ast.Attribute):
            parts.append(curr.attr)
            curr = curr.value
        if isinstance(curr, ast.Name):
            parts.append(curr.id)
        return parts[::-1]

    def _get_attr_root(self, node: ast.Attribute) -> str:
        """Get the root variable name of an attribute chain (client in client.a.b)."""
        curr = node.value
        while isinstance(curr, ast.Attribute):
            curr = curr.value
        if isinstance(curr, ast.Name):
            return curr.id
        return ""

    def _add_call(self, node: ast.Call, provider: Provider, call_type: CallType, chain: List[str]):
        """Helper to create and store a DetectedCall."""
        try:
            raw_args = ast.unparse(node)
        except Exception:
            raw_args = "args_unparse_failed"

        self.detected_calls.append(
            DetectedCall(
                location=self._get_location(node),
                provider=provider,
                call_type=call_type,
                method_chain=".".join(chain),
                raw_args=raw_args,
                function_context=self._current_function,
            )
        )


def detect_python_ai_calls(file_path: Path) -> List[DetectedCall]:
    """
    Detect AI calls in a Python file.

    Args:
        file_path: Path to Python source file

    Returns:
        List of detected calls
    """
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return []

    visitor = PythonAiCallVisitor(file_path)
    visitor.visit(tree)
    return visitor.detected_calls


# =============================================================================
# JAVASCRIPT/TYPESCRIPT DETECTION (Regex-based)
# =============================================================================

# Simple regex patterns for common JS AI SDK patterns
JS_IMPORT_PATTERNS = [
    # OpenAI
    r"""(?:import\s+(?:(\w+)|{[^}]*})\s+from\s+['"]openai['"]|"""
    r"""const\s+(\w+)\s*=\s*require\(['"]openai['"]\))""",
    # Anthropic
    r"""(?:import\s+(?:(\w+)|{[^}]*})\s+from\s+['"]@anthropic-ai/sdk['"]|"""
    r"""const\s+(\w+)\s*=\s*require\(['"]@anthropic-ai/sdk['"]\))""",
    # Google
    r"""(?:import\s+{[^}]*GoogleGenerativeAI[^}]*}\s+from\s+['"]@google/generative-ai['"]|"""
    r"""const\s+{[^}]*GoogleGenerativeAI[^}]*}\s*=\s*require\(['"]@google/generative-ai['"]\))""",
    # Mistral
    r"""(?:import\s+(\w+)\s+from\s+['"]@mistralai/mistralai['"]|"""
    r"""const\s+(\w+)\s*=\s*require\(['"]@mistralai/mistralai['"]\))""",
]

# Client instantiation patterns
JS_OPENAI_CLIENT = re.compile(r"""(?:const|let|var)\s+(\w+)\s*=\s*new\s+OpenAI\s*\(\s*({[^}]*})?\s*\)""", re.MULTILINE)
JS_ANTHROPIC_CLIENT = re.compile(r"""(?:const|let|var)\s+(\w+)\s*=\s*new\s+Anthropic\s*\(""", re.MULTILINE)
JS_GOOGLE_CLIENT = re.compile(r"""(?:const|let|var)\s+(\w+)\s*=\s*new\s+GoogleGenerativeAI\s*\(""", re.MULTILINE)
JS_MISTRAL_CLIENT = re.compile(r"""(?:const|let|var)\s+(\w+)\s*=\s*new\s+MistralClient\s*\(""", re.MULTILINE)

# Call site patterns
JS_CHAT_CALL = re.compile(r"""\.chat\.completions\.create\s*\(""")
JS_MESSAGES_CALL = re.compile(r"""\.messages\.create\s*\(""")
JS_GOOGLE_GENERATE = re.compile(r"""\.generateContent\s*\(""")


@dataclass
class JSDetectionContext:
    """Context for JS/TS detection."""

    file_path: Path
    source: str
    lines: List[str]

    # Track client variables
    openai_clients: Set[str] = field(default_factory=set)
    anthropic_clients: Set[str] = field(default_factory=set)
    google_clients: Set[str] = field(default_factory=set)
    mistral_clients: Set[str] = field(default_factory=set)
    openrouter_clients: Set[str] = field(default_factory=set)


def _get_js_function_context(lines: List[str], line_idx: int) -> Optional[str]:
    """Look backwards from a line to find the containing function name."""
    func_pattern = re.compile(
        r"""(?:async\s+)?(?:function\s+(\w+)|(\w+)\s*[=:]\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>|\w+\s*=>))""",
        re.MULTILINE,
    )

    # Search backwards up to 50 lines
    for i in range(line_idx, max(-1, line_idx - 50), -1):
        line = lines[i]
        match = func_pattern.search(line)
        if match:
            return match.group(1) or match.group(2)

    return None


def detect_js_ai_calls(file_path: Path) -> List[DetectedCall]:
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

    detected_calls: List[DetectedCall] = []

    # Find imports
    for pattern in JS_IMPORT_PATTERNS:
        # Just use these to set context if needed, but instantiation is more reliable
        pass

    # Find client instantiations
    for match in JS_OPENAI_CLIENT.finditer(source):
        var_name = match.group(1)
        config = match.group(2)
        if config and "openrouter.ai" in config:
            ctx.openrouter_clients.add(var_name)
        else:
            ctx.openai_clients.add(var_name)

    for match in JS_ANTHROPIC_CLIENT.finditer(source):
        ctx.anthropic_clients.add(match.group(1))

    for match in JS_MISTRAL_CLIENT.finditer(source):
        ctx.mistral_clients.add(match.group(1))

    # Google model instantiation is a bit different
    # const model = genAI.getGenerativeModel({ model: "gemini-pro" });
    google_model_pattern = re.compile(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:\w+)\.getGenerativeModel\s*\(")
    for match in google_model_pattern.finditer(source):
        ctx.google_clients.add(match.group(1))

    # Find call sites by scanning lines
    for i, line in enumerate(ctx.lines):
        line_num = i + 1

        # 1. OpenAI / OpenRouter
        if ".chat.completions.create(" in line:
            var_match = re.search(r"(\w+)\.chat\.completions\.create", line)
            if var_match:
                client_var = var_match.group(1)
                provider = Provider.OPENAI
                if client_var in ctx.openrouter_clients:
                    provider = Provider.OPENROUTER

                detected_calls.append(
                    DetectedCall(
                        location=Location(
                            file=str(file_path),
                            line=line_num,
                            function=_get_js_function_context(ctx.lines, i),
                        ),
                        provider=provider,
                        call_type=CallType.CHAT,
                        method_chain=f"{client_var}.chat.completions.create",
                        raw_args=_extract_js_args(ctx.lines, i),
                        function_context=_get_js_function_context(ctx.lines, i),
                    )
                )

        # 2. Anthropic
        elif ".messages.create(" in line:
            var_match = re.search(r"(\w+)\.messages\.create", line)
            if var_match:
                client_var = var_match.group(1)
                detected_calls.append(
                    DetectedCall(
                        location=Location(
                            file=str(file_path),
                            line=line_num,
                            function=_get_js_function_context(ctx.lines, i),
                        ),
                        provider=Provider.ANTHROPIC,
                        call_type=CallType.CHAT,
                        method_chain=f"{client_var}.messages.create",
                        raw_args=_extract_js_args(ctx.lines, i),
                        function_context=_get_js_function_context(ctx.lines, i),
                    )
                )

        # 3. Google Gemini
        elif ".generateContent(" in line:
            var_match = re.search(r"(\w+)\.generateContent", line)
            if var_match:
                model_var = var_match.group(1)
                detected_calls.append(
                    DetectedCall(
                        location=Location(
                            file=str(file_path),
                            line=line_num,
                            function=_get_js_function_context(ctx.lines, i),
                        ),
                        provider=Provider.GOOGLE,
                        call_type=CallType.CHAT,
                        method_chain=f"{model_var}.generateContent",
                        raw_args=_extract_js_args(ctx.lines, i),
                        function_context=_get_js_function_context(ctx.lines, i),
                    )
                )

    return detected_calls


def _extract_js_args(lines: List[str], line_idx: int) -> str:
    """Extract arguments from a JS call, potentially multi-line."""
    block = []
    open_brackets = 0
    started = False

    for i in range(line_idx, min(line_idx + 20, len(lines))):
        line = lines[i]
        block.append(line.strip())

        if "(" in line:
            open_brackets += line.count("(")
            started = True
        if ")" in line:
            open_brackets -= line.count(")")

        if started and open_brackets <= 0:
            break

    return " ".join(block)


# =============================================================================
# PUBLIC API
# =============================================================================


def detect_ai_calls(file_path: Path) -> List[DetectedCall]:
    """
    Orchestrate AI call detection based on file type.

    Args:
        file_path: Path to source file

    Returns:
        List of detected calls
    """
    ext = file_path.suffix.lower()
    if ext == ".py":
        return detect_python_ai_calls(file_path)
    elif ext in (".js", ".jsx", ".ts", ".tsx"):
        return detect_js_ai_calls(file_path)
    return []
