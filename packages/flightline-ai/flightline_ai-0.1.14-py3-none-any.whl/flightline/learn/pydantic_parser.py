"""Pydantic model parser - extracts schema from Python files.

This module parses Pydantic models (v1 and v2) into profile schemas
using Python's AST without needing an LLM.
"""

import ast
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Common PII field name patterns (same as TypeScript parser)
PII_PATTERNS = [
    r"email",
    r"phone",
    r"address",
    r"street",
    r"city",
    r"zip",
    r"postal",
    r"ssn",
    r"social.*security",
    r"passport",
    r"license",
    r"credit.*card",
    r"card.*number",
    r"cvv",
    r"name",
    r"first.*name",
    r"last.*name",
    r"full.*name",
    r"birth.*date",
    r"dob",
    r"ip.*address",
    r"latitude",
    r"longitude",
    r"location",
]

# Python type mapping to simplified types
PYTHON_TYPE_MAP = {
    "str": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "datetime": "date",
    "date": "date",
    "time": "time",
    "Decimal": "number",
    "UUID": "string",
    "Any": "any",
    "None": "null",
    "bytes": "binary",
    "dict": "object",
    "Dict": "object",
    "list": "array",
    "List": "array",
    "set": "array",
    "Set": "array",
    "tuple": "array",
    "Tuple": "array",
}


@dataclass
class ParsedField:
    """A parsed Pydantic field."""

    name: str
    type_str: str
    optional: bool = False
    is_list: bool = False
    default: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ParsedModel:
    """A parsed Pydantic model."""

    name: str
    fields: List[ParsedField] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    docstring: Optional[str] = None


def _is_pii_field(field_name: str) -> bool:
    """Check if a field name matches common PII patterns."""
    name_lower = field_name.lower()
    for pattern in PII_PATTERNS:
        if re.search(pattern, name_lower):
            return True
    return False


def _get_type_string(node: ast.expr) -> str:
    """Convert an AST type annotation to a string."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Constant):
        return str(node.value)
    elif isinstance(node, ast.Subscript):
        # Handle generic types like List[str], Optional[int]
        if isinstance(node.value, ast.Name):
            base = node.value.id
            if isinstance(node.slice, ast.Name):
                inner = node.slice.id
            elif isinstance(node.slice, ast.Subscript):
                inner = _get_type_string(node.slice)
            elif isinstance(node.slice, ast.Tuple):
                inner = ", ".join(_get_type_string(e) for e in node.slice.elts)
            else:
                inner = _get_type_string(node.slice)
            return f"{base}[{inner}]"
        return "complex"
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        # Handle union types: str | None
        left = _get_type_string(node.left)
        right = _get_type_string(node.right)
        return f"{left} | {right}"
    elif isinstance(node, ast.Attribute):
        # Handle module.Type
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        return node.attr
    else:
        return "unknown"


def _is_optional_type(type_str: str) -> bool:
    """Check if a type string represents an optional type."""
    type_lower = type_str.lower()
    return (
        type_str.startswith("Optional[")
        or " | none" in type_lower
        or "none | " in type_lower
        or type_lower == "none"
    )


def _is_list_type(type_str: str) -> bool:
    """Check if a type string represents a list type."""
    return type_str.startswith(("List[", "list[", "Sequence[", "Set[", "set["))


def _normalize_type(py_type: str) -> str:
    """Normalize a Python type to a simpler type string."""
    py_type = py_type.strip()

    # Handle Optional types
    if py_type.startswith("Optional["):
        inner = py_type[9:-1]  # Remove Optional[ and ]
        return _normalize_type(inner)

    # Handle union with None
    if " | None" in py_type:
        py_type = py_type.replace(" | None", "")
    if "None | " in py_type:
        py_type = py_type.replace("None | ", "")

    # Handle List types
    if _is_list_type(py_type):
        return "array"

    # Handle Dict types
    if py_type.startswith(("Dict[", "dict[")):
        return "object"

    # Extract base type from generics
    if "[" in py_type:
        py_type = py_type.split("[")[0]

    # Check for known types
    if py_type in PYTHON_TYPE_MAP:
        return PYTHON_TYPE_MAP[py_type]

    # Default to object for custom types
    return "object"


def _has_default(node: ast.AnnAssign) -> bool:
    """Check if an annotated assignment has a default value."""
    if node.value is None:
        return False

    # Check for Field(...) with default
    if isinstance(node.value, ast.Call):
        if isinstance(node.value.func, ast.Name) and node.value.func.id == "Field":
            # Check for default= or default_factory= in keywords
            for kw in node.value.keywords:
                if kw.arg in ("default", "default_factory"):
                    return True
            # Check for positional default (first arg)
            if node.value.args:
                first_arg = node.value.args[0]
                # ... means required
                if isinstance(first_arg, ast.Constant) and first_arg.value is ...:
                    return False
                return True
        return False

    return True


def _extract_field_description(node: ast.AnnAssign) -> Optional[str]:
    """Extract description from Field(..., description="...")."""
    if node.value is None:
        return None

    if isinstance(node.value, ast.Call):
        if isinstance(node.value.func, ast.Name) and node.value.func.id == "Field":
            for kw in node.value.keywords:
                if kw.arg == "description" and isinstance(kw.value, ast.Constant):
                    return str(kw.value.value)
    return None


class PydanticModelVisitor(ast.NodeVisitor):
    """AST visitor to extract Pydantic models."""

    def __init__(self):
        self.models: List[ParsedModel] = []
        self._pydantic_bases = {"BaseModel", "BaseSettings"}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Check if this class inherits from a Pydantic base
        bases = []
        is_pydantic = False

        for base in node.bases:
            base_name = _get_type_string(base)
            bases.append(base_name)

            # Check for direct Pydantic inheritance
            if base_name in self._pydantic_bases:
                is_pydantic = True
            # Check for other models we've already found (inheritance chain)
            elif any(m.name == base_name for m in self.models):
                is_pydantic = True

        if not is_pydantic:
            return

        # Parse the model
        model = ParsedModel(name=node.name, bases=bases)

        # Get docstring
        if node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Constant):
                model.docstring = str(node.body[0].value.value)

        # Parse fields
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field_name = item.target.id

                # Skip private and class vars
                if field_name.startswith("_"):
                    continue

                type_str = _get_type_string(item.annotation)
                optional = _is_optional_type(type_str) or _has_default(item)
                is_list = _is_list_type(type_str)
                description = _extract_field_description(item)

                model.fields.append(
                    ParsedField(
                        name=field_name,
                        type_str=type_str,
                        optional=optional,
                        is_list=is_list,
                        description=description,
                    )
                )

        self.models.append(model)
        self._pydantic_bases.add(node.name)  # Add for inheritance detection


def parse_pydantic_model(content: str) -> dict:
    """Parse Pydantic models from Python content into a profile schema.

    Args:
        content: Raw Python file content

    Returns:
        A dictionary with profile schema fields:
        - schema_data: Field definitions with optional flags
        - data_types: Mapping of field names to types
        - pii_fields: List of likely PII field names
        - patterns: Empty (would need sample data)
        - required_fields: Fields that are not optional

    Example:
        Input:
            class Customer(BaseModel):
                id: str
                email: str
                orders: List[Order]
                nickname: Optional[str] = None

        Output:
            {
                "schema_data": {
                    "id": {"optional": false},
                    "email": {"optional": false},
                    "orders": {"optional": false, "array": true},
                    "nickname": {"optional": true},
                },
                "data_types": {
                    "id": "string",
                    "email": "string",
                    "orders": "array",
                    "nickname": "string",
                },
                "pii_fields": ["email"],
                "required_fields": ["id", "email", "orders"],
                ...
            }
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return {
            "schema_data": {},
            "data_types": {},
            "pii_fields": [],
            "patterns": {},
            "business_rules": [],
            "example_formats": {},
            "required_fields": [],
            "value_constraints": {},
        }

    visitor = PydanticModelVisitor()
    visitor.visit(tree)

    if not visitor.models:
        return {
            "schema_data": {},
            "data_types": {},
            "pii_fields": [],
            "patterns": {},
            "business_rules": [],
            "example_formats": {},
            "required_fields": [],
            "value_constraints": {},
        }

    # Merge all fields from all models
    schema_data: Dict = {}
    data_types: Dict = {}
    pii_fields: List = []
    required_fields: List = []
    business_rules: List = []

    for model in visitor.models:
        for f in model.fields:
            schema_data[f.name] = {
                "optional": f.optional,
                "array": f.is_list,
                "type_definition": f.type_str,
            }
            if f.description:
                schema_data[f.name]["description"] = f.description

            data_types[f.name] = _normalize_type(f.type_str)

            if _is_pii_field(f.name):
                if f.name not in pii_fields:
                    pii_fields.append(f.name)

            if not f.optional and f.name not in required_fields:
                required_fields.append(f.name)

            # Extract business rules from descriptions
            if f.description and ("must" in f.description.lower() or "should" in f.description.lower()):
                business_rules.append(f"{f.name}: {f.description}")

    return {
        "schema_data": schema_data,
        "data_types": data_types,
        "pii_fields": pii_fields,
        "patterns": {},
        "business_rules": business_rules,
        "example_formats": {},
        "required_fields": required_fields,
        "value_constraints": {},
    }


def extract_model_names(content: str) -> List[str]:
    """Extract just the Pydantic model names from Python content.

    Useful for quick inspection without full parsing.
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    visitor = PydanticModelVisitor()
    visitor.visit(tree)

    return [m.name for m in visitor.models]
