"""Unit tests for configuration management (STORY-015)."""

import pytest
from pydantic import ValidationError

from testio_mcp.config import Settings


@pytest.mark.unit
class TestToolEnablementConfiguration:
    """Test tool enable/disable configuration fields."""

    def test_enabled_tools_comma_separated(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test ENABLED_TOOLS with comma-separated string."""
        monkeypatch.setenv("TESTIO_CUSTOMER_API_TOKEN", "test_token")
        monkeypatch.setenv("ENABLED_TOOLS", "health_check,list_products")

        settings = Settings()

        assert settings.ENABLED_TOOLS == ["health_check", "list_products"]

    def test_enabled_tools_json_array(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test ENABLED_TOOLS with JSON array."""
        monkeypatch.setenv("TESTIO_CUSTOMER_API_TOKEN", "test_token")
        monkeypatch.setenv("ENABLED_TOOLS", '["health_check", "list_products"]')

        settings = Settings()

        assert settings.ENABLED_TOOLS == ["health_check", "list_products"]

    def test_enabled_tools_with_spaces(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test ENABLED_TOOLS with spaces around commas."""
        monkeypatch.setenv("TESTIO_CUSTOMER_API_TOKEN", "test_token")
        monkeypatch.setenv("ENABLED_TOOLS", "health_check, list_products, get_test_status")

        settings = Settings()

        assert settings.ENABLED_TOOLS == [
            "health_check",
            "list_products",
            "get_test_status",
        ]

    def test_disabled_tools_comma_separated(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test DISABLED_TOOLS with comma-separated string."""
        monkeypatch.setenv("TESTIO_CUSTOMER_API_TOKEN", "test_token")
        monkeypatch.setenv("DISABLED_TOOLS", "generate_status_report")

        settings = Settings()

        assert settings.DISABLED_TOOLS == ["generate_status_report"]

    def test_disabled_tools_json_array(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test DISABLED_TOOLS with JSON array."""
        monkeypatch.setenv("TESTIO_CUSTOMER_API_TOKEN", "test_token")
        monkeypatch.setenv(
            "DISABLED_TOOLS", '["generate_status_report", "get_test_activity_by_timeframe"]'
        )

        settings = Settings()

        assert settings.DISABLED_TOOLS == [
            "generate_status_report",
            "get_test_activity_by_timeframe",
        ]

    def test_mutual_exclusion_validation_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that setting both ENABLED_TOOLS and DISABLED_TOOLS raises ValidationError."""
        monkeypatch.setenv("TESTIO_CUSTOMER_API_TOKEN", "test_token")
        monkeypatch.setenv("ENABLED_TOOLS", "health_check")
        monkeypatch.setenv("DISABLED_TOOLS", "list_products")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        error_message = str(exc_info.value)
        assert "cannot be used simultaneously" in error_message.lower()

    def test_default_behavior_no_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default behavior when no tool configuration is provided."""
        monkeypatch.setenv("TESTIO_CUSTOMER_API_TOKEN", "test_token")

        settings = Settings()

        assert settings.ENABLED_TOOLS is None
        assert settings.DISABLED_TOOLS is None

    def test_empty_string_treated_as_empty_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that empty string is treated as empty list (no filtering)."""
        monkeypatch.setenv("TESTIO_CUSTOMER_API_TOKEN", "test_token")
        monkeypatch.setenv("ENABLED_TOOLS", "")

        settings = Settings()

        # Empty string becomes empty list after parsing
        assert settings.ENABLED_TOOLS == []

    def test_single_tool_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test enabling a single tool."""
        monkeypatch.setenv("TESTIO_CUSTOMER_API_TOKEN", "test_token")
        monkeypatch.setenv("ENABLED_TOOLS", "health_check")

        settings = Settings()

        assert settings.ENABLED_TOOLS == ["health_check"]

    def test_trailing_commas_handled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that trailing commas are handled correctly."""
        monkeypatch.setenv("TESTIO_CUSTOMER_API_TOKEN", "test_token")
        monkeypatch.setenv("ENABLED_TOOLS", "health_check,list_products,")

        settings = Settings()

        # Trailing comma should not create empty string
        assert settings.ENABLED_TOOLS == ["health_check", "list_products"]
