"""Tests for the utils module."""

from dataclasses import dataclass
from typing import Any, Literal, Optional, Union

import pytest
from pydantic import BaseModel
from typing_extensions import TypedDict

from veris_ai.utils import convert_to_type, extract_json_schema


class TestConvertToType:
    """Test the convert_to_type function."""

    @pytest.mark.parametrize(
        "value,target_type,expected",
        [
            # Primitive types
            ("42", int, 42),
            (42, str, "42"),
            ("3.14", float, 3.14),
            ("true", bool, True),
            ("false", bool, True),  # Non-empty strings are truthy
            ("", bool, False),
            (0, bool, False),
            (1, bool, True),
            # Any type
            ("test", Any, "test"),
            (42, Any, 42),
            ([1, 2, 3], Any, [1, 2, 3]),
            # List types
            ([1, 2, 3], list[int], [1, 2, 3]),
            (["1", "2"], list[int], [1, 2]),
            ([1.0, 2.5], list[float], [1.0, 2.5]),
            (["true", "false"], list[bool], [True, True]),  # Non-empty strings are truthy
            # Dict types
            ({"a": 1}, dict[str, int], {"a": 1}),
            ({"1": "2"}, dict[int, int], {1: 2}),
            ({"a": "1", "b": "2"}, dict[str, int], {"a": 1, "b": 2}),
            # Union types
            ("42", Union[int, str], 42),  # Tries int first
            ("abc", Union[int, str], "abc"),  # Falls back to str
            (42, Union[str, int], "42"),  # Tries str first
            ([1, 2], Union[list[int], str], [1, 2]),
            ("test", Union[list[int], str], "test"),
            # NoneType
            (None, type(None), None),
            ("anything", type(None), None),  # NoneType always returns None
            (42, type(None), None),  # NoneType always returns None
            ([], type(None), None),  # NoneType always returns None
        ],
    )
    def test_convert_to_type_success(self, value, target_type, expected):
        """Test successful type conversions."""
        result = convert_to_type(value, target_type)
        assert result == expected
        assert isinstance(result, type(expected))

    def test_convert_to_type_list_invalid(self):
        """Test that non-list values raise ValueError for list types."""
        with pytest.raises(ValueError, match="Expected list but got <class 'str'>"):
            convert_to_type("not a list", list[int])

    def test_convert_to_type_dict_invalid(self):
        """Test that non-dict values raise ValueError for dict types."""
        with pytest.raises(ValueError, match="Expected dict but got <class 'str'>"):
            convert_to_type("not a dict", dict[str, int])

    def test_convert_to_type_union_all_fail(self):
        """Test that Union conversion raises ValueError when all types fail."""
        with pytest.raises(ValueError, match="Could not convert abc to any of the union types"):
            convert_to_type("abc", Union[int, float])

    def test_convert_to_type_custom_class(self):
        """Test conversion to custom classes."""

        class CustomClass:
            def __init__(self, value):
                self.value = value

        result = convert_to_type("test", CustomClass)
        assert isinstance(result, CustomClass)
        assert result.value == "test"

    def test_convert_to_type_custom_class_with_kwargs(self):
        """Test conversion to custom classes using kwargs."""

        class CustomClass:
            def __init__(self, name: str, age: int):
                self.name = name
                self.age = age

        data = {"name": "John", "age": 30}
        result = convert_to_type(data, CustomClass)
        assert isinstance(result, CustomClass)
        assert result.name == "John"
        assert result.age == 30

    def test_convert_to_type_nested_structures(self):
        """Test conversion of nested data structures."""
        # Nested list
        value = [["1", "2"], ["3", "4"]]
        result = convert_to_type(value, list[list[int]])
        assert result == [[1, 2], [3, 4]]

        # Dict with list values
        value = {"a": ["1", "2"], "b": ["3", "4"]}
        result = convert_to_type(value, dict[str, list[int]])
        assert result == {"a": [1, 2], "b": [3, 4]}

        # List of dicts
        value = [{"a": "1"}, {"b": "2"}]
        result = convert_to_type(value, list[dict[str, int]])
        assert result == [{"a": 1}, {"b": 2}]

    def test_convert_to_type_optional_with_none(self):
        """Test conversion of None values with Optional types."""
        # Test None with Optional[int] - Union[int, None]
        # Since Union tries types in order, it will try int first and fail,
        # then try NoneType and succeed
        result = convert_to_type(None, Optional[int])
        assert result is None

        # Test None with Union[str, None]
        # Since Union tries types in order, it will try str first and succeed
        # converting None to "None" string
        result = convert_to_type(None, Union[str, None])
        assert result == "None"  # str(None) = "None"

        # Test None with Union[None, str] - NoneType first
        result = convert_to_type(None, Union[None, str])
        assert result is None  # NoneType is tried first and succeeds

        # Test actual value with Optional
        result = convert_to_type(42, Optional[int])
        assert result == 42

        result = convert_to_type("42", Optional[int])
        assert result == 42

    def test_convert_to_type_union_python310_syntax(self):
        """Test conversion with Python 3.10+ union syntax (str | int)."""
        # Test with string value that can be converted to int
        result = convert_to_type("42", str | int)
        assert result == "42"  # String type is tried first and succeeds
        assert isinstance(result, str)

        # Test with int value - will be converted to string (first type in union)
        result = convert_to_type(42, str | int)
        assert result == "42"  # Converted to string since str is first in union
        assert isinstance(result, str)

        # Test with int | str (reversed order) - int comes first
        result = convert_to_type("42", int | str)
        assert result == 42  # Converted to int since int is first
        assert isinstance(result, int)

        # Test with a value that only works as string
        result = convert_to_type("hello", str | int | float)
        assert result == "hello"
        assert isinstance(result, str)


class TestExtractJsonSchema:
    """Test the extract_json_schema function."""

    def test_primitive_types(self):
        """Test extraction for primitive types."""
        assert extract_json_schema(str) == {"type": "string"}
        assert extract_json_schema(int) == {"type": "integer"}
        assert extract_json_schema(float) == {"type": "number"}
        assert extract_json_schema(bool) == {"type": "boolean"}
        assert extract_json_schema(type(None)) == {"type": "null"}
        assert extract_json_schema(Any) == {}

    def test_list_types(self):
        """Test extraction for list types."""
        assert extract_json_schema(list) == {"type": "array"}
        assert extract_json_schema(list[int]) == {
            "type": "array",
            "items": {"type": "integer"},
        }
        assert extract_json_schema(list[str]) == {
            "type": "array",
            "items": {"type": "string"},
        }
        assert extract_json_schema(list[list[int]]) == {
            "type": "array",
            "items": {
                "type": "array",
                "items": {"type": "integer"},
            },
        }

    def test_dict_types(self):
        """Test extraction for dict types."""
        assert extract_json_schema(dict) == {"type": "object"}
        assert extract_json_schema(dict[str, int]) == {
            "type": "object",
            "additionalProperties": {"type": "integer"},
        }
        assert extract_json_schema(dict[str, list[int]]) == {
            "type": "object",
            "additionalProperties": {
                "type": "array",
                "items": {"type": "integer"},
            },
        }

    def test_tuple_types(self):
        """Test extraction for tuple types."""
        assert extract_json_schema(tuple) == {"type": "array"}
        assert extract_json_schema(tuple[int, str]) == {
            "type": "array",
            "prefixItems": [
                {"type": "integer"},
                {"type": "string"},
            ],
            "minItems": 2,
            "maxItems": 2,
        }
        assert extract_json_schema(tuple[int, str, bool]) == {
            "type": "array",
            "prefixItems": [
                {"type": "integer"},
                {"type": "string"},
                {"type": "boolean"},
            ],
            "minItems": 3,
            "maxItems": 3,
        }

    def test_literal_types(self):
        """Test extraction for Literal types."""
        assert extract_json_schema(Literal["foo"]) == {"const": "foo"}
        assert extract_json_schema(Literal[42]) == {"const": 42}
        assert extract_json_schema(Literal["foo", "bar", "baz"]) == {
            "enum": ["foo", "bar", "baz"],
        }
        assert extract_json_schema(Literal[1, 2, 3]) == {
            "enum": [1, 2, 3],
        }

        # Test in a list context
        assert extract_json_schema(list[Literal["active", "inactive"]]) == {
            "type": "array",
            "items": {"enum": ["active", "inactive"]},
        }

    def test_union_types(self):
        """Test extraction for union types."""
        assert extract_json_schema(Union[int, str]) == {
            "anyOf": [
                {"type": "integer"},
                {"type": "string"},
            ],
        }
        assert extract_json_schema(Union[int, str, bool]) == {
            "anyOf": [
                {"type": "integer"},
                {"type": "string"},
                {"type": "boolean"},
            ],
        }

    def test_optional_types(self):
        """Test extraction for optional types."""
        assert extract_json_schema(Optional[int]) == {
            "anyOf": [
                {"type": "integer"},
                {"type": "null"},
            ],
        }
        assert extract_json_schema(Optional[str]) == {
            "anyOf": [
                {"type": "string"},
                {"type": "null"},
            ],
        }
        assert extract_json_schema(Union[int, None]) == {
            "anyOf": [
                {"type": "integer"},
                {"type": "null"},
            ],
        }

    def test_pydantic_models(self):
        """Test extraction for Pydantic models."""

        class SimpleModel(BaseModel):
            name: str
            age: int
            active: bool = True

        schema = extract_json_schema(SimpleModel)
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]
        assert "active" in schema["properties"]

        # Test with nested model
        class Address(BaseModel):
            street: str
            city: str
            zip_code: str

        class Person(BaseModel):
            name: str
            age: int
            address: Address

        schema = extract_json_schema(Person)
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "address" in schema["properties"]

    def test_dataclass(self):
        """Test extraction for dataclasses using TypeAdapter."""

        @dataclass
        class SimpleDataclass:
            name: str
            age: int
            active: bool = True

        schema = extract_json_schema(SimpleDataclass)
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert schema["properties"]["name"]["type"] == "string"
        assert "age" in schema["properties"]
        assert schema["properties"]["age"]["type"] == "integer"
        assert "active" in schema["properties"]
        assert schema["properties"]["active"]["type"] == "boolean"

    def test_dataclass_with_optional_fields(self):
        """Test extraction for dataclasses with optional fields."""

        @dataclass
        class DataclassWithOptional:
            name: str
            nickname: Optional[str] = None
            age: int = 0

        schema = extract_json_schema(DataclassWithOptional)
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "nickname" in schema["properties"]
        assert "age" in schema["properties"]
        # Optional fields should have anyOf with null
        nickname_schema = schema["properties"]["nickname"]
        assert "anyOf" in nickname_schema or nickname_schema.get("type") in ["string", "null"]

    def test_nested_dataclass(self):
        """Test extraction for nested dataclasses."""

        @dataclass
        class Address:
            street: str
            city: str
            zip_code: str

        @dataclass
        class PersonWithAddress:
            name: str
            age: int
            address: Address

        schema = extract_json_schema(PersonWithAddress)
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "address" in schema["properties"]
        # The nested dataclass should be properly represented
        address_schema = schema["properties"]["address"]
        # Pydantic's TypeAdapter will create a $ref or inline the object
        assert "$ref" in address_schema or address_schema.get("type") == "object"

    def test_list_of_dataclasses(self):
        """Test extraction for list of dataclasses."""

        @dataclass
        class Item:
            id: str
            name: str
            price: float

        schema = extract_json_schema(list[Item])
        assert schema["type"] == "array"
        assert "items" in schema
        # Items should reference or contain the dataclass schema
        items_schema = schema["items"]
        assert "$ref" in items_schema or items_schema.get("type") == "object"

    def test_typed_dict(self):
        """Test extraction for TypedDict."""

        class PersonDict(TypedDict):
            name: str
            age: int
            email: str

        schema = extract_json_schema(PersonDict)
        assert schema == {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "email": {"type": "string"},
            },
            "required": ["name", "age", "email"],
        }

        # Test with total=False
        class PartialPersonDict(TypedDict, total=False):
            name: str
            age: int
            email: str

        schema = extract_json_schema(PartialPersonDict)
        assert schema == {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "email": {"type": "string"},
            },
        }

    def test_complex_nested_types(self):
        """Test extraction for complex nested types."""
        # List of unions
        assert extract_json_schema(list[Union[int, str]]) == {
            "type": "array",
            "items": {
                "anyOf": [
                    {"type": "integer"},
                    {"type": "string"},
                ],
            },
        }

        # Dict with optional values
        assert extract_json_schema(dict[str, Optional[int]]) == {
            "type": "object",
            "additionalProperties": {
                "anyOf": [
                    {"type": "integer"},
                    {"type": "null"},
                ],
            },
        }

        # Nested TypedDict
        class ContactInfo(TypedDict):
            phone: str
            email: Optional[str]

        class PersonWithContact(TypedDict):
            name: str
            contact: ContactInfo

        schema = extract_json_schema(PersonWithContact)
        assert schema == {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "contact": {
                    "type": "object",
                    "properties": {
                        "phone": {"type": "string"},
                        "email": {
                            "anyOf": [
                                {"type": "string"},
                                {"type": "null"},
                            ],
                        },
                    },
                    "required": ["phone", "email"],
                },
            },
            "required": ["name", "contact"],
        }

    def test_list_of_pydantic_models(self):
        """Test extraction for list of Pydantic models."""

        class Item(BaseModel):
            id: str
            name: str
            price: float

        schema = extract_json_schema(list[Item])
        assert schema["type"] == "array"
        assert "items" in schema
        assert schema["items"]["type"] == "object"
        assert "properties" in schema["items"]

    def test_unknown_types(self):
        """Test extraction for unknown types defaults to object."""

        class CustomClass:
            pass

        assert extract_json_schema(CustomClass) == {"type": "object"}

    def test_openai_agents_types(self):
        """Test extraction for types from openai-agents package."""
        try:
            from agents.items import TResponseInputItem

            # Test list[TResponseInputItem]
            schema = extract_json_schema(list[TResponseInputItem])
            assert schema["type"] == "array"
            assert "items" in schema

            # TResponseInputItem is a Union, so items should have anyOf
            assert "anyOf" in schema["items"]
            assert isinstance(schema["items"]["anyOf"], list)
            assert len(schema["items"]["anyOf"]) > 0

            # Check that at least some of the union members have proper schemas
            # (not just default "type": "object" for all fields)
            has_proper_field_types = False
            for item_schema in schema["items"]["anyOf"]:
                if "properties" in item_schema:
                    for field_name, field_schema in item_schema["properties"].items():
                        # Check if fields like 'type' and 'role' have proper literal/enum schemas
                        if field_name in ["type", "role", "status"] and field_schema != {
                            "type": "object",
                        }:
                            has_proper_field_types = True
                            break
                if has_proper_field_types:
                    break

            # Now that we've enhanced the function, this should work
            assert has_proper_field_types, (
                "Schema should have proper field types, not just default objects"
            )

        except ImportError:
            pytest.skip("openai-agents package not installed")
