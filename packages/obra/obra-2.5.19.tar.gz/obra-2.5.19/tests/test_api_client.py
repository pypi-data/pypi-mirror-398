"""Tests for obra.api.client module.

Focuses on token persistence and error handling behavior.

Resource Limits (per docs/quality/testing/test-guidelines.md):
- Max sleep: 0.5s per test
- Max threads: 5 per test
- Max memory: 20KB per test
"""

import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pydantic import BaseModel, Field

from obra.api.client import APIClient
from obra.exceptions import APIError


class TestTokenSaveLogging:
    """Test logging behavior when token save fails."""

    @pytest.fixture
    def client(self) -> APIClient:
        """Create a basic APIClient instance for testing."""
        return APIClient(
            base_url="https://test.example.com",
            auth_token="test-token",
            refresh_token="test-refresh-token",
        )

    def test_save_token_logs_file_permission_error(self, client: APIClient, caplog: pytest.LogCaptureFixture, tmp_path: Path) -> None:
        """Test that PermissionError during token save is logged with full details."""
        # Create a config file
        config_path = tmp_path / ".obra" / "client-config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("auth_token: old-token\n")

        with caplog.at_level(logging.ERROR):
            with patch("obra.api.client.Path.home", return_value=tmp_path):
                # Mock open to raise PermissionError on write
                original_open = open
                def mock_open_func(path, *args, **kwargs):
                    if "w" in args or kwargs.get("mode", "r").startswith("w"):
                        raise PermissionError("Permission denied")
                    return original_open(path, *args, **kwargs)

                with patch("builtins.open", side_effect=mock_open_func):
                    # This should catch the exception and log it
                    client._save_token_to_config("new-token")

        # Verify the error was logged
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "ERROR"
        assert "Failed to save auth token to config file" in record.message
        assert "Permission denied" in record.message
        assert "PermissionError" in record.message
        # Verify exc_info is included (stack trace)
        assert record.exc_info is not None

    def test_save_token_logs_yaml_error(self, client: APIClient, caplog: pytest.LogCaptureFixture, tmp_path: Path) -> None:
        """Test that YAML serialization errors during token save are logged."""
        # Create a config file
        config_path = tmp_path / ".obra" / "client-config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("auth_token: old-token\n")

        with caplog.at_level(logging.ERROR):
            with patch("obra.api.client.Path.home", return_value=tmp_path):
                # yaml.safe_dump raises an error
                with patch("obra.api.client.yaml.safe_dump", side_effect=ValueError("Invalid YAML")):
                    client._save_token_to_config("new-token")

        # Verify the error was logged
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "ERROR"
        assert "Failed to save auth token to config file" in record.message
        assert "Invalid YAML" in record.message
        assert "ValueError" in record.message
        assert record.exc_info is not None

    def test_save_token_succeeds_without_logging(self, client: APIClient, caplog: pytest.LogCaptureFixture, tmp_path: Path) -> None:
        """Test that successful token save does not generate error logs."""
        config_path = tmp_path / ".obra" / "client-config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("auth_token: old-token\n")

        with caplog.at_level(logging.ERROR):
            with patch("obra.api.client.Path.home", return_value=tmp_path):
                client._save_token_to_config("new-token")

        # Verify no error logs were generated
        assert len(caplog.records) == 0
        # Verify the token was actually saved
        assert "new-token" in config_path.read_text()

    def test_save_token_validates_file_exists_after_write(self, client: APIClient, tmp_path: Path) -> None:
        """Test that ConfigurationError is raised if file doesn't exist after write."""
        from obra.exceptions import ConfigurationError

        config_path = tmp_path / ".obra" / "client-config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("auth_token: old-token\n")

        with patch("obra.api.client.Path.home", return_value=tmp_path):
            # Mock yaml.safe_dump to delete the file after writing (simulating filesystem issue)
            original_dump = __import__("yaml").safe_dump

            def mock_dump(data, file, **kwargs):
                result = original_dump(data, file, **kwargs)
                # Delete the file after writing to simulate a filesystem issue
                file.close()
                config_path.unlink()
                return result

            with patch("obra.api.client.yaml.safe_dump", side_effect=mock_dump):
                with pytest.raises(ConfigurationError, match="Token save validation failed.*does not exist"):
                    client._save_token_to_config("new-token")

    def test_save_token_validates_content_after_write(self, client: APIClient, tmp_path: Path) -> None:
        """Test that ConfigurationError is raised if token content doesn't match after write."""
        from obra.exceptions import ConfigurationError

        config_path = tmp_path / ".obra" / "client-config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("auth_token: old-token\n")

        with patch("obra.api.client.Path.home", return_value=tmp_path):
            # Mock yaml.safe_load to return wrong token during validation read
            original_safe_load = __import__("yaml").safe_load
            call_count = [0]

            def mock_safe_load(f):
                call_count[0] += 1
                result = original_safe_load(f)
                # Return correct data for first call (loading existing config)
                # Return wrong token for validation read
                if call_count[0] == 2:
                    result["auth_token"] = "wrong-token"
                return result

            with patch("obra.api.client.yaml.safe_load", side_effect=mock_safe_load):
                with pytest.raises(ConfigurationError, match="Token save validation failed.*Token mismatch"):
                    client._save_token_to_config("new-token")


class TestSchemaValidation:
    """Test schema validation in APIClient._request()."""

    @pytest.fixture
    def client(self) -> APIClient:
        """Create a basic APIClient instance for testing."""
        return APIClient(
            base_url="https://test.example.com",
            auth_token="test-token",
        )

    def test_request_without_schema_returns_raw_response(self, client: APIClient) -> None:
        """Test that requests without schema return raw response unchanged."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "data": {"id": 123}}

        with patch.object(client.session, "request", return_value=mock_response):
            result = client._request("GET", "test-endpoint")

        assert result == {"status": "success", "data": {"id": 123}}

    def test_request_with_valid_schema_validates_and_returns(self, client: APIClient) -> None:
        """Test that valid responses are validated against schema."""

        class TestSchema(BaseModel):
            status: str
            message: str = Field(default="")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "message": "OK"}

        with patch.object(client.session, "request", return_value=mock_response):
            result = client._request("GET", "test-endpoint", response_schema=TestSchema)

        assert result == {"status": "success", "message": "OK"}

    def test_request_with_invalid_schema_raises_api_error(self, client: APIClient) -> None:
        """Test that invalid responses raise APIError with validation details."""

        class TestSchema(BaseModel):
            status: str
            count: int  # Required field

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}  # Missing 'count'

        with patch.object(client.session, "request", return_value=mock_response):
            with pytest.raises(APIError, match="Response validation failed.*count.*required"):
                client._request("GET", "test-endpoint", response_schema=TestSchema)

    def test_request_with_wrong_type_raises_api_error(self, client: APIClient) -> None:
        """Test that type mismatches raise APIError with details."""

        class TestSchema(BaseModel):
            count: int

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"count": "not-a-number"}  # Wrong type

        with patch.object(client.session, "request", return_value=mock_response):
            with pytest.raises(APIError, match="Response validation failed.*count"):
                client._request("GET", "test-endpoint", response_schema=TestSchema)

    def test_schema_validation_strips_extra_fields(self, client: APIClient) -> None:
        """Test that extra fields are handled according to schema configuration."""
        from pydantic import ConfigDict

        class StrictSchema(BaseModel):
            model_config = ConfigDict(extra="forbid")
            status: str

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "extra_field": "ignored"}

        with patch.object(client.session, "request", return_value=mock_response):
            # Should raise because extra fields are forbidden
            with pytest.raises(APIError, match="Response validation failed.*extra"):
                client._request("GET", "test-endpoint", response_schema=StrictSchema)

    def test_schema_validation_with_optional_fields(self, client: APIClient) -> None:
        """Test that optional fields work correctly in validation."""

        class TestSchema(BaseModel):
            status: str
            message: str | None = None

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}

        with patch.object(client.session, "request", return_value=mock_response):
            result = client._request("GET", "test-endpoint", response_schema=TestSchema)

        assert result == {"status": "success", "message": None}

    def test_schema_validation_with_nested_objects(self, client: APIClient) -> None:
        """Test validation with nested object structures."""

        class NestedData(BaseModel):
            id: int
            name: str

        class TestSchema(BaseModel):
            status: str
            data: NestedData

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": {"id": 123, "name": "test"}
        }

        with patch.object(client.session, "request", return_value=mock_response):
            result = client._request("GET", "test-endpoint", response_schema=TestSchema)

        assert result == {
            "status": "success",
            "data": {"id": 123, "name": "test"}
        }

    def test_schema_validation_with_nested_invalid_data(self, client: APIClient) -> None:
        """Test validation error reporting for nested structures."""

        class NestedData(BaseModel):
            id: int
            name: str

        class TestSchema(BaseModel):
            status: str
            data: NestedData

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": {"id": "not-int", "name": "test"}  # Invalid nested field
        }

        with patch.object(client.session, "request", return_value=mock_response):
            with pytest.raises(APIError, match="Response validation failed.*data.id"):
                client._request("GET", "test-endpoint", response_schema=TestSchema)

    def test_schema_validation_preserves_on_token_refresh(self, client: APIClient) -> None:
        """Test that schema validation is preserved when token refresh triggers retry."""
        client.refresh_token = "test-refresh"
        client.firebase_api_key = "test-api-key"

        class TestSchema(BaseModel):
            status: str

        # First response: 401 (triggers refresh)
        mock_response_401 = Mock()
        mock_response_401.status_code = 401
        mock_response_401.text = "Unauthorized"

        # Second response: 200 with valid data
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"status": "success"}

        with patch.object(client.session, "request", side_effect=[mock_response_401, mock_response_200]):
            with patch.object(client, "refresh_auth_token", return_value=True):
                result = client._request("GET", "test-endpoint", response_schema=TestSchema)

        assert result == {"status": "success"}

    def test_schema_validation_error_includes_response_body(self, client: APIClient) -> None:
        """Test that validation errors include the response body for debugging."""

        class TestSchema(BaseModel):
            required_field: str

        mock_response = Mock()
        mock_response.status_code = 200
        response_data = {"wrong_field": "value"}
        mock_response.json.return_value = response_data

        with patch.object(client.session, "request", return_value=mock_response):
            try:
                client._request("GET", "test-endpoint", response_schema=TestSchema)
                pytest.fail("Expected APIError to be raised")
            except APIError as e:
                assert e.status_code == 200
                assert "wrong_field" in e.response_body
                assert "validation failed" in str(e).lower()


class TestExceptionTypePreservation:
    """Test that original exception types are preserved in APIError conversion."""

    @pytest.fixture
    def client(self) -> APIClient:
        """Create a basic APIClient instance for testing."""
        return APIClient(
            base_url="https://test.example.com",
            auth_token="test-token",
        )

    def test_timeout_exception_preserves_type_in_message(self, client: APIClient) -> None:
        """Test that Timeout exceptions include the original exception type in the message."""
        import requests.exceptions

        mock_timeout = requests.exceptions.Timeout("Connection timed out")

        with patch.object(client.session, "request", side_effect=mock_timeout):
            with pytest.raises(APIError) as exc_info:
                client._request("GET", "test-endpoint")

            error = exc_info.value
            error_message = str(error)
            # Verify exception type is in the message
            assert "Timeout" in error_message
            # Verify timeout duration is in the message
            assert f"{client.timeout}s" in error_message
            # Verify original exception is chained
            assert error.__cause__ is mock_timeout

    def test_connection_error_preserves_type_in_message(self, client: APIClient) -> None:
        """Test that ConnectionError exceptions include the original exception type in the message."""
        import requests.exceptions

        mock_conn_error = requests.exceptions.ConnectionError("Failed to establish connection")

        with patch.object(client.session, "request", side_effect=mock_conn_error):
            with pytest.raises(APIError) as exc_info:
                client._request("GET", "test-endpoint")

            error = exc_info.value
            error_message = str(error)
            # Verify exception type is in the message
            assert "ConnectionError" in error_message
            # Verify error details are in the message
            assert "Failed to establish connection" in error_message
            # Verify original exception is chained
            assert error.__cause__ is mock_conn_error

    def test_generic_exception_preserves_type_in_message(self, client: APIClient) -> None:
        """Test that generic exceptions include the original exception type in the message."""
        mock_error = ValueError("Unexpected error")

        with patch.object(client.session, "request", side_effect=mock_error):
            with pytest.raises(APIError) as exc_info:
                client._request("GET", "test-endpoint")

            error = exc_info.value
            error_message = str(error)
            # Verify exception type is in the message
            assert "ValueError" in error_message
            # Verify error details are in the message
            assert "Unexpected error" in error_message
            # Verify original exception is chained
            assert error.__cause__ is mock_error

    def test_exception_chain_preserves_full_traceback(self, client: APIClient) -> None:
        """Test that exception chaining preserves full traceback for debugging."""
        import requests.exceptions

        original_exception = requests.exceptions.Timeout("Network timeout")

        with patch.object(client.session, "request", side_effect=original_exception):
            with pytest.raises(APIError) as exc_info:
                client._request("GET", "test-endpoint")

            error = exc_info.value
            # Verify the chain is preserved
            assert error.__cause__ is original_exception
            # Verify traceback can access original exception
            assert isinstance(error.__cause__, requests.exceptions.Timeout)
