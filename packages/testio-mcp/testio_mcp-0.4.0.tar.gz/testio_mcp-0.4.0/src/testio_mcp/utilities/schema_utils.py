"""JSON Schema utilities for MCP compatibility.

This module provides utilities for post-processing Pydantic JSON schemas
to work around compatibility issues with certain MCP clients (notably Gemini CLI).

The primary issue: Some MCP clients fail to resolve $ref references in JSON schemas,
even though $ref is a standard JSON Schema Draft 2020-12 feature.

Strategy:
- Keep strongly-typed Pydantic models in code (type safety, IDE support, FastAPI docs)
- Post-process schemas to inline $defs before MCP tool registration
- Zero code changes needed in tools or services

Reference: docs/architecture/PYDANTIC-SCHEMA-RESEARCH.md
"""

from typing import Any, cast


def inline_schema_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """Recursively inline all $ref definitions from $defs into the schema.

    This function resolves JSON schema $ref references by replacing them with
    their actual definitions from the $defs section. This works around bugs in
    some MCP clients (Gemini CLI 0.16.0) that fail to resolve references.

    Args:
        schema: Pydantic JSON schema with potential $ref references

    Returns:
        Schema with all $ref references inlined (no $defs section)

    Example:
        >>> schema = {
        ...     "$defs": {
        ...         "StorageInfo": {
        ...             "type": "object",
        ...             "properties": {"oldest": {"type": "string"}}
        ...         }
        ...     },
        ...     "properties": {
        ...         "storage": {"$ref": "#/$defs/StorageInfo"}
        ...     }
        ... }
        >>> inline_schema_refs(schema)
        {
            "properties": {
                "storage": {
                    "type": "object",
                    "properties": {"oldest": {"type": "string"}}
                }
            }
        }

    Notes:
        - Handles nested $ref references (recursively resolves)
        - Removes $defs section after inlining
        - Safe for schemas without $ref (returns copy)
        - Does not modify original schema (returns new dict)
    """
    # Make a copy to avoid mutating original
    schema = schema.copy()

    # Extract definitions (if present)
    defs = schema.pop("$defs", {})

    def resolve(subschema: Any) -> Any:
        """Recursively resolve $ref references in schema fragment."""
        # Handle dict with potential $ref
        if isinstance(subschema, dict):
            # Check for $ref reference
            ref = subschema.get("$ref")
            if ref:
                # Extract definition name from reference
                # Example: "#/$defs/StorageInfo" -> "StorageInfo"
                def_name = ref.split("/")[-1]
                # Recursively resolve the referenced definition
                resolved = resolve(defs[def_name])

                # Merge other fields from subschema (e.g., description) with resolved definition
                # This preserves fields like "description" that appear alongside $ref
                other_fields = {k: v for k, v in subschema.items() if k != "$ref"}
                if other_fields:
                    # If resolved is a dict, merge fields
                    if isinstance(resolved, dict):
                        return {**resolved, **other_fields}
                return resolved

            # Recursively resolve all values in dict
            return {k: resolve(v) for k, v in subschema.items()}

        # Handle list (recurse into elements)
        if isinstance(subschema, list):
            return [resolve(item) for item in subschema]

        # Base case: primitive value (string, int, bool, None)
        return subschema

    # Resolve all references in the schema
    return cast(dict[str, Any], resolve(schema))
