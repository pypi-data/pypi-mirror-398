"""Tests for trace context management."""

from unittest.mock import MagicMock

import pytest

from lumenova_beacon.tracing.span import Span
from lumenova_beacon.tracing.trace import (
    TraceContext,
    get_current_trace_id,
    get_current_span,
    set_current_trace_id,
    set_current_span,
    clear_context,
)
from lumenova_beacon.types import StatusCode


class TestContextFunctions:
    """Test context variable functions."""

    def test_get_current_trace_id_when_none(self):
        """Test getting trace ID when none is set."""
        clear_context()

        trace_id = get_current_trace_id()

        assert trace_id is None

    def test_set_and_get_current_trace_id(self):
        """Test setting and getting trace ID."""
        set_current_trace_id("trace-123")

        trace_id = get_current_trace_id()

        assert trace_id == "trace-123"

    def test_get_current_span_when_none(self):
        """Test getting span when none is set."""
        clear_context()

        span = get_current_span()

        assert span is None

    def test_set_and_get_current_span(self):
        """Test setting and getting current span."""
        test_span = Span(name="test", trace_id="trace-123")

        set_current_span(test_span)

        span = get_current_span()

        assert span is test_span

    def test_set_current_span_also_sets_trace_id(self):
        """Test that setting span also sets trace ID."""
        test_span = Span(name="test", trace_id="trace-123")

        set_current_span(test_span)

        trace_id = get_current_trace_id()

        assert trace_id == "trace-123"

    def test_clear_context(self):
        """Test clearing the context."""
        test_span = Span(name="test", trace_id="trace-123")
        set_current_span(test_span)

        clear_context()

        assert get_current_span() is None
        assert get_current_trace_id() is None


class TestTraceContextInitialization:
    """Test TraceContext initialization."""

    def test_init_with_span_only(self):
        """Test initialization with span only."""
        span = Span(name="test")
        ctx = TraceContext(span)

        assert ctx.span is span
        assert ctx.client is None
        assert ctx.previous_span is None
        assert ctx.previous_trace_id is None

    def test_init_with_span_and_client(self):
        """Test initialization with span and client."""
        span = Span(name="test")
        mock_client = MagicMock()
        ctx = TraceContext(span, client=mock_client)

        assert ctx.span is span
        assert ctx.client is mock_client


class TestTraceContextSyncContextManager:
    """Test TraceContext as synchronous context manager."""

    def test_enter_sets_current_span(self):
        """Test that entering context sets the current span."""
        span = Span(name="test")
        ctx = TraceContext(span)

        with ctx:
            current = get_current_span()
            assert current is span

    def test_enter_starts_span(self):
        """Test that entering context starts the span."""
        span = Span(name="test")
        ctx = TraceContext(span)

        with ctx:
            assert span.start_time is not None

    def test_enter_doesnt_restart_started_span(self):
        """Test that already-started span is not restarted."""
        span = Span(name="test")
        span.start()
        first_start_time = span.start_time

        ctx = TraceContext(span)

        with ctx:
            # Start time should remain the same
            assert span.start_time == first_start_time

    def test_enter_returns_span(self):
        """Test that entering context returns the span."""
        span = Span(name="test")
        ctx = TraceContext(span)

        with ctx as s:
            assert s is span

    def test_exit_ends_span(self):
        """Test that exiting context ends the span."""
        span = Span(name="test")
        ctx = TraceContext(span)

        with ctx:
            pass

        assert span.end_time is not None

    def test_exit_sets_ok_status_on_success(self):
        """Test that successful exit sets OK status."""
        span = Span(name="test")
        ctx = TraceContext(span)

        with ctx:
            pass

        assert span.status_code == StatusCode.OK

    def test_exit_doesnt_override_existing_status(self):
        """Test that exit doesn't override already-set status."""
        span = Span(name="test")
        span.set_status(StatusCode.ERROR)
        ctx = TraceContext(span)

        with ctx:
            pass

        # Should keep ERROR status
        assert span.status_code == StatusCode.ERROR

    def test_exit_records_exception(self):
        """Test that exit records exceptions."""
        span = Span(name="test")
        ctx = TraceContext(span)

        try:
            with ctx:
                raise ValueError("Test error")
        except ValueError:
            pass

        assert span.status_code == StatusCode.ERROR
        assert span.status_description == "Test error"
        assert span.attributes["exception.type"] == "ValueError"

    def test_exit_propagates_exception(self):
        """Test that exceptions are propagated."""
        span = Span(name="test")
        ctx = TraceContext(span)

        with pytest.raises(ValueError):
            with ctx:
                raise ValueError("Test error")

    def test_exit_restores_previous_context(self):
        """Test that exit restores previous context."""
        parent_span = Span(name="parent", trace_id="trace-parent")
        set_current_span(parent_span)

        child_span = Span(name="child", trace_id="trace-child")
        ctx = TraceContext(child_span)

        with ctx:
            # Inside context, should have child span
            assert get_current_span() is child_span

        # After context, should restore parent span
        assert get_current_span() is parent_span

    def test_exit_with_client(self):
        """Test that exit works when client is provided."""
        span = Span(name="test")
        mock_client = MagicMock()
        ctx = TraceContext(span, client=mock_client)

        with ctx:
            pass

        # Span should be ended
        assert span.end_time is not None

    def test_exit_without_client(self):
        """Test that exit works without client."""
        span = Span(name="test")
        ctx = TraceContext(span)

        # Should not raise
        with ctx:
            pass

        # Span should be ended
        assert span.end_time is not None


class TestTraceContextAsyncContextManager:
    """Test TraceContext as asynchronous context manager."""

    @pytest.mark.asyncio
    async def test_aenter_sets_current_span(self):
        """Test that entering async context sets the current span."""
        span = Span(name="test")
        ctx = TraceContext(span)

        async with ctx:
            current = get_current_span()
            assert current is span

    @pytest.mark.asyncio
    async def test_aenter_starts_span(self):
        """Test that entering async context starts the span."""
        span = Span(name="test")
        ctx = TraceContext(span)

        async with ctx:
            assert span.start_time is not None

    @pytest.mark.asyncio
    async def test_aenter_returns_span(self):
        """Test that entering async context returns the span."""
        span = Span(name="test")
        ctx = TraceContext(span)

        async with ctx as s:
            assert s is span

    @pytest.mark.asyncio
    async def test_aexit_ends_span(self):
        """Test that exiting async context ends the span."""
        span = Span(name="test")
        ctx = TraceContext(span)

        async with ctx:
            pass

        assert span.end_time is not None

    @pytest.mark.asyncio
    async def test_aexit_sets_ok_status_on_success(self):
        """Test that successful async exit sets OK status."""
        span = Span(name="test")
        ctx = TraceContext(span)

        async with ctx:
            pass

        assert span.status_code == StatusCode.OK

    @pytest.mark.asyncio
    async def test_aexit_records_exception(self):
        """Test that async exit records exceptions."""
        span = Span(name="test")
        ctx = TraceContext(span)

        try:
            async with ctx:
                raise ValueError("Test error")
        except ValueError:
            pass

        assert span.status_code == StatusCode.ERROR
        assert span.status_description == "Test error"

    @pytest.mark.asyncio
    async def test_aexit_propagates_exception(self):
        """Test that exceptions are propagated in async context."""
        span = Span(name="test")
        ctx = TraceContext(span)

        with pytest.raises(ValueError):
            async with ctx:
                raise ValueError("Test error")

    @pytest.mark.asyncio
    async def test_aexit_restores_previous_context(self):
        """Test that async exit restores previous context."""
        parent_span = Span(name="parent", trace_id="trace-parent")
        set_current_span(parent_span)

        child_span = Span(name="child", trace_id="trace-child")
        ctx = TraceContext(child_span)

        async with ctx:
            # Inside context, should have child span
            assert get_current_span() is child_span

        # After context, should restore parent span
        assert get_current_span() is parent_span

    @pytest.mark.asyncio
    async def test_aexit_with_client(self):
        """Test that async exit works when client is provided."""
        span = Span(name="test")
        mock_client = MagicMock()
        ctx = TraceContext(span, client=mock_client)

        async with ctx:
            pass

        # Span should be ended
        assert span.end_time is not None


class TestTraceContextNesting:
    """Test nested TraceContext scenarios."""

    def test_nested_contexts(self):
        """Test nested trace contexts."""
        parent_span = Span(name="parent")
        child_span = Span(name="child")

        parent_ctx = TraceContext(parent_span)
        child_ctx = TraceContext(child_span)

        with parent_ctx:
            assert get_current_span() is parent_span

            with child_ctx:
                assert get_current_span() is child_span

            # Back to parent
            assert get_current_span() is parent_span

        # Context cleared
        assert get_current_span() is None

    def test_nested_contexts_with_trace_id_only(self):
        """Test nested contexts with trace ID but no parent span."""
        set_current_trace_id("trace-123")

        child_span = Span(name="child")
        ctx = TraceContext(child_span)

        with ctx:
            assert get_current_span() is child_span

        # Should restore trace ID only
        assert get_current_trace_id() == "trace-123"
        assert get_current_span() is None

    def test_deeply_nested_contexts(self):
        """Test deeply nested trace contexts."""
        span1 = Span(name="level1")
        span2 = Span(name="level2")
        span3 = Span(name="level3")

        with TraceContext(span1):
            assert get_current_span() is span1

            with TraceContext(span2):
                assert get_current_span() is span2

                with TraceContext(span3):
                    assert get_current_span() is span3

                assert get_current_span() is span2

            assert get_current_span() is span1


class TestTraceContextEdgeCases:
    """Test TraceContext edge cases."""

    def test_exit_doesnt_end_already_ended_span(self):
        """Test that exit doesn't re-end an already-ended span."""
        span = Span(name="test")
        span.start()
        span.end()
        first_end_time = span.end_time

        ctx = TraceContext(span)

        with ctx:
            pass

        # End time should remain the same
        assert span.end_time == first_end_time

    def test_context_with_exception_still_restores(self):
        """Test that context is restored even when exception occurs."""
        parent_span = Span(name="parent")
        set_current_span(parent_span)

        child_span = Span(name="child")
        ctx = TraceContext(child_span)

        try:
            with ctx:
                raise ValueError("Test")
        except ValueError:
            pass

        # Should still restore parent context
        assert get_current_span() is parent_span

    def test_restore_context_with_no_previous_context(self):
        """Test restoring context when there was no previous context."""
        clear_context()

        span = Span(name="test")
        ctx = TraceContext(span)

        with ctx:
            assert get_current_span() is span

        # Should clear context
        assert get_current_span() is None
        assert get_current_trace_id() is None

    @pytest.mark.asyncio
    async def test_async_context_with_no_previous_context(self):
        """Test async context when there was no previous context."""
        clear_context()

        span = Span(name="test")
        ctx = TraceContext(span)

        async with ctx:
            assert get_current_span() is span

        # Should clear context
        assert get_current_span() is None
        assert get_current_trace_id() is None

    def test_multiple_sequential_contexts(self):
        """Test multiple sequential (non-nested) contexts."""
        span1 = Span(name="test1")
        span2 = Span(name="test2")
        span3 = Span(name="test3")

        with TraceContext(span1):
            assert get_current_span() is span1

        assert get_current_span() is None

        with TraceContext(span2):
            assert get_current_span() is span2

        assert get_current_span() is None

        with TraceContext(span3):
            assert get_current_span() is span3

        assert get_current_span() is None
