"""Tests for BeaconConfig."""

import pytest

from lumenova_beacon.core.config import BeaconConfig
from lumenova_beacon.exceptions import ConfigurationError


class TestBeaconConfigInitialization:
    """Test BeaconConfig initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        config = BeaconConfig()

        assert config.endpoint == ""
        assert config.api_key is None
        assert config.timeout == 10.0
        assert config.verify is True
        assert config.enabled is True
        assert config.headers == {}
        assert config.debug is False
        assert config.session_id is None
        assert config.file_directory == ""
        assert config.file_filename_pattern == "{span_id}.json"
        assert config.file_pretty_print is True

    def test_init_with_http_config(self):
        """Test initialization with HTTP configuration."""
        config = BeaconConfig(
            endpoint="https://api.test.com",
            api_key="test-key",
            timeout=15.0,
            verify=False,
        )

        assert config.endpoint == "https://api.test.com"
        assert config.api_key == "test-key"
        assert config.timeout == 15.0
        assert config.verify is False

    def test_init_with_file_config(self):
        """Test initialization with file configuration."""
        config = BeaconConfig(
            file_directory="./test_spans",
            file_filename_pattern="{trace_id}_{span_id}.json",
            file_pretty_print=False,
        )

        assert config.file_directory == "./test_spans"
        assert config.file_filename_pattern == "{trace_id}_{span_id}.json"
        assert config.file_pretty_print is False

    def test_init_with_session(self):
        """Test initialization with session ID."""
        config = BeaconConfig(
            endpoint="https://api.test.com",
            session_id="test-session",
        )

        assert config.session_id == "test-session"

    def test_init_with_custom_headers(self):
        """Test initialization with custom headers."""
        headers = {"X-Custom-Header": "value", "X-Another": "value2"}
        config = BeaconConfig(
            endpoint="https://api.test.com",
            headers=headers,
        )

        assert config.headers == headers
        assert "X-Custom-Header" in config.headers

    def test_init_with_debug_enabled(self):
        """Test initialization with debug mode."""
        config = BeaconConfig(
            endpoint="https://api.test.com",
            debug=True,
        )

        assert config.debug is True

    def test_init_with_tracing_disabled(self):
        """Test initialization with tracing disabled."""
        config = BeaconConfig(
            endpoint="https://api.test.com",
            enabled=False,
        )

        assert config.enabled is False


class TestBeaconConfigValidation:
    """Test BeaconConfig validation."""

    def test_validate_http_config_success(self):
        """Test successful validation of HTTP config."""
        config = BeaconConfig(endpoint="https://api.test.com")

        # Should not raise
        config.validate()

    def test_validate_file_config_success(self):
        """Test successful validation of file config."""
        config = BeaconConfig(
            file_directory="./spans",
            file_filename_pattern="{span_id}.json",
        )

        # Should not raise
        config.validate()

    def test_validate_fails_without_endpoint_or_directory(self):
        """Test validation fails when neither endpoint nor file_directory provided."""
        config = BeaconConfig()

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "Either endpoint or file_directory must be provided" in str(
            exc_info.value
        )

    def test_validate_fails_with_negative_timeout(self):
        """Test validation fails with negative timeout."""
        config = BeaconConfig(
            endpoint="https://api.test.com",
            timeout=-1.0,
        )

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "timeout must be positive" in str(exc_info.value)

    def test_validate_fails_with_zero_timeout(self):
        """Test validation fails with zero timeout."""
        config = BeaconConfig(
            endpoint="https://api.test.com",
            timeout=0.0,
        )

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "timeout must be positive" in str(exc_info.value)

    def test_validate_fails_with_empty_filename_pattern(self):
        """Test validation fails with empty filename pattern for file mode."""
        config = BeaconConfig(
            file_directory="./spans",
            file_filename_pattern="",
        )

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "file_filename_pattern is required" in str(exc_info.value)

    def test_validate_accepts_both_endpoint_and_directory(self):
        """Test validation accepts both endpoint and directory (endpoint takes precedence)."""
        config = BeaconConfig(
            endpoint="https://api.test.com",
            file_directory="./spans",
        )

        # Should not raise - endpoint takes precedence
        config.validate()

    def test_validate_accepts_positive_timeout(self):
        """Test validation accepts positive timeout values."""
        config = BeaconConfig(
            endpoint="https://api.test.com",
            timeout=30.0,
        )

        # Should not raise
        config.validate()

    def test_validate_accepts_very_small_positive_timeout(self):
        """Test validation accepts very small positive timeout."""
        config = BeaconConfig(
            endpoint="https://api.test.com",
            timeout=0.001,
        )

        # Should not raise
        config.validate()


class TestBeaconConfigDataclass:
    """Test BeaconConfig dataclass features."""

    def test_config_is_dataclass(self):
        """Test that BeaconConfig is a dataclass."""
        from dataclasses import is_dataclass

        assert is_dataclass(BeaconConfig)

    def test_config_equality(self):
        """Test that two configs with same values are equal."""
        config1 = BeaconConfig(
            endpoint="https://api.test.com",
            api_key="test-key",
        )
        config2 = BeaconConfig(
            endpoint="https://api.test.com",
            api_key="test-key",
        )

        assert config1 == config2

    def test_config_inequality(self):
        """Test that two configs with different values are not equal."""
        config1 = BeaconConfig(endpoint="https://api.test.com")
        config2 = BeaconConfig(endpoint="https://other.test.com")

        assert config1 != config2

    def test_config_repr(self):
        """Test that config has useful repr."""
        config = BeaconConfig(
            endpoint="https://api.test.com",
            api_key="test-key",
        )

        repr_str = repr(config)
        assert "BeaconConfig" in repr_str
        assert "https://api.test.com" in repr_str


class TestBeaconConfigEdgeCases:
    """Test BeaconConfig edge cases."""

    def test_empty_endpoint_string(self):
        """Test with empty endpoint string."""
        config = BeaconConfig(endpoint="", file_directory="./spans")

        # Should pass validation with file_directory
        config.validate()

    def test_whitespace_endpoint(self):
        """Test with whitespace-only endpoint."""
        config = BeaconConfig(endpoint="   ", file_directory="./spans")

        # Should pass validation because file_directory is provided
        config.validate()

    def test_none_api_key(self):
        """Test that None api_key is acceptable."""
        config = BeaconConfig(endpoint="https://api.test.com", api_key=None)

        # Should not raise - api_key is optional
        config.validate()

    def test_large_timeout(self):
        """Test with very large timeout."""
        config = BeaconConfig(
            endpoint="https://api.test.com",
            timeout=3600.0,  # 1 hour
        )

        # Should not raise
        config.validate()

    def test_complex_filename_pattern(self):
        """Test with complex filename pattern."""
        config = BeaconConfig(
            file_directory="./spans",
            file_filename_pattern="trace_{trace_id}/span_{span_id}_{timestamp}.json",
        )

        # Should not raise
        config.validate()

    def test_empty_headers_dict(self):
        """Test with explicitly empty headers dict."""
        config = BeaconConfig(
            endpoint="https://api.test.com",
            headers={},
        )

        assert config.headers == {}
        config.validate()

    def test_multiple_custom_headers(self):
        """Test with multiple custom headers."""
        headers = {
            "X-Header-1": "value1",
            "X-Header-2": "value2",
            "X-Header-3": "value3",
        }
        config = BeaconConfig(
            endpoint="https://api.test.com",
            headers=headers,
        )

        assert len(config.headers) == 3
        config.validate()
