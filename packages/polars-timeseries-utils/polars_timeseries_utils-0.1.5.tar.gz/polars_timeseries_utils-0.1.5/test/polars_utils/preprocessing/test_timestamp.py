from datetime import datetime

import polars as pl
import pytest

from src.polars_timeseries_utils.preprocessing.timestamp import (
	Frequency,
	cast_to_datetime_raises_if_error,
	handle_timestamp_column_raises_if_error,
	last_timestamp,
	next_timestamp,
	next_timestamp_val,
)

TS = "timestamp"
VAL = "value"

# =============================================================================
# next_timestamp_val
# =============================================================================


class TestNextTimestampVal:
	def test_hourly_step_1(self) -> None:
		ts = datetime(2023, 1, 1, 10, 0)
		result = next_timestamp_val(ts, Frequency.HOURLY)
		assert result == datetime(2023, 1, 1, 11, 0)

	def test_daily_step_1(self) -> None:
		ts = datetime(2023, 1, 1)
		result = next_timestamp_val(ts, Frequency.DAILY)
		assert result == datetime(2023, 1, 2)

	def test_monthly_step_1(self) -> None:
		ts = datetime(2023, 1, 15)
		result = next_timestamp_val(ts, Frequency.MONTHLY)
		assert result == datetime(2023, 2, 15)

	def test_monthly_handles_end_of_month(self) -> None:
		ts = datetime(2023, 1, 31)
		result = next_timestamp_val(ts, Frequency.MONTHLY)
		# relativedelta handles this gracefully
		assert result == datetime(2023, 2, 28)

	def test_yearly_step_1(self) -> None:
		ts = datetime(2023, 6, 15)
		result = next_timestamp_val(ts, Frequency.YEARLY)
		assert result == datetime(2024, 6, 15)

	def test_yearly_handles_leap_year(self) -> None:
		ts = datetime(2020, 2, 29)  # Leap year
		result = next_timestamp_val(ts, Frequency.YEARLY)
		assert result == datetime(2021, 2, 28)  # Non-leap year

	def test_custom_step(self) -> None:
		ts = datetime(2023, 1, 1)
		result = next_timestamp_val(ts, Frequency.DAILY, step=5)
		assert result == datetime(2023, 1, 6)

	def test_negative_step(self) -> None:
		ts = datetime(2023, 1, 10)
		result = next_timestamp_val(ts, Frequency.DAILY, step=-3)
		assert result == datetime(2023, 1, 7)


# =============================================================================
# last_timestamp
# =============================================================================


class TestLastTimestamp:
	def test_returns_max_timestamp(self) -> None:
		series = pl.Series(
			"ts",
			[datetime(2023, 1, 1), datetime(2023, 6, 15), datetime(2023, 3, 10)],
		)
		result = last_timestamp(series)
		assert result == datetime(2023, 6, 15)

	def test_single_value(self) -> None:
		series = pl.Series("ts", [datetime(2023, 5, 20)])
		result = last_timestamp(series)
		assert result == datetime(2023, 5, 20)

	def test_sorted_series(self) -> None:
		series = pl.Series(
			"ts",
			[datetime(2023, 1, i) for i in range(1, 11)],
		)
		result = last_timestamp(series)
		assert result == datetime(2023, 1, 10)


# =============================================================================
# next_timestamp
# =============================================================================


class TestNextTimestamp:
	def test_next_after_series_daily(self) -> None:
		series = pl.Series(
			"ts",
			[datetime(2023, 1, i) for i in range(1, 6)],
		)
		result = next_timestamp(series, Frequency.DAILY)
		assert result == datetime(2023, 1, 6)

	def test_next_after_series_monthly(self) -> None:
		series = pl.Series(
			"ts",
			[datetime(2023, i, 1) for i in range(1, 4)],
		)
		result = next_timestamp(series, Frequency.MONTHLY)
		assert result == datetime(2023, 4, 1)

	def test_next_with_step(self) -> None:
		series = pl.Series(
			"ts",
			[datetime(2023, 1, i) for i in range(1, 6)],
		)
		result = next_timestamp(series, Frequency.DAILY, step=3)
		assert result == datetime(2023, 1, 8)


# =============================================================================
# cast_to_datetime_raises_if_error
# =============================================================================


class TestCastToDatetimeRaisesIfError:
	def test_str_ymd_dash_casting(
		self, df_unclean_timestamp_str_ymd_dash: pl.DataFrame
	) -> None:
		df = df_unclean_timestamp_str_ymd_dash.clone()
		result = cast_to_datetime_raises_if_error(df[TS])

		assert isinstance(result, pl.Series)
		assert result.shape == df[TS].shape
		assert result.dtype == pl.Datetime

		df = df.with_columns(result.alias(TS))

		assert df.shape == df_unclean_timestamp_str_ymd_dash.shape
		assert df[TS].dtype == pl.Datetime

	def test_str_dmy_dash_casting(
		self, df_unclean_timestamp_str_dmy_dash: pl.DataFrame
	) -> None:
		df = df_unclean_timestamp_str_dmy_dash.clone()
		result = cast_to_datetime_raises_if_error(df[TS])

		assert isinstance(result, pl.Series)
		assert result.shape == df[TS].shape
		assert result.dtype == pl.Datetime

		df = df.with_columns(result.alias(TS))

		assert df.shape == df_unclean_timestamp_str_dmy_dash.shape
		assert df[TS].dtype == pl.Datetime

	def test_str_ymd_slash_casting(
		self, df_unclean_timestamp_str_ymd_slash: pl.DataFrame
	) -> None:
		df = df_unclean_timestamp_str_ymd_slash.clone()
		result = cast_to_datetime_raises_if_error(df[TS])

		assert isinstance(result, pl.Series)
		assert result.shape == df[TS].shape
		assert result.dtype == pl.Datetime

		df = df.with_columns(result.alias(TS))

		assert df.shape == df_unclean_timestamp_str_ymd_slash.shape
		assert df[TS].dtype == pl.Datetime

	def test_str_dmy_slash_casting(
		self, df_unclean_timestamp_str_dmy_slash: pl.DataFrame
	) -> None:
		df = df_unclean_timestamp_str_dmy_slash.clone()
		result = cast_to_datetime_raises_if_error(df[TS])

		assert isinstance(result, pl.Series)
		assert result.shape == df[TS].shape
		assert result.dtype == pl.Datetime

		df = df.with_columns(result.alias(TS))

		assert df.shape == df_unclean_timestamp_str_dmy_slash.shape
		assert df[TS].dtype == pl.Datetime

	def test_str_datetime_ymd_dash_casting(
		self, df_unclean_timestamp_str_datetime_ymd_dash: pl.DataFrame
	) -> None:
		df = df_unclean_timestamp_str_datetime_ymd_dash.clone()
		result = cast_to_datetime_raises_if_error(df[TS])

		assert isinstance(result, pl.Series)
		assert result.shape == df[TS].shape
		assert result.dtype == pl.Datetime

		df = df.with_columns(result.alias(TS))

		assert df.shape == df_unclean_timestamp_str_datetime_ymd_dash.shape
		assert df[TS].dtype == pl.Datetime

	def test_str_datetime_dmy_dash_casting(
		self, df_unclean_timestamp_str_datetime_dmy_dash: pl.DataFrame
	) -> None:
		df = df_unclean_timestamp_str_datetime_dmy_dash.clone()
		result = cast_to_datetime_raises_if_error(df[TS])

		assert isinstance(result, pl.Series)
		assert result.shape == df[TS].shape
		assert result.dtype == pl.Datetime

		df = df.with_columns(result.alias(TS))

		assert df.shape == df_unclean_timestamp_str_datetime_dmy_dash.shape
		assert df[TS].dtype == pl.Datetime

	def test_str_datetime_ymd_slash_casting(
		self, df_unclean_timestamp_str_datetime_ymd_slash: pl.DataFrame
	) -> None:
		df = df_unclean_timestamp_str_datetime_ymd_slash.clone()
		result = cast_to_datetime_raises_if_error(df[TS])

		assert isinstance(result, pl.Series)
		assert result.shape == df[TS].shape
		assert result.dtype == pl.Datetime

		df = df.with_columns(result.alias(TS))

		assert df.shape == df_unclean_timestamp_str_datetime_ymd_slash.shape
		assert df[TS].dtype == pl.Datetime

	def test_str_datetime_dmy_slash_casting(
		self, df_unclean_timestamp_str_datetime_dmy_slash: pl.DataFrame
	) -> None:
		df = df_unclean_timestamp_str_datetime_dmy_slash.clone()
		result = cast_to_datetime_raises_if_error(df[TS])

		assert isinstance(result, pl.Series)
		assert result.shape == df[TS].shape
		assert result.dtype == pl.Datetime

		df = df.with_columns(result.alias(TS))

		assert df.shape == df_unclean_timestamp_str_datetime_dmy_slash.shape
		assert df[TS].dtype == pl.Datetime

	def test_lf_str_timestamp_casting(
		self, lf_unclean_timestamp_str: pl.LazyFrame
	) -> None:
		lf = lf_unclean_timestamp_str.clone()
		result = cast_to_datetime_raises_if_error(
			lf.select(pl.col(TS)).collect().to_series()
		)

		assert isinstance(result, pl.Series)
		assert result.shape == lf.select(pl.col(TS)).collect().to_series().shape
		assert result.dtype == pl.Datetime

		df = lf.with_columns(result.alias(TS)).collect()
		assert df.shape == lf_unclean_timestamp_str.collect().shape
		assert df[TS].dtype == pl.Datetime

	def test_non_castable_raises_error(
		self, df_invalid_non_castable_timestamp: pl.DataFrame
	) -> None:
		df = df_invalid_non_castable_timestamp.clone()

		with pytest.raises(
			ValueError, match="All datetime format casting attempts failed"
		):
			cast_to_datetime_raises_if_error(df[TS])


# =============================================================================
# handle_timestamp_column_raises_if_error
# =============================================================================


class TestHandleTimestampColumnRaisesIfError:
	def test_valid_timestamp_column_df(self, df_clean: pl.DataFrame) -> None:
		df = df_clean.clone()
		df, col = handle_timestamp_column_raises_if_error(df, TS)

		assert isinstance(df, pl.DataFrame)
		assert df.shape == df_clean.shape
		assert col == TS
		assert df[TS].dtype == pl.Datetime

	def test_valid_timestamp_column_lf(self, lf_clean: pl.LazyFrame) -> None:
		lf = lf_clean.clone()
		lf, col = handle_timestamp_column_raises_if_error(lf, TS)
		df = lf.lazy().collect()

		assert isinstance(lf, pl.LazyFrame)
		assert df.shape == lf_clean.collect().shape
		assert col == TS
		assert df[TS].dtype == pl.Datetime

	def test_auto_detect_timestamp(self, df_clean: pl.DataFrame) -> None:
		df = df_clean.clone()
		df, col = handle_timestamp_column_raises_if_error(df)

		assert isinstance(df, pl.DataFrame)
		assert df.shape == df_clean.shape
		assert col == TS
		assert df[col].dtype == pl.Datetime

	def test_auto_detect_date_col(self, df_clean_date_col: pl.DataFrame) -> None:
		df = df_clean_date_col.clone()
		df, col = handle_timestamp_column_raises_if_error(df)

		assert isinstance(df, pl.DataFrame)
		assert df.shape == df_clean_date_col.shape
		assert col == "date"
		assert df[col].dtype == pl.Datetime

	def test_auto_detect_ds_col(self, df_clean_ds_col: pl.DataFrame) -> None:
		df = df_clean_ds_col.clone()
		df, col = handle_timestamp_column_raises_if_error(df)

		assert isinstance(df, pl.DataFrame)
		assert df.shape == df_clean_ds_col.shape
		assert col == "ds"
		assert df[col].dtype == pl.Datetime

	def test_str_timestamp_casting(
		self, df_unclean_timestamp_str_ymd_dash: pl.DataFrame
	) -> None:
		df = df_unclean_timestamp_str_ymd_dash.clone()
		df, col = handle_timestamp_column_raises_if_error(df)

		assert isinstance(df, pl.DataFrame)
		assert df.shape == df_unclean_timestamp_str_ymd_dash.shape
		assert col == TS
		assert df[col].dtype == pl.Datetime

	def test_lf_str_timestamp_casting(
		self, lf_unclean_timestamp_str: pl.LazyFrame
	) -> None:
		lf = lf_unclean_timestamp_str.clone()
		lf, col = handle_timestamp_column_raises_if_error(lf)

		assert isinstance(lf, pl.LazyFrame)
		df = lf.collect()
		assert df.shape == lf_unclean_timestamp_str.collect().shape
		assert col == TS
		assert df[col].dtype == pl.Datetime

	def test_non_standard_name_auto_detect(
		self, df_unclean_no_standard_timestamp_name: pl.DataFrame
	) -> None:
		df = df_unclean_no_standard_timestamp_name.clone()
		df, col = handle_timestamp_column_raises_if_error(df)

		assert isinstance(df, pl.DataFrame)
		assert df.shape == df_unclean_no_standard_timestamp_name.shape
		assert col == "my_custom_date"
		assert df[col].dtype == pl.Datetime

	def test_no_datetime_col_raises(
		self, df_invalid_no_datetime_col: pl.DataFrame
	) -> None:
		with pytest.raises(
			ValueError, match="Timestamp column could not be determined"
		):
			handle_timestamp_column_raises_if_error(df_invalid_no_datetime_col)

	def test_non_castable_timestamp_raises(
		self, df_invalid_non_castable_timestamp: pl.DataFrame
	) -> None:
		with pytest.raises(ValueError, match="could not be cast to datetime"):
			handle_timestamp_column_raises_if_error(
				df_invalid_non_castable_timestamp, TS
			)

	def test_missing_specified_col_raises(
		self, df_invalid_missing_specified_col: pl.DataFrame
	) -> None:
		with pytest.raises(ValueError, match="not found"):
			handle_timestamp_column_raises_if_error(
				df_invalid_missing_specified_col, TS
			)
