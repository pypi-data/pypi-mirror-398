import json
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from testio_mcp.models.orm import Bug, Feature, Product, Test, TestFeature
from testio_mcp.services.analytics_service import AnalyticsService
from testio_mcp.services.multi_test_report_service import MultiTestReportService


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metric_consistency_between_services(shared_cache, shared_client):
    """
    Verify that 'Product Health' metrics are calculated identically by:
    1. MultiTestReportService (Python logic)
    2. AnalyticsService (SQL logic)

    This ensures no drift between the two engines.
    """
    async with shared_cache.async_session_maker() as session:
        # 1. Setup Data
        # Create Product
        product_data = json.dumps({"id": 1001, "name": "Consistency Product", "type": "web"})
        product = Product(
            id=1001,
            title="Consistency Product",
            type="web",
            customer_id=123,
            data=product_data,
        )
        session.add(product)

        # Create Feature
        feature_data = json.dumps({"id": 2001, "title": "Core Feature"})
        feature = Feature(
            id=2001,
            title="Core Feature",
            product_id=1001,
            customer_id=123,
            raw_data=feature_data,
        )
        session.add(feature)

        # Create Tests covering edge cases
        # Test 1: Standard (Mixed statuses)
        t1_data = json.dumps(
            {
                "id": 3001,
                "title": "Standard Test",
                "status": "locked",
                "testing_type": "rapid",
                "start_at": datetime.now().isoformat(),
                "end_at": datetime.now().isoformat(),
            }
        )
        test1 = Test(
            id=3001,
            title="Standard Test",
            status="locked",
            testing_type="rapid",
            start_at=datetime.now(),
            end_at=datetime.now(),
            product_id=1001,
            created_by_user_id=1,
            customer_id=123,
            data=t1_data,
        )
        # Test 2: Perfect (Only accepted)
        t2_data = json.dumps(
            {
                "id": 3002,
                "title": "Perfect Test",
                "status": "locked",
                "testing_type": "focused",
                "start_at": datetime.now().isoformat(),
                "end_at": datetime.now().isoformat(),
            }
        )
        test2 = Test(
            id=3002,
            title="Perfect Test",
            status="locked",
            testing_type="focused",
            start_at=datetime.now(),
            end_at=datetime.now(),
            product_id=1001,
            created_by_user_id=1,
            customer_id=123,
            data=t2_data,
        )
        # Test 3: Rejected (Only rejected)
        t3_data = json.dumps(
            {
                "id": 3003,
                "title": "Rejected Test",
                "status": "locked",
                "testing_type": "rapid",
                "start_at": datetime.now().isoformat(),
                "end_at": datetime.now().isoformat(),
            }
        )
        test3 = Test(
            id=3003,
            title="Rejected Test",
            status="locked",
            testing_type="rapid",
            start_at=datetime.now(),
            end_at=datetime.now(),
            product_id=1001,
            created_by_user_id=1,
            customer_id=123,
            data=t3_data,
        )
        # Test 4: Empty (No bugs)
        t4_data = json.dumps(
            {
                "id": 3004,
                "title": "Empty Test",
                "status": "locked",
                "testing_type": "coverage",
                "start_at": datetime.now().isoformat(),
                "end_at": datetime.now().isoformat(),
            }
        )
        test4 = Test(
            id=3004,
            title="Empty Test",
            status="locked",
            testing_type="coverage",
            start_at=datetime.now(),
            end_at=datetime.now(),
            product_id=1001,
            created_by_user_id=1,
            customer_id=123,
            data=t4_data,
        )

        session.add_all([test1, test2, test3, test4])
        await session.commit()

        # Link Tests to Feature
        session.add_all(
            [
                TestFeature(
                    id=5001,
                    test_id=3001,
                    feature_id=2001,
                    customer_id=123,
                    title="Core Feature",
                ),
                TestFeature(
                    id=5002,
                    test_id=3002,
                    feature_id=2001,
                    customer_id=123,
                    title="Core Feature",
                ),
                TestFeature(
                    id=5003,
                    test_id=3003,
                    feature_id=2001,
                    customer_id=123,
                    title="Core Feature",
                ),
                TestFeature(
                    id=5004,
                    test_id=3004,
                    feature_id=2001,
                    customer_id=123,
                    title="Core Feature",
                ),
            ]
        )
        await session.commit()

        # Create Bugs
        bugs = []

        # Helper to create bug raw_data
        def bug_raw(bid, status, severity, auto=False, tid=None, tfid=None):
            return json.dumps(
                {
                    "id": bid,
                    "status": status,
                    "severity": severity,
                    "auto_accepted": auto,
                    "test": {"id": tid},
                    "test_feature": {"id": tfid},
                }
            )

        # Test 1 (Standard): 2 Active, 1 Auto, 1 Rejected, 1 Open
        bugs.extend(
            [
                Bug(
                    id=4001,
                    test_feature_id=5001,
                    status="accepted",
                    severity="critical",
                    title="Bug 1",
                    test_id=3001,
                    customer_id=123,
                    raw_data=bug_raw(4001, "accepted", "critical", False, 3001, 5001),
                ),
                Bug(
                    id=4002,
                    test_feature_id=5001,
                    status="accepted",
                    severity="low",
                    title="Bug 2",
                    test_id=3001,
                    customer_id=123,
                    raw_data=bug_raw(4002, "accepted", "low", False, 3001, 5001),
                ),
                Bug(
                    id=4003,
                    test_feature_id=5001,
                    status="auto_accepted",
                    severity="medium",
                    title="Bug 3",
                    test_id=3001,
                    customer_id=123,
                    raw_data=bug_raw(4003, "accepted", "medium", True, 3001, 5001),
                ),
                Bug(
                    id=4004,
                    test_feature_id=5001,
                    status="rejected",
                    severity="high",
                    title="Bug 4",
                    test_id=3001,
                    customer_id=123,
                    raw_data=bug_raw(4004, "rejected", "high", False, 3001, 5001),
                ),
                Bug(
                    id=4005,
                    test_feature_id=5001,
                    status="forwarded",
                    severity="low",
                    title="Bug 5",
                    test_id=3001,
                    customer_id=123,
                    raw_data=bug_raw(4005, "forwarded", "low", False, 3001, 5001),
                ),
            ]
        )

        # Test 2 (Perfect): 2 Active, 1 Auto
        bugs.extend(
            [
                Bug(
                    id=4006,
                    test_feature_id=5002,
                    status="accepted",
                    severity="critical",
                    title="Bug 6",
                    test_id=3002,
                    customer_id=123,
                    raw_data=bug_raw(4006, "accepted", "critical", False, 3002, 5002),
                ),
                Bug(
                    id=4007,
                    test_feature_id=5002,
                    status="accepted",
                    severity="high",
                    title="Bug 7",
                    test_id=3002,
                    customer_id=123,
                    raw_data=bug_raw(4007, "accepted", "high", False, 3002, 5002),
                ),
                Bug(
                    id=4008,
                    test_feature_id=5002,
                    status="auto_accepted",
                    severity="low",
                    title="Bug 8",
                    test_id=3002,
                    customer_id=123,
                    raw_data=bug_raw(4008, "accepted", "low", True, 3002, 5002),
                ),
            ]
        )

        # Test 3 (Rejected): 2 Rejected
        bugs.extend(
            [
                Bug(
                    id=4009,
                    test_feature_id=5003,
                    status="rejected",
                    severity="medium",
                    title="Bug 9",
                    test_id=3003,
                    customer_id=123,
                    raw_data=bug_raw(4009, "rejected", "medium", False, 3003, 5003),
                ),
                Bug(
                    id=4010,
                    test_feature_id=5003,
                    status="rejected",
                    severity="low",
                    title="Bug 10",
                    test_id=3003,
                    customer_id=123,
                    raw_data=bug_raw(4010, "rejected", "low", False, 3003, 5003),
                ),
            ]
        )

        # Test 4 (Empty): 0 Bugs

        session.add_all(bugs)
        await session.commit()

        # 2. Run MultiTestReportService (Report)
        # We need to mock the repositories to return our DB data or use the real ones if possible.
        # Since MultiTestReportService uses Repositories which use the session, we can instantiate
        # it with real repositories connected to our shared_cache session.

        from testio_mcp.repositories.bug_repository import BugRepository
        from testio_mcp.repositories.product_repository import ProductRepository
        from testio_mcp.repositories.test_repository import TestRepository
        from testio_mcp.repositories.user_repository import UserRepository

        user_repo = UserRepository(session, shared_client, 123)
        test_repo = TestRepository(session, shared_client, 123, user_repo, shared_cache)
        bug_repo = BugRepository(session, shared_client, 123, user_repo, shared_cache)
        product_repo = ProductRepository(session, shared_client, 123)

        # Mock API calls to avoid external requests, but allow DB queries
        # We mock the *refresh* part, but the *get* part should hit the DB
        test_repo._fetch_tests_from_api = AsyncMock(return_value=[])
        bug_repo._fetch_bugs_from_api = AsyncMock(return_value=[])
        product_repo._fetch_products_from_api = AsyncMock(return_value=[])

        # Force cache hit by setting last_updated
        # (In integration tests, we just want to read what we wrote)

        report_service = MultiTestReportService(shared_client, test_repo, bug_repo, product_repo)

        # Run Report
        report_result = await report_service.get_product_quality_report(product_ids=[1001])
        report_summary = report_result["summary"]

        # 3. Run AnalyticsService (Analytics)
        analytics_service = AnalyticsService(session, 123, shared_client)

        analytics_result = await analytics_service.query_metrics(
            metrics=[
                "test_count",
                "bug_count",
                "bugs_per_test",
                "active_acceptance_rate",
                "auto_acceptance_rate",
                "overall_acceptance_rate",
                "rejection_rate",
                "review_rate",
            ],
            dimensions=[],
            filters={"product_id": 1001},
        )
        analytics_data = analytics_result.data[0]

        # 4. Assert Consistency
        # Test Count
        assert report_summary["total_tests"] == analytics_data["test_count"] == 4

        # Bug Count
        assert report_summary["total_bugs"] == analytics_data["bug_count"] == 10

        # Avg Bugs Per Test
        assert report_summary["avg_bugs_per_test"] == analytics_data["bugs_per_test"] == 2.5

        # Active Acceptance Rate
        # Active Accepted: 4 (2 from T1, 2 from T2)
        # Total Bugs: 10
        # Active Rate: 4 / 10 = 0.4
        assert (
            report_summary["active_acceptance_rate"]
            == analytics_data["active_acceptance_rate"]
            == 0.4
        )

        # Auto Acceptance Rate
        # Auto Accepted: 2 (1 from T1, 1 from T2)
        # Total Accepted: 6 (4 active + 2 auto)
        # Auto Rate: 2 / 6 = 0.3333...
        assert (
            report_summary["auto_acceptance_rate"]
            == analytics_data["auto_acceptance_rate"]
            == pytest.approx(2 / 6)
        )

        # Overall Acceptance Rate
        # Total Accepted: 6
        # Total Bugs: 10
        # Overall Rate: 6 / 10 = 0.6
        assert (
            report_summary["overall_acceptance_rate"]
            == analytics_data["overall_acceptance_rate"]
            == 0.6
        )

        # Rejection Rate
        # Rejected: 3 (1 from T1, 2 from T3)
        # Total Bugs: 10
        # Rejection Rate: 3 / 10 = 0.3
        assert report_summary["rejection_rate"] == analytics_data["rejection_rate"] == 0.3

        # Review Rate
        # Reviewed: 7 (4 active accepted + 3 rejected)
        # Total Bugs: 10
        # Review Rate: 7 / 10 = 0.7
        assert report_summary["review_rate"] == analytics_data["review_rate"] == 0.7

        print(
            "\n✅ Consistency Verified: Report Service and Analytics Service "
            "produce identical metrics."
        )
