#!/usr/bin/env python3
"""Standalone script to validate TestIO API chronological ordering assumption.

CRITICAL PRE-TASK for STORY-021: Incremental Sync Algorithm

This script validates the fundamental assumption that the TestIO API returns tests
in chronological order (newest first). The incremental sync algorithm in STORY-021
depends on this ordering to work correctly.

What This Script Does:
    1. Fetches multiple pages of tests from a production product
    2. Checks chronological ordering WITHIN each page
    3. Checks chronological ordering ACROSS page boundaries
    4. Identifies which field is used for sorting (created_at, start_at, end_at, or id)
    5. Provides detailed diagnostics if ordering is violated

Why This Matters:
    The incremental sync algorithm uses chronological ordering to efficiently detect new tests:
    - Fetch page 1 (newest tests)
    - For each test: check if ID exists in local DB
    - STOP when encountering first known test ID
    - This "stop on known ID" logic ONLY works if tests are chronologically ordered

Failure Mode:
    If the API does NOT return tests chronologically:
    - Incremental sync will stop too early (missing new tests)
    - OR sync will fetch all pages every time (no performance benefit)
    - The entire STORY-021 approach would need to be redesigned

Usage:
    # Set environment variables
    export TESTIO_CUSTOMER_API_TOKEN="your-production-token"
    export TESTIO_CUSTOMER_API_BASE_URL="https://api.test.io/customer/v2"
    export TESTIO_PRODUCT_ID=25073  # Product with 100+ tests recommended

    # Run the script
    uv run python scripts/validate_api_chronological_ordering.py

    # Or with inline token (for quick testing)
    TESTIO_CUSTOMER_API_TOKEN="token" TESTIO_PRODUCT_ID=25073 \\
        uv run python scripts/validate_api_chronological_ordering.py

Output:
    - ✅ PASS: Detailed report showing chronological ordering is valid
    - ❌ FAIL: Clear error messages showing where ordering breaks
    - 📊 Analysis: Identifies the field used for sorting

References:
    - STORY-021 AC2: Incremental Sync Algorithm
    - STORY-021 Dev Notes: Key Design Insight - Chronological Ordering
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

# Load .env file from project root (if it exists)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_success(message: str) -> None:
    """Print success message in green."""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")


def print_error(message: str) -> None:
    """Print error message in red."""
    print(f"{Colors.RED}❌ {message}{Colors.END}")


def print_warning(message: str) -> None:
    """Print warning message in yellow."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")


def print_info(message: str) -> None:
    """Print info message in blue."""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")


def print_header(message: str) -> None:
    """Print header message in bold."""
    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{message}{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.END}\n")


async def fetch_tests_page(
    client: httpx.AsyncClient, product_id: int, page: int, per_page: int = 10
) -> list[dict[str, Any]]:
    """Fetch a single page of tests from the API.

    Args:
        client: HTTP client
        product_id: Product ID to fetch tests for
        page: Page number (1-indexed)
        per_page: Tests per page (default: 10, reduced to avoid 500 errors)

    Returns:
        List of test dictionaries
    """
    endpoint = f"products/{product_id}/exploratory_tests"
    response = await client.get(endpoint, params={"page": page, "per_page": per_page})
    response.raise_for_status()
    data = response.json()
    tests: list[dict[str, Any]] = data.get("exploratory_tests", [])
    return tests


def parse_timestamp(timestamp_str: str | None) -> datetime | None:
    """Parse ISO 8601 timestamp string to datetime object.

    Args:
        timestamp_str: ISO 8601 timestamp string (e.g., "2024-01-15T10:30:00Z")

    Returns:
        datetime object or None if parsing fails
    """
    if not timestamp_str:
        return None

    try:
        # Remove timezone suffix for parsing (Z or +00:00)
        clean_timestamp = timestamp_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_timestamp)
    except (ValueError, AttributeError):
        return None


def check_chronological_ordering_within_page(
    tests: list[dict[str, Any]], page_num: int
) -> tuple[bool, str, str]:
    """Check if tests are chronologically ordered within a page by start_at AND end_at.

    Args:
        tests: List of test dictionaries
        page_num: Page number for error messages

    Returns:
        Tuple of (is_ordered, error_message, sort_field)
        sort_field can be: "start_at", "end_at", "both", or "neither"
    """
    # Parse both timestamp fields
    start_timestamps = [parse_timestamp(test.get("start_at")) for test in tests]
    end_timestamps = [parse_timestamp(test.get("end_at")) for test in tests]

    # Check if all timestamps parsed successfully
    if None in start_timestamps:
        none_indices = [i for i, ts in enumerate(start_timestamps) if ts is None]
        return (
            False,
            (
                f"Page {page_num}: Some tests missing start_at timestamp\n"
                f"  Indices with missing start_at: {none_indices}"
            ),
            "neither",
        )

    if None in end_timestamps:
        none_indices = [i for i, ts in enumerate(end_timestamps) if ts is None]
        return (
            False,
            (
                f"Page {page_num}: Some tests missing end_at timestamp\n"
                f"  Indices with missing end_at: {none_indices}"
            ),
            "neither",
        )

    # Check if start_at is in descending order
    start_at_ordered = True
    start_error_index = -1
    for i in range(len(start_timestamps) - 1):
        if start_timestamps[i] < start_timestamps[i + 1]:  # type: ignore
            start_at_ordered = False
            start_error_index = i
            break

    # Check if end_at is in descending order
    end_at_ordered = True
    end_error_index = -1
    for i in range(len(end_timestamps) - 1):
        if end_timestamps[i] < end_timestamps[i + 1]:  # type: ignore
            end_at_ordered = False
            end_error_index = i
            break

    # Determine result
    if start_at_ordered and end_at_ordered:
        return True, "", "both"
    elif start_at_ordered and not end_at_ordered:
        test1_end = tests[end_error_index].get("end_at")
        test1_id = tests[end_error_index]["id"]
        test2_end = tests[end_error_index + 1].get("end_at")
        test2_id = tests[end_error_index + 1]["id"]
        msg = (
            f"Page {page_num}: end_at NOT in descending order "
            f"at index {end_error_index}\n"
            f"  Test {end_error_index}: end_at={test1_end} (ID={test1_id})\n"
            f"  Test {end_error_index + 1}: end_at={test2_end} (ID={test2_id})\n"
            f"  Note: start_at IS ordered correctly"
        )
        return (False, msg, "start_at")
    elif not start_at_ordered and end_at_ordered:
        test1_start = tests[start_error_index].get("start_at")
        test1_id = tests[start_error_index]["id"]
        test2_start = tests[start_error_index + 1].get("start_at")
        test2_id = tests[start_error_index + 1]["id"]
        msg = (
            f"Page {page_num}: start_at NOT in descending order "
            f"at index {start_error_index}\n"
            f"  Test {start_error_index}: start_at={test1_start} (ID={test1_id})\n"
            f"  Test {start_error_index + 1}: start_at={test2_start} "
            f"(ID={test2_id})\n"
            f"  Note: end_at IS ordered correctly"
        )
        return (False, msg, "end_at")
    else:
        return (
            False,
            (
                f"Page {page_num}: NEITHER start_at NOR end_at in descending order\n"
                f"  start_at error at index {start_error_index}\n"
                f"  end_at error at index {end_error_index}"
            ),
            "neither",
        )


def identify_sort_field(tests: list[dict[str, Any]]) -> str:
    """Identify which field is used for sorting tests.

    Analyzes test data to determine if tests are sorted by:
    - id (test ID)
    - created_at (test creation date)
    - start_at (test start date)
    - end_at (test end date)

    Args:
        tests: List of test dictionaries (should span multiple pages)

    Returns:
        Name of the field used for sorting (or "unknown")
    """
    if len(tests) < 10:
        return "unknown (insufficient data)"

    # Check if sorted by ID (descending)
    ids = [test["id"] for test in tests]
    if ids == sorted(ids, reverse=True):
        # IDs are in descending order, check if timestamps also follow
        created_timestamps = [
            parse_timestamp(test.get("created_at")) for test in tests if test.get("created_at")
        ]
        start_timestamps = [
            parse_timestamp(test.get("start_at")) for test in tests if test.get("start_at")
        ]

        # Filter out None values
        created_timestamps = [ts for ts in created_timestamps if ts]
        start_timestamps = [ts for ts in start_timestamps if ts]

        # Check if created_at also descending
        if created_timestamps and created_timestamps == sorted(
            created_timestamps, reverse=True, key=lambda x: x or datetime.min
        ):
            return "id (and created_at correlates)"

        # Check if start_at also descending
        if start_timestamps and start_timestamps == sorted(
            start_timestamps, reverse=True, key=lambda x: x or datetime.min
        ):
            return "id (and start_at correlates)"

        return "id (descending)"

    return "unknown (not sorted by id)"


async def main() -> int:
    """Main validation logic.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    print_header("TestIO API Chronological Ordering Validation")

    # Load configuration from environment
    api_token = os.getenv("TESTIO_CUSTOMER_API_TOKEN")
    base_url = os.getenv("TESTIO_CUSTOMER_API_BASE_URL", "https://api.test.io/customer/v2")
    product_id_str = os.getenv("TESTIO_PRODUCT_ID")

    # Validate configuration
    if not api_token:
        print_error("TESTIO_CUSTOMER_API_TOKEN environment variable is required")
        print_info("Usage: export TESTIO_CUSTOMER_API_TOKEN='your-token'")
        return 1

    if not product_id_str:
        print_error("TESTIO_PRODUCT_ID environment variable is required")
        print_info("Usage: export TESTIO_PRODUCT_ID=25073")
        return 1

    try:
        product_id = int(product_id_str)
    except ValueError:
        print_error(f"TESTIO_PRODUCT_ID must be an integer, got: {product_id_str}")
        return 1

    print_info(f"Product ID: {product_id}")
    print_info(f"Base URL: {base_url}")
    print_info(f"API Token: {api_token[:10]}... (redacted)")
    print()

    # Create HTTP client
    async with httpx.AsyncClient(
        base_url=base_url,
        headers={
            "Authorization": f"Token {api_token}",
            "User-Agent": "TestIO-MCP-Validation-Script/1.0",
        },
        timeout=30.0,
    ) as client:
        # Fetch multiple pages
        print_info("Fetching tests from API (up to 25 pages, 10 tests per page)...")
        all_tests: list[dict[str, Any]] = []
        pages_data: list[list[dict[str, Any]]] = []
        max_pages = 25  # Fetch more pages since we're using smaller page size

        try:
            consecutive_500s = 0
            for page_num in range(1, max_pages + 1):
                try:
                    tests = await fetch_tests_page(client, product_id, page_num)

                    if not tests:
                        print_info(f"No more tests available (stopped at page {page_num})")
                        break

                    pages_data.append(tests)
                    all_tests.extend(tests)
                    print_info(f"  Page {page_num}: {len(tests)} tests fetched")
                    consecutive_500s = 0  # Reset counter on success

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 500:
                        consecutive_500s += 1
                        print_warning(f"Page {page_num}: API returned 500 error (skipping)")

                        if consecutive_500s >= 3:
                            print_warning("  3 consecutive 500 errors - stopping pagination")
                            print_warning(
                                "  This is likely an API bug, not a chronological ordering issue"
                            )
                            num_tests = len(all_tests)
                            num_pages = len(pages_data)
                            print_warning(
                                f"  Continuing validation with {num_tests} tests "
                                f"from {num_pages} pages"
                            )
                            break
                        else:
                            print_warning(
                                f"  Trying next page (consecutive 500s: {consecutive_500s})"
                            )
                            continue
                    else:
                        # Re-raise non-500 errors
                        raise

        except httpx.HTTPStatusError as e:
            print_error(f"HTTP error: {e.response.status_code}")
            print_error(f"Response: {e.response.text}")
            return 1
        except Exception as e:
            print_error(f"Failed to fetch tests: {e}")
            return 1

    # Validate we have enough data
    if len(all_tests) < 50:
        print_warning(
            f"Product {product_id} has only {len(all_tests)} tests. "
            "Use a product with 100+ tests for reliable validation."
        )

    if len(pages_data) < 2:
        print_warning(
            f"Only {len(pages_data)} page(s) fetched. "
            "Use a product with 200+ tests to validate cross-page ordering."
        )

    print()
    print_header("Validation Results")

    # ========================================
    # Check 1: Chronological ordering WITHIN each page (start_at AND end_at)
    # ========================================
    print_info(
        "Check 1: Chronological ordering WITHIN each page (checking both start_at and end_at)"
    )
    within_page_valid = True
    sort_fields = []

    for page_num, tests in enumerate(pages_data, start=1):
        is_ordered, error_msg, sort_field = check_chronological_ordering_within_page(
            tests, page_num
        )
        sort_fields.append(sort_field)

        if not is_ordered:
            print_error(f"Page {page_num}: NOT chronologically ordered")
            print(f"  {error_msg}")
            within_page_valid = False
        else:
            first_start = tests[0].get("start_at")
            last_start = tests[-1].get("start_at")
            first_end = tests[0].get("end_at")
            last_end = tests[-1].get("end_at")
            print_success(f"Page {page_num}: ✅ Both start_at AND end_at are ordered")
            print(f"    start_at: {first_start} ... {last_start}")
            print(f"    end_at:   {first_end} ... {last_end}")

    print()

    # ========================================
    # Check 2: Chronological ordering ACROSS page boundaries (start_at AND end_at)
    # ========================================
    print_info(
        "Check 2: Chronological ordering ACROSS page boundaries (checking both start_at and end_at)"
    )
    across_pages_valid = True

    if len(pages_data) >= 2:
        for i in range(len(pages_data) - 1):
            page_n = pages_data[i]
            page_n_plus_1 = pages_data[i + 1]

            last_test_page_n = page_n[-1]
            first_test_page_n_plus_1 = page_n_plus_1[0]

            last_start_at = parse_timestamp(last_test_page_n.get("start_at"))
            first_start_at = parse_timestamp(first_test_page_n_plus_1.get("start_at"))
            last_end_at = parse_timestamp(last_test_page_n.get("end_at"))
            first_end_at = parse_timestamp(first_test_page_n_plus_1.get("end_at"))

            # Check for missing timestamps
            if last_start_at is None or first_start_at is None:
                print_error(f"Page {i + 1} → Page {i + 2}: Missing start_at timestamp")
                across_pages_valid = False
                continue

            if last_end_at is None or first_end_at is None:
                print_error(f"Page {i + 1} → Page {i + 2}: Missing end_at timestamp")
                across_pages_valid = False
                continue

            # Check both fields
            start_at_ordered = last_start_at >= first_start_at
            end_at_ordered = last_end_at >= first_end_at

            if start_at_ordered and end_at_ordered:
                print_success(f"Page {i + 1} → Page {i + 2}: ✅ Both fields ordered")
                last_start = last_test_page_n.get("start_at")
                first_start = first_test_page_n_plus_1.get("start_at")
                last_end = last_test_page_n.get("end_at")
                first_end = first_test_page_n_plus_1.get("end_at")
                print(f"    start_at: {last_start} >= {first_start}")
                print(f"    end_at:   {last_end} >= {first_end}")
            else:
                print_error(
                    f"Page {i + 1} → Page {i + 2}: NOT chronologically ordered across boundary"
                )
                last_start = last_test_page_n.get("start_at")
                first_start = first_test_page_n_plus_1.get("start_at")
                last_end = last_test_page_n.get("end_at")
                first_end = first_test_page_n_plus_1.get("end_at")

                if not start_at_ordered:
                    print(f"  ❌ start_at: {last_start} < {first_start}")
                else:
                    print(f"  ✅ start_at: {last_start} >= {first_start}")

                if not end_at_ordered:
                    print(f"  ❌ end_at:   {last_end} < {first_end}")
                else:
                    print(f"  ✅ end_at:   {last_end} >= {first_end}")
                across_pages_valid = False
    else:
        print_warning("Insufficient pages to validate cross-page ordering")

    print()

    # ========================================
    # Check 3: Identify sort field
    # ========================================
    print_info("Check 3: Identify sort field")
    sort_field = identify_sort_field(all_tests)
    print_success(f"Sort field: {sort_field}")

    # Show sample data for manual inspection
    if all_tests:
        print()
        print_info("Sample test data (first 5 tests):")
        for i, test in enumerate(all_tests[:5]):
            print(f"\n  Test {i + 1}:")
            print(f"    id:         {test.get('id')}")
            print(f"    created_at: {test.get('created_at')}")
            print(f"    start_at:   {test.get('start_at')}")
            print(f"    end_at:     {test.get('end_at')}")

    print()
    print_header("Summary")

    # Final verdict
    all_checks_passed = within_page_valid and across_pages_valid

    if all_checks_passed:
        print_success("VALIDATION PASSED")
        print_success(f"API returns {len(all_tests)} tests in chronological order (newest first)")
        print_success(f"Pages validated: {len(pages_data)}")
        print_success(f"Sort field: {sort_field}")
        print()
        print_success("✅ STORY-021 incremental sync assumption is VALID!")
        print_info("The incremental sync algorithm can safely use 'stop on known ID' logic.")
        return 0
    else:
        print_error("VALIDATION FAILED")
        print_error("TestIO API does NOT return tests in chronological order!")
        print()
        print_warning("⚠️  IMPACT:")
        print("   - STORY-021 incremental sync algorithm CANNOT be implemented as designed")
        print("   - The 'stop on known ID' optimization will NOT work correctly")
        print()
        print_info("💡 ACTION REQUIRED:")
        print("   1. Investigate why API ordering is not chronological")
        print("   2. Contact TestIO support to clarify API ordering behavior")
        print("   3. Redesign STORY-021 sync algorithm (use different stop condition)")
        print("   4. Update story estimates and acceptance criteria")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
