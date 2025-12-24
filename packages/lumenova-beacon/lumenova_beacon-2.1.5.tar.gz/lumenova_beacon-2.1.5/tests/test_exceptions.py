"""Tests for custom exceptions."""

import pytest

from lumenova_beacon.exceptions import (
    BeaconError,
    ConfigurationError,
    TransportError,
    HTTPTransportError,
    FileTransportError,
    SpanError,
    DatasetError,
    DatasetNotFoundError,
    DatasetValidationError,
    PromptError,
    PromptNotFoundError,
    PromptValidationError,
    PromptCompilationError,
    PromptNetworkError,
)


class TestBeaconError:
    """Test base BeaconError exception."""

    def test_is_exception(self):
        """Test that BeaconError is an Exception."""
        assert issubclass(BeaconError, Exception)

    def test_can_raise_and_catch(self):
        """Test that BeaconError can be raised and caught."""
        with pytest.raises(BeaconError):
            raise BeaconError("Test error")

    def test_error_message(self):
        """Test that error message is preserved."""
        with pytest.raises(BeaconError) as exc_info:
            raise BeaconError("Test error message")

        assert str(exc_info.value) == "Test error message"

    def test_can_catch_as_base_exception(self):
        """Test that BeaconError can be caught as Exception."""
        with pytest.raises(Exception):
            raise BeaconError("Test error")


class TestConfigurationError:
    """Test ConfigurationError exception."""

    def test_inherits_from_beacon_error(self):
        """Test that ConfigurationError inherits from BeaconError."""
        assert issubclass(ConfigurationError, BeaconError)

    def test_can_raise_and_catch(self):
        """Test that ConfigurationError can be raised and caught."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Invalid configuration")

    def test_can_catch_as_beacon_error(self):
        """Test that ConfigurationError can be caught as BeaconError."""
        with pytest.raises(BeaconError):
            raise ConfigurationError("Invalid configuration")

    def test_error_message(self):
        """Test that error message is preserved."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Missing endpoint")

        assert str(exc_info.value) == "Missing endpoint"


class TestTransportError:
    """Test TransportError exception."""

    def test_inherits_from_beacon_error(self):
        """Test that TransportError inherits from BeaconError."""
        assert issubclass(TransportError, BeaconError)

    def test_can_raise_and_catch(self):
        """Test that TransportError can be raised and caught."""
        with pytest.raises(TransportError):
            raise TransportError("Transport failed")

    def test_can_catch_as_beacon_error(self):
        """Test that TransportError can be caught as BeaconError."""
        with pytest.raises(BeaconError):
            raise TransportError("Transport failed")


class TestHTTPTransportError:
    """Test HTTPTransportError exception."""

    def test_inherits_from_transport_error(self):
        """Test that HTTPTransportError inherits from TransportError."""
        assert issubclass(HTTPTransportError, TransportError)

    def test_inherits_from_beacon_error(self):
        """Test that HTTPTransportError inherits from BeaconError."""
        assert issubclass(HTTPTransportError, BeaconError)

    def test_can_raise_with_message_only(self):
        """Test raising HTTPTransportError with message only."""
        with pytest.raises(HTTPTransportError) as exc_info:
            raise HTTPTransportError("HTTP request failed")

        assert str(exc_info.value) == "HTTP request failed"
        assert exc_info.value.status_code is None

    def test_can_raise_with_status_code(self):
        """Test raising HTTPTransportError with status code."""
        with pytest.raises(HTTPTransportError) as exc_info:
            raise HTTPTransportError("Not found", status_code=404)

        assert str(exc_info.value) == "Not found"
        assert exc_info.value.status_code == 404

    def test_different_status_codes(self):
        """Test HTTPTransportError with different status codes."""
        test_cases = [
            (400, "Bad Request"),
            (404, "Not Found"),
            (500, "Internal Server Error"),
            (503, "Service Unavailable"),
        ]

        for status_code, message in test_cases:
            with pytest.raises(HTTPTransportError) as exc_info:
                raise HTTPTransportError(message, status_code=status_code)

            assert exc_info.value.status_code == status_code

    def test_can_catch_as_transport_error(self):
        """Test that HTTPTransportError can be caught as TransportError."""
        with pytest.raises(TransportError):
            raise HTTPTransportError("HTTP error", status_code=500)

    def test_can_catch_as_beacon_error(self):
        """Test that HTTPTransportError can be caught as BeaconError."""
        with pytest.raises(BeaconError):
            raise HTTPTransportError("HTTP error", status_code=500)


class TestFileTransportError:
    """Test FileTransportError exception."""

    def test_inherits_from_transport_error(self):
        """Test that FileTransportError inherits from TransportError."""
        assert issubclass(FileTransportError, TransportError)

    def test_inherits_from_beacon_error(self):
        """Test that FileTransportError inherits from BeaconError."""
        assert issubclass(FileTransportError, BeaconError)

    def test_can_raise_and_catch(self):
        """Test that FileTransportError can be raised and caught."""
        with pytest.raises(FileTransportError):
            raise FileTransportError("File write failed")

    def test_can_catch_as_transport_error(self):
        """Test that FileTransportError can be caught as TransportError."""
        with pytest.raises(TransportError):
            raise FileTransportError("File error")


class TestSpanError:
    """Test SpanError exception."""

    def test_inherits_from_beacon_error(self):
        """Test that SpanError inherits from BeaconError."""
        assert issubclass(SpanError, BeaconError)

    def test_can_raise_and_catch(self):
        """Test that SpanError can be raised and caught."""
        with pytest.raises(SpanError):
            raise SpanError("Span operation failed")

    def test_can_catch_as_beacon_error(self):
        """Test that SpanError can be caught as BeaconError."""
        with pytest.raises(BeaconError):
            raise SpanError("Span error")


class TestDatasetErrors:
    """Test Dataset-related exceptions."""

    def test_dataset_error_inherits_from_beacon_error(self):
        """Test that DatasetError inherits from BeaconError."""
        assert issubclass(DatasetError, BeaconError)

    def test_dataset_not_found_error_inherits(self):
        """Test that DatasetNotFoundError inherits from DatasetError."""
        assert issubclass(DatasetNotFoundError, DatasetError)
        assert issubclass(DatasetNotFoundError, BeaconError)

    def test_dataset_validation_error_inherits(self):
        """Test that DatasetValidationError inherits from DatasetError."""
        assert issubclass(DatasetValidationError, DatasetError)
        assert issubclass(DatasetValidationError, BeaconError)

    def test_raise_dataset_not_found(self):
        """Test raising DatasetNotFoundError."""
        with pytest.raises(DatasetNotFoundError) as exc_info:
            raise DatasetNotFoundError("Dataset 'test' not found")

        assert "Dataset 'test' not found" in str(exc_info.value)

    def test_raise_dataset_validation_error(self):
        """Test raising DatasetValidationError."""
        with pytest.raises(DatasetValidationError) as exc_info:
            raise DatasetValidationError("Invalid dataset data")

        assert "Invalid dataset data" in str(exc_info.value)

    def test_catch_dataset_errors_as_base(self):
        """Test catching specific dataset errors as DatasetError."""
        # DatasetNotFoundError
        with pytest.raises(DatasetError):
            raise DatasetNotFoundError("Not found")

        # DatasetValidationError
        with pytest.raises(DatasetError):
            raise DatasetValidationError("Invalid")


class TestPromptErrors:
    """Test Prompt-related exceptions."""

    def test_prompt_error_inherits_from_beacon_error(self):
        """Test that PromptError inherits from BeaconError."""
        assert issubclass(PromptError, BeaconError)

    def test_prompt_not_found_error_inherits(self):
        """Test that PromptNotFoundError inherits from PromptError."""
        assert issubclass(PromptNotFoundError, PromptError)
        assert issubclass(PromptNotFoundError, BeaconError)

    def test_prompt_validation_error_inherits(self):
        """Test that PromptValidationError inherits from PromptError."""
        assert issubclass(PromptValidationError, PromptError)
        assert issubclass(PromptValidationError, BeaconError)

    def test_prompt_compilation_error_inherits(self):
        """Test that PromptCompilationError inherits from PromptError."""
        assert issubclass(PromptCompilationError, PromptError)
        assert issubclass(PromptCompilationError, BeaconError)

    def test_prompt_network_error_inherits(self):
        """Test that PromptNetworkError inherits from PromptError."""
        assert issubclass(PromptNetworkError, PromptError)
        assert issubclass(PromptNetworkError, BeaconError)

    def test_raise_prompt_not_found(self):
        """Test raising PromptNotFoundError."""
        with pytest.raises(PromptNotFoundError) as exc_info:
            raise PromptNotFoundError("Prompt 'test' not found")

        assert "Prompt 'test' not found" in str(exc_info.value)

    def test_raise_prompt_validation_error(self):
        """Test raising PromptValidationError."""
        with pytest.raises(PromptValidationError) as exc_info:
            raise PromptValidationError("Invalid prompt data")

        assert "Invalid prompt data" in str(exc_info.value)

    def test_raise_prompt_compilation_error(self):
        """Test raising PromptCompilationError."""
        with pytest.raises(PromptCompilationError) as exc_info:
            raise PromptCompilationError("Template compilation failed")

        assert "Template compilation failed" in str(exc_info.value)

    def test_raise_prompt_network_error(self):
        """Test raising PromptNetworkError."""
        with pytest.raises(PromptNetworkError) as exc_info:
            raise PromptNetworkError("Network request failed after retries")

        assert "Network request failed after retries" in str(exc_info.value)

    def test_catch_prompt_errors_as_base(self):
        """Test catching specific prompt errors as PromptError."""
        # PromptNotFoundError
        with pytest.raises(PromptError):
            raise PromptNotFoundError("Not found")

        # PromptValidationError
        with pytest.raises(PromptError):
            raise PromptValidationError("Invalid")

        # PromptCompilationError
        with pytest.raises(PromptError):
            raise PromptCompilationError("Compilation failed")

        # PromptNetworkError
        with pytest.raises(PromptError):
            raise PromptNetworkError("Network failed")


class TestExceptionHierarchy:
    """Test exception hierarchy and inheritance."""

    def test_all_exceptions_inherit_from_beacon_error(self):
        """Test that all custom exceptions inherit from BeaconError."""
        exceptions = [
            ConfigurationError,
            TransportError,
            HTTPTransportError,
            FileTransportError,
            SpanError,
            DatasetError,
            DatasetNotFoundError,
            DatasetValidationError,
            PromptError,
            PromptNotFoundError,
            PromptValidationError,
            PromptCompilationError,
            PromptNetworkError,
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, BeaconError)

    def test_transport_error_hierarchy(self):
        """Test transport error hierarchy."""
        assert issubclass(HTTPTransportError, TransportError)
        assert issubclass(FileTransportError, TransportError)
        assert issubclass(TransportError, BeaconError)

    def test_dataset_error_hierarchy(self):
        """Test dataset error hierarchy."""
        assert issubclass(DatasetNotFoundError, DatasetError)
        assert issubclass(DatasetValidationError, DatasetError)
        assert issubclass(DatasetError, BeaconError)

    def test_prompt_error_hierarchy(self):
        """Test prompt error hierarchy."""
        assert issubclass(PromptNotFoundError, PromptError)
        assert issubclass(PromptValidationError, PromptError)
        assert issubclass(PromptCompilationError, PromptError)
        assert issubclass(PromptNetworkError, PromptError)
        assert issubclass(PromptError, BeaconError)

    def test_catch_all_with_beacon_error(self):
        """Test that BeaconError catches all custom exceptions."""
        exceptions_to_test = [
            ConfigurationError("config"),
            HTTPTransportError("http", 500),
            FileTransportError("file"),
            SpanError("span"),
            DatasetNotFoundError("dataset"),
            PromptCompilationError("prompt"),
        ]

        for exc in exceptions_to_test:
            with pytest.raises(BeaconError):
                raise exc


class TestExceptionUsability:
    """Test exception usability in practice."""

    def test_can_distinguish_http_errors_by_status_code(self):
        """Test that HTTP errors can be distinguished by status code."""
        try:
            raise HTTPTransportError("Not found", status_code=404)
        except HTTPTransportError as e:
            assert e.status_code == 404
            if e.status_code == 404:
                # Can handle 404 specifically
                pass

    def test_can_catch_specific_error_types(self):
        """Test that specific error types can be caught."""
        # Can catch ConfigurationError specifically
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Invalid config")

        # Can catch DatasetNotFoundError specifically
        with pytest.raises(DatasetNotFoundError):
            raise DatasetNotFoundError("Dataset not found")

    def test_can_catch_error_categories(self):
        """Test that error categories can be caught."""
        # Can catch all transport errors
        with pytest.raises(TransportError):
            raise HTTPTransportError("HTTP error", 500)

        # Can catch all dataset errors
        with pytest.raises(DatasetError):
            raise DatasetNotFoundError("Not found")

        # Can catch all prompt errors
        with pytest.raises(PromptError):
            raise PromptValidationError("Invalid")
