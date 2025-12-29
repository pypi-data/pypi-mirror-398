"""Test to verify fixtures are working correctly.

This minimal test file exists to confirm the test infrastructure is operational.
"""


def test_mock_api_client_fixture(mock_api_client):
    """Verify mock_api_client fixture is available and configured."""
    assert mock_api_client is not None
    assert mock_api_client.health_check() == {"status": "healthy", "version": "1.0.0"}


def test_mock_working_dir_fixture(mock_working_dir):
    """Verify mock_working_dir fixture creates expected structure."""
    assert mock_working_dir.exists()
    assert (mock_working_dir / "README.md").exists()
    assert (mock_working_dir / "pyproject.toml").exists()
    assert (mock_working_dir / "src").is_dir()


def test_sample_derive_request_fixture(sample_derive_request):
    """Verify sample_derive_request fixture has expected fields."""
    assert sample_derive_request.objective == "Add user authentication to the application"
    assert "python" in sample_derive_request.project_context.get("languages", [])


EXPECTED_PLAN_ITEM_COUNT = 2


def test_sample_execution_request_fixture(sample_execution_request):
    """Verify sample_execution_request fixture has expected fields."""
    assert len(sample_execution_request.plan_items) == EXPECTED_PLAN_ITEM_COUNT
    assert sample_execution_request.current_item is not None
    assert sample_execution_request.current_item["id"] == "T1"
