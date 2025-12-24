"""Unit tests for get_test_summary MCP tool and TestService requirements summary."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.exceptions import TestIOAPIError, TestNotFoundException
from testio_mcp.services.test_service import TestService
from testio_mcp.tools.test_summary_tool import get_test_summary as get_test_summary_tool
from tests.unit.test_utils import mock_service_context

get_test_summary = get_test_summary_tool.fn


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_not_found_to_tool_error() -> None:
    """Verify TestNotFoundException → ToolError."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_test_summary.side_effect = TestNotFoundException(test_id=123)

    with patch(
        "testio_mcp.tools.test_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await get_test_summary(test_id=123, ctx=mock_ctx)

        assert "❌" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_api_error_to_tool_error() -> None:
    """Verify TestIOAPIError → ToolError."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_test_summary.side_effect = TestIOAPIError(message="Timeout", status_code=504)

    with patch(
        "testio_mcp.tools.test_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await get_test_summary(test_id=123, ctx=mock_ctx)

        assert "❌" in str(exc_info.value)
        assert "504" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_to_service_correctly() -> None:
    """Verify tool delegates to TestService."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_test_summary.return_value = {
        "test": {
            "id": 123,
            "title": "Test",
            "testing_type": "exploratory",
            "status": "running",
            "product": {"id": 456, "name": "Product"},
            "requirements_summary": [],  # New format: list of platform requirements
        },
        "bugs": {
            "total_count": 0,
            "by_severity": {},
            "by_status": {},
            "by_platform": {
                "operating_systems": {},
                "browsers": {},
                "device_categories": {},
            },
            "acceptance_rates": {  # Required field (STORY-081: always present, not optional)
                "active_acceptance_rate": None,
                "auto_acceptance_rate": None,
                "overall_acceptance_rate": None,
                "rejection_rate": None,
                "review_rate": None,
                "open_count": 0,
                "has_alert": False,
            },
            "recent_bugs": [],  # Required field
        },
    }

    with patch(
        "testio_mcp.tools.test_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await get_test_summary(test_id=123, ctx=mock_ctx)

        mock_service.get_test_summary.assert_called_once_with(123)
        assert result["test"]["id"] == 123


# TestService._summarize_requirements unit tests


@pytest.mark.unit
def test_summarize_requirements_preserves_device_context() -> None:
    """Verify requirements summary preserves device type context for duplicate OS entries.

    This test addresses the bug where "iOS 17.0+" appeared twice in allowed_platforms
    without indicating one was for Smartphones and one was for Tablets.
    """
    # Create service with minimal mocks (method doesn't use client)
    service = TestService(
        client=MagicMock(),
        test_repo=MagicMock(),
        bug_repo=MagicMock(),
        product_repo=MagicMock(),
    )

    # Real-world requirements from TestIO API (test 120138)
    requirements = [
        {
            "id": 1668246,
            "category": {"id": 1, "key": "computer", "name": "Computers"},
            "operating_system": {"id": 6, "key": "windows", "name": "Windows"},
            "min_operating_system_version": {"id": 198, "name": "10"},
            "browsers": [{"id": 18, "name": "Chrome"}, {"id": 21, "name": "Firefox"}],
        },
        {
            "id": 1668247,
            "category": {"id": 1, "key": "computer", "name": "Computers"},
            "operating_system": {"id": 10, "key": "mac-os", "name": "Mac OS"},
            "min_operating_system_version": {"id": 324, "name": "10.14"},
            "browsers": [{"id": 29, "name": "Chrome"}, {"id": 31, "name": "Safari"}],
        },
        {
            "id": 1668248,
            "category": {"id": 2, "key": "smartphone", "name": "Smartphones"},
            "operating_system": {"id": 1, "key": "android", "name": "Android"},
            "min_operating_system_version": None,
            "browsers": [{"id": 11, "name": "Chrome"}],
        },
        {
            "id": 1668249,
            "category": {"id": 2, "key": "smartphone", "name": "Smartphones"},
            "operating_system": {"id": 2, "key": "ios", "name": "iOS"},
            "min_operating_system_version": None,
            "browsers": [{"id": 1, "name": "Chrome"}, {"id": 3, "name": "Safari"}],
        },
        {
            "id": 1668250,
            "category": {"id": 6, "key": "tablet", "name": "Tablets"},
            "operating_system": {"id": 1, "key": "android", "name": "Android"},
            "min_operating_system_version": None,
            "browsers": [{"id": 11, "name": "Chrome"}],
        },
        {
            "id": 1668251,
            "category": {"id": 6, "key": "tablet", "name": "Tablets"},
            "operating_system": {"id": 2, "key": "ios", "name": "iOS"},
            "min_operating_system_version": None,
            "browsers": [{"id": 1, "name": "Chrome"}, {"id": 3, "name": "Safari"}],
        },
    ]

    result = service._summarize_requirements(requirements)

    # New format: list of platform requirements with browsers
    assert len(result) == 6

    # Verify platforms preserve device context and include browsers
    assert result[0] == {
        "platform": "Windows 10+ (Computers)",
        "browsers": ["Chrome", "Firefox"],
    }
    assert result[1] == {
        "platform": "Mac OS 10.14+ (Computers)",
        "browsers": ["Chrome", "Safari"],
    }
    assert result[2] == {
        "platform": "Android (Smartphones)",
        "browsers": ["Chrome"],
    }
    assert result[3] == {
        "platform": "iOS (Smartphones)",
        "browsers": ["Chrome", "Safari"],
    }
    assert result[4] == {
        "platform": "Android (Tablets)",
        "browsers": ["Chrome"],
    }
    assert result[5] == {
        "platform": "iOS (Tablets)",
        "browsers": ["Chrome", "Safari"],
    }


@pytest.mark.unit
def test_summarize_requirements_handles_missing_version() -> None:
    """Verify requirements summary handles missing min_operating_system_version."""
    service = TestService(
        client=MagicMock(),
        test_repo=MagicMock(),
        bug_repo=MagicMock(),
        product_repo=MagicMock(),
    )

    requirements = [
        {
            "id": 1,
            "category": {"id": 1, "key": "computer", "name": "Computers"},
            "operating_system": {"id": 6, "key": "windows", "name": "Windows"},
            "min_operating_system_version": None,  # No version
            "browsers": [{"id": 18, "name": "Chrome"}],
        },
    ]

    result = service._summarize_requirements(requirements)

    # Without version, should be "Windows (Computers)" not "Windows + (Computers)"
    assert result == [{"platform": "Windows (Computers)", "browsers": ["Chrome"]}]


@pytest.mark.unit
def test_summarize_requirements_handles_missing_category() -> None:
    """Verify requirements summary handles missing category gracefully."""
    service = TestService(
        client=MagicMock(),
        test_repo=MagicMock(),
        bug_repo=MagicMock(),
        product_repo=MagicMock(),
    )

    requirements = [
        {
            "id": 1,
            "category": None,  # No category
            "operating_system": {"id": 6, "key": "windows", "name": "Windows"},
            "min_operating_system_version": {"id": 198, "name": "10"},
            "browsers": [{"id": 18, "name": "Chrome"}],
        },
    ]

    result = service._summarize_requirements(requirements)

    # Without category, should be "Windows 10+" without device type suffix
    assert result == [{"platform": "Windows 10+", "browsers": ["Chrome"]}]


@pytest.mark.unit
def test_summarize_requirements_empty_list() -> None:
    """Verify requirements summary handles empty requirements list."""
    service = TestService(
        client=MagicMock(),
        test_repo=MagicMock(),
        bug_repo=MagicMock(),
        product_repo=MagicMock(),
    )

    result = service._summarize_requirements([])

    assert result == []


@pytest.mark.unit
def test_summarize_requirements_exact_version() -> None:
    """Verify requirements summary shows exact version when min == max."""
    service = TestService(
        client=MagicMock(),
        test_repo=MagicMock(),
        bug_repo=MagicMock(),
        product_repo=MagicMock(),
    )

    requirements = [
        {
            "id": 1,
            "category": {"id": 1, "key": "computer", "name": "Computers"},
            "operating_system": {"id": 6, "key": "windows", "name": "Windows"},
            "min_operating_system_version": {"id": 566, "name": "11"},
            "max_operating_system_version": {"id": 566, "name": "11"},
            "browsers": [{"id": 18, "name": "Chrome"}],
        },
    ]

    result = service._summarize_requirements(requirements)

    # Should show "Windows 11" not "Windows 11+"
    assert result == [{"platform": "Windows 11 (Computers)", "browsers": ["Chrome"]}]


@pytest.mark.unit
def test_summarize_requirements_version_range() -> None:
    """Verify requirements summary shows version range when min != max."""
    service = TestService(
        client=MagicMock(),
        test_repo=MagicMock(),
        bug_repo=MagicMock(),
        product_repo=MagicMock(),
    )

    requirements = [
        {
            "id": 1,
            "category": {"id": 1, "key": "computer", "name": "Computers"},
            "operating_system": {"id": 6, "key": "windows", "name": "Windows"},
            "min_operating_system_version": {"id": 198, "name": "10"},
            "max_operating_system_version": {"id": 566, "name": "11"},
            "browsers": [{"id": 18, "name": "Chrome"}, {"id": 21, "name": "Firefox"}],
        },
    ]

    result = service._summarize_requirements(requirements)

    # Should show "Windows 10-11"
    assert result == [{"platform": "Windows 10-11 (Computers)", "browsers": ["Chrome", "Firefox"]}]


@pytest.mark.unit
def test_summarize_requirements_max_version_only() -> None:
    """Verify requirements summary handles max_version without min_version."""
    service = TestService(
        client=MagicMock(),
        test_repo=MagicMock(),
        bug_repo=MagicMock(),
        product_repo=MagicMock(),
    )

    requirements = [
        {
            "id": 1,
            "category": {"id": 1, "key": "computer", "name": "Computers"},
            "operating_system": {"id": 6, "key": "windows", "name": "Windows"},
            "min_operating_system_version": None,
            "max_operating_system_version": {"id": 566, "name": "11"},
            "browsers": [{"id": 31, "name": "Safari"}],
        },
    ]

    result = service._summarize_requirements(requirements)

    # Should show "Windows ≤11"
    assert result == [{"platform": "Windows ≤11 (Computers)", "browsers": ["Safari"]}]


@pytest.mark.unit
def test_summarize_requirements_real_world_with_versions() -> None:
    """Verify requirements summary with real-world test 145267 data."""
    service = TestService(
        client=MagicMock(),
        test_repo=MagicMock(),
        bug_repo=MagicMock(),
        product_repo=MagicMock(),
    )

    # Real requirements from test 145267
    requirements = [
        {
            "id": 2486762,
            "category": {"id": 1, "key": "computer", "name": "Computers"},
            "operating_system": {"id": 6, "key": "windows", "name": "Windows"},
            "min_operating_system_version": {"id": 566, "name": "11"},
            "max_operating_system_version": {"id": 566, "name": "11"},
            "browsers": [
                {"id": 18, "name": "Chrome"},
                {"id": 21, "name": "Firefox"},
                {"id": 48, "name": "Edge Chromium"},
            ],
        },
        {
            "id": 2486763,
            "category": {"id": 1, "key": "computer", "name": "Computers"},
            "operating_system": {"id": 10, "key": "mac-os", "name": "Mac OS"},
            "min_operating_system_version": {"id": 812, "name": "14.0"},
            "max_operating_system_version": None,
            "browsers": [
                {"id": 29, "name": "Chrome"},
                {"id": 30, "name": "Firefox"},
                {"id": 31, "name": "Safari"},
            ],
        },
        {
            "id": 2486764,
            "category": {"id": 2, "key": "smartphone", "name": "Smartphones"},
            "operating_system": {"id": 2, "key": "ios", "name": "iOS"},
            "min_operating_system_version": {"id": 806, "name": "17.0"},
            "max_operating_system_version": None,
            "browsers": [{"id": 1, "name": "Chrome"}, {"id": 3, "name": "Safari"}],
        },
        {
            "id": 2486766,
            "category": {"id": 2, "key": "smartphone", "name": "Smartphones"},
            "operating_system": {"id": 1, "key": "android", "name": "Android"},
            "min_operating_system_version": {"id": 380, "name": "10"},
            "max_operating_system_version": None,
            "browsers": [{"id": 11, "name": "Chrome"}],
        },
        {
            "id": 2486765,
            "category": {"id": 6, "key": "tablet", "name": "Tablets"},
            "operating_system": {"id": 2, "key": "ios", "name": "iOS"},
            "min_operating_system_version": {"id": 806, "name": "17.0"},
            "max_operating_system_version": None,
            "browsers": [{"id": 1, "name": "Chrome"}, {"id": 3, "name": "Safari"}],
        },
        {
            "id": 2486767,
            "category": {"id": 6, "key": "tablet", "name": "Tablets"},
            "operating_system": {"id": 1, "key": "android", "name": "Android"},
            "min_operating_system_version": {"id": 380, "name": "10"},
            "max_operating_system_version": None,
            "browsers": [{"id": 11, "name": "Chrome"}],
        },
    ]

    result = service._summarize_requirements(requirements)

    expected = [
        {
            "platform": "Windows 11 (Computers)",
            "browsers": ["Chrome", "Firefox", "Edge Chromium"],
        },
        {
            "platform": "Mac OS 14.0+ (Computers)",
            "browsers": ["Chrome", "Firefox", "Safari"],
        },
        {"platform": "iOS 17.0+ (Smartphones)", "browsers": ["Chrome", "Safari"]},
        {"platform": "Android 10+ (Smartphones)", "browsers": ["Chrome"]},
        {"platform": "iOS 17.0+ (Tablets)", "browsers": ["Chrome", "Safari"]},
        {"platform": "Android 10+ (Tablets)", "browsers": ["Chrome"]},
    ]
    assert result == expected
