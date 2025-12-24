"""Unit tests for MCP resources."""

import pytest
from fastmcp import FastMCP

from testio_mcp.resources import register_resources


class TestPlaybookResource:
    """Tests for testio://knowledge/playbook resource."""

    def test_resource_registration_and_content(self):
        """Verify playbook resource is registered and returns correct content."""
        mcp = FastMCP("Test")
        register_resources(mcp)

        # Verify resource is registered
        # Note: Accessing internal _resource_manager to verify registration
        assert "testio://knowledge/playbook" in mcp._resource_manager._resources

        # Get the resource handler
        resource = mcp._resource_manager._resources["testio://knowledge/playbook"]

        # Execute the handler function
        content = resource.fn()

        # Verify content structure
        assert "# TestIO CSM Playbook" in content
        assert "Tactical Patterns (Escalation Investigation)" in content
        assert "### Pattern: Noisy Cycle" in content
        assert "Strategic Templates (EBR/QBR)" in content
        assert "### Template: Quarterly Quality Review" in content

        # Verify specific details
        assert "Rejection Rate > 30%" in content
        assert "coach tester" in content


class TestProgrammaticAccessResource:
    """Tests for testio://knowledge/programmatic-access resource."""

    @pytest.fixture
    def resource_content(self) -> str:
        """Get the programmatic-access resource content."""
        mcp = FastMCP("Test")
        register_resources(mcp)
        resource = mcp._resource_manager._resources["testio://knowledge/programmatic-access"]
        return resource.fn()

    def test_programmatic_access_resource_exists(self, resource_content: str):
        """Verify resource is registered and returns content."""
        assert resource_content is not None
        assert len(resource_content) > 0
        assert "# Programmatic Access to TestIO Data" in resource_content

    def test_programmatic_access_teaches_openapi_discovery(self, resource_content: str):
        """Verify resource shows how to query openapi.json (jq/python examples)."""
        # Should teach openapi.json as source of truth
        assert "openapi.json" in resource_content
        assert "/openapi.json" in resource_content

        # Should show jq examples
        assert "jq" in resource_content
        assert ".paths" in resource_content

        # Should show python examples for discovery
        assert "python -c" in resource_content or "python" in resource_content

    def test_programmatic_access_contains_export_patterns(self, resource_content: str):
        """Verify resource includes JSON, CSV, Excel export code snippets."""
        # JSON export
        assert "json.dump" in resource_content

        # CSV export
        assert "csv" in resource_content
        assert "DictWriter" in resource_content

        # Excel export
        assert "openpyxl" in resource_content
        assert "Workbook" in resource_content
