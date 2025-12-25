"""Input source tracing and output flow tracking.

Traces where AI call inputs come from and where outputs flow to.
This enables downstream phases to:
- Connect to prompt sources
- Generate synthetic variations of inputs
- Understand which outputs need validation
"""

import ast
import re
from pathlib import Path
from typing import Optional

from flightline.discover.detect import DetectedCall
from flightline.discover.schema import (
    ConditionalType,
    ContextVariable,
    InputObservations,
    InputSource,
    Location,
    OutputObservations,
    SinkType,
    SourceType,
    UsageObservations,
    ValidationInfo,
    ValidationType,
)

# =============================================================================
# SINK DETECTION PATTERNS
# =============================================================================

# Patterns for different types of sinks
SINK_PATTERNS = {
    SinkType.HTTP_RESPONSE: [
        r"res\.send",
        r"res\.json",
        r"response\.json",
        r"return\s+jsonify",
        r"return\s+Response",
        r"return\s+\{",
        r"res\.status",
    ],
    SinkType.DB_WRITE: [
        r"\.save\(",
        r"\.create\(",
        r"\.update\(",
        r"\.insert\(",
        r"\.upsert\(",
        r"db\.",
        r"database\.",
        r"prisma\.",
        r"repo\.",
    ],
    SinkType.EMAIL_SEND: [r"sendEmail", r"mail\.", r"resend\.", r"sendgrid\.", r"postmark\.", r"email\.", r"smtp"],
    SinkType.VENDOR_DISPATCH: [
        r"dispatch",
        r"trigger",
        r"notify",
        r"webhook",
        r"api\.",
        r"client\.",
        r"service\.",
        r"callVendor",
        r"vendor",
    ],
    SinkType.ERROR_LOG: [r"Error\(", r"Exception\(", r"console\.error", r"logger\.error", r"throw\s+", r"logging\."],
    SinkType.USER_DISPLAY: [r"render", r"display", r"alert", r"toast", r"show", r"print"],
}


# =============================================================================
# SOURCE TYPE DETECTION PATTERNS
# =============================================================================

# Patterns that indicate database access
DB_PATTERNS = [
    r"\.find\s*\(",
    r"\.findOne\s*\(",
    r"\.query\s*\(",
    r"\.execute\s*\(",
    r"prisma\.",
    r"mongoose\.",
    r"sequelize\.",
    r"\.get\s*\(",  # Could be DB
    r"db\.",
    r"database\.",
    r"SELECT\s+",
    r"INSERT\s+",
]

# Patterns that indicate API calls
API_PATTERNS = [
    r"fetch\s*\(",
    r"axios\.",
    r"httpx\.",
    r"requests\.",
    r"\.get\s*\(['\"]http",
    r"\.post\s*\(",
]

# Patterns that indicate file access
FILE_PATTERNS = [
    r"readFile",
    r"readFileSync",
    r"open\s*\(",
    r"\.read\s*\(",
    r"fs\.",
    r"pathlib",
    r"Path\s*\(",
]

# Patterns that indicate config/env access
CONFIG_PATTERNS = [
    r"process\.env\.",
    r"os\.environ",
    r"getenv\s*\(",
    r"config\.",
    r"settings\.",
    r"\.env",
]

# Patterns that indicate user input
USER_INPUT_PATTERNS = [
    r"request\.",
    r"req\.",
    r"body\.",
    r"params\.",
    r"query\.",
    r"input\.",
    r"args\.",
]

# Template engine patterns
TEMPLATE_PATTERNS = {
    "handlebars": [r"Handlebars", r"\.compile\s*\(", r"\{\{"],
    "jinja": [r"jinja", r"render_template", r"\{\%", r"\{\{"],
    "fstring": [r"f['\"]", r"\.format\s*\("],
}


def _classify_source(code_hint: str) -> SourceType:
    """Classify the source type from a code snippet."""
    if not code_hint:
        return SourceType.UNKNOWN

    # Check patterns in order of specificity
    for pattern in DB_PATTERNS:
        if re.search(pattern, code_hint, re.IGNORECASE):
            return SourceType.DATABASE

    for pattern in API_PATTERNS:
        if re.search(pattern, code_hint, re.IGNORECASE):
            return SourceType.API

    for pattern in FILE_PATTERNS:
        if re.search(pattern, code_hint, re.IGNORECASE):
            return SourceType.FILE

    for pattern in CONFIG_PATTERNS:
        if re.search(pattern, code_hint, re.IGNORECASE):
            return SourceType.CONFIG

    for pattern in USER_INPUT_PATTERNS:
        if re.search(pattern, code_hint, re.IGNORECASE):
            return SourceType.USER_INPUT

    # Check for string literals
    if re.match(r'^[\'"].*[\'"]$', code_hint.strip()):
        return SourceType.INLINE

    return SourceType.VARIABLE


def _classify_sink(code_hint: str) -> Optional[SinkType]:
    """Classify a sink from a code hint."""
    for sink_type, patterns in SINK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, code_hint, re.IGNORECASE):
                return sink_type
    return None


def _detect_template_engine(code: str) -> Optional[str]:
    """Detect which template engine is being used."""
    for engine, patterns in TEMPLATE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, code):
                return engine
    return None


# =============================================================================
# PYTHON TRACING
# =============================================================================


class PythonInputTracer(ast.NodeVisitor):
    """Traces input sources in Python code around an AI call."""

    def __init__(self, source: str, call_line: int):
        self.source = source
        self.lines = source.splitlines()
        self.call_line = call_line

        # Variable assignments we've found
        self.variable_sources: dict[str, str] = {}  # var_name -> code_hint

        # Current function context
        self._in_target_function = False

    def _get_code_for_node(self, node: ast.AST) -> str:
        """Get source code for an AST node."""
        try:
            return ast.unparse(node)
        except Exception:
            return ""

    def visit_Assign(self, node: ast.Assign) -> None:
        """Track variable assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variable_sources[target.id] = self._get_code_for_node(node.value)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Track annotated assignments."""
        if isinstance(node.target, ast.Name) and node.value:
            self.variable_sources[node.target.id] = self._get_code_for_node(node.value)
        self.generic_visit(node)

    def get_variable_source(self, var_name: str) -> tuple[SourceType, Optional[str]]:
        """Get the source type and hint for a variable."""
        code_hint = self.variable_sources.get(var_name)
        if code_hint:
            source_type = _classify_source(code_hint)
            return source_type, code_hint
        return SourceType.UNKNOWN, None


def _extract_python_call_args(source: str, call_line: int) -> dict[str, str]:
    """Extract argument names and values from a Python AI call."""
    args = {}

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return args

    # Find the call on the target line
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and hasattr(node, "lineno"):
            if node.lineno == call_line:
                # Extract keyword arguments
                for kw in node.keywords:
                    if kw.arg:
                        try:
                            args[kw.arg] = ast.unparse(kw.value)
                        except Exception:
                            args[kw.arg] = "<complex>"
                break

    return args


def trace_python_inputs(
    file_path: Path,
    call: DetectedCall,
) -> InputObservations:
    """
    Trace input sources for a Python AI call.

    Args:
        file_path: Path to Python file
        call: Detected AI call

    Returns:
        InputObservations with traced sources
    """
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return InputObservations()

    obs = InputObservations()

    # Parse and trace
    try:
        tree = ast.parse(source)
        tracer = PythonInputTracer(source, call.location.line)
        tracer.visit(tree)
    except SyntaxError:
        return obs

    # Extract call arguments
    call_args = _extract_python_call_args(source, call.location.line)

    # Check for messages/prompt arguments
    if "messages" in call_args:
        messages_code = call_args["messages"]
        source_type = _classify_source(messages_code)

        # Look for system message
        if "system" in messages_code.lower():
            obs.system_prompt = InputSource(
                source_type=source_type,
                source_hint=messages_code[:200] if len(messages_code) > 200 else messages_code,
            )

        obs.messages.append(
            InputSource(
                source_type=source_type,
                source_hint=messages_code[:200] if len(messages_code) > 200 else messages_code,
            )
        )

    if "prompt" in call_args:
        prompt_code = call_args["prompt"]
        source_type = _classify_source(prompt_code)
        obs.system_prompt = InputSource(
            source_type=source_type,
            source_hint=prompt_code[:200] if len(prompt_code) > 200 else prompt_code,
        )

    # Find context variables referenced in the call
    if call.raw_args:
        # Look for variable references in the call
        for var_name, code_hint in tracer.variable_sources.items():
            if var_name in call.raw_args and var_name not in {"messages", "prompt", "model"}:
                source_type, hint = tracer.get_variable_source(var_name)
                obs.context_variables.append(
                    ContextVariable(
                        name=var_name,
                        source_type=source_type,
                        source_hint=hint,
                    )
                )

    # Detect template engine
    obs.template_engine = _detect_template_engine(source)

    return obs


def trace_python_outputs(
    file_path: Path,
    call: DetectedCall,
) -> tuple[OutputObservations, UsageObservations]:
    """
    Trace output flow for a Python AI call.

    Args:
        file_path: Path to Python file
        call: Detected AI call

    Returns:
        Tuple of (OutputObservations, UsageObservations)
    """
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return OutputObservations(), UsageObservations()

    output_obs = OutputObservations()
    usage_obs = UsageObservations()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return output_obs, usage_obs

    # Find the containing function and analyze
    call_line = call.location.line

    for node in ast.walk(tree):
        # Check for response_format in the call
        if isinstance(node, ast.Call) and hasattr(node, "lineno"):
            if node.lineno == call_line:
                for kw in node.keywords:
                    if kw.arg == "response_format":
                        output_obs.response_format_specified = True
                        output_obs.expected_format = "json"

    # Find variable assignment
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if hasattr(node.value, "lineno") and node.value.lineno == call_line:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        output_obs.assigned_to = target.id

                        # Now trace usage of this variable
                        _trace_python_variable_usage(tree, target.id, call_line, usage_obs, str(file_path))

    # Check for validation libraries
    if "pydantic" in source.lower() or "BaseModel" in source:
        output_obs.validation = ValidationInfo(
            type=ValidationType.PYDANTIC,
        )

    return output_obs, usage_obs


def _trace_python_variable_usage(
    tree: ast.AST,
    var_name: str,
    after_line: int,
    usage_obs: UsageObservations,
    file_path: str,
) -> None:
    """Trace how a variable is used after assignment."""
    for node in ast.walk(tree):
        if not hasattr(node, "lineno") or node.lineno <= after_line:
            continue

        # Check for conditionals
        if isinstance(node, ast.If):
            if _name_in_node(var_name, node.test):
                usage_obs.used_in_conditional = True
                usage_obs.conditional_location = Location(
                    file=file_path,
                    line=node.lineno,
                )
                usage_obs.conditional_type = ConditionalType.IF

        # Check for match statements (Python 3.10+)
        # Use getattr for compatibility with Python 3.9
        match_cls = getattr(ast, "Match", None)
        if match_cls is not None and isinstance(node, match_cls):
            if _name_in_node(var_name, node.subject):
                usage_obs.used_in_conditional = True
                usage_obs.conditional_location = Location(
                    file=file_path,
                    line=node.lineno,
                )
                usage_obs.conditional_type = ConditionalType.MATCH

        # Check for return statements
        if isinstance(node, ast.Return) and node.value:
            if _name_in_node(var_name, node.value):
                usage_obs.returned_from_function = True
                usage_obs.sinks.append(SinkType.HTTP_RESPONSE)

        # Check for function calls using the variable
        if isinstance(node, ast.Call):
            for arg in node.args:
                if _name_in_node(var_name, arg):
                    func_name = _get_call_func_name(node)
                    if func_name and func_name not in usage_obs.passed_to_functions:
                        usage_obs.passed_to_functions.append(func_name)

                    # Detect sink from function call
                    code_hint = ast.unparse(node)
                    sink = _classify_sink(code_hint)
                    if sink and sink not in usage_obs.sinks:
                        usage_obs.sinks.append(sink)

            for kw in node.keywords:
                if _name_in_node(var_name, kw.value):
                    func_name = _get_call_func_name(node)
                    if func_name and func_name not in usage_obs.passed_to_functions:
                        usage_obs.passed_to_functions.append(func_name)

                    # Detect sink from function call
                    code_hint = ast.unparse(node)
                    sink = _classify_sink(code_hint)
                    if sink and sink not in usage_obs.sinks:
                        usage_obs.sinks.append(sink)


def _name_in_node(var_name: str, node: ast.AST) -> bool:
    """Check if a variable name appears in an AST node."""
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id == var_name:
            return True
    return False


def _get_call_func_name(node: ast.Call) -> Optional[str]:
    """Get the function name from a Call node."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    elif isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


# =============================================================================
# JAVASCRIPT/TYPESCRIPT TRACING
# =============================================================================


def trace_js_inputs(
    file_path: Path,
    call: DetectedCall,
) -> InputObservations:
    """
    Trace input sources for a JS/TS AI call.

    Args:
        file_path: Path to JS/TS file
        call: Detected AI call

    Returns:
        InputObservations with traced sources
    """
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return InputObservations()

    obs = InputObservations()
    lines = source.splitlines()

    # Get context around the call (20 lines before and after)
    start = max(0, call.location.line - 20)
    end = min(len(lines), call.location.line + 20)
    context = "\n".join(lines[start:end])

    # Find the full call by looking for matching braces
    call_block = _extract_js_call_block(lines, call.location.line - 1)

    # Check for messages array
    messages_match = re.search(r"messages\s*:\s*\[", call_block)
    if messages_match:
        # Extract messages array
        messages_content = _extract_js_array(call_block, messages_match.end() - 1)

        source_type = _classify_source(messages_content)
        obs.messages.append(
            InputSource(
                source_type=source_type,
                source_hint=messages_content[:200] if len(messages_content) > 200 else messages_content,
            )
        )

        # Look for system role
        if "system" in messages_content.lower():
            obs.system_prompt = InputSource(
                source_type=source_type,
                source_hint="System message in messages array",
            )

    # Find variable assignments in context
    var_pattern = re.compile(r"(?:const|let|var)\s+(\w+)\s*=\s*([^;]+);", re.MULTILINE)
    for match in var_pattern.finditer(context):
        var_name = match.group(1)
        var_value = match.group(2)

        if var_name in call_block:
            source_type = _classify_source(var_value)
            obs.context_variables.append(
                ContextVariable(
                    name=var_name,
                    source_type=source_type,
                    source_hint=var_value[:100] if len(var_value) > 100 else var_value,
                )
            )

    # Detect template engine
    obs.template_engine = _detect_template_engine(source)

    return obs


def trace_js_outputs(
    file_path: Path,
    call: DetectedCall,
) -> tuple[OutputObservations, UsageObservations]:
    """
    Trace output flow for a JS/TS AI call.

    Args:
        file_path: Path to JS/TS file
        call: Detected AI call

    Returns:
        Tuple of (OutputObservations, UsageObservations)
    """
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return OutputObservations(), UsageObservations()

    output_obs = OutputObservations()
    usage_obs = UsageObservations()
    lines = source.splitlines()

    call_line_idx = call.location.line - 1
    if call_line_idx >= len(lines):
        return output_obs, usage_obs

    # Check for response_format
    call_block = _extract_js_call_block(lines, call_line_idx)
    if "response_format" in call_block:
        output_obs.response_format_specified = True
        if "json" in call_block.lower():
            output_obs.expected_format = "json"

    # Find assignment
    assign_pattern = re.compile(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:await\s+)?")

    # Check current line and a few lines before
    for i in range(max(0, call_line_idx - 2), call_line_idx + 1):
        match = assign_pattern.search(lines[i])
        if match:
            output_obs.assigned_to = match.group(1)
            break

    if output_obs.assigned_to:
        var_name = output_obs.assigned_to

        # Search after the call for usage
        for i in range(call_line_idx + 1, min(len(lines), call_line_idx + 50)):
            line = lines[i]

            if var_name not in line:
                continue

            # Check for conditionals
            if re.search(rf"\bif\s*\([^)]*{var_name}", line):
                usage_obs.used_in_conditional = True
                usage_obs.conditional_location = Location(
                    file=str(file_path),
                    line=i + 1,
                )
                usage_obs.conditional_type = ConditionalType.IF

            if re.search(rf"\bswitch\s*\([^)]*{var_name}", line):
                usage_obs.used_in_conditional = True
                usage_obs.conditional_location = Location(
                    file=str(file_path),
                    line=i + 1,
                )
                usage_obs.conditional_type = ConditionalType.SWITCH

            # Check for return
            if re.search(rf"\breturn\b.*{var_name}", line):
                usage_obs.returned_from_function = True
                if SinkType.HTTP_RESPONSE not in usage_obs.sinks:
                    usage_obs.sinks.append(SinkType.HTTP_RESPONSE)

            # Check for function calls
            func_call_match = re.search(rf"(\w+)\s*\([^)]*{var_name}", line)
            if func_call_match:
                func_name = func_call_match.group(1)
                if func_name not in {"if", "switch", "while", "for", "return"}:
                    if func_name not in usage_obs.passed_to_functions:
                        usage_obs.passed_to_functions.append(func_name)

                    # Detect sink from function call
                    sink = _classify_sink(line)
                    if sink and sink not in usage_obs.sinks:
                        usage_obs.sinks.append(sink)

    # Check for zod validation
    if "zod" in source.lower() or ".parse(" in source or ".safeParse(" in source:
        output_obs.validation = ValidationInfo(
            type=ValidationType.ZOD,
        )

    return output_obs, usage_obs


def _extract_js_call_block(lines: list[str], start_idx: int) -> str:
    """Extract a multi-line call block."""
    result = []
    brace_count = 0
    paren_count = 0
    started = False

    for i in range(start_idx, min(len(lines), start_idx + 30)):
        line = lines[i]
        result.append(line)

        for char in line:
            if char == "(":
                paren_count += 1
                started = True
            elif char == ")":
                paren_count -= 1
            elif char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1

        if started and paren_count == 0 and brace_count == 0:
            break

    return "\n".join(result)


def _extract_js_array(text: str, start_pos: int) -> str:
    """Extract array content starting from [."""
    bracket_count = 0
    result = []

    for i in range(start_pos, len(text)):
        char = text[i]
        result.append(char)

        if char == "[":
            bracket_count += 1
        elif char == "]":
            bracket_count -= 1
            if bracket_count == 0:
                break

    return "".join(result)


# =============================================================================
# UNIFIED TRACING
# =============================================================================


def trace_inputs(file_path: Path, call: DetectedCall) -> InputObservations:
    """Trace inputs for any supported language."""
    suffix = file_path.suffix.lower()

    if suffix == ".py":
        return trace_python_inputs(file_path, call)
    elif suffix in {".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs"}:
        return trace_js_inputs(file_path, call)

    return InputObservations()


def trace_outputs(
    file_path: Path,
    call: DetectedCall,
) -> tuple[OutputObservations, UsageObservations]:
    """Trace outputs for any supported language."""
    suffix = file_path.suffix.lower()

    if suffix == ".py":
        return trace_python_outputs(file_path, call)
    elif suffix in {".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs"}:
        return trace_js_outputs(file_path, call)

    return OutputObservations(), UsageObservations()
