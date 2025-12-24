"""Unit tests for MCP prompts.

STORY-059: MCP Prompts for Workflows
Tests prompt rendering with various argument combinations.

Note: FastMCP's @mcp.prompt decorator wraps functions in FunctionPrompt objects.
To test the underlying function, access it via `.fn` attribute.
"""

from collections.abc import Callable
from typing import Any

import pytest


def get_prompt_fn(prompt_wrapper: Any) -> Callable[..., str]:
    """Extract the underlying function from FastMCP FunctionPrompt wrapper."""
    return prompt_wrapper.fn  # type: ignore[return-value]


class TestAnalyzeProductQualityPrompt:
    """Tests for analyze-product-quality prompt (STORY-087)."""

    @pytest.fixture
    def prompt_fn(self) -> Callable[..., str]:
        """Get the analyze_product_quality prompt function."""
        from testio_mcp.prompts.analyze_product_quality import analyze_product_quality

        return get_prompt_fn(analyze_product_quality)

    def test_renders_with_product_id(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt renders with product_identifier as ID."""
        result = prompt_fn(product_identifier="18559")

        assert "18559" in result
        assert "last 30 days" in result  # Default period
        assert "overall quality" in result  # Default focus_area
        assert "**YOLO Mode:** NO" in result  # Not YOLO mode

    def test_renders_with_product_name(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt renders with product_identifier as name."""
        result = prompt_fn(product_identifier="Acme Mobile")

        assert "Acme Mobile" in result
        assert "last 30 days" in result

    def test_renders_without_product(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt renders with no product (guided discovery)."""
        result = prompt_fn()

        assert "NOT_PROVIDED" in result
        assert "last 30 days" in result

    def test_renders_with_custom_period(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt renders with custom period."""
        result = prompt_fn(product_identifier="598", period="Q3 2025")

        assert "598" in result
        assert "Q3 2025" in result

    def test_renders_with_focus_area(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt renders with focus_area."""
        result = prompt_fn(product_identifier="123", period="last 7 days", focus_area="bug density")

        assert "123" in result
        assert "last 7 days" in result
        assert "bug density" in result

    def test_yolo_mode_detection_full_report(self, prompt_fn: Callable[..., str]) -> None:
        """Verify YOLO mode triggers on 'full report'."""
        result = prompt_fn(product_identifier="598", focus_area="full report")

        assert "**YOLO Mode:** YES" in result

    def test_yolo_mode_detection_comprehensive(self, prompt_fn: Callable[..., str]) -> None:
        """Verify YOLO mode triggers on 'comprehensive'."""
        result = prompt_fn(product_identifier="598", focus_area="comprehensive")

        assert "**YOLO Mode:** YES" in result

    def test_yolo_mode_detection_everything(self, prompt_fn: Callable[..., str]) -> None:
        """Verify YOLO mode triggers on 'everything'."""
        result = prompt_fn(product_identifier="598", focus_area="everything")

        assert "**YOLO Mode:** YES" in result

    def test_yolo_mode_detection_complete_analysis(self, prompt_fn: Callable[..., str]) -> None:
        """Verify YOLO mode triggers on 'complete analysis'."""
        result = prompt_fn(product_identifier="598", focus_area="complete analysis")

        assert "**YOLO Mode:** YES" in result

    def test_yolo_mode_case_insensitive(self, prompt_fn: Callable[..., str]) -> None:
        """Verify YOLO mode detection is case-insensitive."""
        result = prompt_fn(product_identifier="598", focus_area="Full Report")

        assert "**YOLO Mode:** YES" in result

    def test_yolo_mode_not_triggered_by_regular_focus(self, prompt_fn: Callable[..., str]) -> None:
        """Verify YOLO mode doesn't trigger for regular focus areas."""
        result = prompt_fn(product_identifier="598", focus_area="bug density")

        assert "**YOLO Mode:** NO" in result

    def test_contains_three_phase_workflow(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt describes three-phase workflow."""
        result = prompt_fn(product_identifier="100")

        assert "Phase 1" in result
        assert "Phase 2" in result
        assert "Phase 3" in result

    def test_contains_workflow_steps(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt contains expected workflow steps."""
        result = prompt_fn(product_identifier="100")

        # Should contain key workflow steps
        assert "sync_data" in result
        assert "get_product_quality_report" in result
        assert "search" in result  # For product name resolution
        assert "list_products" in result  # For guided discovery

    def test_contains_key_metrics(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt mentions key metrics to analyze."""
        result = prompt_fn(product_identifier="100")

        # Check for auto-acceptance/acceptance rate terminology
        assert "auto_acceptance_rate" in result.lower() or "auto-accept" in result.lower()
        assert "rejection_rate" in result.lower() or "rejection rate" in result.lower()

    def test_contains_playbook_reference(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt references CSM Playbook resource."""
        result = prompt_fn(product_identifier="100")

        assert "testio://knowledge/playbook" in result

    def test_contains_context_workflows(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt includes context-driven workflows."""
        result = prompt_fn(product_identifier="100")

        assert "EBR" in result or "QBR" in result
        assert "escalation" in result.lower()
        assert "routine" in result.lower()

    def test_contains_portfolio_workflow(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt includes portfolio/multi-product workflow."""
        result = prompt_fn(product_identifier="portfolio")

        assert "Portfolio" in result or "Multi-Product" in result
        assert "Workflow E" in result

    def test_contains_multi_product_resolution_modes(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt describes multi-product resolution options."""
        result = prompt_fn(product_identifier="100")

        # Should show product resolution modes
        assert "comma-separated" in result.lower() or "multi-product" in result.lower()
        assert "portfolio" in result.lower()

    def test_contains_cross_product_query_pattern(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt shows cross-product query patterns."""
        result = prompt_fn(product_identifier="100")

        # Should show query_metrics with product dimension (no product_id filter)
        assert 'dimensions=["product"]' in result or 'dimensions=["product"]' in result

    def test_portfolio_example_in_few_shot(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt includes multi-product example in few-shot section."""
        result = prompt_fn(product_identifier="100")

        # Example 5 should be present
        assert "Example 5" in result
        assert "Multi-Product" in result or "Portfolio" in result


class TestRegistryBuilderFunctions:
    """Tests for extracted registry builder functions."""

    def test_build_dimension_registry_returns_dict(self) -> None:
        """Verify dimension registry returns expected structure."""
        from testio_mcp.services.analytics_service import build_dimension_registry

        registry = build_dimension_registry()

        assert isinstance(registry, dict)
        assert len(registry) == 14  # 14 dimensions (added platform)

    def test_build_metric_registry_returns_dict(self) -> None:
        """Verify metric registry returns expected structure."""
        from testio_mcp.services.analytics_service import build_metric_registry

        registry = build_metric_registry()

        assert isinstance(registry, dict)
        assert (
            len(registry) == 13
        )  # 6 original + 2 customer engagement + 5 rate metrics (STORY-082)

    def test_dimension_def_has_required_fields(self) -> None:
        """Verify DimensionDef has expected attributes."""
        from testio_mcp.services.analytics_service import build_dimension_registry

        registry = build_dimension_registry()
        feature_dim = registry["feature"]

        assert hasattr(feature_dim, "key")
        assert hasattr(feature_dim, "description")
        assert hasattr(feature_dim, "column")
        assert hasattr(feature_dim, "join_path")
        assert hasattr(feature_dim, "example")

    def test_metric_def_has_required_fields(self) -> None:
        """Verify MetricDef has expected attributes."""
        from testio_mcp.services.analytics_service import build_metric_registry

        registry = build_metric_registry()
        bug_metric = registry["bug_count"]

        assert hasattr(bug_metric, "key")
        assert hasattr(bug_metric, "description")
        assert hasattr(bug_metric, "expression")
        assert hasattr(bug_metric, "join_path")
        assert hasattr(bug_metric, "formula")


class TestPrepMeetingPrompt:
    """Tests for prep-meeting prompt."""

    @pytest.fixture
    def prompt_fn(self) -> Callable[..., str]:
        """Get the prep_meeting prompt function."""
        from testio_mcp.prompts.prep_meeting import prep_meeting

        return get_prompt_fn(prep_meeting)

    def test_prep_meeting_requires_analysis_dir(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt requires analysis_dir parameter."""
        result = prompt_fn(analysis_dir="./panera-ebr-12-03/")

        assert "./panera-ebr-12-03/" in result
        assert "analysis_dir" in result.lower() or "panera-ebr-12-03" in result

    def test_prep_meeting_renders_without_context(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt renders with no context provided."""
        result = prompt_fn(analysis_dir="./test-dir/")

        assert "./test-dir/" in result
        assert "NOT_PROVIDED" in result  # No context provided
        assert "What type of meeting is this?" in result  # Asks in Phase 1
        assert "How long is the meeting?" in result  # Asks in Phase 1

    def test_prep_meeting_renders_with_context(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt renders with user-provided context."""
        result = prompt_fn(
            analysis_dir="./test-dir/", context="EBR with new partner, want to show value"
        )

        assert "./test-dir/" in result
        assert "EBR with new partner, want to show value" in result
        assert "User mentioned:" in result  # Context hint appears

    def test_prep_meeting_references_programmatic_access_resource(
        self, prompt_fn: Callable[..., str]
    ) -> None:
        """Verify prompt mentions the resource URI for script generation."""
        result = prompt_fn(analysis_dir="./test-dir/")

        assert "testio://knowledge/programmatic-access" in result

    def test_prep_meeting_includes_conversation_guide_structure(
        self, prompt_fn: Callable[..., str]
    ) -> None:
        """Verify output includes questions > statements philosophy."""
        result = prompt_fn(analysis_dir="./test-dir/")

        # Should include key conversation guide elements
        assert "conversation" in result.lower() or "guide" in result.lower()
        assert "question" in result.lower()

        # Should emphasize customer talking > presenting
        assert "Customer talks > We talk" in result or "customer talks" in result.lower()

    def test_prep_meeting_includes_artifact_generation(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt guides agent to generate expected artifacts."""
        result = prompt_fn(analysis_dir="./test-dir/")

        # Should mention all three artifacts
        assert "fetch_metrics.py" in result
        assert "slide-data.md" in result
        assert "conversation-guide.md" in result

    def test_prep_meeting_includes_phase_workflow(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt describes phased workflow with new structure."""
        result = prompt_fn(analysis_dir="./test-dir/")

        assert "Phase 0" in result  # Load Knowledge Base
        assert "Phase 1" in result  # Understand Narrative
        assert "Phase 2" in result  # Identify Supporting Evidence
        assert "Phase 3" in result  # Gather Evidence
        assert "Phase 3.5" in result  # HITL Validation
        assert "Phase 4" in result  # Generate Artifacts

    def test_prep_meeting_requires_playbook_resource(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt requires loading playbook resource first."""
        result = prompt_fn(analysis_dir="./test-dir/")

        assert "testio://knowledge/playbook" in result
        assert "Phase 0" in result
        assert "REQUIRED FIRST STEP" in result or "Load Knowledge Base" in result

    def test_prep_meeting_narrative_first_approach(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt follows narrative-first approach."""
        result = prompt_fn(analysis_dir="./test-dir/")

        # Phase 1 should ask about narrative before reading analysis
        phase_1_idx = result.find("Phase 1")
        phase_3_idx = result.find("Phase 3")

        assert phase_1_idx < phase_3_idx  # Narrative comes before reading analysis
        assert "narrative hypothesis" in result.lower()
        assert "What's driving this meeting?" in result

    def test_prep_meeting_includes_hitl_validation(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt includes HITL validation loop."""
        result = prompt_fn(analysis_dir="./test-dir/")

        assert "HITL" in result or "validation" in result.lower()
        assert "STOP" in result  # Multiple STOP points for user input
        assert "Phase 3.5" in result
        assert "approve" in result.lower()

    def test_prep_meeting_emphasizes_schema_boundaries(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt emphasizes staying within schema boundaries."""
        result = prompt_fn(analysis_dir="./test-dir/")

        assert "schema" in result.lower()
        assert "playbook" in result.lower()
        assert "Stay within" in result or "do not invent" in result.lower()

    def test_prep_meeting_includes_narrative_types(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt provides narrative type examples."""
        result = prompt_fn(analysis_dir="./test-dir/")

        # Should include common narrative types
        assert "renewal" in result.lower()
        assert "escalation" in result.lower()
        assert "value" in result.lower() or "proof" in result.lower()

    def test_prep_meeting_no_hardcoded_file_patterns(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt doesn't contain hardcoded file patterns in Phase 3."""
        result = prompt_fn(analysis_dir="./test-dir/")

        # Should NOT contain hardcoded glob patterns
        assert "*-analysis*.md" not in result
        # Allowed in other contexts like artifact examples
        assert "executive-summary.md" not in result or "Always" in result
        assert "*-quality*.md" not in result

    def test_prep_meeting_has_flexible_exploration(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt instructs flexible directory exploration."""
        result = prompt_fn(analysis_dir="./test-dir/")

        # Should contain flexible exploration instructions
        assert "Explore the analysis directory" in result or "explore" in result.lower()
        assert "List all files" in result or "list all" in result.lower()

    def test_prep_meeting_has_phase_0_5(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt includes Phase 0.5 for analysis verification."""
        result = prompt_fn(analysis_dir="./test-dir/")

        assert "Phase 0.5" in result
        assert "Verify Analysis Exists" in result or "verify" in result.lower()


class TestAnalyzeProductQualityPromptExport:
    """Tests for analyze-product-quality export requirements."""

    @pytest.fixture
    def prompt_fn(self) -> Callable[..., str]:
        """Get the analyze_product_quality prompt function."""
        from testio_mcp.prompts.analyze_product_quality import analyze_product_quality

        return get_prompt_fn(analyze_product_quality)

    def test_contains_phase_5(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt contains Phase 5 for artifact export."""
        result = prompt_fn(product_identifier="100")

        assert "Phase 5" in result
        assert "Export Artifacts" in result

    def test_enforces_export_before_completion(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt enforces artifact export before session completion."""
        result = prompt_fn(product_identifier="100")

        assert (
            "DO NOT end session without exporting" in result
            or "DO NOT consider the analysis complete" in result
        )

    def test_requires_executive_summary(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt requires executive summary as mandatory artifact."""
        result = prompt_fn(product_identifier="100")

        # Check for executive summary requirement
        assert "executive-summary.md" in result.lower() or "executive summary" in result.lower()
        assert "Always" in result or "Required" in result  # Must be marked as required

    def test_requires_full_analysis_report(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt requires full analysis report as mandatory artifact."""
        result = prompt_fn(product_identifier="100")

        # Check for full analysis report requirement
        assert "quality-analysis" in result.lower() or "full analysis" in result.lower()

    def test_export_requirements_in_critical_reminders(self, prompt_fn: Callable[..., str]) -> None:
        """Verify Critical Reminders section includes export requirements."""
        result = prompt_fn(product_identifier="100")

        # Should have Export Requirements section in Critical Reminders
        assert "Export Requirements" in result
        assert "DO NOT end session without exporting" in result

    def test_offers_prep_meeting_after_export(self, prompt_fn: Callable[..., str]) -> None:
        """Verify prompt offers prep-meeting workflow after export."""
        result = prompt_fn(product_identifier="100")

        # Should mention prep-meeting as next step
        assert "prep-meeting" in result.lower() or "prep meeting" in result.lower()
