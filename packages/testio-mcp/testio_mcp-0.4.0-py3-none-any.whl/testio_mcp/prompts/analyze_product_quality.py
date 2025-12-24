"""MCP prompt for product quality analysis workflow.

This prompt guides an AI agent through a multi-step quality analysis
workflow: sync → summarize → report → analyze.
"""

from pathlib import Path

from testio_mcp.config import settings
from testio_mcp.server import mcp

TEMPLATE_PATH = Path(__file__).parent / "analyze_product_quality.md"


@mcp.prompt(name="analyze-product-quality")
def analyze_product_quality(
    product_identifier: str | None = None,
    period: str = "last 30 days",
    focus_area: str | None = None,
) -> str:
    """Interactive product quality analysis with three-phase workflow.

    Supports flexible product resolution (ID, name, guided discovery, or multi-product),
    time scoping, and context-driven investigation workflows (EBR prep, escalation,
    routine check, portfolio analysis).

    Args:
        product_identifier: Flexible product resolution modes:
            - Single product ID: "24734"
            - Product name: "Acme Mobile"
            - Multi-product: "24734,24836" (comma-separated IDs)
            - Portfolio mode: "portfolio", "all", or "compare"
            - Customer discovery: "Panera" (lists matching products)
            - Omit for guided discovery
        period: Time period for analysis (default: "last 30 days").
            Examples: "last week", "Q3 2025", "YTD", "all-time", "2025-01-01 to 2025-03-31"
        focus_area: Optional focus area or mode trigger (default: "overall quality").
            YOLO mode triggers: "full report", "comprehensive", "everything", "complete analysis"
            Regular focus: "bug density", "feature stability", "rejection patterns"

    Workflow Phases:
        Phase 1: Product resolution + executive summary (auto-execute if product identified)
        Phase 2: Context gathering (interactive - understand business driver)
        Phase 3: Targeted investigation (EBR / escalation / routine / comprehensive / portfolio)

    Usage Examples:
        # Single product by ID
        /analyze-product-quality 24734

        # Single product by name
        /analyze-product-quality "Acme Mobile"

        # Guided discovery (no product specified)
        /analyze-product-quality

        # Multi-product comparison (comma-separated IDs)
        /analyze-product-quality 24734,24836

        # Portfolio mode (guided selection of all products)
        /analyze-product-quality portfolio

        # Customer products discovery
        /analyze-product-quality "Panera"

        # Custom time period
        /analyze-product-quality 24734 "Q3 2025"

        # YOLO mode (skip interaction, run comprehensive analysis)
        /analyze-product-quality 24734 "last 30 days" "full report"

    Returns:
        Formatted prompt template with placeholders for AI agent to execute workflow.
    """
    # Detect YOLO mode based on focus_area keywords
    yolo_keywords = ["full report", "comprehensive", "everything", "complete analysis"]
    yolo_mode = any(keyword in (focus_area or "").lower() for keyword in yolo_keywords)

    template = TEMPLATE_PATH.read_text()
    return template.format(
        product_identifier=product_identifier or "NOT_PROVIDED",
        period=period,
        focus_area=focus_area or "overall quality",
        yolo_mode="YES" if yolo_mode else "NO",
        # Inject threshold values from config (convert 0.20 -> 20)
        rejection_warning_pct=int(settings.PLAYBOOK_REJECTION_WARNING * 100),
        rejection_critical_pct=int(settings.PLAYBOOK_REJECTION_CRITICAL * 100),
        auto_acceptance_warning_pct=int(settings.PLAYBOOK_AUTO_ACCEPTANCE_WARNING * 100),
        auto_acceptance_critical_pct=int(settings.PLAYBOOK_AUTO_ACCEPTANCE_CRITICAL * 100),
        review_warning_pct=int(settings.PLAYBOOK_REVIEW_WARNING * 100),
        review_critical_pct=int(settings.PLAYBOOK_REVIEW_CRITICAL * 100),
    )
