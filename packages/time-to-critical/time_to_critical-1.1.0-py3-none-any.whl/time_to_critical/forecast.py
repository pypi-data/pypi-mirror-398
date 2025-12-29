"""FFT-based forecasting for time series data."""

from dataclasses import dataclass
from typing import List

import numpy as np

from time_to_critical.timeseries import TimeSeries
from time_to_critical.trend import TrendInfo, add_trend_back, detect_trend, detrend_timeseries


@dataclass
class FFTResult:
    """Contains the result of FFT forecasting."""

    forecasted_values: List[float]
    method: str
    trend_info: TrendInfo


def next_power_of_2(n: int) -> int:
    """Return the next power of 2 greater than or equal to n.

    Args:
        n: Input integer

    Returns:
        Next power of 2
    """
    if n <= 1:
        return 1

    power = 1
    while power < n:
        power <<= 1
    return power


def forecast_fft_without_trend(
    ts: TimeSeries, horizon_steps: int, trend_info: TrendInfo
) -> FFTResult:
    """Perform FFT forecasting for stationary time series.

    Args:
        ts: TimeSeries object
        horizon_steps: Number of steps to forecast
        trend_info: TrendInfo object for metadata

    Returns:
        FFTResult object with forecasted values
    """
    values = np.array(ts.get_values())
    n = len(values)

    # Use larger padding to avoid contamination from zeros
    min_size = n + horizon_steps
    padded_size = next_power_of_2(min_size * 2)
    padded_values = np.zeros(padded_size)
    padded_values[:n] = values

    # Use mean-padding to reduce artifacts
    mean = np.mean(values)
    padded_values[n:] = mean

    # Perform FFT
    fft = np.fft.fft(padded_values)

    # More conservative frequency filtering - keep 50% instead of 25%
    cutoff = padded_size // 2
    fft[cutoff : padded_size - cutoff] = 0

    # Perform inverse FFT
    ifft = np.fft.ifft(fft)

    # Extract forecasted values using periodicity
    forecasted = np.zeros(horizon_steps)
    for i in range(horizon_steps):
        idx = i % n
        forecasted[i] = np.real(ifft[idx])

    # Apply bounds checking to prevent unrealistic values
    min_val = np.min(values)
    max_val = np.max(values)

    # Add 10% margin
    margin = (max_val - min_val) * 0.1
    lower_bound = min_val - margin
    upper_bound = max_val + margin

    # Clamp forecast values to reasonable bounds
    forecasted = np.clip(forecasted, lower_bound, upper_bound)

    return FFTResult(
        forecasted_values=forecasted.tolist(),
        method="FFT without trend preservation",
        trend_info=trend_info,
    )


def forecast_fft_with_trend(ts: TimeSeries, horizon_steps: int, trend_info: TrendInfo) -> FFTResult:
    """Perform FFT forecasting while preserving trend.

    Args:
        ts: TimeSeries object
        horizon_steps: Number of steps to forecast
        trend_info: TrendInfo object with trend parameters

    Returns:
        FFTResult object with forecasted values
    """
    # First, detrend the time series
    detrended_ts = detrend_timeseries(ts, trend_info)

    # Perform FFT on detrended data
    result = forecast_fft_without_trend(detrended_ts, horizon_steps, trend_info)

    # Add trend back to forecasted values
    start_index = len(ts)
    forecasted_with_trend = add_trend_back(result.forecasted_values, trend_info, start_index)

    return FFTResult(
        forecasted_values=forecasted_with_trend,
        method="FFT with trend preservation",
        trend_info=trend_info,
    )


def forecast_fft(ts: TimeSeries, horizon_steps: int) -> FFTResult:
    """Perform FFT-based forecasting.

    If the time series has a positive trend, it preserves the trend.
    Otherwise, it uses FFT without trend preservation.

    Args:
        ts: TimeSeries object to forecast
        horizon_steps: Number of steps to forecast ahead

    Returns:
        FFTResult object with forecasted values and metadata
    """
    trend_info = detect_trend(ts)

    if trend_info.has_positive_trend:
        return forecast_fft_with_trend(ts, horizon_steps, trend_info)

    return forecast_fft_without_trend(ts, horizon_steps, trend_info)
