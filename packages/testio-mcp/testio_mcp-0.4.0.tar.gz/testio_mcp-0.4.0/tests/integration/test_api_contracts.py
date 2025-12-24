"""API contract tests for features and user stories endpoints.

These tests validate:
1. Endpoint availability (200 status codes)
2. Response schema compliance (required fields present with correct types)
3. Section vs non-section product behavior

Purpose: Detect API changes BEFORE they break production sync.

Note: Uses real API with test product from TESTIO_PRODUCT_ID/TESTIO_PRODUCT_IDS.

IMPORTANT: These tests are READ-ONLY contract validations.
They validate that the TestIO API returns expected response structures.

Section Detection: Tests use has_sections() to dynamically detect product type
and use the appropriate endpoint:
- Section products: /products/{id}/sections/{sid}/features
- Non-section products: /products/{id}/features
"""

import pytest

from testio_mcp.client import TestIOClient
from testio_mcp.exceptions import TestIOAPIError
from testio_mcp.utilities.section_detection import get_section_ids, has_sections


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.asyncio
async def test_features_endpoint_returns_valid_response(
    shared_client: TestIOClient, test_product_id: int
) -> None:
    """Contract test: Features endpoint returns 200 with valid structure.

    Validates:
    - GET /products/{id}/features returns 200 (non-section products)
    - GET /products/{id}/sections/{sid}/features returns 200 (section products)
    - Response contains 'features' array
    - Response structure is valid JSON
    """
    # Detect product type upfront
    product_response = await shared_client.get(f"products/{test_product_id}")
    product = product_response.get("product", {})

    if has_sections(product):
        section_ids = get_section_ids(product)
        response = await shared_client.get(
            f"products/{test_product_id}/sections/{section_ids[0]}/features"
        )
    else:
        response = await shared_client.get(f"products/{test_product_id}/features")

    # Validate response structure (same for both endpoints)
    assert "features" in response, "Response missing 'features' key"
    assert isinstance(response["features"], list), "'features' must be array"


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.asyncio
async def test_features_have_required_fields(
    shared_client: TestIOClient, test_product_id: int
) -> None:
    """Contract test: Each feature has required fields with correct types.

    Validates:
    - Feature objects contain 'id' (integer)
    - Feature objects contain 'title' (string)
    - Optional fields: description, howtofind (may be null)
    """
    # Detect product type upfront
    product_response = await shared_client.get(f"products/{test_product_id}")
    product = product_response.get("product", {})

    if has_sections(product):
        section_ids = get_section_ids(product)
        response = await shared_client.get(
            f"products/{test_product_id}/sections/{section_ids[0]}/features"
        )
    else:
        response = await shared_client.get(f"products/{test_product_id}/features")

    features = response["features"]

    assert len(features) > 0, "Expected at least one feature for validation"

    # Validate first feature schema (representative)
    feature = features[0]

    # Required fields
    assert "id" in feature, "Feature missing 'id' field"
    assert "title" in feature, "Feature missing 'title' field"

    # Type validation
    assert isinstance(feature["id"], int), "Feature 'id' must be integer"
    assert isinstance(feature["title"], str), "Feature 'title' must be string"

    # Optional fields (may be null)
    if "description" in feature:
        assert isinstance(feature["description"], (str, type(None))), (
            "Feature 'description' must be string or null"
        )

    if "howtofind" in feature:
        assert isinstance(feature["howtofind"], (str, type(None))), (
            "Feature 'howtofind' must be string or null"
        )


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.asyncio
async def test_features_array_not_empty_for_known_product(
    shared_client: TestIOClient, test_product_id: int
) -> None:
    """Contract test: Known product returns non-empty features array.

    Validates:
    - GET /products/{id}/features returns at least one feature
    - API has not removed or hidden product features

    Purpose: Detect if API changes cause features to disappear.
    """
    # Detect product type upfront
    product_response = await shared_client.get(f"products/{test_product_id}")
    product = product_response.get("product", {})

    if has_sections(product):
        section_ids = get_section_ids(product)
        response = await shared_client.get(
            f"products/{test_product_id}/sections/{section_ids[0]}/features"
        )
    else:
        response = await shared_client.get(f"products/{test_product_id}/features")

    features = response["features"]

    assert len(features) > 0, f"Product {test_product_id} should have at least one feature"
    # Note: We don't assert exact count because that's too brittle.
    # If features drop to 0, that's a breaking change. If count varies slightly, that's acceptable.


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.asyncio
async def test_features_endpoint_handles_not_found(shared_client: TestIOClient) -> None:
    """Contract test: Non-existent product returns 404.

    Validates:
    - GET /products/999999/features returns 404 (or 403)
    - API error handling is consistent
    """
    with pytest.raises(TestIOAPIError) as exc_info:
        await shared_client.get("products/999999/features")

    # Accept 404 (Not Found) or 403 (Forbidden) as valid error responses
    assert exc_info.value.status_code in {403, 404}, (
        f"Expected 404 or 403 for non-existent product, got {exc_info.value.status_code}"
    )


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.asyncio
async def test_features_id_uniqueness(shared_client: TestIOClient, test_product_id: int) -> None:
    """Contract test: Feature IDs are unique within product.

    Validates:
    - No duplicate feature IDs in response
    - API does not return malformed data

    Purpose: Detect data integrity issues in API responses.
    """
    # Detect product type upfront
    product_response = await shared_client.get(f"products/{test_product_id}")
    product = product_response.get("product", {})

    if has_sections(product):
        section_ids = get_section_ids(product)
        response = await shared_client.get(
            f"products/{test_product_id}/sections/{section_ids[0]}/features"
        )
    else:
        response = await shared_client.get(f"products/{test_product_id}/features")

    features = response["features"]

    feature_ids = [f["id"] for f in features]
    unique_ids = set(feature_ids)

    assert len(feature_ids) == len(unique_ids), (
        f"Duplicate feature IDs found: {len(feature_ids)} total, {len(unique_ids)} unique"
    )


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.asyncio
async def test_features_schema_stability(shared_client: TestIOClient, test_product_id: int) -> None:
    """Contract test: Validate ALL features have consistent schema.

    Validates:
    - All features in response have same field structure
    - No schema variation between features
    - Type consistency across all items

    Purpose: Detect schema drift or inconsistent API responses.
    """
    # Detect product type upfront
    product_response = await shared_client.get(f"products/{test_product_id}")
    product = product_response.get("product", {})

    if has_sections(product):
        section_ids = get_section_ids(product)
        response = await shared_client.get(
            f"products/{test_product_id}/sections/{section_ids[0]}/features"
        )
    else:
        response = await shared_client.get(f"products/{test_product_id}/features")

    features = response["features"]

    # Validate ALL features (not just first one)
    for idx, feature in enumerate(features):
        # Required fields
        assert "id" in feature, f"Feature {idx} missing 'id' field"
        assert "title" in feature, f"Feature {idx} missing 'title' field"

        # Type consistency
        assert isinstance(feature["id"], int), f"Feature {idx} 'id' must be integer"
        assert isinstance(feature["title"], str), f"Feature {idx} 'title' must be string"


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.asyncio
async def test_section_product_features_endpoint(
    shared_client: TestIOClient, test_product_id: int
) -> None:
    """Contract test: Section product features endpoint.

    Validates:
    - GET /products/{id}/sections/{sid}/features returns 200
    - Endpoint exists and is accessible
    - Response contains 'features' array
    - Each feature has required fields
    """
    # Check if this is a section product
    product_response = await shared_client.get(f"products/{test_product_id}")
    product = product_response.get("product", {})

    if not has_sections(product):
        pytest.skip(f"Product {test_product_id} is not a section product")

    section_ids = get_section_ids(product)
    response = await shared_client.get(
        f"products/{test_product_id}/sections/{section_ids[0]}/features"
    )

    # Validate response structure
    assert "features" in response, "Response missing 'features' key"
    assert isinstance(response["features"], list), "'features' must be array"

    # Validate feature schema if features exist
    if response["features"]:
        feature = response["features"][0]
        assert "id" in feature, "Feature missing 'id' field"
        assert "title" in feature, "Feature missing 'title' field"
        assert isinstance(feature["id"], int), "Feature 'id' must be integer"
        assert isinstance(feature["title"], str), "Feature 'title' must be string"


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.asyncio
async def test_section_product_features_without_section_fails(
    shared_client: TestIOClient, test_product_id: int
) -> None:
    """Contract test: Section product REQUIRES section in path.

    Validates that calling /products/{id}/features for a section product
    returns 422 (section_id required).
    """
    # Check if this is a section product
    product_response = await shared_client.get(f"products/{test_product_id}")
    product = product_response.get("product", {})

    if not has_sections(product):
        pytest.skip(f"Product {test_product_id} is not a section product")

    # Verify that calling features without section returns 422
    with pytest.raises(TestIOAPIError) as exc_info:
        await shared_client.get(f"products/{test_product_id}/features")

    assert exc_info.value.status_code == 422, (
        f"Expected 422 for section product without section_id, got {exc_info.value.status_code}"
    )


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.asyncio
async def test_non_section_product_user_stories_endpoint(
    shared_client: TestIOClient, test_product_id: int
) -> None:
    """Contract test: Non-section product user stories endpoint.

    Validates:
    - GET /products/{id}/user_stories returns 200 (or 500 for section products)
    - Response contains 'user_stories' array
    - Each user story has required fields: id, title, path

    Note: feature_id field is optional in API response.
    """
    # Check if this is a section product (skip - this test is for non-section products)
    product_response = await shared_client.get(f"products/{test_product_id}")
    product = product_response.get("product", {})
    if has_sections(product):
        pytest.skip(f"Product {test_product_id} is a section product")

    response = await shared_client.get(f"products/{test_product_id}/user_stories")

    # Validate response structure
    assert "user_stories" in response, "Response missing 'user_stories' key"
    user_stories = response["user_stories"]
    assert isinstance(user_stories, list), "'user_stories' must be array"
    assert len(user_stories) > 0, "User stories array should not be empty"

    # Validate user story schema (first story as representative)
    user_story = user_stories[0]
    assert "id" in user_story, "User story missing 'id' field"
    assert "title" in user_story, "User story missing 'title' field"
    # Note: feature_id and path may be present but not required
    assert isinstance(user_story["id"], int), "User story 'id' must be integer"
    assert isinstance(user_story["title"], str), "User story 'title' must be string"


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.asyncio
async def test_section_product_user_stories_with_section_param(
    shared_client: TestIOClient, test_product_id: int
) -> None:
    """Contract test: Section product user stories with section_id param.

    Validates:
    - GET /products/{id}/user_stories?section_id={sid} returns 200
    - Response contains 'user_stories' array
    - Each user story has required fields
    """
    # Check if this is a section product
    product_response = await shared_client.get(f"products/{test_product_id}")
    product = product_response.get("product", {})

    if not has_sections(product):
        pytest.skip(f"Product {test_product_id} is not a section product")

    section_ids = get_section_ids(product)
    response = await shared_client.get(
        f"products/{test_product_id}/user_stories?section_id={section_ids[0]}"
    )

    # Validate response structure
    assert "user_stories" in response, "Response missing 'user_stories' key"
    assert isinstance(response["user_stories"], list), "'user_stories' must be array"

    # Validate user story schema if stories exist
    if response["user_stories"]:
        story = response["user_stories"][0]
        assert "id" in story, "User story missing 'id' field"
        assert "title" in story, "User story missing 'title' field"
        assert isinstance(story["id"], int), "User story 'id' must be integer"
        assert isinstance(story["title"], str), "User story 'title' must be string"


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.asyncio
async def test_section_product_user_stories_without_section_param_fails(
    shared_client: TestIOClient, test_product_id: int
) -> None:
    """Contract test: Section product user stories REQUIRE section_id param.

    Validates that calling /products/{id}/user_stories for a section product
    without section_id returns 400 or 500.
    """
    # Check if this is a section product
    product_response = await shared_client.get(f"products/{test_product_id}")
    product = product_response.get("product", {})

    if not has_sections(product):
        pytest.skip(f"Product {test_product_id} is not a section product")

    # Verify that calling user_stories without section_id fails
    with pytest.raises(TestIOAPIError) as exc_info:
        await shared_client.get(f"products/{test_product_id}/user_stories")

    assert exc_info.value.status_code in {400, 500}, (
        f"Expected 400 or 500 for section product without section_id, "
        f"got {exc_info.value.status_code}"
    )


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.asyncio
async def test_schema_field_types_validation(
    shared_client: TestIOClient, test_product_id: int
) -> None:
    """Contract test: Validate field TYPES not just presence.

    Codex Enhancement: Detect field type changes (e.g., id becomes string).
    """
    # Detect product type upfront
    product_response = await shared_client.get(f"products/{test_product_id}")
    product = product_response.get("product", {})
    is_section_product = has_sections(product)

    # Get features (use section endpoint for section products)
    if is_section_product:
        section_ids = get_section_ids(product)
        response = await shared_client.get(
            f"products/{test_product_id}/sections/{section_ids[0]}/features"
        )
    else:
        response = await shared_client.get(f"products/{test_product_id}/features")

    features = response["features"]

    # Validate first feature has correct types (if features exist)
    if features:
        feature = features[0]
        assert isinstance(feature["id"], int), "Feature 'id' must be integer"
        assert isinstance(feature["title"], str), "Feature 'title' must be string"
        assert isinstance(feature.get("description"), (str, type(None))), (
            "Feature 'description' must be string or null"
        )

    # Get user stories (use section_id param for section products)
    if is_section_product:
        response = await shared_client.get(
            f"products/{test_product_id}/user_stories?section_id={section_ids[0]}"
        )
    else:
        response = await shared_client.get(f"products/{test_product_id}/user_stories")

    user_stories = response["user_stories"]

    # Validate first user story has correct types (if stories exist)
    if user_stories:
        story = user_stories[0]
        assert isinstance(story["id"], int), "User story 'id' must be integer"
        assert isinstance(story["title"], str), "User story 'title' must be string"
        # Note: feature_id is optional, skip validation if not present
        if "feature_id" in story:
            assert isinstance(story["feature_id"], int), "User story 'feature_id' must be integer"


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.asyncio
async def test_pagination_sentinel_large_dataset(
    shared_client: TestIOClient, test_product_id: int
) -> None:
    """Contract test: Detect if pagination appears unexpectedly.

    Codex Enhancement: Warn if response > 2000 items (pagination may be coming).
    """
    # Check if this is a section product (skip - this test is for non-section products)
    product_response = await shared_client.get(f"products/{test_product_id}")
    product = product_response.get("product", {})
    if has_sections(product):
        pytest.skip(f"Product {test_product_id} is a section product")

    response = await shared_client.get(f"products/{test_product_id}/user_stories")

    # Check for pagination indicators
    pagination_keys = {"pagination", "next", "total", "page", "per_page"}
    found_pagination = pagination_keys.intersection(response.keys())

    # Validate no pagination (current behavior)
    assert not found_pagination, f"Unexpected pagination keys found: {found_pagination}"

    # Warn if response is very large (>2000 items)
    user_stories = response.get("user_stories", [])
    if len(user_stories) > 2000:
        import warnings

        warnings.warn(
            f"Large response detected: {len(user_stories)} user stories. "
            "API may add pagination in future.",
            UserWarning,
            stacklevel=2,
        )


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.asyncio
async def test_features_422_fallback_to_sections(
    shared_client: TestIOClient, test_product_id: int
) -> None:
    """Contract test: 422→section fallback pattern.

    Validates the fallback pattern:
    1. Call /products/{id}/features → 422 for section products
    2. Fallback to /products/{id}/sections/{sid}/features → 200
    """
    # Check if this is a section product
    product_response = await shared_client.get(f"products/{test_product_id}")
    product = product_response.get("product", {})

    if not has_sections(product):
        pytest.skip(f"Product {test_product_id} is not a section product")

    section_ids = get_section_ids(product)

    # Step 1: Verify non-section endpoint returns 422
    with pytest.raises(TestIOAPIError) as exc_info:
        await shared_client.get(f"products/{test_product_id}/features")

    assert exc_info.value.status_code == 422, (
        f"Expected 422 for section product, got {exc_info.value.status_code}"
    )

    # Step 2: Verify section endpoint works
    response = await shared_client.get(
        f"products/{test_product_id}/sections/{section_ids[0]}/features"
    )
    assert "features" in response, "Fallback endpoint should return features"


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.asyncio
async def test_concurrent_section_calls(shared_client: TestIOClient, test_product_id: int) -> None:
    """Contract test: Minimal concurrency test (2 endpoints in parallel).

    Validates that concurrent calls to section endpoints work correctly.
    """
    import asyncio

    # Check if this is a section product
    product_response = await shared_client.get(f"products/{test_product_id}")
    product = product_response.get("product", {})

    if not has_sections(product):
        pytest.skip(f"Product {test_product_id} is not a section product")

    section_ids = get_section_ids(product)
    section_id = section_ids[0]

    # Make concurrent calls to features and user_stories
    async def get_features() -> dict:
        return await shared_client.get(f"products/{test_product_id}/sections/{section_id}/features")

    async def get_user_stories() -> dict:
        return await shared_client.get(
            f"products/{test_product_id}/user_stories?section_id={section_id}"
        )

    features_response, user_stories_response = await asyncio.gather(
        get_features(), get_user_stories()
    )

    # Validate both responses
    assert "features" in features_response, "Features response missing 'features' key"
    assert "user_stories" in user_stories_response, "User stories response missing key"
