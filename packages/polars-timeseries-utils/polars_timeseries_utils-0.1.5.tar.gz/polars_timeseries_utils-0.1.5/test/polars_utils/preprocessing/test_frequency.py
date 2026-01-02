from datetime import datetime

import polars as pl
import pytest
from dateutil.relativedelta import relativedelta

from src.polars_timeseries_utils.preprocessing.frequency import (
	Frequency,
	determine_frequency,
	frequency_to_interval,
	periods_to_relativedelta,
)

TS = "timestamp"
VAL = "value"


class TestFrequencyToInterval:
	def test_hourly_returns_1h(self) -> None:
		assert frequency_to_interval(Frequency.HOURLY) == "1h"

	def test_daily_returns_1d(self) -> None:
		assert frequency_to_interval(Frequency.DAILY) == "1d"

	def test_monthly_returns_1mo(self) -> None:
		assert frequency_to_interval(Frequency.MONTHLY) == "1mo"

	def test_yearly_returns_1y(self) -> None:
		assert frequency_to_interval(Frequency.YEARLY) == "1y"

	def test_unknown_raises_value_error(self) -> None:
		with pytest.raises(ValueError, match="Unsupported frequency"):
			frequency_to_interval(Frequency.UNKNOWN)


# =============================================================================
# periods_to_relativedelta
# =============================================================================


class TestNPeriodsToDelta:
	def test_hourly_returns_hours_delta(self) -> None:
		result = periods_to_relativedelta(5, Frequency.HOURLY)
		assert result == relativedelta(hours=5)

	def test_daily_returns_days_delta(self) -> None:
		result = periods_to_relativedelta(10, Frequency.DAILY)
		assert result == relativedelta(days=10)

	def test_monthly_returns_months_delta(self) -> None:
		result = periods_to_relativedelta(3, Frequency.MONTHLY)
		assert result == relativedelta(months=3)

	def test_yearly_returns_years_delta(self) -> None:
		result = periods_to_relativedelta(2, Frequency.YEARLY)
		assert result == relativedelta(years=2)

	def test_zero_periods(self) -> None:
		result = periods_to_relativedelta(0, Frequency.DAILY)
		assert result == relativedelta(days=0)

	def test_unknown_raises_value_error(self) -> None:
		with pytest.raises(ValueError, match="Unknown frequency"):
			periods_to_relativedelta(1, Frequency.UNKNOWN)


class TestDetermineFrequency:
	def test_hourly_frequency(self) -> None:
		df = pl.DataFrame(
			{"ts": [datetime(2023, 1, 1, i) for i in range(10)], "y": range(10)}
		)
		result = determine_frequency(df["ts"])
		assert result == Frequency.HOURLY

	def test_daily_frequency(self) -> None:
		df = pl.DataFrame(
			{"ts": [datetime(2023, 1, i) for i in range(1, 11)], "y": range(10)}
		)
		result = determine_frequency(df["ts"])
		assert result == Frequency.DAILY

	def test_monthly_frequency(self) -> None:
		df = pl.DataFrame(
			{"ts": [datetime(2023, i, 1) for i in range(1, 11)], "y": range(10)}
		)
		result = determine_frequency(df["ts"])
		assert result == Frequency.MONTHLY

	def test_yearly_frequency(self) -> None:
		df = pl.DataFrame(
			{"ts": [datetime(2015 + i, 1, 1) for i in range(10)], "y": range(10)}
		)
		result = determine_frequency(df["ts"])
		assert result == Frequency.YEARLY

	def test_lazyframe_input(self) -> None:
		lf = pl.LazyFrame(
			{"ts": [datetime(2023, 1, i) for i in range(1, 11)], "y": range(10)}
		)
		result = determine_frequency(lf.select(pl.col("ts")).collect().to_series())
		assert result == Frequency.DAILY
