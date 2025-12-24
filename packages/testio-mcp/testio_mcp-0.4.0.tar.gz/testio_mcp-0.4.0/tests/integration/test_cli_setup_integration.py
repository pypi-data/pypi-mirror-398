"""Integration tests for CLI setup command.

Tests full setup flow with mocked API and user input.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from testio_mcp.cli.setup import run_setup_flow


@pytest.mark.integration
@pytest.mark.asyncio
class TestSetupFlowIntegration:
    """Integration test for complete setup workflow."""

    async def test_full_setup_flow_happy_path(self, tmp_path: Path) -> None:
        """Verify complete setup flow from prompts to file creation."""
        env_path = tmp_path / ".testio-mcp.env"

        # Mock all user inputs in sequence
        with patch("testio_mcp.cli.setup.prompt_customer_name", return_value="testCustomer"):
            with patch("testio_mcp.cli.setup.prompt_api_token", return_value="a" * 64):
                with patch("testio_mcp.cli.setup.prompt_customer_id", return_value="999"):
                    with patch("testio_mcp.cli.setup.prompt_log_format", return_value="text"):
                        with patch("testio_mcp.cli.setup.prompt_log_level", return_value="DEBUG"):
                            with patch(
                                "testio_mcp.cli.setup.prompt_product_ids", return_value="598,1024"
                            ):
                                with patch(
                                    "testio_mcp.cli.setup.prompt_disable_capabilities_tool",
                                    return_value=True,
                                ):
                                    with patch(
                                        "testio_mcp.cli.setup.check_api_connectivity",
                                        return_value=(True, ""),
                                    ):
                                        with patch(
                                            "testio_mcp.cli.setup.show_confirmation_summary",
                                            return_value="save",
                                        ):
                                            with patch(
                                                "testio_mcp.cli.setup.Path.home",
                                                return_value=tmp_path,
                                            ):
                                                await run_setup_flow()

        # Verify file was created
        assert env_path.exists()

        # Verify file content
        content = env_path.read_text()
        assert "TESTIO_CUSTOMER_API_TOKEN=" in content
        assert "TESTIO_CUSTOMER_API_BASE_URL=https://api.test.io/customer/v2" in content
        assert "TESTIO_CUSTOMER_NAME=testCustomer" in content
        assert "TESTIO_CUSTOMER_ID=999" in content
        assert "LOG_FORMAT=text" in content
        assert "LOG_LEVEL=DEBUG" in content
        assert "TESTIO_PRODUCT_IDS=598,1024" in content

        # Verify permissions (user read/write only)
        import stat

        mode = env_path.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600

    async def test_setup_flow_with_retry_and_force_save(self, tmp_path: Path) -> None:
        """Verify setup flow handles API validation failure with force save."""
        env_path = tmp_path / ".testio-mcp.env"

        # Mock API validation failure followed by force save
        with patch("testio_mcp.cli.setup.prompt_customer_name", return_value="testCustomer"):
            with patch("testio_mcp.cli.setup.prompt_api_token", return_value="a" * 64):
                with patch("testio_mcp.cli.setup.prompt_customer_id", return_value="1"):
                    with patch("testio_mcp.cli.setup.prompt_log_format", return_value="json"):
                        with patch("testio_mcp.cli.setup.prompt_log_level", return_value="INFO"):
                            with patch("testio_mcp.cli.setup.prompt_product_ids", return_value=""):
                                with patch(
                                    "testio_mcp.cli.setup.prompt_disable_capabilities_tool",
                                    return_value=True,
                                ):
                                    with patch(
                                        "testio_mcp.cli.setup.check_api_connectivity",
                                        return_value=(False, "API Error"),
                                    ):
                                        with patch(
                                            "testio_mcp.cli.setup.Prompt.ask", return_value="2"
                                        ):
                                            with patch(
                                                "testio_mcp.cli.setup.Confirm.ask",
                                                return_value=True,
                                            ):
                                                with patch(
                                                    "testio_mcp.cli.setup.show_confirmation_summary",
                                                    return_value="save",
                                                ):
                                                    with patch(
                                                        "testio_mcp.cli.setup.Path.home",
                                                        return_value=tmp_path,
                                                    ):
                                                        await run_setup_flow()

        # Verify file was created despite validation failure
        assert env_path.exists()
        content = env_path.read_text()
        assert "TESTIO_CUSTOMER_NAME=testCustomer" in content
        assert "LOG_FORMAT=json" in content
        assert "LOG_LEVEL=INFO" in content

    async def test_setup_flow_with_file_overwrite(self, tmp_path: Path) -> None:
        """Verify setup flow handles existing file with backup."""
        env_path = tmp_path / ".testio-mcp.env"
        backup_path = tmp_path / ".testio-mcp.env.backup"

        # Create existing file
        env_path.write_text("old_config")

        # Mock user confirming overwrite
        with patch("testio_mcp.cli.setup.prompt_customer_name", return_value="newCustomer"):
            with patch("testio_mcp.cli.setup.prompt_api_token", return_value="b" * 64):
                with patch("testio_mcp.cli.setup.prompt_customer_id", return_value="1"):
                    with patch("testio_mcp.cli.setup.prompt_log_format", return_value="text"):
                        with patch("testio_mcp.cli.setup.prompt_log_level", return_value="WARNING"):
                            with patch(
                                "testio_mcp.cli.setup.prompt_product_ids", return_value="598"
                            ):
                                with patch(
                                    "testio_mcp.cli.setup.prompt_disable_capabilities_tool",
                                    return_value=True,
                                ):
                                    with patch(
                                        "testio_mcp.cli.setup.check_api_connectivity",
                                        return_value=(True, ""),
                                    ):
                                        with patch(
                                            "testio_mcp.cli.setup.show_confirmation_summary",
                                            return_value="save",
                                        ):
                                            with patch(
                                                "testio_mcp.cli.setup.Confirm.ask",
                                                return_value=True,
                                            ):
                                                with patch(
                                                    "testio_mcp.cli.setup.Path.home",
                                                    return_value=tmp_path,
                                                ):
                                                    await run_setup_flow()

        # Verify backup was created
        assert backup_path.exists()
        assert backup_path.read_text() == "old_config"

        # Verify new file has updated content
        content = env_path.read_text()
        assert "TESTIO_CUSTOMER_NAME=newCustomer" in content

    async def test_setup_flow_with_edit_restart(self, tmp_path: Path) -> None:
        """Verify setup flow restarts when user chooses edit."""
        env_path = tmp_path / ".testio-mcp.env"

        # Mock user inputs with edit followed by save
        customer_names = ["firstAttempt", "secondAttempt"]
        tokens = ["a" * 64, "b" * 64]

        with patch(
            "testio_mcp.cli.setup.prompt_customer_name", side_effect=customer_names
        ) as mock_name:
            with patch("testio_mcp.cli.setup.prompt_api_token", side_effect=tokens):
                with patch("testio_mcp.cli.setup.prompt_customer_id", return_value="1"):
                    with patch("testio_mcp.cli.setup.prompt_log_format", return_value="json"):
                        with patch("testio_mcp.cli.setup.prompt_log_level", return_value="INFO"):
                            with patch("testio_mcp.cli.setup.prompt_product_ids", return_value=""):
                                with patch(
                                    "testio_mcp.cli.setup.prompt_disable_capabilities_tool",
                                    return_value=True,
                                ):
                                    with patch(
                                        "testio_mcp.cli.setup.check_api_connectivity",
                                        return_value=(True, ""),
                                    ):
                                        with patch(
                                            "testio_mcp.cli.setup.show_confirmation_summary",
                                            side_effect=["edit", "save"],
                                        ):
                                            with patch(
                                                "testio_mcp.cli.setup.Path.home",
                                                return_value=tmp_path,
                                            ):
                                                await run_setup_flow()

        # Verify file contains second attempt data
        content = env_path.read_text()
        assert "TESTIO_CUSTOMER_NAME=secondAttempt" in content

        # Verify prompt was called twice (once for each attempt)
        assert mock_name.call_count == 2
