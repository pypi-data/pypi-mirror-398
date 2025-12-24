from pathlib import Path

from fastmcp import FastMCP

from testio_mcp.config import settings


def register_resources(mcp: FastMCP) -> None:
    """Register MCP resources."""

    @mcp.resource("testio://knowledge/playbook")
    def get_playbook() -> str:
        """Expert heuristics for analyzing TestIO data (patterns, templates)."""
        playbook_path = Path(__file__).parent / "playbook.md"
        template = playbook_path.read_text(encoding="utf-8")

        # Inject threshold values from config (convert 0.20 -> 20)
        return template.format(
            rejection_warning_pct=int(settings.PLAYBOOK_REJECTION_WARNING * 100),
            rejection_critical_pct=int(settings.PLAYBOOK_REJECTION_CRITICAL * 100),
            auto_acceptance_warning_pct=int(settings.PLAYBOOK_AUTO_ACCEPTANCE_WARNING * 100),
            auto_acceptance_critical_pct=int(settings.PLAYBOOK_AUTO_ACCEPTANCE_CRITICAL * 100),
            review_warning_pct=int(settings.PLAYBOOK_REVIEW_WARNING * 100),
            review_critical_pct=int(settings.PLAYBOOK_REVIEW_CRITICAL * 100),
        )

    @mcp.resource("testio://knowledge/programmatic-access")
    def get_programmatic_access() -> str:
        """How to discover and use the TestIO REST API via OpenAPI schema."""
        access_path = Path(__file__).parent / "programmatic_access.md"
        return access_path.read_text(encoding="utf-8")
