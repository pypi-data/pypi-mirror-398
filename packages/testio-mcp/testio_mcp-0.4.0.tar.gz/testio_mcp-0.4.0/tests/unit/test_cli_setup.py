"""Unit tests for CLI setup command.

Tests validation, token preview, API connectivity, and file operations.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from testio_mcp.cli.setup import (
    check_api_connectivity,
    display_token_url,
    handle_file_overwrite,
    prompt_customer_id,
    prompt_customer_name,
    prompt_log_format,
    prompt_log_level,
    prompt_product_ids,
    show_confirmation_summary,
    show_success_message,
    show_token_preview,
    validate_customer_name,
    validate_token_format,
    validate_token_with_retry,
    write_env_file,
)


@pytest.mark.unit
class TestCustomerNameValidation:
    """Test customer name/subdomain validation."""

    def test_valid_alphanumeric_only(self) -> None:
        """Verify alphanumeric-only subdomains pass validation."""
        validate_customer_name("customerName")
        validate_customer_name("test123")
        validate_customer_name("MyCompany456")

    def test_valid_with_hyphens(self) -> None:
        """Verify subdomains with hyphens pass validation."""
        validate_customer_name("customer-name")
        validate_customer_name("test-123")
        validate_customer_name("my-company-456")

    def test_invalid_empty_string(self) -> None:
        """Verify empty subdomain is rejected."""
        with pytest.raises(ValueError, match="Subdomain cannot be empty"):
            validate_customer_name("")

    def test_invalid_underscores(self) -> None:
        """Verify underscores are rejected."""
        with pytest.raises(ValueError, match="Invalid subdomain format"):
            validate_customer_name("customer_name")

    def test_invalid_spaces(self) -> None:
        """Verify spaces are rejected."""
        with pytest.raises(ValueError, match="Invalid subdomain format"):
            validate_customer_name("customer name")

    def test_invalid_leading_hyphen(self) -> None:
        """Verify leading hyphens are rejected."""
        with pytest.raises(ValueError, match="Invalid subdomain format"):
            validate_customer_name("-invalid")

    def test_invalid_trailing_hyphen(self) -> None:
        """Verify trailing hyphens are rejected."""
        with pytest.raises(ValueError, match="Invalid subdomain format"):
            validate_customer_name("invalid-")

    def test_invalid_too_long(self) -> None:
        """Verify subdomains >63 chars are rejected."""
        long_name = "a" * 64  # Exceeds DNS subdomain limit
        with pytest.raises(ValueError, match="must be between"):
            validate_customer_name(long_name)

    def test_valid_max_length(self) -> None:
        """Verify 63-char subdomains pass validation."""
        max_length_name = "a" * 63
        validate_customer_name(max_length_name)


@pytest.mark.unit
class TestTokenFormatValidation:
    """Test API token format validation."""

    def test_valid_token_alphanumeric(self) -> None:
        """Verify alphanumeric tokens ≥40 chars pass validation."""
        validate_token_format("a" * 40)
        validate_token_format("0123456789abcdefghijklmnopqrstuvwxyzABCD")

    def test_valid_token_with_dashes_underscores(self) -> None:
        """Verify tokens with dashes/underscores pass validation."""
        validate_token_format("abcd-efgh-1234-5678-abcd-efgh-1234-56789")  # 41 chars
        validate_token_format("abcd_efgh_1234_5678_abcd_efgh_1234_56789")  # 41 chars

    def test_invalid_too_short(self) -> None:
        """Verify tokens <40 chars are rejected."""
        with pytest.raises(ValueError, match="Token too short"):
            validate_token_format("a" * 39)

    def test_invalid_special_characters(self) -> None:
        """Verify tokens with special characters are rejected."""
        with pytest.raises(ValueError, match="Invalid token format"):
            # 42 chars with special chars
            validate_token_format("abcd@efgh!1234#5678$abcd%efgh^1234&56789")


@pytest.mark.unit
class TestTokenPreview:
    """Test token preview masking."""

    def test_preview_format(self, capsys: pytest.CaptureFixture) -> None:
        """Verify token preview shows first/last 4 chars and length."""
        token = "abcdefghijklmnopqrstuvwxyz1234567890"  # pragma: allowlist secret
        show_token_preview(token)

        captured = capsys.readouterr()
        assert "abcd" in captured.out  # First 4 chars
        assert "7890" in captured.out  # Last 4 chars
        assert f"({len(token)} characters)" in captured.out
        assert "●●●●" in captured.out  # Masking bullets

    def test_preview_hides_middle(self, capsys: pytest.CaptureFixture) -> None:
        """Verify middle characters are masked."""
        token = "abcd1234MIDDLE5678xyz9"
        show_token_preview(token)

        captured = capsys.readouterr()
        assert "MIDDLE" not in captured.out  # Middle should be hidden


@pytest.mark.unit
class TestPromptCustomerName:
    """Test customer name prompt function."""

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_valid_input_returned(self, mock_ask: MagicMock) -> None:
        """Verify valid customer name is returned."""
        mock_ask.return_value = "customerName"
        result = prompt_customer_name()
        assert result == "customerName"

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_invalid_input_retries(self, mock_ask: MagicMock) -> None:
        """Verify invalid input triggers retry loop."""
        mock_ask.side_effect = ["invalid_name", "customer-name"]
        result = prompt_customer_name()
        assert result == "customer-name"
        assert mock_ask.call_count == 2

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_keyboard_interrupt_exits(self, mock_ask: MagicMock) -> None:
        """Verify Ctrl+C exits gracefully."""
        mock_ask.side_effect = KeyboardInterrupt()
        with pytest.raises(SystemExit):
            prompt_customer_name()


@pytest.mark.unit
class TestDisplayTokenUrl:
    """Test token URL display function."""

    def test_url_format(self, capsys: pytest.CaptureFixture) -> None:
        """Verify correct URL is displayed."""
        display_token_url("customerName")
        captured = capsys.readouterr()
        assert "https://customerName.test.io/api_integrations" in captured.out
        assert "🔑" in captured.out


@pytest.mark.unit
class TestPromptCustomerId:
    """Test customer ID prompt function."""

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_default_value_used(self, mock_ask: MagicMock) -> None:
        """Verify default customer ID is '1'."""
        mock_ask.return_value = "1"
        result = prompt_customer_id()
        assert result == "1"

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_custom_value_accepted(self, mock_ask: MagicMock) -> None:
        """Verify custom customer IDs are accepted."""
        mock_ask.return_value = "12345"
        result = prompt_customer_id()
        assert result == "12345"

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_keyboard_interrupt_exits(self, mock_ask: MagicMock) -> None:
        """Verify Ctrl+C exits gracefully."""
        mock_ask.side_effect = KeyboardInterrupt()
        with pytest.raises(SystemExit):
            prompt_customer_id()


@pytest.mark.unit
class TestPromptLogFormat:
    """Test log format prompt function."""

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_text_format_selected(self, mock_ask: MagicMock) -> None:
        """Verify choice '1' returns 'text'."""
        mock_ask.return_value = "1"
        result = prompt_log_format()
        assert result == "text"

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_json_format_selected(self, mock_ask: MagicMock) -> None:
        """Verify choice '2' returns 'json'."""
        mock_ask.return_value = "2"
        result = prompt_log_format()
        assert result == "json"

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_keyboard_interrupt_exits(self, mock_ask: MagicMock) -> None:
        """Verify Ctrl+C exits gracefully."""
        mock_ask.side_effect = KeyboardInterrupt()
        with pytest.raises(SystemExit):
            prompt_log_format()


@pytest.mark.unit
class TestPromptLogLevel:
    """Test log level prompt function."""

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_info_level_selected(self, mock_ask: MagicMock) -> None:
        """Verify choice '1' returns 'INFO'."""
        mock_ask.return_value = "1"
        result = prompt_log_level()
        assert result == "INFO"

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_debug_level_selected(self, mock_ask: MagicMock) -> None:
        """Verify choice '2' returns 'DEBUG'."""
        mock_ask.return_value = "2"
        result = prompt_log_level()
        assert result == "DEBUG"

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_warning_level_selected(self, mock_ask: MagicMock) -> None:
        """Verify choice '3' returns 'WARNING'."""
        mock_ask.return_value = "3"
        result = prompt_log_level()
        assert result == "WARNING"

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_keyboard_interrupt_exits(self, mock_ask: MagicMock) -> None:
        """Verify Ctrl+C exits gracefully."""
        mock_ask.side_effect = KeyboardInterrupt()
        with pytest.raises(SystemExit):
            prompt_log_level()


@pytest.mark.unit
class TestPromptProductIds:
    """Test product IDs prompt function."""

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_product_ids_provided(self, mock_ask: MagicMock) -> None:
        """Verify product IDs are returned as-is."""
        mock_ask.return_value = "598,1024,25073"
        result = prompt_product_ids()
        assert result == "598,1024,25073"

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_empty_returns_empty_string(self, mock_ask: MagicMock) -> None:
        """Verify empty input returns empty string."""
        mock_ask.return_value = ""
        result = prompt_product_ids()
        assert result == ""

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_whitespace_trimmed(self, mock_ask: MagicMock) -> None:
        """Verify leading/trailing whitespace is trimmed."""
        mock_ask.return_value = "  598, 1024  "
        result = prompt_product_ids()
        assert result == "598, 1024"

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_keyboard_interrupt_exits(self, mock_ask: MagicMock) -> None:
        """Verify Ctrl+C exits gracefully."""
        mock_ask.side_effect = KeyboardInterrupt()
        with pytest.raises(SystemExit):
            prompt_product_ids()


@pytest.mark.unit
@pytest.mark.asyncio
class TestApiConnectivityTest:
    """Test API connectivity validation using TestIOClient (SEC-002 compliant)."""

    async def test_success_200_returns_true(self) -> None:
        """Verify successful API call returns success."""
        with patch("testio_mcp.client.TestIOClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = {"products": []}
            mock_client_class.return_value.__aenter__.return_value = mock_client

            success, error_msg = await check_api_connectivity("valid_token", "customer")

            assert success is True
            assert error_msg == ""

    async def test_failure_401_returns_false(self) -> None:
        """Verify 401 error returns failure."""
        from testio_mcp.exceptions import TestIOAPIError

        with patch("testio_mcp.client.TestIOClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = TestIOAPIError(
                message="Authentication failed", status_code=401
            )
            mock_client_class.return_value.__aenter__.return_value = mock_client

            success, error_msg = await check_api_connectivity("invalid_token", "customer")

            assert success is False
            assert "401 Unauthorized" in error_msg

    async def test_failure_403_returns_false(self) -> None:
        """Verify 403 error returns failure."""
        from testio_mcp.exceptions import TestIOAPIError

        with patch("testio_mcp.client.TestIOClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = TestIOAPIError(message="Access denied", status_code=403)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            success, error_msg = await check_api_connectivity("forbidden_token", "customer")

            assert success is False
            assert "403 Forbidden" in error_msg

    async def test_connection_error_returns_false(self) -> None:
        """Verify connection errors return failure with generic message (SEC-002)."""
        with patch("testio_mcp.client.TestIOClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("Network error with token details")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            success, error_msg = await check_api_connectivity("token", "customer")

            assert success is False
            assert "Connection failed" in error_msg
            # Verify generic message doesn't leak exception details (SEC-002)
            assert "Network error" not in error_msg
            assert "token" not in error_msg.lower()
            assert "check your network" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
class TestValidateTokenWithRetry:
    """Test token validation with retry flow."""

    async def test_success_returns_token(self) -> None:
        """Verify successful validation returns token."""
        with patch(
            "testio_mcp.cli.setup.check_api_connectivity", return_value=(True, "")
        ) as mock_test:
            result = await validate_token_with_retry("valid_token", "customer")
            assert result == "valid_token"
            mock_test.assert_called_once()

    async def test_retry_with_new_token(self) -> None:
        """Verify retry option allows entering new token."""
        with patch("testio_mcp.cli.setup.check_api_connectivity") as mock_test:
            mock_test.side_effect = [
                (False, "Invalid token"),  # First attempt fails
                (True, ""),  # Second attempt succeeds
            ]

            with patch("testio_mcp.cli.setup.Prompt.ask") as mock_prompt:
                mock_prompt.side_effect = [
                    "1",  # Choose retry
                ]

                with patch("testio_mcp.cli.setup.prompt_api_token", return_value="new_token"):
                    result = await validate_token_with_retry("old_token", "customer")
                    assert result == "new_token"

    async def test_force_save_confirmed(self) -> None:
        """Verify force save option skips validation."""
        with patch("testio_mcp.cli.setup.check_api_connectivity", return_value=(False, "Error")):
            with patch("testio_mcp.cli.setup.Prompt.ask", return_value="2"):  # Choose force save
                with patch("testio_mcp.cli.setup.Confirm.ask", return_value=True):  # Confirm
                    result = await validate_token_with_retry("unvalidated", "customer")
                    assert result == "unvalidated"

    async def test_cancel_exits(self) -> None:
        """Verify cancel option exits."""
        with patch("testio_mcp.cli.setup.check_api_connectivity", return_value=(False, "Error")):
            with patch("testio_mcp.cli.setup.Prompt.ask", return_value="3"):  # Choose cancel
                with pytest.raises(SystemExit):
                    await validate_token_with_retry("token", "customer")


@pytest.mark.unit
class TestConfirmationSummary:
    """Test confirmation summary display and options."""

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_save_option_returns_save(self, mock_ask: MagicMock) -> None:
        """Verify 'S' option returns 'save'."""
        mock_ask.return_value = "S"
        config = {
            "customer_name": "test",
            "token": "a" * 40,
            "customer_id": "1",
            "file_path": Path("/tmp/test.env"),
        }
        result = show_confirmation_summary(config)
        assert result == "save"

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_edit_option_returns_edit(self, mock_ask: MagicMock) -> None:
        """Verify 'E' option returns 'edit'."""
        mock_ask.return_value = "E"
        config = {
            "customer_name": "test",
            "token": "a" * 40,
            "customer_id": "1",
            "file_path": Path("/tmp/test.env"),
        }
        result = show_confirmation_summary(config)
        assert result == "edit"

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_cancel_option_returns_cancel(self, mock_ask: MagicMock) -> None:
        """Verify 'C' option returns 'cancel'."""
        mock_ask.return_value = "C"
        config = {
            "customer_name": "test",
            "token": "a" * 40,
            "customer_id": "1",
            "file_path": Path("/tmp/test.env"),
        }
        result = show_confirmation_summary(config)
        assert result == "cancel"

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_displays_new_settings(
        self, mock_ask: MagicMock, capsys: pytest.CaptureFixture
    ) -> None:
        """Verify new settings are displayed in summary."""
        mock_ask.return_value = "S"
        config = {
            "customer_name": "test",
            "token": "a" * 40,
            "customer_id": "1",
            "log_format": "text",
            "log_level": "DEBUG",
            "product_ids": "598,1024",
            "file_path": Path("/tmp/test.env"),
        }
        result = show_confirmation_summary(config)

        captured = capsys.readouterr()
        assert "text" in captured.out  # Log format
        assert "DEBUG" in captured.out  # Log level
        assert "598,1024" in captured.out  # Product IDs
        assert result == "save"

    @patch("testio_mcp.cli.setup.Prompt.ask")
    def test_displays_all_products_when_empty(
        self, mock_ask: MagicMock, capsys: pytest.CaptureFixture
    ) -> None:
        """Verify 'All products' displayed when product_ids is empty."""
        mock_ask.return_value = "S"
        config = {
            "customer_name": "test",
            "token": "a" * 40,
            "customer_id": "1",
            "log_format": "json",
            "log_level": "INFO",
            "product_ids": "",
            "file_path": Path("/tmp/test.env"),
        }
        result = show_confirmation_summary(config)

        captured = capsys.readouterr()
        assert "All products" in captured.out
        assert result == "save"


@pytest.mark.unit
class TestFileOverwriteHandling:
    """Test file overwrite and backup logic."""

    def test_no_file_returns_immediately(self, tmp_path: Path) -> None:
        """Verify function returns if file doesn't exist."""
        env_path = tmp_path / ".testio-mcp.env"
        handle_file_overwrite(env_path)  # Should not raise

    def test_overwrite_confirmed_creates_backup(self, tmp_path: Path) -> None:
        """Verify backup is created when overwrite is confirmed."""
        env_path = tmp_path / ".testio-mcp.env"
        env_path.write_text("old_content")

        with patch("testio_mcp.cli.setup.Confirm.ask", return_value=True):
            handle_file_overwrite(env_path)

        backup_path = env_path.with_suffix(".env.backup")
        assert backup_path.exists()
        assert backup_path.read_text() == "old_content"

    def test_overwrite_declined_exits(self, tmp_path: Path) -> None:
        """Verify exit when overwrite is declined."""
        env_path = tmp_path / ".testio-mcp.env"
        env_path.write_text("old_content")

        with patch("testio_mcp.cli.setup.Confirm.ask", return_value=False):
            with pytest.raises(SystemExit):
                handle_file_overwrite(env_path)


@pytest.mark.unit
class TestWriteEnvFile:
    """Test environment file writing and permissions."""

    def test_file_content_format(self, tmp_path: Path) -> None:
        """Verify file contains correct environment variables."""
        env_path = tmp_path / ".testio-mcp.env"
        config = {
            "customer_name": "testCustomer",
            "token": "test_token_12345",
            "customer_id": "999",
            "log_format": "text",
            "log_level": "DEBUG",
            "product_ids": "598,1024",
            "file_path": env_path,
        }

        write_env_file(config)

        content = env_path.read_text()
        assert "TESTIO_CUSTOMER_API_TOKEN=test_token_12345" in content
        assert "TESTIO_CUSTOMER_API_BASE_URL=https://api.test.io/customer/v2" in content
        assert "TESTIO_CUSTOMER_NAME=testCustomer" in content
        assert "TESTIO_CUSTOMER_ID=999" in content
        assert "LOG_FORMAT=text" in content
        assert "LOG_LEVEL=DEBUG" in content
        assert "TESTIO_PRODUCT_IDS=598,1024" in content

    def test_file_content_without_product_ids(self, tmp_path: Path) -> None:
        """Verify file includes commented TESTIO_PRODUCT_IDS when empty."""
        env_path = tmp_path / ".testio-mcp.env"
        config = {
            "customer_name": "testCustomer",
            "token": "test_token_12345",
            "customer_id": "999",
            "log_format": "json",
            "log_level": "INFO",
            "product_ids": "",
            "file_path": env_path,
        }

        write_env_file(config)

        content = env_path.read_text()
        # Should include commented example for discoverability
        assert "# TESTIO_PRODUCT_IDS=" in content
        assert "Optional: filter to specific products" in content
        assert "LOG_FORMAT=json" in content
        assert "LOG_LEVEL=INFO" in content

    def test_file_permissions_secure(self, tmp_path: Path) -> None:
        """Verify file permissions are 0o600 (user read/write only) on Unix systems.

        Note: Windows doesn't support Unix-style permissions (uses ACLs instead),
        so chmod(0o600) doesn't set the same permission bits on Windows.
        We skip the strict permission check on Windows.
        """
        import stat
        import sys

        env_path = tmp_path / ".testio-mcp.env"
        config = {
            "customer_name": "test",
            "token": "a" * 40,
            "customer_id": "1",
            "file_path": env_path,
        }

        write_env_file(config)

        # Check permissions (user read/write only on Unix)
        mode = env_path.stat().st_mode

        if sys.platform == "win32":
            # On Windows, just verify the file was created
            # Windows uses ACLs, not Unix permission bits
            assert env_path.exists()
        else:
            # On Unix-like systems, verify 0o600 permissions
            assert stat.S_IMODE(mode) == 0o600


@pytest.mark.unit
class TestSuccessMessage:
    """Test success message display."""

    def test_success_message_format(self, capsys: pytest.CaptureFixture, tmp_path: Path) -> None:
        """Verify success message contains next steps."""
        env_path = tmp_path / ".testio-mcp.env"
        show_success_message(env_path)

        captured = capsys.readouterr()
        assert "✅ Configuration saved!" in captured.out
        assert "Config:" in captured.out
        # Note: "Docs:" only appears if copy_docs_to_config_dir() succeeds
        # In editable install mode, docs may not be bundled
        assert "Next:" in captured.out
        assert "uvx testio-mcp serve" in captured.out
        assert "http://127.0.0.1:8080/docs" in captured.out
        assert "http://127.0.0.1:8080/health" in captured.out
