"""Input source tracing and output flow tracking.

Traces where AI call inputs come from and where outputs flow to.
This enables downstream phases to:
- Connect to prompt sources
- Generate synthetic variations of inputs
- Understand which outputs need validation
"""

import ast
import re
from typing import Dict, List, Optional, Tuple

from flightline.discover.detect import DetectedCall
from flightline.discover.schema import (
    ConditionalType,
    ContextVariable,
    ExtractionConfidence,
    InputObservations,
    InputSource,
    OutputObservations,
    SinkType,
    SourceType,
    UsageObservations,
    ValidationInfo,
    ValidationType,
)


def trace_inputs(call: DetectedCall, file_content: str) -> InputObservations:
    """Trace input sources for an AI call.

    Combines AST analysis for Python and regex-based tracing for JS/TS.
    """
    if call.location.file.endswith(".py"):
        return trace_python_inputs(call, file_content)
    else:
        return trace_js_inputs(call, file_content)


def trace_outputs(call: DetectedCall, file_content: str) -> Tuple[OutputObservations, UsageObservations]:
    """Trace where the AI call output flows."""
    if call.location.file.endswith(".py"):
        return trace_python_outputs(call, file_content)
    else:
        return trace_js_outputs(call, file_content)


# =============================================================================
# PYTHON TRACING (AST-based)
# =============================================================================


class PythonInputTracer(ast.NodeVisitor):
    """Traces input sources in Python code around an AI call."""

    def __init__(self, source: str, call_line: int):
        self.source = source
        self.lines = source.splitlines()
        self.call_line = call_line

        # Variable assignments we've found
        self.variable_sources: Dict[str, str] = {}  # var_name -> code_hint
        self.variable_types: Dict[str, str] = {}  # var_name -> type annotation
        self.variable_type_defs: Dict[str, str] = {}  # var_name -> full type definition

        # Pydantic/dataclass model definitions
        self.model_definitions: Dict[str, str] = {}  # model_name -> definition

        # Current function context
        self._in_target_function = False
        self._current_function_params: Dict[str, str] = {}  # param_name -> type

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Capture Pydantic model or dataclass definitions."""
        # Check if it looks like a model
        is_model = any(
            isinstance(base, ast.Name) and base.id in ("BaseModel", "dataclass") for base in node.bases
        ) or any(isinstance(decorator, ast.Name) and decorator.id == "dataclass" for decorator in node.decorator_list)

        if is_model:
            try:
                self.model_definitions[node.name] = ast.unparse(node)
            except Exception:
                pass

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Capture function parameters and types."""
        # Check if this function contains our target call line
        if node.lineno <= self.call_line <= (node.end_lineno or node.lineno):
            self._in_target_function = True
            for arg in node.args.args:
                if arg.annotation:
                    try:
                        self._current_function_params[arg.arg] = ast.unparse(arg.annotation)
                    except Exception:
                        pass
            self.generic_visit(node)
            self._in_target_function = False
        else:
            self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Capture variable assignments before the call."""
        if hasattr(node, "lineno") and node.lineno < self.call_line:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        self.variable_sources[target.id] = ast.unparse(node.value)
                    except Exception:
                        pass
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Capture annotated assignments (types)."""
        if hasattr(node, "lineno") and node.lineno < self.call_line:
            if isinstance(node.target, ast.Name):
                var_name = node.target.id
                try:
                    self.variable_types[var_name] = ast.unparse(node.annotation)
                    if node.value:
                        self.variable_sources[var_name] = ast.unparse(node.value)
                except Exception:
                    pass
        self.generic_visit(node)

    def get_variable_source(self, var_name: str) -> tuple:
        """Determine SourceType and hint for a variable."""
        # 1. Check local assignments
        if var_name in self.variable_sources:
            source_code = self.variable_sources[var_name]

            if "os.getenv" in source_code or "os.environ" in source_code:
                return SourceType.CONFIG, source_code
            if "request." in source_code or "json()" in source_code:
                return SourceType.USER_INPUT, source_code
            if "db." in source_code or "session.query" in source_code:
                return SourceType.DATABASE, source_code
            if "requests.get" in source_code or "httpx." in source_code:
                return SourceType.API, source_code

            return SourceType.VARIABLE, source_code

        # 2. Check function parameters
        if var_name in self._current_function_params:
            return SourceType.USER_INPUT, f"function parameter: {var_name}"

        return SourceType.UNKNOWN, None

    def get_variable_type(self, var_name: str) -> tuple:
        """Determine type reference and definition for a variable."""
        type_ref = self.variable_types.get(var_name)
        if not type_ref:
            type_ref = self._current_function_params.get(var_name)

        if type_ref:
            # If it's a known model name, provide the definition
            type_def = self.model_definitions.get(type_ref)
            return type_ref, type_def

        return None, None


def trace_python_inputs(call: DetectedCall, source: str) -> InputObservations:
    """Trace inputs for a Python AI call using AST."""
    obs = InputObservations()

    try:
        tree = ast.parse(source)
        tracer = PythonInputTracer(source, call.location.line)
        tracer.visit(tree)
    except SyntaxError:
        return obs

    # Extract call arguments
    args = _extract_python_call_args(source, call.location.line)

    # 1. System Prompt
    inline_prompt = _extract_inline_prompt_content_python(source, call.location.line)
    if inline_prompt:
        obs.system_prompt = InputSource(
            source_type=SourceType.INLINE,
            inline_content=inline_prompt,
            confidence=ExtractionConfidence.HIGH,
        )
    elif "messages" in args:
        msg_val = args["messages"]
        # If messages is a variable, trace it
        if re.match(r"^[a-zA-Z_]\w*$", msg_val):
            src_type, hint = tracer.get_variable_source(msg_val)
            obs.system_prompt = InputSource(
                source_type=src_type,
                source_hint=hint,
                variable_name=msg_val,
                confidence=ExtractionConfidence.MEDIUM if hint else ExtractionConfidence.LOW,
            )

    # 2. Context Variables (scan args for variables)
    for arg_name, arg_val in args.items():
        if arg_name in ("messages", "prompt", "input"):
            # Find all variable-like tokens in the argument value
            vars_found = re.findall(r"\b([a-zA-Z_]\w*)\b", arg_val)
            for v in vars_found:
                # Skip keywords and common constants
                if v in ("self", "cls", "None", "True", "False", "List", "Dict", "Optional"):
                    continue

                src_type, hint = tracer.get_variable_source(v)
                if src_type != SourceType.UNKNOWN:
                    type_ref, type_def = tracer.get_variable_type(v)
                    obs.context_variables.append(
                        ContextVariable(
                            name=v,
                            source_type=src_type,
                            source_hint=hint,
                            type_reference=type_ref,
                            type_definition=type_def,
                            confidence=ExtractionConfidence.MEDIUM,
                        )
                    )

    # 3. Template Engine
    if "{{" in source or "{% " in source:
        obs.template_engine = "jinja"
    elif 'f"' in source or "f'" in source:
        obs.template_engine = "fstring"

    return obs


def _extract_python_call_args(source: str, call_line: int) -> Dict[str, str]:
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
                            args[kw.arg] = "complex_expression"
                # Extract positional arguments (if any)
                for i, arg in enumerate(node.args):
                    try:
                        args[f"pos_{i}"] = ast.unparse(arg)
                    except Exception:
                        args[f"pos_{i}"] = "complex_expression"
                break

    return args


def _extract_inline_prompt_content_python(source: str, call_line: int) -> Optional[str]:
    """Extract string content from messages if they are defined inline."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and hasattr(node, "lineno"):
            if node.lineno == call_line:
                # Look for messages argument
                for kw in node.keywords:
                    if kw.arg == "messages":
                        # Try to extract string literals from the messages
                        return _extract_strings_from_messages(kw.value)
                break

    return None


def _extract_strings_from_messages(node: ast.AST) -> Optional[str]:
    """Extract string content from a messages list."""
    strings = []

    if isinstance(node, ast.List):
        for elem in node.elts:
            if isinstance(elem, ast.Dict):
                # Look for 'content' key
                for i, key in enumerate(elem.keys):
                    if isinstance(key, ast.Constant) and key.value == "content":
                        value = elem.values[i]
                        if isinstance(value, ast.Constant) and isinstance(value.value, str):
                            strings.append(value.value)
                        elif isinstance(value, ast.JoinedStr):
                            # f-string - extract the static parts
                            for part in value.values:
                                if isinstance(part, ast.Constant):
                                    strings.append(str(part.value))

    if strings:
        combined = "\n---\n".join(strings)
        # Truncate if too long
        if len(combined) > 500:
            return combined[:500] + "..."
        return combined

    return None


def _extract_validation_schema_python(source: str, var_name: str, after_line: int) -> Optional[Tuple[str, str, str]]:
    """Find validation schema applied to a variable after assignment.

    Returns tuple of (schema_type, schema_name, schema_definition) or None.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    # Search for Pydantic validation: Model.model_validate(var) or Model(**var)
    for node in ast.walk(tree):
        if not hasattr(node, "lineno") or node.lineno <= after_line:
            continue

        # Look for model_validate(var) or parse_obj(var)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("model_validate", "parse_obj", "validate"):
                if node.args and isinstance(node.args[0], ast.Name) and node.args[0].id == var_name:
                    if isinstance(node.func.value, ast.Name):
                        model_name = node.func.value.id
                        return "pydantic", model_name, f"Used for validation of {var_name}"

        # Look for Model(**var)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            for kw in node.keywords:
                if kw.arg is None and isinstance(kw.value, ast.Name) and kw.value.id == var_name:
                    model_name = node.func.id
                    if model_name != "dict":  # Filter out dict(**var)
                        return "pydantic", model_name, f"Used for validation of {var_name}"

    return None


def trace_python_outputs(call: DetectedCall, source: str) -> Tuple[OutputObservations, UsageObservations]:
    """Trace output usage for a Python AI call."""
    out = OutputObservations()
    usage = UsageObservations()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return out, usage

    # 1. Find assignment
    var_name = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and hasattr(node.value, "lineno") and node.value.lineno == call.location.line:
            if node.targets and isinstance(node.targets[0], ast.Name):
                var_name = node.targets[0].id
                out.assigned_to = var_name
                break
        elif (
            isinstance(node, ast.AnnAssign)
            and hasattr(node.value, "lineno")
            and node.value
            and node.value.lineno == call.location.line
        ):
            if isinstance(node.target, ast.Name):
                var_name = node.target.id
                out.assigned_to = var_name
                break

    if not var_name:
        return out, usage

    # 2. Look for validation
    val_info = _extract_validation_schema_python(source, var_name, call.location.line)
    if val_info:
        v_type, v_name, v_def = val_info
        out.validation = ValidationInfo(
            type=ValidationType(v_type),
            schema_name=v_name,
            schema_definition=v_def,
            confidence=ExtractionConfidence.MEDIUM,
        )

    # 3. Look for usage (sinks and conditionals)
    for node in ast.walk(tree):
        if not hasattr(node, "lineno") or node.lineno <= call.location.line:
            continue

        # Used in if/while
        if isinstance(node, (ast.If, ast.While)):
            try:
                if var_name in ast.unparse(node.test):
                    usage.used_in_conditional = True
                    usage.conditional_type = ConditionalType.IF if isinstance(node, ast.If) else ConditionalType.MATCH
                    usage.sinks.append(SinkType.CONDITIONAL)
            except Exception:
                pass

        # Returned
        if isinstance(node, ast.Return):
            try:
                if node.value and var_name in ast.unparse(node.value):
                    usage.returned_from_function = True
            except Exception:
                pass

        # Saved to DB or API (heuristic based on method names)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            try:
                call_str = ast.unparse(node)
                if var_name in call_str:
                    if any(
                        word in node.func.attr.lower()
                        for word in ("save", "update", "insert", "create", "db", "session")
                    ):
                        usage.sinks.append(SinkType.DATABASE)
                    if any(word in node.func.attr.lower() for word in ("send", "post", "dispatch", "emit", "publish")):
                        usage.sinks.append(SinkType.API)
                    if any(word in node.func.attr.lower() for word in ("print", "display", "render", "show")):
                        usage.sinks.append(SinkType.UI)
            except Exception:
                pass

    usage.sinks = list(set(usage.sinks))
    return out, usage


# =============================================================================
# JS/TS TRACING (Regex-based)
# =============================================================================


def trace_js_inputs(call: DetectedCall, source: str) -> InputObservations:
    """Trace inputs for a JS/TS AI call using regex."""
    obs = InputObservations()
    lines = source.splitlines()

    # 1. Inline Prompt Extraction
    # Look for the call block to find inline content
    call_block = _extract_js_call_block(lines, call.location.line - 1)
    inline_content = _extract_inline_prompt_content_js(call_block)
    if inline_content:
        obs.system_prompt = InputSource(
            source_type=SourceType.INLINE,
            inline_content=inline_content,
            confidence=ExtractionConfidence.HIGH,
        )

    # 2. Context Variables (look for variables used in call block)
    # Simple regex to find variables like ${var} or content: var
    potential_vars = re.findall(r"\$\{([a-zA-Z_]\w*)\}", call_block)
    potential_vars += re.findall(r"content:\s*([a-zA-Z_]\w*)", call_block)

    for v in set(potential_vars):
        if v in ("item", "msg", "m", "content", "role"):
            continue

        # Trace variable source
        src_type, hint = _trace_js_variable_source(source, v, call.location.line)
        if src_type != SourceType.UNKNOWN:
            # Trace type
            type_name, type_def = _trace_js_type(source, v)
            obs.context_variables.append(
                ContextVariable(
                    name=v,
                    source_type=src_type,
                    source_hint=hint,
                    type_reference=type_name,
                    type_definition=type_def,
                    confidence=ExtractionConfidence.MEDIUM if type_name else ExtractionConfidence.LOW,
                )
            )

    return obs


def _extract_inline_prompt_content_js(call_block: str) -> Optional[str]:
    """Extract string literals from a JS call block."""
    # Match strings in "", '', or ``
    # This is a bit naive but works for common cases
    strings = re.findall(
        r'"([^"]{10,})"'  # Double quoted, min 10 chars
        r"|'([^']{10,})'"  # Single quoted
        r"|`([^`]{10,})`",  # Template literal
        call_block,
    )

    results = []
    for match in strings:
        content = match[0] or match[1] or match[2]
        if content and len(content) > 20:  # Only long strings
            results.append(content)

    if results:
        combined = "\n---\n".join(results)
        return combined[:500] + "..." if len(combined) > 500 else combined

    return None


def _trace_js_variable_source(source: str, var_name: str, before_line: int) -> Tuple[SourceType, Optional[str]]:
    """Determine SourceType for a JS variable."""
    # Look for assignment before the call
    lines = source.splitlines()[:before_line]
    context = "\n".join(lines)

    # Pattern for assignment: const var = ...
    assign_match = re.search(rf"(?:const|let|var)\s+{re.escape(var_name)}\s*=\s*([^;\n]+)", context, re.MULTILINE)
    if assign_match:
        val = assign_match.group(1).lower()
        if "process.env" in val:
            return SourceType.CONFIG, assign_match.group(0)
        if "req." in val or "params" in val or "query" in val:
            return SourceType.USER_INPUT, assign_match.group(0)
        if "db." in val or "prisma." in val or "select" in val:
            return SourceType.DATABASE, assign_match.group(0)
        if "fetch" in val or "axios" in val:
            return SourceType.API, assign_match.group(0)

        return SourceType.VARIABLE, assign_match.group(0)

    # Check function parameters
    if re.search(rf"function\s*\w*\s*\([^)]*\b{re.escape(var_name)}\b", context):
        return SourceType.USER_INPUT, f"function parameter: {var_name}"

    return SourceType.UNKNOWN, None


def _trace_js_type(source: str, var_name: str) -> Tuple[Optional[str], Optional[str]]:
    """Try to find TypeScript type for a variable."""
    # 1. Look for inline type: const v: Type = ...
    type_match = re.search(
        rf"(?:const|let|var)\s+{re.escape(var_name)}\s*:\s*([A-Z]\w*(?:<[^>]+>)?)",
        source,
    )
    if type_match:
        type_name = type_match.group(1)
        # 2. Look for interface/type definition
        interface_match = re.search(
            rf"interface\s+{re.escape(type_name)}\s*\{{([^}}]+)\}}", source, re.MULTILINE | re.DOTALL
        )
        if interface_match:
            return type_name, interface_match.group(0)
        return type_name, None

    return None, None


def _extract_zod_schema_name(source: str, var_name: str, after_line: int) -> Optional[Tuple[str, Optional[str]]]:
    """Find Zod schema used to parse a variable."""
    # Look for schema.parse(var) or schema.safeParse(var)
    lines = source.splitlines()[after_line:]
    context = "\n".join(lines)

    parse_match = re.search(r"(\w+)\.(?:safeP|p)arse\s*\(\s*" + re.escape(var_name) + r"\s*\)", context)
    if parse_match:
        schema_name = parse_match.group(1)
        # Try to find schema definition
        schema_def_match = re.search(
            rf"(?:const|let|var)\s+{re.escape(schema_name)}\s*=\s*(z\.[^;]+);", context, re.MULTILINE | re.DOTALL
        )
        return schema_name, schema_def_match.group(0) if schema_def_match else None

    return None


def trace_js_outputs(call: DetectedCall, source: str) -> Tuple[OutputObservations, UsageObservations]:
    """Trace output usage for a JS/TS AI call."""
    out = OutputObservations()
    usage = UsageObservations()

    lines = source.splitlines()
    call_idx = call.location.line - 1

    # 1. Find assignment: const result = await ...
    if call_idx >= 0:
        line = lines[call_idx]
        assign_match = re.search(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:await\s+)?", line)
        if assign_match:
            var_name = assign_match.group(1)
            out.assigned_to = var_name

            # 2. Look for validation (Zod)
            zod_info = _extract_zod_schema_name(source, var_name, call.location.line)
            if zod_info:
                s_name, s_def = zod_info
                out.validation = ValidationInfo(
                    type=ValidationType.ZOD,
                    schema_name=s_name,
                    schema_definition=s_def,
                    confidence=ExtractionConfidence.MEDIUM,
                )

            # 3. Look for usage in subsequent lines
            after_context = "\n".join(lines[call.location.line : call.location.line + 50])

            # Used in if/switch
            if re.search(rf"if\s*\(\s*[^)]*{re.escape(var_name)}", after_context):
                usage.used_in_conditional = True
                usage.conditional_type = ConditionalType.IF
                usage.sinks.append(SinkType.CONDITIONAL)

            # Sinks
            if re.search(rf"res\.(?:send|json|render)\s*\([^)]*{re.escape(var_name)}", after_context):
                usage.sinks.append(SinkType.UI)
            if re.search(
                rf"(?:db|prisma|repo)\.\w*\.(?:create|update|save)\s*\([^)]*{re.escape(var_name)}",
                after_context,
            ):
                usage.sinks.append(SinkType.DATABASE)

    usage.sinks = list(set(usage.sinks))
    return out, usage


def _extract_js_call_block(lines: List[str], start_idx: int) -> str:
    """Extract a full multi-line JS call block starting from start_idx."""
    block = []
    bracket_count = 0
    started = False

    for i in range(start_idx, min(start_idx + 50, len(lines))):
        line = lines[i]
        block.append(line)

        if "(" in line:
            bracket_count += line.count("(")
            started = True
        if ")" in line:
            bracket_count -= line.count(")")

        if started and bracket_count <= 0:
            break

    return "\n".join(block)
