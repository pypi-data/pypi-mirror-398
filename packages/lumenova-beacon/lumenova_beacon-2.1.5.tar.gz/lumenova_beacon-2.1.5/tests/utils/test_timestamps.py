"""Tests for timestamp utilities."""

import re
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from lumenova_beacon.utils.timestamps import get_current_timestamp


class TestGetCurrentTimestamp:
    """Test get_current_timestamp function."""

    def test_returns_string(self):
        """Test that function returns a string."""
        timestamp = get_current_timestamp()

        assert isinstance(timestamp, str)

    def test_matches_iso_format_with_z(self):
        """Test that timestamp matches ISO format with Z suffix."""
        timestamp = get_current_timestamp()

        # Should match pattern like: 2024-01-01T12:34:56.123456Z
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$"
        assert re.match(pattern, timestamp)

    def test_ends_with_z(self):
        """Test that timestamp ends with 'Z' suffix."""
        timestamp = get_current_timestamp()

        assert timestamp.endswith("Z")

    def test_does_not_contain_plus_zero(self):
        """Test that timestamp doesn't contain +00:00 timezone."""
        timestamp = get_current_timestamp()

        assert "+00:00" not in timestamp

    def test_contains_microseconds(self):
        """Test that timestamp includes microseconds."""
        timestamp = get_current_timestamp()

        # Should have a decimal point for microseconds
        assert "." in timestamp

    def test_can_parse_back_to_datetime(self):
        """Test that timestamp can be parsed back to datetime."""
        timestamp = get_current_timestamp()

        # Replace Z with +00:00 for parsing
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        assert isinstance(dt, datetime)
        assert dt.tzinfo is not None

    def test_is_utc_time(self):
        """Test that timestamp represents UTC time."""
        timestamp = get_current_timestamp()

        # Parse and verify timezone
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        assert dt.tzinfo == timezone.utc

    def test_successive_calls_increase(self):
        """Test that successive calls produce increasing timestamps."""
        timestamp1 = get_current_timestamp()
        timestamp2 = get_current_timestamp()

        # Second timestamp should be >= first
        # (might be equal if calls are very fast)
        assert timestamp2 >= timestamp1

    def test_format_consistency(self):
        """Test that format is consistent across multiple calls."""
        timestamps = [get_current_timestamp() for _ in range(10)]

        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$"
        for timestamp in timestamps:
            assert re.match(pattern, timestamp)

    def test_contains_current_date(self):
        """Test that timestamp contains current date."""
        timestamp = get_current_timestamp()
        now = datetime.now(timezone.utc)

        # Extract date part from timestamp
        date_part = timestamp.split("T")[0]
        current_date = now.strftime("%Y-%m-%d")

        assert date_part == current_date

    def test_approximate_current_time(self):
        """Test that timestamp is approximately current time."""
        before = datetime.now(timezone.utc)
        timestamp = get_current_timestamp()
        after = datetime.now(timezone.utc)

        # Parse timestamp
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        # Timestamp should be between before and after
        assert before <= dt <= after

    @patch("lumenova_beacon.utils.timestamps.datetime")
    def test_with_mocked_datetime(self, mock_datetime):
        """Test timestamp generation with mocked datetime."""
        # Create a specific datetime
        fixed_dt = datetime(2024, 1, 15, 12, 30, 45, 123456, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fixed_dt

        timestamp = get_current_timestamp()

        # Should match the mocked datetime
        assert timestamp.startswith("2024-01-15T12:30:45")
        assert timestamp.endswith("Z")


class TestTimestampFormat:
    """Test timestamp format details."""

    def test_year_is_four_digits(self):
        """Test that year is represented with 4 digits."""
        timestamp = get_current_timestamp()

        year = timestamp.split("-")[0]
        assert len(year) == 4
        assert year.isdigit()

    def test_month_is_two_digits(self):
        """Test that month is represented with 2 digits."""
        timestamp = get_current_timestamp()

        month = timestamp.split("-")[1]
        assert len(month) == 2
        assert month.isdigit()
        assert 1 <= int(month) <= 12

    def test_day_is_two_digits(self):
        """Test that day is represented with 2 digits."""
        timestamp = get_current_timestamp()

        day = timestamp.split("-")[2].split("T")[0]
        assert len(day) == 2
        assert day.isdigit()
        assert 1 <= int(day) <= 31

    def test_has_t_separator(self):
        """Test that date and time are separated by 'T'."""
        timestamp = get_current_timestamp()

        assert "T" in timestamp
        parts = timestamp.split("T")
        assert len(parts) == 2

    def test_time_components(self):
        """Test that time components are present and valid."""
        timestamp = get_current_timestamp()

        # Get time part (before the dot for microseconds)
        time_part = timestamp.split("T")[1].split(".")[0]
        hour, minute, second = time_part.split(":")

        assert len(hour) == 2
        assert 0 <= int(hour) <= 23

        assert len(minute) == 2
        assert 0 <= int(minute) <= 59

        assert len(second) == 2
        assert 0 <= int(second) <= 59


class TestTimestampUsability:
    """Test timestamp usability in various contexts."""

    def test_can_use_in_json(self):
        """Test that timestamp can be used in JSON."""
        import json

        timestamp = get_current_timestamp()
        data = {"timestamp": timestamp}

        # Should be JSON serializable
        json_str = json.dumps(data)
        assert timestamp in json_str

    def test_can_sort_chronologically(self):
        """Test that timestamps can be sorted chronologically."""
        import time

        timestamps = []
        for _ in range(5):
            timestamps.append(get_current_timestamp())
            time.sleep(0.001)  # Small delay

        # Timestamps should already be in order
        sorted_timestamps = sorted(timestamps)
        assert timestamps == sorted_timestamps

    def test_string_comparison_matches_time_order(self):
        """Test that string comparison gives correct time order."""
        import time

        timestamp1 = get_current_timestamp()
        time.sleep(0.01)  # Small delay
        timestamp2 = get_current_timestamp()

        # String comparison should match time order
        assert timestamp1 < timestamp2
