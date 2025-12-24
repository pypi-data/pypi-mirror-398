"""MCP prompt for meeting preparation workflow.

This prompt transforms deep analysis artifacts into meeting-ready materials:
- fetch_metrics.py script for programmatic data access
- slide-data.md for PowerPoint copy/paste
- conversation-guide.md with questions > statements philosophy
"""

from pathlib import Path

from testio_mcp.server import mcp

TEMPLATE_PATH = Path(__file__).parent / "prep_meeting.md"


@mcp.prompt(name="prep-meeting")
def prep_meeting(
    analysis_dir: str,
    context: str = "",
) -> str:
    """Prepare meeting materials from analysis artifacts.

    Transforms deep analysis output (from analyze-product-quality) into
    meeting-ready materials focused on conversation, not presentation.

    Args:
        analysis_dir: Directory containing analysis artifacts (e.g., "./panera-ebr-12-03/").
            Should contain files like *-analysis*.md, executive-summary.md from prior analysis.
        context: Optional free-form meeting context to help guide preparation.
            Examples: "EBR with new partner, want to show value",
            "renewal coming up, escalation risk"

    Workflow:
        Phase 0: Load playbook resource (understand schema boundaries)
        Phase 1: Understand the narrative (meeting context, success criteria)
        Phase 2: Identify supporting evidence (metrics that support narrative)
        Phase 3: Gather evidence from analysis
        Phase 3.5: HITL validation & investigation
        Phase 4: Generate artifacts (fetch_metrics.py, slide-data.md, conversation-guide.md)

    Design Principles:
        - Narrative first, metrics second (story drives evidence)
        - Customer talks > We talk (questions elicit conversation)
        - Schema-grounded (stay within playbook boundaries)
        - HITL validation (user must approve evidence)
        - Reproducible (scripts can be re-run for fresh data)

    Usage Examples:
        # Basic usage with analysis directory
        /prep-meeting ./panera-ebr-12-03/

        # With context to guide preparation
        /prep-meeting ./panera-ebr-12-03/ "EBR coming soon, onboard new partner and show value"

        # Renewal context
        /prep-meeting ./acme-analysis/ "renewal at risk, need to prove ROI"

    Returns:
        Formatted prompt template guiding the agent through meeting preparation.
    """
    template = TEMPLATE_PATH.read_text()

    # Generate context hint if user provided context
    context_hint = ""
    if context:
        context_hint = f'**Note**: User mentioned: "{context}"'

    return template.format(
        analysis_dir=analysis_dir,
        context=context if context else "NOT_PROVIDED",
        context_hint=context_hint,
    )
