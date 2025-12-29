"""Tests for the timeseries module."""

from datetime import datetime
from pathlib import Path

import pytest

from time_to_critical.timeseries import (
    TimePoint,
    TimeSeries,
    parse_flexible_date,
    read_csv,
    read_parquet,
)


class TestTimePoint:
    """Tests for TimePoint dataclass."""

    def test_create_timepoint(self):
        """Test creating a TimePoint."""
        date = datetime(2024, 1, 1)
        value = 10.5
        point = TimePoint(date=date, value=value)

        assert point.date == date
        assert point.value == value


class TestTimeSeries:
    """Tests for TimeSeries class."""

    def test_create_empty_timeseries(self):
        """Test creating an empty TimeSeries."""
        ts = TimeSeries("test")
        assert ts.name == "test"
        assert len(ts) == 0
        assert ts.get_values() == []
        assert ts.get_dates() == []

    def test_add_point(self):
        """Test adding a point to TimeSeries."""
        ts = TimeSeries("test")
        date = datetime(2024, 1, 1)
        value = 10.5

        ts.add_point(date, value)

        assert len(ts) == 1
        assert ts.get_values() == [value]
        assert ts.get_dates() == [date]

    def test_multiple_points(self):
        """Test adding multiple points."""
        ts = TimeSeries("test")
        dates = [datetime(2024, 1, i) for i in range(1, 4)]
        values = [10.5, 11.2, 12.3]

        for date, value in zip(dates, values):
            ts.add_point(date, value)

        assert len(ts) == 3
        assert ts.get_values() == values
        assert ts.get_dates() == dates


class TestParseFlexibleDate:
    """Tests for flexible date parsing."""

    def test_parse_iso_date(self):
        """Test parsing ISO 8601 date."""
        date, fmt = parse_flexible_date("2024-01-15")
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15

    def test_parse_us_date(self):
        """Test parsing US format date."""
        date, fmt = parse_flexible_date("01/15/2024")
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15

    def test_parse_european_date(self):
        """Test parsing European format date."""
        date, fmt = parse_flexible_date("15.01.2024")
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15

    def test_parse_invalid_date(self):
        """Test parsing invalid date."""
        with pytest.raises(ValueError):
            parse_flexible_date("invalid-date")


class TestReadCSV:
    """Tests for CSV reading functionality."""

    def test_read_csv_with_header(self, tmp_path):
        """Test reading CSV with header."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("date,value\n2024-01-01,10.5\n2024-01-02,11.2\n")

        ts = read_csv(str(csv_file))

        assert len(ts) == 2
        assert ts.get_values() == [10.5, 11.2]

    def test_read_csv_without_header(self, tmp_path):
        """Test reading CSV without header."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("2024-01-01,10.5\n2024-01-02,11.2\n")

        ts = read_csv(str(csv_file))

        assert len(ts) == 2
        assert ts.get_values() == [10.5, 11.2]

    def test_read_csv_file_not_found(self):
        """Test reading non-existent CSV file."""
        with pytest.raises(FileNotFoundError):
            read_csv("nonexistent.csv")


class TestReadParquet:
    """Tests for Parquet reading functionality."""

    @pytest.mark.skipif(
        not Path("sample-data/sample_data.parquet").exists(),
        reason="Sample parquet file not found",
    )
    def test_read_parquet_file(self):
        """Test reading a Parquet file."""
        ts = read_parquet("sample-data/sample_data.parquet")

        assert len(ts) > 0
        assert all(isinstance(v, float) for v in ts.get_values())

    def test_read_parquet_file_not_found(self):
        """Test reading non-existent Parquet file."""
        with pytest.raises(FileNotFoundError):
            read_parquet("nonexistent.parquet")
