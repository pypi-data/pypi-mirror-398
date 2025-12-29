"""Tests for the trend module."""

from datetime import datetime

from time_to_critical.timeseries import TimeSeries
from time_to_critical.trend import add_trend_back, detect_trend, detrend_timeseries


class TestDetectTrend:
    """Tests for trend detection."""

    def test_detect_positive_trend(self):
        """Test detecting a positive trend."""
        ts = TimeSeries("test")
        for i in range(10):
            ts.add_point(datetime(2024, 1, i + 1), float(i * 2 + 10))

        trend_info = detect_trend(ts)

        assert trend_info.has_positive_trend is True
        assert trend_info.slope > 0
        assert trend_info.r_squared > 0.9  # Strong linear trend

    def test_detect_no_trend(self):
        """Test detecting no trend (flat line)."""
        ts = TimeSeries("test")
        for i in range(10):
            ts.add_point(datetime(2024, 1, i + 1), 10.0)

        trend_info = detect_trend(ts)

        assert trend_info.has_positive_trend is False
        assert abs(trend_info.slope) < 0.01  # Near zero

    def test_detect_negative_trend(self):
        """Test detecting a negative trend."""
        ts = TimeSeries("test")
        for i in range(10):
            ts.add_point(datetime(2024, 1, i + 1), float(20 - i * 2))

        trend_info = detect_trend(ts)

        assert trend_info.has_positive_trend is False
        assert trend_info.slope < 0

    def test_detect_trend_short_series(self):
        """Test trend detection with short series."""
        ts = TimeSeries("test")
        ts.add_point(datetime(2024, 1, 1), 10.0)

        trend_info = detect_trend(ts)

        assert trend_info.has_positive_trend is False


class TestDetrendTimeseries:
    """Tests for detrending functionality."""

    def test_detrend_removes_trend(self):
        """Test that detrending removes the linear trend."""
        ts = TimeSeries("test")
        for i in range(10):
            ts.add_point(datetime(2024, 1, i + 1), float(i * 2 + 10))

        trend_info = detect_trend(ts)
        detrended = detrend_timeseries(ts, trend_info)

        # Detrended series should have near-zero mean and small variance
        values = detrended.get_values()
        mean = sum(values) / len(values)
        assert abs(mean) < 0.01  # Mean should be near zero


class TestAddTrendBack:
    """Tests for adding trend back to forecasted values."""

    def test_add_trend_back(self):
        """Test adding trend back to values."""
        ts = TimeSeries("test")
        for i in range(10):
            ts.add_point(datetime(2024, 1, i + 1), float(i * 2 + 10))

        trend_info = detect_trend(ts)
        forecasted_values = [0.0, 0.0, 0.0]  # Flat forecast
        start_index = len(ts)

        result = add_trend_back(forecasted_values, trend_info, start_index)

        # Result should reflect the continuing trend
        assert len(result) == 3
        assert all(isinstance(v, float) for v in result)
        # Values should be increasing due to positive trend
        assert result[1] > result[0]
        assert result[2] > result[1]
