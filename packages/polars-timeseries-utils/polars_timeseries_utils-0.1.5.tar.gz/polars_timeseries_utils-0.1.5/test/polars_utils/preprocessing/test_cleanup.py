from datetime import datetime

import polars as pl

from polars_timeseries_utils.preprocessing.cleanup import clean_timeseries_df


class TestCleanTimeseriesDf:
	"""Tests for the clean_timeseries_df function."""

	def test_sorts_by_timestamp(self) -> None:
		"""Test that data is sorted by timestamp column."""
		df = pl.DataFrame(
			{
				"timestamp": [
					datetime(2023, 1, 3),
					datetime(2023, 1, 1),
					datetime(2023, 1, 2),
				],
				"value": [3.0, 1.0, 2.0],
			}
		)

		result = clean_timeseries_df(df, ts_col="timestamp")

		assert result["timestamp"].to_list() == [  # type: ignore
			datetime(2023, 1, 1),
			datetime(2023, 1, 2),
			datetime(2023, 1, 3),
		]

	def test_removes_duplicates(self) -> None:
		"""Test that duplicate timestamps are removed."""
		df = pl.DataFrame(
			{
				"timestamp": [
					datetime(2023, 1, 1),
					datetime(2023, 1, 1),
					datetime(2023, 1, 2),
				],
				"value": [1.0, 1.5, 2.0],
			}
		)

		result = clean_timeseries_df(df, ts_col="timestamp")

		assert len(result) == 2  # type: ignore
		assert result["timestamp"].n_unique() == 2  # type: ignore

	def test_imputes_missing_values(self) -> None:
		"""Test that missing values are imputed."""
		df = pl.DataFrame(
			{
				"timestamp": [datetime(2023, 1, i) for i in range(1, 11)],
				"value": [1.0, 2.0, None, 4.0, 5.0, None, 7.0, 8.0, 9.0, 10.0],
			}
		)

		result = clean_timeseries_df(df, ts_col="timestamp", window_size=3)

		# Nulls should be filled
		assert result["value"].null_count() == 0  # type: ignore

	def test_smooths_outliers(self) -> None:
		"""Test that outliers are smoothed."""
		df = pl.DataFrame(
			{
				"timestamp": [datetime(2023, 1, i) for i in range(1, 11)],
				"value": [1.0, 2.0, 3.0, 100.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
			}
		)

		result = clean_timeseries_df(
			df, ts_col="timestamp", window_size=3, max_zscore=2.0
		)

		# The outlier (100.0) should be reduced
		assert result["value"][3] < 100.0  # type: ignore

	def test_preserves_column_order(self) -> None:
		"""Test that original column order is preserved."""
		df = pl.DataFrame(
			{
				"timestamp": [datetime(2023, 1, i) for i in range(1, 6)],
				"col_a": [1.0, 2.0, 3.0, 4.0, 5.0],
				"col_b": [10.0, 20.0, 30.0, 40.0, 50.0],
			}
		)

		result = clean_timeseries_df(df, ts_col="timestamp")

		assert result.columns == ["timestamp", "col_a", "col_b"]

	def test_rounds_values(self) -> None:
		"""Test that values are rounded to specified precision."""
		df = pl.DataFrame(
			{
				"timestamp": [datetime(2023, 1, i) for i in range(1, 6)],
				"value": [1.123456, 2.654321, 3.111111, 4.999999, 5.555555],
			}
		)

		result = clean_timeseries_df(df, ts_col="timestamp", round=2)

		# Values should be rounded to 2 decimal places
		for val in result["value"].to_list():  # type: ignore
			# Check that value has at most 2 decimal places
			assert val == round(val, 2)  # type: ignore

	def test_lazyframe_support(self) -> None:
		"""Test that LazyFrame input returns LazyFrame output."""
		lf = pl.DataFrame(
			{
				"timestamp": [datetime(2023, 1, i) for i in range(1, 6)],
				"value": [1.0, 2.0, 3.0, 4.0, 5.0],
			}
		).lazy()

		result = clean_timeseries_df(lf, ts_col="timestamp")

		assert isinstance(result, pl.LazyFrame)

	def test_dataframe_support(self) -> None:
		"""Test that DataFrame input returns DataFrame output."""
		df = pl.DataFrame(
			{
				"timestamp": [datetime(2023, 1, i) for i in range(1, 6)],
				"value": [1.0, 2.0, 3.0, 4.0, 5.0],
			}
		)

		result = clean_timeseries_df(df, ts_col="timestamp")

		assert isinstance(result, pl.DataFrame)

	def test_custom_window_size(self) -> None:
		"""Test with custom window size."""
		df = pl.DataFrame(
			{
				"timestamp": [datetime(2023, 1, i) for i in range(1, 11)],
				"value": [1.0, None, None, None, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
			}
		)

		result = clean_timeseries_df(df, ts_col="timestamp", window_size=10)

		# Should still fill nulls with larger window
		assert result["value"].null_count() == 0  # type: ignore

	def test_non_numeric_columns_unchanged(self) -> None:
		"""Test that non-numeric columns are not modified."""
		df = pl.DataFrame(
			{
				"timestamp": [datetime(2023, 1, i) for i in range(1, 6)],
				"value": [1.0, 2.0, 3.0, 4.0, 5.0],
				"category": ["a", "b", "c", "d", "e"],
			}
		)

		result = clean_timeseries_df(df, ts_col="timestamp")

		assert result["category"].to_list() == ["a", "b", "c", "d", "e"]  # type: ignore
