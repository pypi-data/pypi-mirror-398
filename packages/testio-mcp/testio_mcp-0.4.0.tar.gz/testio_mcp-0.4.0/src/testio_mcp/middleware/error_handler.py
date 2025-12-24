"""Custom error handling middleware for user-friendly prompt error messages.

This middleware extends FastMCP's ErrorHandlingMiddleware to provide better
error messages for prompt validation failures.
"""

import logging
import re

from fastmcp.exceptions import PromptError
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
from mcp import McpError
from mcp.types import ErrorData
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class PromptErrorMiddleware(ErrorHandlingMiddleware):
    """Middleware that provides user-friendly error messages for prompt validation failures.

    This middleware catches:
    1. PromptError - Raised when prompt rendering fails
    2. ValidationError - Raised by Pydantic when argument types don't match

    It transforms technical validation errors into friendly guidance with:
    - ❌ Clear error description
    - ℹ️ Context about what went wrong
    - 💡 How to fix it
    """

    def __init__(self) -> None:
        """Initialize middleware with user-friendly error transformation."""
        super().__init__(
            include_traceback=False,  # Don't include tracebacks in user-facing errors
            transform_errors=True,  # Transform errors to MCP format
        )

    def _transform_error(self, error: Exception) -> Exception:
        """Transform errors into user-friendly MCP errors.

        Args:
            error: The exception to transform

        Returns:
            Transformed McpError with friendly message, or original error
        """
        # Let parent handle McpError as-is
        if isinstance(error, McpError):
            return error

        # Handle PromptError (prompt rendering failed)
        if isinstance(error, PromptError):
            return self._handle_prompt_error(error)

        # Handle Pydantic ValidationError (argument validation failed)
        if isinstance(error, ValidationError):
            return self._handle_validation_error(error)

        # Let parent handle other errors
        return super()._transform_error(error)

    def _handle_prompt_error(self, error: PromptError) -> McpError:
        """Transform PromptError into user-friendly McpError.

        Args:
            error: The PromptError exception

        Returns:
            McpError with friendly message
        """
        error_str = str(error)
        prompt_name = self._extract_prompt_name(error_str)

        # Check if the PromptError has a __cause__ with the actual validation error
        if error.__cause__ is not None:
            cause_str = str(error.__cause__)
            logger.debug(f"PromptError cause: {cause_str}")

            # Check if the cause is a Pydantic validation error
            if isinstance(error.__cause__, ValidationError):
                # Use the actual ValidationError for better messages
                friendly_message = self._format_pydantic_error(error.__cause__)
                logger.warning(f"Prompt validation error caught: {friendly_message}")
                return McpError(ErrorData(code=-32602, message=friendly_message))
            elif (
                "validation error" in cause_str.lower()
                or "unable to parse string" in cause_str.lower()
            ):
                # Parse the cause string for validation details
                friendly_message = self._format_validation_error(cause_str, prompt_name)
                logger.warning(f"Prompt error caught by middleware: {friendly_message}")
                return McpError(ErrorData(code=-32602, message=friendly_message))

        # Fallback: parse the error string itself
        if "validation error" in error_str.lower() or "unable to parse string" in error_str.lower():
            friendly_message = self._format_validation_error(error_str, prompt_name)
        else:
            # Generic PromptError - include the full error for debugging
            friendly_message = (
                f"❌ Prompt error: {error_str}\n\n"
                f"ℹ️ This prompt may have invalid arguments or configuration.\n"
                f"💡 Check the prompt documentation or use the correct argument types."
            )

        logger.warning(f"Prompt error caught by middleware: {friendly_message}")

        return McpError(ErrorData(code=-32602, message=friendly_message))  # Invalid params

    def _handle_validation_error(self, error: ValidationError) -> McpError:
        """Transform Pydantic ValidationError into user-friendly McpError.

        Args:
            error: The ValidationError exception

        Returns:
            McpError with friendly message
        """
        friendly_message = self._format_pydantic_error(error)
        logger.warning(f"Validation error caught by middleware: {friendly_message}")

        return McpError(ErrorData(code=-32602, message=friendly_message))

    def _extract_prompt_name(self, error_str: str) -> str | None:
        """Extract prompt name from error message.

        Args:
            error_str: The error message string

        Returns:
            The prompt name if found, None otherwise
        """
        # Look for patterns like "prompt 'analyze-product-quality'"
        # or "prompt analyze-product-quality"
        match = re.search(r"prompt ['\"]?([a-z-]+)['\"]?", error_str)
        return match.group(1) if match else None

    def _format_validation_error(self, error_str: str, prompt_name: str | None) -> str:
        """Format Pydantic validation error into user-friendly message.

        Args:
            error_str: The raw error string
            prompt_name: The name of the prompt that failed

        Returns:
            Formatted error message with guidance
        """
        # Extract key information from Pydantic error
        if "unable to parse string as an integer" in error_str.lower():
            param_name = "argument"
            invalid_value = "unknown"

            # Try to extract parameter name and value
            import re

            param_match = re.search(r"argument ['\"]?(\w+)['\"]?", error_str)
            if param_match:
                param_name = param_match.group(1)

            value_match = re.search(r"input_value=['\"]?(\w+)['\"]?", error_str)
            if value_match:
                invalid_value = value_match.group(1)

            prompt_guidance = ""
            if prompt_name == "analyze-product-quality":
                prompt_guidance = (
                    "\n\n💡 Usage:\n"
                    "   Correct:   /testio-mcp:analyze-product-quality 24734\n"
                    '   Correct:   /testio-mcp:analyze-product-quality 24734 "Q3 2025"\n'
                    "   Incorrect: /testio-mcp:analyze-product-quality product 24734  ❌\n\n"
                    "ℹ️  Use 'list_products' tool to find product IDs."
                )

            return (
                f"❌ Invalid {param_name}: expected integer, got '{invalid_value}'\n\n"
                f"ℹ️ The prompt '{prompt_name}' requires numeric IDs, not text labels."
                f"{prompt_guidance}"
            )

        # Generic validation error
        return (
            f"❌ Validation error: Invalid argument type\n\n"
            f"ℹ️ {error_str}\n\n"
            f"💡 Check that all arguments match the expected types (integers, strings, etc.)"
        )

    def _format_pydantic_error(self, error: ValidationError) -> str:
        """Format Pydantic ValidationError into user-friendly message.

        Args:
            error: The Pydantic validation error

        Returns:
            Formatted error message with guidance
        """
        errors = error.errors()
        if not errors:
            return "❌ Validation error occurred"

        # Take first error for simplicity
        first_error = errors[0]
        field = ".".join(str(loc) for loc in first_error["loc"])
        msg = first_error["msg"]
        error_type = first_error["type"]
        input_value = first_error.get("input", "unknown")

        # Build base error message
        base_msg = f"❌ Invalid argument '{field}': {msg}\n\n"

        # Add specific guidance based on error type
        if error_type == "int_parsing":
            guidance = (
                f"💡 You provided: '{input_value}' (text)\n"
                f"   Expected: numeric ID (e.g., 24734)\n\n"
                f"ℹ️  Use 'list_products' tool to find product IDs.\n\n"
                f"Examples:\n"
                f"  Correct:   /testio-mcp:analyze-product-quality 24734\n"
                f"  Incorrect: /testio-mcp:analyze-product-quality product 24734  ❌"
            )
        elif error_type in ("string_type", "str_type"):
            guidance = (
                f"💡 Expected a string value, got: {type(input_value).__name__}\n"
                f"   Wrap text arguments in quotes if they contain spaces."
            )
        else:
            guidance = (
                f"💡 Check the argument type and value.\n"
                f"   Provided: {input_value} ({type(input_value).__name__})\n"
                f"   Error: {error_type}"
            )

        return base_msg + guidance
