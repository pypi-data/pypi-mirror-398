"""Custom exceptions for TestIO MCP Server.

This module defines domain exceptions raised by services and converted
to transport-specific formats (MCP error messages, HTTP status codes) by
the tool/controller layer.
"""


class TestIOException(Exception):
    """Base exception for all TestIO MCP errors."""

    pass


class TestNotFoundException(TestIOException):
    """Test not found (404 from TestIO API).

    Raised when:
    - Requested test ID doesn't exist
    - Test has been deleted
    - User doesn't have access to test
    """

    __test__ = False  # Not a pytest test class

    def __init__(self, test_id: int, message: str | None = None):
        """Initialize test not found exception.

        Args:
            test_id: The test ID that wasn't found (integer from API)
            message: Optional custom message
        """
        self.test_id = test_id
        self.message = message or f"Test {test_id} not found"
        super().__init__(self.message)


class TestIOAPIError(TestIOException):
    """TestIO API returned an error (4xx/5xx status code).

    Raised when:
    - Authentication fails (401)
    - Rate limit exceeded (429)
    - Server error (5xx)
    - Other HTTP errors
    """

    __test__ = False  # Not a pytest test class

    def __init__(self, message: str, status_code: int):
        """Initialize API error.

        Args:
            message: Error message (already sanitized by client)
            status_code: HTTP status code from API
        """
        self.message = message
        self.status_code = status_code
        super().__init__(f"API error ({status_code}): {message}")


class ProductNotFoundException(TestIOException):
    """Product not found (404 from TestIO API).

    Raised when:
    - Requested product ID doesn't exist
    - Product has been deleted
    - User doesn't have access to product

    Used in Stories 3-6 for product-related operations.
    """

    __test__ = False  # Not a pytest test class

    def __init__(self, product_id: int | list[int], message: str | None = None):
        """Initialize product not found exception.

        Args:
            product_id: The product ID(s) that weren't found (single int or list)
            message: Optional custom message
        """
        self.product_id = product_id
        if message:
            self.message = message
        elif isinstance(product_id, list):
            ids_str = ", ".join(str(pid) for pid in product_id)
            self.message = f"Products not found: {ids_str}"
        else:
            self.message = f"Product {product_id} not found"
        super().__init__(self.message)


class FeatureNotFoundException(TestIOException):
    """Feature not found in local database.

    Raised when:
    - Requested feature ID doesn't exist
    - Feature has been deleted
    - Feature not yet synced

    STORY-057: Added for get_feature_summary tool.
    """

    __test__ = False  # Not a pytest test class

    def __init__(self, feature_id: int, message: str | None = None):
        """Initialize feature not found exception.

        Args:
            feature_id: The feature ID that wasn't found
            message: Optional custom message
        """
        self.feature_id = feature_id
        self.message = message or f"Feature {feature_id} not found"
        super().__init__(self.message)


class UserNotFoundException(TestIOException):
    """User not found in local database.

    Raised when:
    - Requested user ID doesn't exist
    - User has been deleted
    - User not yet synced

    STORY-057: Added for get_user_summary tool.
    """

    __test__ = False  # Not a pytest test class

    def __init__(self, user_id: int, message: str | None = None):
        """Initialize user not found exception.

        Args:
            user_id: The user ID that wasn't found
            message: Optional custom message
        """
        self.user_id = user_id
        self.message = message or f"User {user_id} not found"
        super().__init__(self.message)


class ValidationError(TestIOException):
    """Input validation error.

    Raised when:
    - Invalid parameters provided
    - Out of range values
    - Invalid continuation tokens
    """

    def __init__(self, field: str, message: str):
        """Initialize validation error.

        Args:
            field: Field name that failed validation
            message: Validation error message
        """
        self.field = field
        self.message = message
        super().__init__(f"Validation error ({field}): {message}")


class BugNotFoundException(TestIOException):
    """Bug not found in local database.

    Raised when:
    - Requested bug ID doesn't exist
    - Bug has been deleted
    - Bug not yet synced

    STORY-085: Added for get_bug_summary tool.
    """

    __test__ = False  # Not a pytest test class

    def __init__(self, bug_id: int, message: str | None = None):
        """Initialize bug not found exception.

        Args:
            bug_id: The bug ID that wasn't found
            message: Optional custom message
        """
        self.bug_id = bug_id
        self.message = message or f"Bug {bug_id} not found"
        super().__init__(self.message)


class InvalidSearchQueryError(TestIOException):
    """Invalid search query error.

    Raised when:
    - Search query is empty
    - Search query is too short
    - Search query has invalid FTS5 syntax

    STORY-065: Added for search MCP tool.
    """

    def __init__(self, message: str):
        """Initialize invalid search query error.

        Args:
            message: Error message describing the issue
        """
        self.message = message
        super().__init__(message)


class TestProductMismatchError(TestIOException):
    """Test does not belong to the specified product(s).

    Raised when:
    - A test_id is provided that belongs to a different product
    - Used in generate_quality_report when test_ids filter references tests outside product_ids

    PQR Refactor: Added for multi-product quality report validation.
    """

    __test__ = False  # Not a pytest test class

    def __init__(
        self,
        test_id: int,
        actual_product_id: int,
        allowed_product_ids: list[int],
        message: str | None = None,
    ):
        """Initialize test product mismatch error.

        Args:
            test_id: The test ID that doesn't match
            actual_product_id: The product the test actually belongs to
            allowed_product_ids: The product IDs that were specified in the query
            message: Optional custom message
        """
        self.test_id = test_id
        self.actual_product_id = actual_product_id
        self.allowed_product_ids = allowed_product_ids
        self.message = (
            message
            or f"Test {test_id} belongs to product {actual_product_id}, "
            f"not in product_ids {allowed_product_ids}"
        )
        super().__init__(self.message)
