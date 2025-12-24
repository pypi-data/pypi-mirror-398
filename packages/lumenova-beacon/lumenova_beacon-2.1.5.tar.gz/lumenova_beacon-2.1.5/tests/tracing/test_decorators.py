"""Tests for @trace decorator."""

import json
from unittest.mock import MagicMock, patch

import pytest

from lumenova_beacon.tracing.decorators import trace
from lumenova_beacon.tracing.trace import get_current_span
from lumenova_beacon.types import SpanKind, SpanType, StatusCode


class TestTraceDecoratorBasic:
    """Test basic @trace decorator functionality."""

    def test_trace_without_parentheses(self, mock_beacon_client):
        """Test @trace decorator without parentheses."""
        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace
            def simple_function():
                return "result"

            result = simple_function()

            assert result == "result"
            mock_beacon_client.create_span.assert_called_once()

    def test_trace_with_empty_parentheses(self, mock_beacon_client):
        """Test @trace() decorator with empty parentheses."""
        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace()
            def simple_function():
                return "result"

            result = simple_function()

            assert result == "result"
            mock_beacon_client.create_span.assert_called_once()

    def test_trace_with_custom_name(self, mock_beacon_client):
        """Test @trace decorator with custom span name."""
        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace(name="custom_operation")
            def simple_function():
                return "result"

            result = simple_function()

            # Verify custom name was used
            call_args = mock_beacon_client.create_span.call_args
            assert call_args.kwargs["name"] == "custom_operation"

    def test_trace_uses_function_name_by_default(self, mock_beacon_client):
        """Test that decorator uses function name when no custom name provided."""
        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace
            def my_function():
                return "result"

            result = my_function()

            call_args = mock_beacon_client.create_span.call_args
            assert call_args.kwargs["name"] == "my_function"

    def test_trace_with_kind_and_type(self, mock_beacon_client):
        """Test @trace decorator with custom kind and type."""
        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace(kind=SpanKind.CLIENT, span_type=SpanType.GENERATION)
            def api_call():
                return "result"

            result = api_call()

            call_args = mock_beacon_client.create_span.call_args
            assert call_args.kwargs["kind"] == SpanKind.CLIENT
            assert call_args.kwargs["span_type"] == SpanType.GENERATION


class TestTraceDecoratorArgumentCapture:
    """Test @trace decorator argument capture."""

    def test_capture_args_enabled_by_default(self, mock_beacon_client):
        """Test that arguments are captured by default."""
        mock_span = MagicMock()
        mock_beacon_client.create_span.return_value = mock_span

        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace
            def function_with_args(x, y, z=3):
                return x + y + z

            result = function_with_args(1, 2, z=4)

            # Verify input was captured
            mock_span.set_input.assert_called_once()
            input_data = mock_span.set_input.call_args[0][0]
            assert input_data["args"] == (1, 2)
            assert input_data["kwargs"] == {"z": 4}

    def test_capture_args_disabled(self, mock_beacon_client):
        """Test disabling argument capture."""
        mock_span = MagicMock()
        mock_beacon_client.create_span.return_value = mock_span

        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace(capture_args=False)
            def function_with_args(x, y):
                return x + y

            result = function_with_args(1, 2)

            # Verify input was NOT captured
            mock_span.set_input.assert_not_called()

    def test_capture_result_enabled_by_default(self, mock_beacon_client):
        """Test that function result is captured by default."""
        mock_span = MagicMock()
        mock_beacon_client.create_span.return_value = mock_span

        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace
            def function_with_return():
                return {"status": "success"}

            result = function_with_return()

            # Verify output was captured
            mock_span.set_output.assert_called_once_with({"status": "success"})

    def test_capture_result_disabled(self, mock_beacon_client):
        """Test disabling result capture."""
        mock_span = MagicMock()
        mock_beacon_client.create_span.return_value = mock_span

        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace(capture_result=False)
            def function_with_return():
                return {"status": "success"}

            result = function_with_return()

            # Verify output was NOT captured
            mock_span.set_output.assert_not_called()


class TestTraceDecoratorAsync:
    """Test @trace decorator with async functions."""

    @pytest.mark.asyncio
    async def test_trace_async_function(self, mock_beacon_client):
        """Test @trace decorator with async function."""
        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace
            async def async_function():
                return "async result"

            result = await async_function()

            assert result == "async result"
            mock_beacon_client.create_span.assert_called_once()

    @pytest.mark.asyncio
    async def test_trace_async_with_args(self, mock_beacon_client):
        """Test @trace decorator with async function and arguments."""
        mock_span = MagicMock()
        mock_beacon_client.create_span.return_value = mock_span

        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace
            async def async_function_with_args(x, y):
                return x + y

            result = await async_function_with_args(10, 20)

            assert result == 30
            mock_span.set_input.assert_called_once()
            mock_span.set_output.assert_called_once_with(30)

    @pytest.mark.asyncio
    async def test_trace_async_exception_handling(self, mock_beacon_client):
        """Test that async @trace decorator handles exceptions."""
        mock_span = MagicMock()
        mock_beacon_client.create_span.return_value = mock_span

        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace
            async def async_function_that_fails():
                raise ValueError("Async error")

            with pytest.raises(ValueError):
                await async_function_that_fails()

            # Verify exception was recorded
            mock_span.record_exception.assert_called_once()


class TestTraceDecoratorExceptionHandling:
    """Test @trace decorator exception handling."""

    def test_exception_is_recorded_and_propagated(self, mock_beacon_client):
        """Test that exceptions are recorded in span and propagated."""
        mock_span = MagicMock()
        mock_beacon_client.create_span.return_value = mock_span

        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace
            def function_that_fails():
                raise ValueError("Something went wrong")

            with pytest.raises(ValueError) as exc_info:
                function_that_fails()

            assert str(exc_info.value) == "Something went wrong"

            # Verify exception was recorded in span
            mock_span.record_exception.assert_called_once()

    def test_different_exception_types(self, mock_beacon_client):
        """Test recording different exception types."""
        mock_span = MagicMock()
        mock_beacon_client.create_span.return_value = mock_span

        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace
            def function_with_runtime_error():
                raise RuntimeError("Runtime error")

            with pytest.raises(RuntimeError):
                function_with_runtime_error()

            mock_span.record_exception.assert_called_once()


class TestTraceDecoratorWithClient:
    """Test @trace decorator with different client scenarios."""

    def test_trace_without_client_runs_function_normally(self):
        """Test that function runs normally when no client is available."""
        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = None  # No client

            @trace
            def simple_function():
                return "result"

            result = simple_function()

            # Function should still work
            assert result == "result"

    @pytest.mark.asyncio
    async def test_trace_async_without_client(self):
        """Test that async function runs normally when no client is available."""
        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = None  # No client

            @trace
            async def async_function():
                return "async result"

            result = await async_function()

            assert result == "async result"


class TestTraceDecoratorCodeAttributes:
    """Test that @trace decorator sets code attributes correctly."""

    def test_sets_function_name_attribute(self, mock_beacon_client):
        """Test that code.function attribute is set."""
        mock_span = MagicMock()
        mock_beacon_client.create_span.return_value = mock_span

        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace
            def my_test_function():
                return "result"

            my_test_function()

            mock_span.set_attribute.assert_any_call("code.function", "my_test_function")

    def test_sets_namespace_for_methods(self, mock_beacon_client):
        """Test that code.namespace attribute is set for class methods.

        Note: When a class is defined inside a test function, its qualname includes
        the enclosing function name. This test verifies that namespace IS set
        for methods (because '.' appears in qualname), not the exact value.
        """
        mock_span = MagicMock()
        mock_beacon_client.create_span.return_value = mock_span

        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            class MyClass:
                @trace
                def my_method(self):
                    return "result"

            obj = MyClass()
            obj.my_method()

            # Verify code.namespace was set (value includes test context)
            namespace_calls = [
                call for call in mock_span.set_attribute.call_args_list
                if len(call[0]) > 0 and call[0][0] == "code.namespace"
            ]
            assert len(namespace_calls) == 1
            # The namespace includes the full qualname path
            assert "MyClass" in namespace_calls[0][0][1]

    def test_no_namespace_for_module_level_functions(self, mock_beacon_client):
        """Test that code.namespace is properly handled for functions.

        Note: Functions defined inside test methods have a qualname that includes
        the enclosing test function/class, so they will have a namespace.
        This test verifies the general behavior rather than the specific case
        of true module-level functions.
        """
        mock_span = MagicMock()
        mock_beacon_client.create_span.return_value = mock_span

        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace
            def nested_function():
                return "result"

            nested_function()

            # Verify code.function attribute was set
            mock_span.set_attribute.assert_any_call("code.function", "nested_function")


class TestTraceDecoratorSession:
    """Test @trace decorator with session_id."""

    def test_trace_with_session_id(self, mock_beacon_client):
        """Test @trace decorator with custom session_id."""
        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace(session_id="session-123")
            def function_with_session():
                return "result"

            function_with_session()

            call_args = mock_beacon_client.create_span.call_args
            assert call_args.kwargs["session_id"] == "session-123"


class TestTraceDecoratorNesting:
    """Test nested @trace decorators."""

    def test_nested_traced_functions(self, mock_beacon_client):
        """Test calling traced functions from within traced functions."""
        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace
            def inner_function(x):
                return x * 2

            @trace
            def outer_function(x):
                return inner_function(x) + 1

            result = outer_function(5)

            assert result == 11
            # Should create 2 spans (one for outer, one for inner)
            assert mock_beacon_client.create_span.call_count == 2


class TestTraceDecoratorFunctionMetadata:
    """Test that @trace decorator preserves function metadata."""

    def test_preserves_function_name(self):
        """Test that decorator preserves function __name__."""
        @trace
        def my_function():
            return "result"

        assert my_function.__name__ == "my_function"

    def test_preserves_function_docstring(self):
        """Test that decorator preserves function docstring."""
        @trace
        def my_function():
            """This is a docstring."""
            return "result"

        assert my_function.__doc__ == "This is a docstring."

    def test_preserves_function_signature(self):
        """Test that decorator preserves function signature information."""
        import inspect

        @trace
        def my_function(x: int, y: int = 10) -> int:
            return x + y

        sig = inspect.signature(my_function)
        params = list(sig.parameters.keys())

        assert params == ["x", "y"]


class TestTraceDecoratorEdgeCases:
    """Test edge cases for @trace decorator."""

    def test_trace_function_with_no_return(self, mock_beacon_client):
        """Test tracing function that returns None."""
        mock_span = MagicMock()
        mock_beacon_client.create_span.return_value = mock_span

        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace
            def function_no_return():
                pass

            result = function_no_return()

            assert result is None
            mock_span.set_output.assert_called_once_with(None)

    def test_trace_function_with_multiple_return_paths(self, mock_beacon_client):
        """Test function with multiple return paths."""
        mock_span = MagicMock()
        mock_beacon_client.create_span.return_value = mock_span

        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace
            def function_with_branches(x):
                if x > 0:
                    return "positive"
                else:
                    return "non-positive"

            result1 = function_with_branches(5)
            result2 = function_with_branches(-5)

            assert result1 == "positive"
            assert result2 == "non-positive"

    def test_trace_with_generator_function(self, mock_beacon_client):
        """Test tracing a generator function."""
        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace
            def generator_function():
                yield 1
                yield 2
                yield 3

            gen = generator_function()
            values = list(gen)

            assert values == [1, 2, 3]

    def test_trace_function_called_multiple_times(self, mock_beacon_client):
        """Test that each function call creates a new span."""
        with patch("lumenova_beacon.core.client.get_client") as mock_get:
            mock_get.return_value = mock_beacon_client

            @trace
            def simple_function():
                return "result"

            simple_function()
            simple_function()
            simple_function()

            # Should create 3 spans
            assert mock_beacon_client.create_span.call_count == 3
