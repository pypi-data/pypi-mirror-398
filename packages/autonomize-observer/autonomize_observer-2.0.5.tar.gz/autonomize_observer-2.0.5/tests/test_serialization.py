"""Tests for serialization utilities."""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import BaseModel

from autonomize_observer.tracing.utils.serialization import safe_serialize


class TestSafeSerialize:
    """Tests for safe_serialize function."""

    def test_none(self) -> None:
        """Test None handling."""
        assert safe_serialize(None) is None

    def test_basic_types(self) -> None:
        """Test basic type handling."""
        assert safe_serialize("hello") == "hello"
        assert safe_serialize(123) == 123
        assert safe_serialize(3.14) == 3.14
        assert safe_serialize(True) is True
        assert safe_serialize(False) is False

    def test_uuid(self) -> None:
        """Test UUID handling."""
        uuid = UUID("12345678-1234-5678-1234-567812345678")
        result = safe_serialize(uuid)
        assert result == "12345678-1234-5678-1234-567812345678"
        assert isinstance(result, str)

    def test_datetime(self) -> None:
        """Test datetime handling."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = safe_serialize(dt)
        assert "2024-01-15" in result
        assert isinstance(result, str)

    def test_bytes(self) -> None:
        """Test bytes handling."""
        # UTF-8 decodable
        result = safe_serialize(b"hello world")
        assert result == "hello world"

        # Non-UTF-8
        result = safe_serialize(b"\x80\x81\x82")
        assert "<bytes:" in result

    def test_dict(self) -> None:
        """Test dictionary handling."""
        data = {"key": "value", "number": 42}
        result = safe_serialize(data)
        assert result == {"key": "value", "number": 42}

    def test_nested_dict(self) -> None:
        """Test nested dictionary handling."""
        data = {"outer": {"inner": {"deep": "value"}}}
        result = safe_serialize(data)
        assert result == {"outer": {"inner": {"deep": "value"}}}

    def test_list(self) -> None:
        """Test list handling."""
        data = [1, 2, 3, "four"]
        result = safe_serialize(data)
        assert result == [1, 2, 3, "four"]

    def test_tuple(self) -> None:
        """Test tuple handling."""
        data = (1, 2, 3)
        result = safe_serialize(data)
        assert result == [1, 2, 3]
        assert isinstance(result, list)

    def test_set(self) -> None:
        """Test set handling."""
        data = {1, 2, 3}
        result = safe_serialize(data)
        assert isinstance(result, list)
        assert sorted(result) == [1, 2, 3]

    def test_pydantic_model(self) -> None:
        """Test Pydantic model handling."""

        class TestModel(BaseModel):
            name: str
            value: int

        model = TestModel(name="test", value=42)
        result = safe_serialize(model)
        assert result == {"name": "test", "value": 42}

    def test_object_with_dict(self) -> None:
        """Test object with __dict__ attribute."""

        class SimpleObject:
            def __init__(self) -> None:
                self.name = "test"
                self.value = 42

        obj = SimpleObject()
        result = safe_serialize(obj)
        assert result["name"] == "test"
        assert result["value"] == 42

    def test_object_with_to_dict(self) -> None:
        """Test object with to_dict method."""

        class DictObject:
            __slots__ = ()  # No __dict__

            def to_dict(self) -> dict:
                return {"key": "value"}

        obj = DictObject()
        result = safe_serialize(obj)
        assert result == {"key": "value"}

    def test_object_with_text_attr(self) -> None:
        """Test object with text attribute (Langflow Message-like)."""

        class MessageLike:
            __slots__ = ("text",)

            def __init__(self) -> None:
                self.text = "Hello, World!"

        obj = MessageLike()
        result = safe_serialize(obj)
        assert result == "Hello, World!"

    def test_object_with_content_attr(self) -> None:
        """Test object with content attribute (LangChain message-like)."""

        class LangChainMessage:
            __slots__ = ("content",)

            def __init__(self) -> None:
                self.content = "Message content"

        obj = LangChainMessage()
        result = safe_serialize(obj)
        assert result == "Message content"

    def test_object_with_page_content_attr(self) -> None:
        """Test object with page_content attribute (LangChain document-like)."""

        class LangChainDocument:
            __slots__ = ("page_content",)

            def __init__(self) -> None:
                self.page_content = "Document content"

        obj = LangChainDocument()
        result = safe_serialize(obj)
        assert result == "Document content"

    def test_max_depth(self) -> None:
        """Test max depth limiting."""
        # Create deeply nested structure
        data: dict = {"level": 0}
        current = data
        for i in range(15):
            current["nested"] = {"level": i + 1}
            current = current["nested"]

        result = safe_serialize(data, max_depth=5)
        # Should still return something, even if truncated
        assert "level" in result

    def test_complex_mixed_data(self) -> None:
        """Test complex mixed data structures."""
        data = {
            "string": "hello",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "none": None,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
            "uuid": UUID("12345678-1234-5678-1234-567812345678"),
            "datetime": datetime(2024, 1, 15, tzinfo=timezone.utc),
        }
        result = safe_serialize(data)
        assert result["string"] == "hello"
        assert result["number"] == 42
        assert result["float"] == 3.14
        assert result["bool"] is True
        assert result["none"] is None
        assert result["list"] == [1, 2, 3]
        assert result["nested"] == {"key": "value"}
        assert isinstance(result["uuid"], str)
        assert isinstance(result["datetime"], str)

    def test_unserializable_fallback(self) -> None:
        """Test fallback for unserializable objects."""

        class UnserializableObject:
            __slots__ = ()  # No __dict__

            def __str__(self) -> str:
                return "UnserializableObject"

        obj = UnserializableObject()
        result = safe_serialize(obj)
        assert "UnserializableObject" in result

    def test_dict_with_special_keys(self) -> None:
        """Test dictionary with non-string keys."""
        data = {1: "one", 2: "two"}
        result = safe_serialize(data)
        # Keys should be converted to strings
        assert "1" in result or 1 in result

    def test_pydantic_model_dump_exception(self) -> None:
        """Test Pydantic model when model_dump raises exception."""

        class FailingModel:
            """Model that fails on model_dump."""

            __slots__ = ()

            def model_dump(self) -> dict:
                raise RuntimeError("model_dump failed")

            def __str__(self) -> str:
                return "FailingModel"

        obj = FailingModel()
        result = safe_serialize(obj)
        # Should fall back to str()
        assert "FailingModel" in result

    def test_to_dict_returns_none(self) -> None:
        """Test object with to_dict returning None."""

        class NoneToDict:
            """Object with to_dict returning None."""

            __slots__ = ()

            def to_dict(self) -> None:
                return None

            def __str__(self) -> str:
                return "NoneToDict"

        obj = NoneToDict()
        result = safe_serialize(obj)
        # Should fall back to str()
        assert "NoneToDict" in result

    def test_to_dict_exception(self) -> None:
        """Test object with to_dict that raises exception."""

        class FailingToDict:
            """Object with failing to_dict."""

            __slots__ = ()

            def to_dict(self) -> dict:
                raise ValueError("to_dict failed")

            def __str__(self) -> str:
                return "FailingToDict"

        obj = FailingToDict()
        result = safe_serialize(obj)
        # Should fall back to str()
        assert "FailingToDict" in result

    def test_dict_access_exception(self) -> None:
        """Test object with __dict__ that raises exception on access."""

        class FailingDict:
            """Object with failing __dict__."""

            @property
            def __dict__(self) -> dict:  # type: ignore[override]
                raise RuntimeError("dict access failed")

            def __str__(self) -> str:
                return "FailingDict"

        obj = FailingDict()
        result = safe_serialize(obj)
        # Should fall back to str()
        assert "FailingDict" in result

    def test_str_fallback_exception(self) -> None:
        """Test when str() also fails."""

        class TotallyUnserializable:
            """Object that can't be serialized at all."""

            __slots__ = ()

            def __str__(self) -> str:
                raise RuntimeError("str() failed")

        obj = TotallyUnserializable()
        result = safe_serialize(obj)
        # Should return unserializable marker
        assert "<unserializable:" in result
        assert "TotallyUnserializable" in result
