"""Time series forecasting tool using FFT with automatic trend detection."""

__version__ = "1.0.0"

from time_to_critical.forecast import FFTResult, forecast_fft
from time_to_critical.timeseries import TimeSeries
from time_to_critical.trend import TrendInfo, detect_trend

__all__ = [
    "TimeSeries",
    "TrendInfo",
    "FFTResult",
    "detect_trend",
    "forecast_fft",
]
