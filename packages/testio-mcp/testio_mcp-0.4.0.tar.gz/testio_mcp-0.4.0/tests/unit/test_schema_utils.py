"""Unit tests for JSON schema inlining utilities.

Tests the inline_schema_refs function that resolves $ref references
to work around Gemini CLI compatibility issues.
"""

import pytest

from testio_mcp.utilities.schema_utils import inline_schema_refs


@pytest.mark.unit
def test_inline_simple_ref() -> None:
    """Verify simple $ref reference is inlined correctly."""
    schema = {
        "$defs": {
            "StorageInfo": {
                "type": "object",
                "properties": {"oldest": {"type": "string"}},
            }
        },
        "properties": {"storage": {"$ref": "#/$defs/StorageInfo"}},
    }

    result = inline_schema_refs(schema)

    # $defs should be removed
    assert "$defs" not in result

    # $ref should be resolved
    assert result["properties"]["storage"] == {
        "type": "object",
        "properties": {"oldest": {"type": "string"}},
    }


@pytest.mark.unit
def test_inline_multiple_refs() -> None:
    """Verify multiple $ref references are all inlined."""
    schema = {
        "$defs": {
            "ProductInfo": {"type": "object", "properties": {"id": {"type": "integer"}}},
            "BugSummary": {"type": "object", "properties": {"count": {"type": "integer"}}},
        },
        "properties": {
            "product": {"$ref": "#/$defs/ProductInfo"},
            "bugs": {"$ref": "#/$defs/BugSummary"},
        },
    }

    result = inline_schema_refs(schema)

    assert "$defs" not in result
    assert result["properties"]["product"] == {
        "type": "object",
        "properties": {"id": {"type": "integer"}},
    }
    assert result["properties"]["bugs"] == {
        "type": "object",
        "properties": {"count": {"type": "integer"}},
    }


@pytest.mark.unit
def test_inline_nested_refs() -> None:
    """Verify nested $ref references are resolved recursively."""
    schema = {
        "$defs": {
            "FeatureInfo": {"type": "object", "properties": {"name": {"type": "string"}}},
            "ProductInfo": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "feature": {"$ref": "#/$defs/FeatureInfo"},
                },
            },
        },
        "properties": {"product": {"$ref": "#/$defs/ProductInfo"}},
    }

    result = inline_schema_refs(schema)

    assert "$defs" not in result
    # Nested $ref should be fully resolved
    assert result["properties"]["product"] == {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "feature": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
            },
        },
    }


@pytest.mark.unit
def test_inline_ref_in_array() -> None:
    """Verify $ref inside array items is resolved."""
    schema = {
        "$defs": {"TestSummary": {"type": "object", "properties": {"id": {"type": "integer"}}}},
        "properties": {"tests": {"type": "array", "items": {"$ref": "#/$defs/TestSummary"}}},
    }

    result = inline_schema_refs(schema)

    assert "$defs" not in result
    assert result["properties"]["tests"]["items"] == {
        "type": "object",
        "properties": {"id": {"type": "integer"}},
    }


@pytest.mark.unit
def test_inline_no_refs() -> None:
    """Verify schema without $ref is returned unchanged."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "count": {"type": "integer"},
        },
    }

    result = inline_schema_refs(schema)

    # Should be a copy, not the same object
    assert result is not schema
    # But content should be identical
    assert result == schema


@pytest.mark.unit
def test_inline_preserves_other_fields() -> None:
    """Verify other schema fields are preserved during inlining."""
    schema = {
        "$defs": {"Info": {"type": "object"}},
        "type": "object",
        "title": "TestOutput",
        "description": "Test output model",
        "properties": {
            "name": {"type": "string", "description": "Name field"},
            "info": {"$ref": "#/$defs/Info", "description": "Info field"},
        },
        "required": ["name"],
    }

    result = inline_schema_refs(schema)

    # Non-$ref fields preserved
    assert result["type"] == "object"
    assert result["title"] == "TestOutput"
    assert result["description"] == "Test output model"
    assert result["required"] == ["name"]

    # Field descriptions preserved
    assert result["properties"]["name"]["description"] == "Name field"
    assert result["properties"]["info"]["description"] == "Info field"

    # But $ref is resolved
    assert result["properties"]["info"]["type"] == "object"


@pytest.mark.unit
def test_inline_real_pydantic_schema() -> None:
    """Verify inlining works with actual Pydantic-generated schema."""
    from pydantic import BaseModel, Field

    class StorageInfo(BaseModel):
        oldest_test_date: str | None = Field(default=None)
        newest_test_date: str | None = Field(default=None)

    class DatabaseStats(BaseModel):
        database_size_mb: float
        storage_info: StorageInfo

    # Generate Pydantic schema (contains $ref)
    schema = DatabaseStats.model_json_schema()

    # Verify it has $defs (before inlining)
    assert "$defs" in schema
    assert "StorageInfo" in schema["$defs"]

    # Inline references
    result = inline_schema_refs(schema)

    # After inlining: no $defs, no $ref
    assert "$defs" not in result
    assert "$ref" not in str(result)

    # Storage info is fully inlined
    storage_props = result["properties"]["storage_info"]["properties"]
    assert "oldest_test_date" in storage_props
    assert "newest_test_date" in storage_props


@pytest.mark.unit
def test_inline_does_not_mutate_original() -> None:
    """Verify original schema is not mutated during inlining."""
    original = {
        "$defs": {"Info": {"type": "object"}},
        "properties": {"info": {"$ref": "#/$defs/Info"}},
    }

    # Keep reference to original $defs
    original_defs = original["$defs"]

    # Inline (should not mutate original)
    result = inline_schema_refs(original)

    # Original still has $defs
    assert "$defs" in original
    assert original["$defs"] is original_defs

    # But result does not
    assert "$defs" not in result
