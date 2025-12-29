"""Integration tests for the entire forecasting pipeline."""

from datetime import datetime
from pathlib import Path

import pytest

from time_to_critical.forecast import forecast_fft
from time_to_critical.timeseries import TimeSeries, read_csv


class TestFullPipeline:
    """Integration tests for the complete forecasting workflow."""

    def test_forecast_with_trend(self):
        """Test full forecasting pipeline with trending data."""
        ts = TimeSeries("test")
        for i in range(20):
            ts.add_point(datetime(2024, 1, i + 1), float(i * 2 + 10 + (i % 3)))

        forecast = forecast_fft(ts, horizon_steps=5)

        assert forecast is not None
        assert len(forecast.forecasted_values) == 5
        assert forecast.trend_info is not None
        assert all(isinstance(v, float) for v in forecast.forecasted_values)

    def test_forecast_without_trend(self):
        """Test full forecasting pipeline with stationary data."""
        ts = TimeSeries("test")
        for i in range(20):
            ts.add_point(datetime(2024, 1, i + 1), 10.0 + (i % 3))

        forecast = forecast_fft(ts, horizon_steps=5)

        assert forecast is not None
        assert len(forecast.forecasted_values) == 5
        assert forecast.trend_info is not None

    @pytest.mark.skipif(
        not Path("sample-data/sample_data.csv").exists(),
        reason="Sample CSV file not found",
    )
    def test_forecast_from_sample_csv(self):
        """Test forecasting using sample CSV file."""
        ts = read_csv("sample-data/sample_data.csv")

        forecast = forecast_fft(ts, horizon_steps=10)

        assert len(forecast.forecasted_values) == 10
        assert all(isinstance(v, float) for v in forecast.forecasted_values)
        # Check that forecasted values are reasonable (not NaN or Inf)
        assert all(abs(v) < 1e6 for v in forecast.forecasted_values)

    def test_forecast_small_dataset(self):
        """Test forecasting with minimal data."""
        ts = TimeSeries("test")
        for i in range(5):
            ts.add_point(datetime(2024, 1, i + 1), float(10 + i))

        forecast = forecast_fft(ts, horizon_steps=3)

        assert len(forecast.forecasted_values) == 3
        assert all(isinstance(v, float) for v in forecast.forecasted_values)
