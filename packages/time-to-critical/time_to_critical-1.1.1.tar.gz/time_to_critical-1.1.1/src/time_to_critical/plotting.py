"""Plotting and reporting functionality using matplotlib."""

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import DateFormatter

from time_to_critical.forecast import FFTResult
from time_to_critical.timeseries import TimeSeries


@dataclass
class PlotConfig:
    """Configuration for plotting."""

    title: str = "Time Series"
    width: float = 10.0  # inches
    height: float = 6.0  # inches
    show_forecast: bool = True
    output_file: str = ""
    show_plot: bool = False
    dpi: int = 150


def default_plot_config() -> PlotConfig:
    """Return a default plotting configuration.

    Returns:
        PlotConfig with default values
    """
    return PlotConfig()


def plot_timeseries_with_forecast(
    ts: TimeSeries,
    forecast: Optional[FFTResult] = None,
    config: Optional[PlotConfig] = None,
) -> None:
    """Create a plot showing both original and forecasted values.

    Args:
        ts: TimeSeries object with original data
        forecast: FFTResult object with forecast data (optional)
        config: PlotConfig for customization (optional)

    Raises:
        ValueError: If time series is empty
    """
    if len(ts) == 0:
        raise ValueError("Time series is empty")

    if config is None:
        config = default_plot_config()

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(config.width, config.height))

    # Get data
    dates = ts.get_dates()
    values = ts.get_values()

    # Plot original data
    ax.plot(dates, values, "o-", color="#0064C8", linewidth=2, markersize=4, label="Original Data")

    # Plot forecast if provided
    if forecast is not None and config.show_forecast and len(forecast.forecasted_values) > 0:
        # Calculate forecast dates
        last_date = dates[-1]
        interval = timedelta(days=1)  # Default 1 day
        if len(dates) >= 2:
            interval = dates[1] - dates[0]

        forecast_dates = [
            last_date + (i + 1) * interval for i in range(len(forecast.forecasted_values))
        ]

        # Plot forecast
        # Connect last original point to first forecast point
        ax.plot(
            [last_date, forecast_dates[0]],
            [values[-1], forecast.forecasted_values[0]],
            "--",
            color="#C86400",
            linewidth=2,
            alpha=0.7,
        )
        ax.plot(
            forecast_dates,
            forecast.forecasted_values,
            "s--",
            color="#C86400",
            linewidth=2,
            markersize=4,
            label="Forecast",
        )

    # Configure plot
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Value", fontsize=12)
    ax.set_title(config.title, fontsize=14, fontweight="bold")
    ax.legend(loc="best", fontsize=10)
    ax.grid(True, alpha=0.3, linestyle="--")

    # Format x-axis dates
    ax.xaxis.set_major_formatter(DateFormatter("%m/%d"))
    fig.autofmt_xdate()

    # Adjust layout
    plt.tight_layout()

    # Save to file if specified
    if config.output_file:
        plt.savefig(config.output_file, dpi=config.dpi, bbox_inches="tight")
        print(f"Plot saved to {config.output_file}")

    # Show plot if requested
    if config.show_plot:
        plt.show()
    else:
        plt.close()


def save_plot_to_file(ts: TimeSeries, forecast: FFTResult, filename: str, title: str) -> None:
    """Save a plot to a PNG file.

    Args:
        ts: TimeSeries object with original data
        forecast: FFTResult object with forecast data
        filename: Output filename
        title: Plot title
    """
    config = default_plot_config()
    config.output_file = filename
    config.title = title
    config.show_plot = False

    plot_timeseries_with_forecast(ts, forecast, config)


def generate_report(ts: TimeSeries, forecast: FFTResult, output_file: str) -> None:
    """Generate a comprehensive report with statistics and plot.

    Args:
        ts: TimeSeries object with original data
        forecast: FFTResult object with forecast data
        output_file: Output filename for the report

    Raises:
        IOError: If file cannot be written
    """
    report_lines = []

    # Header
    report_lines.append("Time Series Forecasting Report")
    report_lines.append("=" * 50)
    report_lines.append("")

    # Basic statistics
    values = np.array(ts.get_values())
    min_val = np.min(values)
    max_val = np.max(values)
    mean_val = np.mean(values)
    std_dev = np.std(values)

    report_lines.append("Original Time Series Statistics:")
    report_lines.append(f"  Data Points: {len(values)}")
    report_lines.append(f"  Minimum: {min_val:.4f}")
    report_lines.append(f"  Maximum: {max_val:.4f}")
    report_lines.append(f"  Mean: {mean_val:.4f}")
    report_lines.append(f"  Std Dev: {std_dev:.4f}")
    report_lines.append("")

    # Forecast information
    if forecast is not None:
        report_lines.append("Forecast Information:")
        report_lines.append(f"  Method: {forecast.method}")
        report_lines.append(f"  Forecast Steps: {len(forecast.forecasted_values)}")

        if forecast.trend_info is not None:
            report_lines.append(f"  Trend Detected: {forecast.trend_info.has_positive_trend}")
            if forecast.trend_info.has_positive_trend:
                report_lines.append(f"  Slope: {forecast.trend_info.slope:.6f}")
                report_lines.append(f"  R-squared: {forecast.trend_info.r_squared:.4f}")

        # Forecast statistics
        forecast_vals = np.array(forecast.forecasted_values)
        forecast_min = np.min(forecast_vals)
        forecast_max = np.max(forecast_vals)
        forecast_mean = np.mean(forecast_vals)

        report_lines.append("")
        report_lines.append("Forecast Statistics:")
        report_lines.append(f"  Minimum: {forecast_min:.4f}")
        report_lines.append(f"  Maximum: {forecast_max:.4f}")
        report_lines.append(f"  Mean: {forecast_mean:.4f}")
        report_lines.append("")

    # Generate plot and save as PNG
    plot_filename = str(Path(output_file).with_suffix("")) + "_plot.png"
    try:
        save_plot_to_file(ts, forecast, plot_filename, "Time Series with Forecast")
        report_lines.append(f"Plot saved as: {plot_filename}")
    except Exception as e:
        report_lines.append(f"Warning: Could not generate plot: {e}")

    report_lines.append("")
    report_lines.append(
        "Note: This report includes comprehensive statistics and a separate PNG plot file."
    )

    # Save report to file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
    except IOError as e:
        raise IOError(f"Error writing report file: {e}") from e
