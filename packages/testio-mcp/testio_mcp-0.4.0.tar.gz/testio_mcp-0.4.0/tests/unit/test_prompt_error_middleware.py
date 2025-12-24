"""Unit tests for PromptErrorMiddleware.

Tests that the middleware properly transforms PromptError and ValidationError
into user-friendly error messages.
"""

import pytest
from fastmcp.exceptions import PromptError
from mcp import McpError
from pydantic import ValidationError

from testio_mcp.middleware.error_handler import PromptErrorMiddleware


@pytest.fixture
def middleware() -> PromptErrorMiddleware:
    """Create middleware instance for testing."""
    return PromptErrorMiddleware()


@pytest.mark.unit
def test_transforms_validation_error_in_prompt_error_cause(
    middleware: PromptErrorMiddleware,
) -> None:
    """Test that ValidationError nested in PromptError.__cause__ is properly extracted."""
    # Create a Pydantic ValidationError
    try:
        from pydantic import BaseModel, Field

        class TestModel(BaseModel):
            product_id: int = Field(...)

        TestModel(product_id="product")  # type: ignore[arg-type]
    except ValidationError as ve:
        # Wrap it in a PromptError (simulating what FastMCP does)
        prompt_error = PromptError("Error rendering prompt analyze-product-quality.")
        prompt_error.__cause__ = ve

        # Transform the error
        result = middleware._transform_error(prompt_error)

        # Should be McpError with friendly message
        assert isinstance(result, McpError)
        error_msg = result.error.message

        # Check for user-friendly formatting
        assert "❌" in error_msg
        assert "Invalid argument" in error_msg
        assert "product_id" in error_msg
        assert "💡" in error_msg  # Guidance
        assert "Examples:" in error_msg
        assert "/testio-mcp:analyze-product-quality 24734" in error_msg


@pytest.mark.unit
def test_transforms_generic_prompt_error(middleware: PromptErrorMiddleware) -> None:
    """Test that generic PromptError without validation details is handled."""
    prompt_error = PromptError("Something went wrong rendering the prompt")

    result = middleware._transform_error(prompt_error)

    assert isinstance(result, McpError)
    error_msg = result.error.message
    assert "❌" in error_msg
    assert "Prompt error" in error_msg
    assert "💡" in error_msg


@pytest.mark.unit
def test_format_pydantic_error_with_int_parsing(middleware: PromptErrorMiddleware) -> None:
    """Test formatting of int_parsing validation error."""
    try:
        from pydantic import BaseModel

        class TestModel(BaseModel):
            product_id: int

        TestModel(product_id="product")  # type: ignore[arg-type]
    except ValidationError as ve:
        result = middleware._format_pydantic_error(ve)

        # Check formatting
        assert "❌ Invalid argument 'product_id'" in result
        assert "💡 You provided: 'product'" in result
        assert "Expected: numeric ID" in result
        assert "list_products" in result
        assert "Examples:" in result


@pytest.mark.unit
def test_extract_prompt_name(middleware: PromptErrorMiddleware) -> None:
    """Test extraction of prompt name from error message."""
    # Test various formats
    assert (
        middleware._extract_prompt_name("Error rendering prompt 'analyze-product-quality'.")
        == "analyze-product-quality"
    )
    assert (
        middleware._extract_prompt_name("Error rendering prompt analyze-product-quality.")
        == "analyze-product-quality"
    )
    assert middleware._extract_prompt_name("Some other error") is None


@pytest.mark.unit
def test_passthrough_mcp_error(middleware: PromptErrorMiddleware) -> None:
    """Test that McpError is passed through unchanged."""
    from mcp.types import ErrorData

    original_error = McpError(ErrorData(code=-32600, message="Test error"))

    result = middleware._transform_error(original_error)

    # Should be the same error object
    assert result is original_error
