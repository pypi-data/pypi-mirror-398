"""Tests for the HUD module."""

import re

from flightline.hud import (
    hud_line,
    mil_time,
    status_indicator,
    waypoint,
)


class TestMilTime:
    """Tests for mil_time function."""

    def test_returns_zulu_format(self):
        """Should return time in HHMMZ format."""
        result = mil_time()
        # Should match pattern like "1435Z"
        assert re.match(r"^\d{4}Z$", result), f"Expected HHMMZ format, got {result}"

    def test_hours_in_valid_range(self):
        """Hours should be 00-23."""
        result = mil_time()
        hours = int(result[:2])
        assert 0 <= hours <= 23

    def test_minutes_in_valid_range(self):
        """Minutes should be 00-59."""
        result = mil_time()
        minutes = int(result[2:4])
        assert 0 <= minutes <= 59


class TestWaypoint:
    """Tests for waypoint function."""

    def test_single_digit(self):
        """Single digit should be zero-padded."""
        assert waypoint(1) == "WP01"
        assert waypoint(9) == "WP09"

    def test_double_digit(self):
        """Double digits should work normally."""
        assert waypoint(10) == "WP10"
        assert waypoint(99) == "WP99"

    def test_zero(self):
        """Zero should be WP00."""
        assert waypoint(0) == "WP00"


class TestStatusIndicator:
    """Tests for status_indicator function."""

    def test_rdy_status(self):
        """RDY status should be styled correctly."""
        result = status_indicator("RDY")
        assert "[RDY]" in result.plain

    def test_err_status(self):
        """ERR status should be styled correctly."""
        result = status_indicator("ERR")
        assert "[ERR]" in result.plain

    def test_case_insensitive(self):
        """Status should be case-insensitive."""
        result_lower = status_indicator("rdy")
        result_upper = status_indicator("RDY")
        assert result_lower.plain == result_upper.plain

    def test_unknown_status(self):
        """Unknown status should still work."""
        result = status_indicator("CUSTOM")
        assert "[CUSTOM]" in result.plain


class TestHudLine:
    """Tests for hud_line function."""

    def test_default_width(self):
        """Default width should be 60."""
        result = hud_line()
        assert len(result) == 60

    def test_custom_width(self):
        """Custom width should be respected."""
        result = hud_line(width=40)
        assert len(result) == 40

    def test_custom_char(self):
        """Custom character should be used."""
        result = hud_line(char="=", width=10)
        assert result == "=" * 10
