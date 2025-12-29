"""Time series data handling and file I/O."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple

import pandas as pd
from dateutil import parser as dateutil_parser


@dataclass
class TimePoint:
    """Represents a single data point in the time series."""

    date: datetime
    value: float


class TimeSeries:
    """Represents a collection of time-ordered data points."""

    def __init__(self, name: str = ""):
        """Initialize a new TimeSeries instance.

        Args:
            name: Name identifier for the time series
        """
        self.name = name
        self.data: List[TimePoint] = []

    def add_point(self, date: datetime, value: float) -> None:
        """Add a new data point to the time series.

        Args:
            date: Datetime of the data point
            value: Numeric value of the data point
        """
        self.data.append(TimePoint(date=date, value=value))

    def get_values(self) -> List[float]:
        """Return only the values from the time series.

        Returns:
            List of float values
        """
        return [point.value for point in self.data]

    def get_dates(self) -> List[datetime]:
        """Return only the dates from the time series.

        Returns:
            List of datetime objects
        """
        return [point.date for point in self.data]

    def __len__(self) -> int:
        """Return the length of the time series.

        Returns:
            Number of data points in the series
        """
        return len(self.data)


def parse_flexible_date(date_str: str, verbose: bool = False) -> Tuple[datetime, str]:
    """Try to parse date strings in multiple formats.

    Args:
        date_str: Date string to parse
        verbose: If True, return the format used for parsing

    Returns:
        Tuple of (parsed datetime, format string used)

    Raises:
        ValueError: If date cannot be parsed with any known format
    """
    # List of date formats ordered by priority (unambiguous first)
    formats = [
        # ISO 8601 formats (unambiguous - highest priority)
        "%Y-%m-%d",  # YYYY-MM-DD
        "%Y-%m-%d %H:%M:%S",  # YYYY-MM-DD HH:MM:SS
        "%Y-%m-%dT%H:%M:%SZ",  # YYYY-MM-DDTHH:MM:SSZ
        "%Y-%m-%dT%H:%M:%S.%fZ",  # YYYY-MM-DDTHH:MM:SS.sssZ
        "%Y-%m-%dT%H:%M:%S%z",  # YYYY-MM-DDTHH:MM:SS+/-TZ:TZ
        "%Y-%m-%dT%H:%M:%S.%f%z",  # YYYY-MM-DDTHH:MM:SS.sss+/-TZ:TZ
        # Unambiguous YYYY-based formats
        "%Y/%m/%d",  # YYYY/MM/DD
        "%Y/%m/%d %H:%M:%S",  # YYYY/MM/DD HH:MM:SS
        "%Y/%m/%d",  # YYYY/M/D
        "%Y-%m-%d",  # YYYY-M-D
        "%y/%m/%d",  # YY/MM/DD
        # Text-based months (unambiguous)
        "%b %d, %Y",  # Mon D, YYYY
        "%B %d, %Y",  # Month D, YYYY
        "%d %b %Y",  # D Mon YYYY
        "%d %B %Y",  # D Month YYYY
        "%b %Y",  # Mon YYYY
        "%B %Y",  # Month YYYY
        # European formats with dots (common in Europe)
        "%d.%m.%Y",  # DD.MM.YYYY
        "%d.%m.%Y %H:%M:%S",  # DD.MM.YYYY HH:MM:SS
        "%d.%m.%Y",  # D.M.YYYY
        "%d.%m.%y",  # D.M.YY
        # European formats with dashes (prioritize DD-MM-YYYY interpretation)
        "%d-%m-%Y",  # DD-MM-YYYY
        "%d-%m-%Y %H:%M:%S",  # DD-MM-YYYY HH:MM:SS
        "%d-%m-%Y",  # D-M-YYYY
        # Single digit ambiguous formats - prioritize US format
        "%m/%d/%Y",  # M/D/YYYY (US: Jan 2)
        "%m/%d/%y",  # M/D/YY
        # European formats with slashes
        "%d/%m/%Y",  # DD/MM/YYYY
        "%d/%m/%Y %H:%M:%S",  # DD/MM/YYYY HH:MM:SS
        "%d/%m/%Y",  # D/M/YYYY (European: 2 Jan)
        "%d/%m/%y",  # D/M/YY
        "%d/%m/%y",  # DD/MM/YY
        # US formats (lower priority due to ambiguity)
        "%m/%d/%Y",  # MM/DD/YYYY
        "%m/%d/%Y %H:%M:%S",  # MM/DD/YYYY HH:MM:SS
        "%m/%d/%y",  # MM/DD/YY
        # US formats with dashes (lowest priority)
        "%m-%d-%Y",  # MM-DD-YYYY
        "%m-%d-%Y %H:%M:%S",  # MM-DD-YYYY HH:MM:SS
        "%m-%d-%Y",  # M-D-YYYY
    ]

    # First try dateutil parser (very flexible)
    try:
        parsed_date = dateutil_parser.parse(date_str)
        return parsed_date, "dateutil_auto"
    except (ValueError, TypeError):
        pass

    # Then try specific formats
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date, fmt
        except ValueError:
            continue

    # If all fails, raise error
    raise ValueError(
        f"Unable to parse date string '{date_str}' with any known format. "
        f"Attempted {len(formats)} formats."
    )


def read_csv(filename: str, date_format: str = "auto", verbose: bool = False) -> TimeSeries:
    """Read time series data from a CSV file.

    Expected format: first column is date, second column is value.
    Header row is optional and automatically detected.

    Args:
        filename: Path to CSV file
        date_format: Date format ('auto' for flexible parsing, or specific strftime format)
        verbose: Enable logging of date format detection

    Returns:
        TimeSeries object with loaded data

    Raises:
        ValueError: If file cannot be parsed or dates are invalid
        FileNotFoundError: If file does not exist
    """
    try:
        # Read CSV file
        df = pd.read_csv(filename, header=None)

        # Check if first row is header
        try:
            float(df.iloc[0, 1])
            has_header = False
        except (ValueError, TypeError):
            has_header = True

        if has_header:
            df = df.iloc[1:]

        # Create TimeSeries
        ts = TimeSeries(filename)

        # Parse each row
        for _idx, row in df.iterrows():
            date_str = str(row.iloc[0])
            value = float(row.iloc[1])

            # Parse date
            if date_format == "auto" or date_format == "":
                date, used_format = parse_flexible_date(date_str, verbose)
                if verbose:
                    print(f"Date '{date_str}' parsed using format: {used_format}")
            else:
                date = datetime.strptime(date_str, date_format)
                if verbose:
                    print(f"Date '{date_str}' parsed using specified format: {date_format}")

            ts.add_point(date, value)

        return ts

    except FileNotFoundError as e:
        raise FileNotFoundError(f"CSV file not found: {filename}") from e
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}") from e


def read_parquet(filename: str, verbose: bool = False) -> TimeSeries:
    """Read time series data from a Parquet file.

    Expected schema: columns named 'date' and 'value'.

    Args:
        filename: Path to Parquet file
        verbose: Enable logging of date format detection

    Returns:
        TimeSeries object with loaded data

    Raises:
        ValueError: If file cannot be parsed or schema is invalid
        FileNotFoundError: If file does not exist
    """
    try:
        # Read Parquet file
        df = pd.read_parquet(filename, engine="pyarrow")

        # Verify columns exist
        if "date" not in df.columns or "value" not in df.columns:
            raise ValueError(
                f"Parquet file must have 'date' and 'value' columns. " f"Found: {list(df.columns)}"
            )

        # Create TimeSeries
        ts = TimeSeries(filename)

        # Parse each row
        for _, row in df.iterrows():
            date_str = str(row["date"])
            value = float(row["value"])

            # Parse date with flexible parsing
            date, used_format = parse_flexible_date(date_str, verbose)
            if verbose:
                print(f"Date '{date_str}' parsed using format: {used_format}")

            ts.add_point(date, value)

        return ts

    except FileNotFoundError as e:
        raise FileNotFoundError(f"Parquet file not found: {filename}") from e
    except Exception as e:
        raise ValueError(f"Error reading Parquet file: {e}") from e
