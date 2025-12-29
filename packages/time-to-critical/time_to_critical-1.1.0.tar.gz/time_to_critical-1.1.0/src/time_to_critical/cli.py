"""Command-line interface for the time series forecasting tool."""

import argparse
import sys
from pathlib import Path

from time_to_critical.forecast import forecast_fft
from time_to_critical.plotting import (
    PlotConfig,
    generate_report,
    plot_timeseries_with_forecast,
    save_plot_to_file,
)
from time_to_critical.timeseries import read_csv, read_parquet


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="time-to-critical",
        description="Time Series Forecasting Tool using FFT",
        epilog=(
            "Examples:\n"
            "  %(prog)s -i data.csv -s 20 -p\n"
            "  %(prog)s -i data.csv --steps 15 -o forecast.csv --report report.txt\n"
            "  %(prog)s -i data.csv -d '%%Y-%%m-%%d' --save-plot plot.png -v\n"
            "  %(prog)s -i data.csv -d auto -v\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Input file (required)
    parser.add_argument(
        "-i",
        "--input",
        dest="input_file",
        required=True,
        help="Input CSV or Parquet file path (required)",
    )

    # Output file (optional)
    parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        default="",
        help="Output CSV file path for forecast results",
    )

    # Date format (optional)
    parser.add_argument(
        "-d",
        "--date-format",
        dest="date_format",
        default="auto",
        help="Date format for parsing (strftime format) or 'auto' for flexible parsing (default: auto)",
    )

    # Forecast steps (optional)
    parser.add_argument(
        "-s",
        "--steps",
        dest="horizon_steps",
        type=int,
        default=10,
        help="Number of steps to forecast ahead (default: 10)",
    )

    # Plot (optional)
    parser.add_argument(
        "-p",
        "--plot",
        dest="show_plot",
        action="store_true",
        help="Display PNG plot of the time series and forecast",
    )

    # Save plot (optional)
    parser.add_argument("--save-plot", dest="save_plot", default="", help="Save plot to PNG file")

    # Report (optional)
    parser.add_argument(
        "--report", dest="generate_report", default="", help="Generate comprehensive report to file"
    )

    # Verbose (optional)
    parser.add_argument(
        "-v", "--verbose", dest="verbose", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # Validate horizon steps
    if args.horizon_steps <= 0:
        parser.error("Horizon steps must be positive")

    return args


def load_timeseries(filename: str, date_format: str, verbose: bool):
    """Load time series data from file.

    Args:
        filename: Path to input file
        date_format: Date format for parsing
        verbose: Enable verbose output

    Returns:
        TimeSeries object

    Raises:
        SystemExit: If file cannot be loaded
    """
    ext = Path(filename).suffix.lower()

    try:
        if ext == ".csv":
            return read_csv(filename, date_format, verbose)
        elif ext == ".parquet":
            return read_parquet(filename, verbose)
        else:
            print(
                f"Error: Unsupported file format: {ext} (supported: .csv, .parquet)",
                file=sys.stderr,
            )
            sys.exit(1)
    except Exception as e:
        print(f"Error loading time series: {e}", file=sys.stderr)
        sys.exit(1)


def print_forecast(forecast, verbose: bool) -> None:
    """Print forecasted values to stdout.

    Args:
        forecast: FFTResult object
        verbose: Enable verbose output
    """
    if verbose:
        print("Forecasted Values:")
        print("=" * 40)

    for i, value in enumerate(forecast.forecasted_values):
        if verbose:
            print(f"Step {i + 1}: {value:.6f}")
        else:
            print(f"{value:.6f}")


def save_forecast_to_csv(forecast, filename: str) -> None:
    """Save forecast results to a CSV file.

    Args:
        forecast: FFTResult object
        filename: Output CSV filename

    Raises:
        SystemExit: If file cannot be written
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("step,forecasted_value\n")
            for i, value in enumerate(forecast.forecasted_values):
                f.write(f"{i + 1},{value:.6f}\n")
    except IOError as e:
        print(f"Error saving forecast: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI application."""
    args = parse_arguments()

    if args.verbose:
        print("Time Series Forecasting Tool")
        print("=" * 40)
        print()

    # Load the time series data
    ts = load_timeseries(args.input_file, args.date_format, args.verbose)

    if args.verbose:
        print(f"Loaded {len(ts)} data points from {args.input_file}")

    # Perform forecasting
    forecast = forecast_fft(ts, args.horizon_steps)

    if args.verbose:
        print(f"Applied {forecast.method}")
        if forecast.trend_info.has_positive_trend:
            print(
                f"Positive trend detected (slope: {forecast.trend_info.slope:.6f}, "
                f"R²: {forecast.trend_info.r_squared:.3f})"
            )
        else:
            print("No significant positive trend detected")
        print(f"Generated {len(forecast.forecasted_values)} forecast points")
        print()

    # Output forecasted values
    if args.output_file:
        save_forecast_to_csv(forecast, args.output_file)
        if args.verbose:
            print(f"Forecast saved to {args.output_file}")
    else:
        print_forecast(forecast, args.verbose)

    # Show plot if requested
    if args.show_plot:
        config = PlotConfig()
        config.title = f"Time Series Forecast ({Path(args.input_file).name})"
        config.show_plot = True
        try:
            plot_timeseries_with_forecast(ts, forecast, config)
        except Exception as e:
            print(f"Error creating plot: {e}", file=sys.stderr)

    # Save plot if requested
    if args.save_plot:
        title = f"Time Series Forecast ({Path(args.input_file).name})"
        try:
            save_plot_to_file(ts, forecast, args.save_plot, title)
            if args.verbose:
                print(f"Plot saved to {args.save_plot}")
        except Exception as e:
            print(f"Error saving plot: {e}", file=sys.stderr)

    # Generate report if requested
    if args.generate_report:
        try:
            generate_report(ts, forecast, args.generate_report)
            if args.verbose:
                print(f"Report saved to {args.generate_report}")
        except Exception as e:
            print(f"Error generating report: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
