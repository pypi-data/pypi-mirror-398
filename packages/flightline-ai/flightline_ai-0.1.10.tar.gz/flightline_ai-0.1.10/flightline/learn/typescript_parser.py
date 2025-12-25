"""TypeScript interface parser - extracts schema from .ts/.d.ts files.

This module parses TypeScript interfaces and type definitions into
profile schemas without using an LLM.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Common PII field name patterns
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

# TypeScript type mapping to simplified types
TS_TYPE_MAP = {
    "string": "string",
    "number": "number",
    "boolean": "boolean",
    "Date": "date",
    "any": "any",
    "unknown": "unknown",
    "null": "null",
    "undefined": "undefined",
    "void": "void",
    "never": "never",
    "object": "object",
    "bigint": "number",
}


@dataclass
class ParsedField:
    """A parsed TypeScript field."""

    name: str
    type_str: str
    optional: bool = False
    is_array: bool = False
    description: Optional[str] = None


@dataclass
class ParsedInterface:
    """A parsed TypeScript interface."""

    name: str
    fields: List[ParsedField] = field(default_factory=list)
    extends: List[str] = field(default_factory=list)
    description: Optional[str] = None


def _is_pii_field(field_name: str) -> bool:
    """Check if a field name matches common PII patterns."""
    name_lower = field_name.lower()
    for pattern in PII_PATTERNS:
        if re.search(pattern, name_lower):
            return True
    return False


def _normalize_type(ts_type: str) -> str:
    """Normalize a TypeScript type to a simpler type string."""
    ts_type = ts_type.strip()

    # Check for array types
    if ts_type.endswith("[]"):
        return "array"

    # Check for Array<T> syntax
    if ts_type.startswith("Array<"):
        return "array"

    # Check for union types
    if "|" in ts_type:
        return "union"

    # Check for literal types
    if ts_type.startswith('"') or ts_type.startswith("'"):
        return "string"

    # Check for known types
    if ts_type in TS_TYPE_MAP:
        return TS_TYPE_MAP[ts_type]

    # Default to object for custom types
    return "object"


def _parse_field_line(line: str) -> Optional[ParsedField]:
    """Parse a single field line from a TypeScript interface.

    Examples:
        id: string;
        email?: string;
        orders: Order[];
        readonly name: string;
    """
    line = line.strip()

    # Skip empty lines, comments, and non-field lines
    if not line or line.startswith("//") or line.startswith("/*"):
        return None

    # Remove trailing semicolon and comma
    line = line.rstrip(";,")

    # Remove readonly modifier
    line = re.sub(r"^\s*readonly\s+", "", line)

    # Match field pattern: name?: Type
    # Also handles multi-word types like Record<string, number>
    match = re.match(r"^([a-zA-Z_$][a-zA-Z0-9_$]*)(\?)?:\s*(.+)$", line)
    if not match:
        return None

    name = match.group(1)
    optional = match.group(2) == "?"
    type_str = match.group(3).strip()

    is_array = type_str.endswith("[]") or type_str.startswith("Array<")

    return ParsedField(
        name=name,
        type_str=type_str,
        optional=optional,
        is_array=is_array,
    )


def _extract_interfaces(content: str) -> List[ParsedInterface]:
    """Extract all interfaces from TypeScript content."""
    interfaces: List[ParsedInterface] = []

    # Pattern to match interface declarations
    # Handles: interface Name { ... } and interface Name extends Other { ... }
    interface_pattern = re.compile(
        r"(?:export\s+)?interface\s+([a-zA-Z_$][a-zA-Z0-9_$]*)"
        r"(?:\s+extends\s+([\w\s,]+))?"
        r"\s*\{([^}]*)\}",
        re.MULTILINE | re.DOTALL,
    )

    for match in interface_pattern.finditer(content):
        name = match.group(1)
        extends_str = match.group(2)
        body = match.group(3)

        extends = []
        if extends_str:
            extends = [e.strip() for e in extends_str.split(",")]

        fields = []
        for line in body.split("\n"):
            parsed = _parse_field_line(line)
            if parsed:
                fields.append(parsed)

        interfaces.append(
            ParsedInterface(
                name=name,
                fields=fields,
                extends=extends,
            )
        )

    return interfaces


def _extract_type_aliases(content: str) -> List[ParsedInterface]:
    """Extract type aliases that look like object types."""
    type_aliases: List[ParsedInterface] = []

    # Pattern for type Foo = { ... }
    type_pattern = re.compile(
        r"(?:export\s+)?type\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*\{([^}]*)\}",
        re.MULTILINE | re.DOTALL,
    )

    for match in type_pattern.finditer(content):
        name = match.group(1)
        body = match.group(2)

        fields = []
        for line in body.split("\n"):
            parsed = _parse_field_line(line)
            if parsed:
                fields.append(parsed)

        if fields:  # Only include if we found fields
            type_aliases.append(
                ParsedInterface(
                    name=name,
                    fields=fields,
                )
            )

    return type_aliases


def parse_typescript_interface(content: str) -> Dict:
    """Parse TypeScript interfaces/types into a profile schema.

    Args:
        content: Raw TypeScript file content

    Returns:
        A dictionary with profile schema fields:
        - schema_data: Field definitions with optional flags
        - data_types: Mapping of field names to types
        - pii_fields: List of likely PII field names
        - patterns: Empty (would need sample data)
        - required_fields: Fields that are not optional

    Example:
        Input:
            interface Customer {
                id: string;
                email: string;
                orders: Order[];
                nickname?: string;
            }

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
    # Extract all interfaces and type aliases
    interfaces = _extract_interfaces(content)
    type_aliases = _extract_type_aliases(content)

    all_types = interfaces + type_aliases

    if not all_types:
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

    # Merge all fields from all interfaces
    # Later interfaces override earlier ones for same field names
    schema_data: Dict = {}
    data_types: Dict = {}
    pii_fields: List = []
    required_fields: List = []

    for parsed in all_types:
        for f in parsed.fields:
            schema_data[f.name] = {
                "optional": f.optional,
                "array": f.is_array,
                "type_definition": f.type_str,
            }
            data_types[f.name] = _normalize_type(f.type_str)

            if _is_pii_field(f.name):
                if f.name not in pii_fields:
                    pii_fields.append(f.name)

            if not f.optional and f.name not in required_fields:
                required_fields.append(f.name)

    return {
        "schema_data": schema_data,
        "data_types": data_types,
        "pii_fields": pii_fields,
        "patterns": {},
        "business_rules": [],
        "example_formats": {},
        "required_fields": required_fields,
        "value_constraints": {},
    }


def extract_interface_names(content: str) -> List[str]:
    """Extract just the interface/type names from TypeScript content.

    Useful for quick inspection without full parsing.
    """
    names = []

    # Interface names
    for match in re.finditer(r"(?:export\s+)?interface\s+([a-zA-Z_$][a-zA-Z0-9_$]*)", content):
        names.append(match.group(1))

    # Type alias names
    for match in re.finditer(r"(?:export\s+)?type\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=", content):
        names.append(match.group(1))

    return names
