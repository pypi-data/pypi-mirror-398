"""Trend detection and manipulation for time series data."""

from dataclasses import dataclass
from typing import List

import numpy as np

from time_to_critical.timeseries import TimeSeries


@dataclass
class TrendInfo:
    """Contains information about the trend in a time series."""

    has_positive_trend: bool
    slope: float
    intercept: float
    r_squared: float


def detect_trend(ts: TimeSeries) -> TrendInfo:
    """Analyze the time series to detect if there's a positive trend.

    Uses linear regression to determine the slope of the trend line.

    Args:
        ts: TimeSeries object to analyze

    Returns:
        TrendInfo object with trend analysis results
    """
    if len(ts) < 2:
        return TrendInfo(has_positive_trend=False, slope=0.0, intercept=0.0, r_squared=0.0)

    values = np.array(ts.get_values())
    n = len(values)

    # Create x values (time indices)
    x = np.arange(n, dtype=float)

    # Calculate means
    mean_x = np.mean(x)
    mean_y = np.mean(values)

    # Calculate slope and intercept using least squares
    numerator = np.sum((x - mean_x) * (values - mean_y))
    denominator = np.sum((x - mean_x) ** 2)

    if denominator == 0:
        slope = 0.0
    else:
        slope = numerator / denominator

    intercept = mean_y - slope * mean_x

    # Calculate R-squared
    predicted = slope * x + intercept
    ss_res = np.sum((values - predicted) ** 2)  # Sum of squares of residuals
    ss_tot = np.sum((values - mean_y) ** 2)  # Total sum of squares

    if ss_tot == 0:
        r_squared = 0.0
    else:
        r_squared = 1.0 - (ss_res / ss_tot)

    # Consider trend positive if slope > 0 and R-squared > 0.1
    has_positive_trend = slope > 0 and r_squared > 0.1

    return TrendInfo(
        has_positive_trend=bool(has_positive_trend),
        slope=float(slope),
        intercept=float(intercept),
        r_squared=float(r_squared),
    )


def detrend_timeseries(ts: TimeSeries, trend_info: TrendInfo) -> TimeSeries:
    """Remove the trend from a time series.

    Args:
        ts: Original TimeSeries object
        trend_info: TrendInfo object containing trend parameters

    Returns:
        New TimeSeries object with trend removed
    """
    detrended = TimeSeries(ts.name + "_detrended")

    for i, point in enumerate(ts.data):
        # Calculate trend value at this point
        trend_value = trend_info.slope * i + trend_info.intercept

        # Subtract trend from actual value
        detrended_value = point.value - trend_value

        detrended.add_point(point.date, detrended_value)

    return detrended


def add_trend_back(
    forecasted_values: List[float], trend_info: TrendInfo, start_index: int
) -> List[float]:
    """Add the trend back to forecasted values.

    Args:
        forecasted_values: List of forecasted values without trend
        trend_info: TrendInfo object containing trend parameters
        start_index: Starting index for forecast (length of original series)

    Returns:
        List of forecasted values with trend added back
    """
    result = []

    for i, value in enumerate(forecasted_values):
        # Calculate trend value at this future point
        trend_value = trend_info.slope * (start_index + i) + trend_info.intercept

        # Add trend back to the forecasted value
        result.append(value + trend_value)

    return result
