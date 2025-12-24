"""Tests for ID generation utilities."""

import re

import pytest

from lumenova_beacon.utils.ids import generate_span_id, generate_trace_id


class TestGenerateSpanId:
    """Test generate_span_id function."""

    def test_generates_16_char_hex_string(self):
        """Test that span ID is 16 characters."""
        span_id = generate_span_id()

        assert len(span_id) == 16

    def test_contains_only_hex_characters(self):
        """Test that span ID contains only hexadecimal characters."""
        span_id = generate_span_id()

        assert all(c in "0123456789abcdef" for c in span_id)

    def test_matches_hex_pattern(self):
        """Test that span ID matches hexadecimal pattern."""
        span_id = generate_span_id()

        assert re.match(r"^[0-9a-f]{16}$", span_id)

    def test_generates_unique_ids(self):
        """Test that successive calls generate different IDs."""
        id1 = generate_span_id()
        id2 = generate_span_id()
        id3 = generate_span_id()

        # All should be different
        assert id1 != id2
        assert id2 != id3
        assert id1 != id3

    def test_generates_many_unique_ids(self):
        """Test that generating many IDs produces unique values."""
        ids = [generate_span_id() for _ in range(1000)]

        # All should be unique
        assert len(ids) == len(set(ids))

    def test_no_uppercase_letters(self):
        """Test that span ID contains no uppercase letters."""
        span_id = generate_span_id()

        assert span_id == span_id.lower()


class TestGenerateTraceId:
    """Test generate_trace_id function."""

    def test_generates_32_char_hex_string(self):
        """Test that trace ID is 32 characters."""
        trace_id = generate_trace_id()

        assert len(trace_id) == 32

    def test_contains_only_hex_characters(self):
        """Test that trace ID contains only hexadecimal characters."""
        trace_id = generate_trace_id()

        assert all(c in "0123456789abcdef" for c in trace_id)

    def test_matches_hex_pattern(self):
        """Test that trace ID matches hexadecimal pattern."""
        trace_id = generate_trace_id()

        assert re.match(r"^[0-9a-f]{32}$", trace_id)

    def test_generates_unique_ids(self):
        """Test that successive calls generate different IDs."""
        id1 = generate_trace_id()
        id2 = generate_trace_id()
        id3 = generate_trace_id()

        # All should be different
        assert id1 != id2
        assert id2 != id3
        assert id1 != id3

    def test_generates_many_unique_ids(self):
        """Test that generating many IDs produces unique values."""
        ids = [generate_trace_id() for _ in range(1000)]

        # All should be unique
        assert len(ids) == len(set(ids))

    def test_no_uppercase_letters(self):
        """Test that trace ID contains no uppercase letters."""
        trace_id = generate_trace_id()

        assert trace_id == trace_id.lower()

    def test_different_from_span_id(self):
        """Test that trace ID is different length from span ID."""
        trace_id = generate_trace_id()
        span_id = generate_span_id()

        assert len(trace_id) != len(span_id)
        assert len(trace_id) == 32
        assert len(span_id) == 16


class TestIdCollisions:
    """Test for ID collision probability."""

    def test_span_ids_extremely_unlikely_to_collide(self):
        """Test that span IDs are extremely unlikely to collide."""
        # Generate a large batch of IDs
        num_ids = 10000
        ids = [generate_span_id() for _ in range(num_ids)]

        # Verify all are unique
        assert len(ids) == len(set(ids))

    def test_trace_ids_extremely_unlikely_to_collide(self):
        """Test that trace IDs are extremely unlikely to collide."""
        # Generate a large batch of IDs
        num_ids = 10000
        ids = [generate_trace_id() for _ in range(num_ids)]

        # Verify all are unique
        assert len(ids) == len(set(ids))


class TestIdFormat:
    """Test ID format compatibility."""

    def test_span_id_format_consistent(self):
        """Test that span ID format is consistent across multiple generations."""
        ids = [generate_span_id() for _ in range(100)]

        for span_id in ids:
            assert isinstance(span_id, str)
            assert len(span_id) == 16
            assert re.match(r"^[0-9a-f]{16}$", span_id)

    def test_trace_id_format_consistent(self):
        """Test that trace ID format is consistent across multiple generations."""
        ids = [generate_trace_id() for _ in range(100)]

        for trace_id in ids:
            assert isinstance(trace_id, str)
            assert len(trace_id) == 32
            assert re.match(r"^[0-9a-f]{32}$", trace_id)
