"""Tests for TypeScript and Pydantic parsers."""


from flightline.learn.pydantic_parser import extract_model_names, parse_pydantic_model
from flightline.learn.typescript_parser import extract_interface_names, parse_typescript_interface


class TestTypeScriptParser:
    """Tests for TypeScript interface parsing."""

    def test_parse_simple_interface(self):
        """Test parsing a simple interface."""
        ts_code = """
interface Customer {
    id: string;
    name: string;
    email: string;
}
"""
        result = parse_typescript_interface(ts_code)

        assert "id" in result["schema_data"]
        assert "name" in result["schema_data"]
        assert "email" in result["schema_data"]
        assert result["data_types"]["id"] == "string"
        assert "email" in result["pii_fields"]
        assert "name" in result["pii_fields"]

    def test_parse_optional_fields(self):
        """Test parsing optional fields."""
        ts_code = """
interface User {
    id: string;
    nickname?: string;
}
"""
        result = parse_typescript_interface(ts_code)

        assert result["schema_data"]["id"]["optional"] is False
        assert result["schema_data"]["nickname"]["optional"] is True
        assert "id" in result["required_fields"]
        assert "nickname" not in result["required_fields"]

    def test_parse_array_types(self):
        """Test parsing array types."""
        ts_code = """
interface Order {
    items: string[];
    tags: Array<string>;
}
"""
        result = parse_typescript_interface(ts_code)

        assert result["schema_data"]["items"]["array"] is True
        assert result["schema_data"]["tags"]["array"] is True
        assert result["data_types"]["items"] == "array"
        assert result["data_types"]["tags"] == "array"

    def test_parse_exported_interface(self):
        """Test parsing exported interface."""
        ts_code = """
export interface ApiResponse {
    status: number;
    data: any;
}
"""
        result = parse_typescript_interface(ts_code)

        assert "status" in result["schema_data"]
        assert "data" in result["schema_data"]

    def test_parse_type_alias(self):
        """Test parsing type aliases."""
        ts_code = """
type RequestPayload = {
    action: string;
    payload: object;
}
"""
        result = parse_typescript_interface(ts_code)

        assert "action" in result["schema_data"]
        assert "payload" in result["schema_data"]

    def test_extract_interface_names(self):
        """Test extracting interface names."""
        ts_code = """
interface Foo {}
interface Bar {}
type Baz = {}
"""
        names = extract_interface_names(ts_code)

        assert "Foo" in names
        assert "Bar" in names
        assert "Baz" in names

    def test_pii_detection(self):
        """Test PII field detection."""
        ts_code = """
interface Person {
    firstName: string;
    lastName: string;
    emailAddress: string;
    phoneNumber: string;
    ssn: string;
    favoriteColor: string;
}
"""
        result = parse_typescript_interface(ts_code)

        assert "firstName" in result["pii_fields"]
        assert "lastName" in result["pii_fields"]
        assert "emailAddress" in result["pii_fields"]
        assert "phoneNumber" in result["pii_fields"]
        assert "ssn" in result["pii_fields"]
        assert "favoriteColor" not in result["pii_fields"]


class TestPydanticParser:
    """Tests for Pydantic model parsing."""

    def test_parse_simple_model(self):
        """Test parsing a simple Pydantic model."""
        py_code = """
from pydantic import BaseModel

class Customer(BaseModel):
    id: str
    name: str
    email: str
"""
        result = parse_pydantic_model(py_code)

        assert "id" in result["schema_data"]
        assert "name" in result["schema_data"]
        assert "email" in result["schema_data"]
        assert result["data_types"]["id"] == "string"
        assert "email" in result["pii_fields"]

    def test_parse_optional_fields(self):
        """Test parsing Optional fields."""
        py_code = """
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: str
    nickname: Optional[str] = None
"""
        result = parse_pydantic_model(py_code)

        assert result["schema_data"]["id"]["optional"] is False
        assert result["schema_data"]["nickname"]["optional"] is True
        assert "id" in result["required_fields"]
        assert "nickname" not in result["required_fields"]

    def test_parse_union_optional(self):
        """Test parsing union optional (str | None)."""
        py_code = """
from pydantic import BaseModel

class User(BaseModel):
    id: str
    nickname: str | None = None
"""
        result = parse_pydantic_model(py_code)

        assert result["schema_data"]["nickname"]["optional"] is True

    def test_parse_list_types(self):
        """Test parsing List types."""
        py_code = """
from pydantic import BaseModel
from typing import List

class Order(BaseModel):
    items: List[str]
    tags: List[str]
"""
        result = parse_pydantic_model(py_code)

        assert result["schema_data"]["items"]["array"] is True
        assert result["schema_data"]["tags"]["array"] is True
        assert result["data_types"]["items"] == "array"

    def test_parse_field_with_default(self):
        """Test parsing Field with default."""
        py_code = """
from pydantic import BaseModel, Field

class Config(BaseModel):
    timeout: int = Field(default=30)
    retries: int = 3
"""
        result = parse_pydantic_model(py_code)

        assert result["schema_data"]["timeout"]["optional"] is True
        assert result["schema_data"]["retries"]["optional"] is True

    def test_parse_field_required(self):
        """Test parsing required Field (...)."""
        py_code = """
from pydantic import BaseModel, Field

class Request(BaseModel):
    action: str = Field(...)
    data: dict
"""
        result = parse_pydantic_model(py_code)

        assert result["schema_data"]["action"]["optional"] is False
        assert result["schema_data"]["data"]["optional"] is False

    def test_extract_model_names(self):
        """Test extracting model names."""
        py_code = """
from pydantic import BaseModel

class Foo(BaseModel):
    pass

class Bar(Foo):
    pass
"""
        names = extract_model_names(py_code)

        assert "Foo" in names
        assert "Bar" in names

    def test_skip_private_fields(self):
        """Test that private fields are skipped."""
        py_code = """
from pydantic import BaseModel

class Config(BaseModel):
    name: str
    _internal: str
    __private: str
"""
        result = parse_pydantic_model(py_code)

        assert "name" in result["schema_data"]
        assert "_internal" not in result["schema_data"]
        assert "__private" not in result["schema_data"]

    def test_pii_detection(self):
        """Test PII field detection."""
        py_code = """
from pydantic import BaseModel

class Person(BaseModel):
    first_name: str
    last_name: str
    email_address: str
    phone_number: str
    favorite_color: str
"""
        result = parse_pydantic_model(py_code)

        assert "first_name" in result["pii_fields"]
        assert "last_name" in result["pii_fields"]
        assert "email_address" in result["pii_fields"]
        assert "phone_number" in result["pii_fields"]
        assert "favorite_color" not in result["pii_fields"]

    def test_non_pydantic_class_ignored(self):
        """Test that non-Pydantic classes are ignored."""
        py_code = """
class PlainClass:
    def __init__(self):
        self.id = "123"
"""
        result = parse_pydantic_model(py_code)

        assert result["schema_data"] == {}

