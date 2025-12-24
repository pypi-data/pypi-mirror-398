"""Tests for JSON serialization utilities."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from lumenova_beacon.utils.serialization import serialize_for_json


class TestSerializePrimitives:
    """Test serialization of primitive types."""

    def test_serialize_none(self):
        """Test serializing None."""
        result = serialize_for_json(None)

        assert result is None

    def test_serialize_string(self):
        """Test serializing string."""
        result = serialize_for_json("test string")

        assert result == "test string"

    def test_serialize_int(self):
        """Test serializing integer."""
        result = serialize_for_json(42)

        assert result == 42

    def test_serialize_float(self):
        """Test serializing float."""
        result = serialize_for_json(3.14)

        assert result == 3.14

    def test_serialize_bool_true(self):
        """Test serializing True."""
        result = serialize_for_json(True)

        assert result is True

    def test_serialize_bool_false(self):
        """Test serializing False."""
        result = serialize_for_json(False)

        assert result is False


class TestSerializeUUID:
    """Test serialization of UUID objects."""

    def test_serialize_uuid(self):
        """Test serializing UUID to string."""
        test_uuid = uuid4()

        result = serialize_for_json(test_uuid)

        assert isinstance(result, str)
        assert result == str(test_uuid)

    def test_serialize_fixed_uuid(self):
        """Test serializing specific UUID."""
        test_uuid = UUID("12345678-1234-5678-1234-567812345678")

        result = serialize_for_json(test_uuid)

        assert result == "12345678-1234-5678-1234-567812345678"


class TestSerializeDatetime:
    """Test serialization of datetime objects."""

    def test_serialize_datetime(self):
        """Test serializing datetime to ISO format."""
        dt = datetime(2024, 1, 15, 12, 30, 45, tzinfo=timezone.utc)

        result = serialize_for_json(dt)

        assert isinstance(result, str)
        assert result.startswith("2024-01-15T12:30:45")

    def test_serialize_datetime_with_microseconds(self):
        """Test serializing datetime with microseconds."""
        dt = datetime(2024, 1, 15, 12, 30, 45, 123456, tzinfo=timezone.utc)

        result = serialize_for_json(dt)

        assert ".123456" in result


class TestSerializeCollections:
    """Test serialization of collection types."""

    def test_serialize_dict(self):
        """Test serializing dictionary."""
        data = {"key1": "value1", "key2": 42}

        result = serialize_for_json(data)

        assert result == {"key1": "value1", "key2": 42}

    def test_serialize_nested_dict(self):
        """Test serializing nested dictionary."""
        data = {
            "level1": {
                "level2": {
                    "level3": "deep value"
                }
            }
        }

        result = serialize_for_json(data)

        assert result["level1"]["level2"]["level3"] == "deep value"

    def test_serialize_list(self):
        """Test serializing list."""
        data = [1, 2, 3, "four"]

        result = serialize_for_json(data)

        assert result == [1, 2, 3, "four"]

    def test_serialize_tuple(self):
        """Test serializing tuple to list."""
        data = (1, 2, 3)

        result = serialize_for_json(data)

        assert result == [1, 2, 3]
        assert isinstance(result, list)

    def test_serialize_set(self):
        """Test serializing set to list."""
        data = {1, 2, 3}

        result = serialize_for_json(data)

        assert isinstance(result, list)
        assert set(result) == {1, 2, 3}

    def test_serialize_empty_dict(self):
        """Test serializing empty dictionary."""
        result = serialize_for_json({})

        assert result == {}

    def test_serialize_empty_list(self):
        """Test serializing empty list."""
        result = serialize_for_json([])

        assert result == []


class TestSerializeComplexStructures:
    """Test serialization of complex nested structures."""

    def test_serialize_dict_with_uuid_values(self):
        """Test serializing dict with UUID values."""
        test_uuid = uuid4()
        data = {"id": test_uuid, "name": "test"}

        result = serialize_for_json(data)

        assert result["id"] == str(test_uuid)
        assert result["name"] == "test"

    def test_serialize_list_of_dicts(self):
        """Test serializing list of dictionaries."""
        data = [
            {"id": 1, "name": "first"},
            {"id": 2, "name": "second"},
        ]

        result = serialize_for_json(data)

        assert len(result) == 2
        assert result[0]["name"] == "first"
        assert result[1]["name"] == "second"

    def test_serialize_dict_with_datetime_values(self):
        """Test serializing dict with datetime values."""
        dt = datetime(2024, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        data = {"timestamp": dt, "event": "test"}

        result = serialize_for_json(data)

        assert isinstance(result["timestamp"], str)
        assert result["event"] == "test"

    def test_serialize_deeply_nested_structure(self):
        """Test serializing deeply nested structure."""
        data = {
            "level1": [
                {
                    "level2": {
                        "level3": [1, 2, {"level4": "value"}]
                    }
                }
            ]
        }

        result = serialize_for_json(data)

        assert result["level1"][0]["level2"]["level3"][2]["level4"] == "value"


class TestSerializePydanticModels:
    """Test serialization of Pydantic models."""

    def test_serialize_pydantic_v2_model(self):
        """Test serializing Pydantic v2 model (with model_dump)."""
        # Create a mock Pydantic v2 model
        mock_model = MagicMock()
        mock_model.model_dump.return_value = {"field1": "value1", "field2": 42}

        result = serialize_for_json(mock_model)

        assert result == {"field1": "value1", "field2": 42}
        mock_model.model_dump.assert_called_once()

    def test_serialize_pydantic_v1_model(self):
        """Test serializing Pydantic v1 model (with dict)."""
        # Create a mock Pydantic v1 model (no model_dump)
        mock_model = MagicMock()
        del mock_model.model_dump  # Remove model_dump attribute
        mock_model.dict.return_value = {"field1": "value1", "field2": 42}

        result = serialize_for_json(mock_model)

        assert result == {"field1": "value1", "field2": 42}
        mock_model.dict.assert_called_once()


class TestSerializeObjectsWithJsonMethod:
    """Test serialization of objects with .json() method."""

    def test_serialize_object_with_json_method_returning_string(self):
        """Test serializing object with json() method returning string."""
        mock_obj = MagicMock()
        mock_obj.json.return_value = '{"key": "value"}'
        # Remove model_dump and dict to avoid Pydantic path
        del mock_obj.model_dump
        del mock_obj.dict

        result = serialize_for_json(mock_obj)

        assert result == {"key": "value"}

    def test_serialize_object_with_json_method_returning_dict(self):
        """Test serializing object with json() method returning dict."""
        mock_obj = MagicMock()
        mock_obj.json.return_value = {"key": "value"}
        del mock_obj.model_dump
        del mock_obj.dict

        result = serialize_for_json(mock_obj)

        assert result == {"key": "value"}


class TestSerializeFallback:
    """Test fallback serialization for unknown types."""

    def test_serialize_custom_object_to_string(self):
        """Test that unknown objects are converted to string."""
        class CustomObject:
            def __str__(self):
                return "custom object representation"

        obj = CustomObject()

        result = serialize_for_json(obj)

        assert result == "custom object representation"

    def test_serialize_object_without_str(self):
        """Test serializing object that can't be converted to string gracefully."""
        class BadObject:
            def __str__(self):
                raise Exception("Cannot convert to string")

        obj = BadObject()

        result = serialize_for_json(obj)

        # Should return fallback value
        assert result == "<unserializable>"


class TestSerializeEdgeCases:
    """Test edge cases in serialization."""

    def test_serialize_zero(self):
        """Test serializing zero."""
        result = serialize_for_json(0)

        assert result == 0

    def test_serialize_empty_string(self):
        """Test serializing empty string."""
        result = serialize_for_json("")

        assert result == ""

    def test_serialize_negative_number(self):
        """Test serializing negative number."""
        result = serialize_for_json(-42)

        assert result == -42

    def test_serialize_very_large_number(self):
        """Test serializing very large number."""
        large_num = 10**100

        result = serialize_for_json(large_num)

        assert result == large_num

    def test_serialize_unicode_string(self):
        """Test serializing Unicode string."""
        unicode_str = "Hello 世界 🌍"

        result = serialize_for_json(unicode_str)

        assert result == unicode_str

    def test_serialize_dict_with_special_keys(self):
        """Test serializing dict with special characters in keys."""
        data = {
            "key.with.dots": "value1",
            "key-with-dashes": "value2",
            "key_with_underscores": "value3",
        }

        result = serialize_for_json(data)

        assert result == data


class TestSerializeRealWorldScenarios:
    """Test serialization in real-world scenarios."""

    def test_serialize_span_like_structure(self):
        """Test serializing a span-like structure."""
        span_data = {
            "trace_id": uuid4(),
            "span_id": uuid4(),
            "timestamp": datetime.now(timezone.utc),
            "attributes": {
                "key1": "value1",
                "key2": [1, 2, 3],
            },
            "metadata": {
                "user_id": uuid4(),
                "timestamp": datetime.now(timezone.utc),
            }
        }

        result = serialize_for_json(span_data)

        # All UUIDs should be strings
        assert isinstance(result["trace_id"], str)
        assert isinstance(result["span_id"], str)
        assert isinstance(result["timestamp"], str)
        assert isinstance(result["metadata"]["user_id"], str)
        assert isinstance(result["metadata"]["timestamp"], str)

        # Other data should be preserved
        assert result["attributes"]["key1"] == "value1"
        assert result["attributes"]["key2"] == [1, 2, 3]

    def test_serialize_mixed_type_list(self):
        """Test serializing list with mixed types."""
        data = [
            "string",
            42,
            3.14,
            True,
            None,
            {"nested": "dict"},
            [1, 2, 3],
            uuid4(),
            datetime.now(timezone.utc),
        ]

        result = serialize_for_json(data)

        assert isinstance(result, list)
        assert len(result) == 9
        assert result[0] == "string"
        assert result[1] == 42
        assert result[2] == 3.14
        assert result[3] is True
        assert result[4] is None
        assert result[5] == {"nested": "dict"}
        assert result[6] == [1, 2, 3]
        assert isinstance(result[7], str)  # UUID
        assert isinstance(result[8], str)  # datetime

    def test_serialize_preserves_json_compatibility(self):
        """Test that serialized data is JSON-compatible."""
        import json

        data = {
            "id": uuid4(),
            "timestamp": datetime.now(timezone.utc),
            "values": [1, 2, 3],
            "metadata": {"key": "value"},
        }

        result = serialize_for_json(data)

        # Should be JSON serializable
        json_str = json.dumps(result)
        assert isinstance(json_str, str)

        # Should be JSON deserializable
        deserialized = json.loads(json_str)
        assert isinstance(deserialized, dict)
