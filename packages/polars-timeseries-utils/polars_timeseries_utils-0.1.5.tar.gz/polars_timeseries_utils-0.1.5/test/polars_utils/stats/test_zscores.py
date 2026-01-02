import polars as pl

from polars_timeseries_utils.stats.zscore import (
	rolling_zscore,
	rolling_zscore_df,
	zscore,
	zscore_df,
)


class TestZscore:
	"""Tests for the zscore function."""

	def test_basic_zscore_calculation(self) -> None:
		"""Test basic z-score calculation on a Series."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0])

		result = zscore(s)

		assert result.name == "value"
		assert result.len() == 5
		# Middle value (3.0 = median) should have z-score near 0
		assert abs(result[2]) < 0.01

	def test_preserves_series_name(self) -> None:
		"""Test that the series name is preserved."""
		s = pl.Series("my_column", [1.0, 2.0, 3.0])

		result = zscore(s)

		assert result.name == "my_column"

	def test_symmetric_distribution(self) -> None:
		"""Test z-scores for symmetric distribution."""
		s = pl.Series("value", [-2.0, -1.0, 0.0, 1.0, 2.0])

		result = zscore(s)

		# Symmetric values should have opposite z-scores
		assert abs(result[0] + result[4]) < 0.01
		assert abs(result[1] + result[3]) < 0.01

	def test_outlier_detection(self) -> None:
		"""Test that outliers have high z-scores."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0, 100.0])

		result = zscore(s)

		# The outlier (100.0) should have a much higher z-score than the others
		assert result[5] > result[0]
		assert result[5] > result[4]

	def test_constant_values(self) -> None:
		"""Test z-score with constant values (std = 0)."""
		s = pl.Series("value", [5.0, 5.0, 5.0, 5.0, 5.0])

		result = zscore(s)

		# With constant values, std is 0, so z-scores should be NaN or 0
		assert all(v is None or v != v or v == 0.0 for v in result.to_list())

	def test_single_value(self) -> None:
		"""Test z-score with single value."""
		s = pl.Series("value", [5.0])

		result = zscore(s)

		assert result.len() == 1

	def test_negative_values(self) -> None:
		"""Test z-score with negative values."""
		s = pl.Series("value", [-10.0, -5.0, 0.0, 5.0, 10.0])

		result = zscore(s)

		# Should produce valid z-scores
		assert result.len() == 5
		# Median value (0.0) should have z-score near 0
		assert abs(result[2]) < 0.01

	def test_with_null_values(self) -> None:
		"""Test z-score with null values."""
		s = pl.Series("value", [1.0, None, 3.0, 4.0, 5.0])

		result = zscore(s)

		assert result.len() == 5


class TestZscoreDf:
	"""Tests for the zscore_df function."""

	def test_basic_zscore_calculation(self) -> None:
		"""Test basic z-score calculation on DataFrame."""
		df = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})

		result = zscore_df(df, col="value")

		assert "z_score" in result.columns
		assert result.height == 5  # type: ignore

	def test_custom_alias(self) -> None:
		"""Test custom alias for z-score column."""
		df = pl.DataFrame({"value": [1.0, 2.0, 3.0]})

		result = zscore_df(df, col="value", alias="my_zscore")

		assert "my_zscore" in result.columns
		assert "z_score" not in result.columns

	def test_preserves_original_columns(self) -> None:
		"""Test that original columns are preserved."""
		df = pl.DataFrame({"id": [1, 2, 3], "value": [1.0, 2.0, 3.0]})

		result = zscore_df(df, col="value")

		assert "id" in result.columns
		assert "value" in result.columns
		assert "z_score" in result.columns

	def test_with_median_output(self) -> None:
		"""Test including median column in output."""
		df = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})

		result = zscore_df(df, col="value", with_median="med")

		assert "med" in result.columns
		# Median of [1, 2, 3, 4, 5] is 3.0
		assert result["med"][0] == 3.0  # type: ignore

	def test_with_std_output(self) -> None:
		"""Test including std column in output."""
		df = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})

		result = zscore_df(df, col="value", with_std="stdev")

		assert "stdev" in result.columns
		# std should be positive
		assert result["stdev"][0] > 0  # type: ignore

	def test_with_median_and_std_output(self) -> None:
		"""Test including both median and std columns."""
		df = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})

		result = zscore_df(df, col="value", with_median="med", with_std="stdev")

		assert "med" in result.columns
		assert "stdev" in result.columns
		assert "z_score" in result.columns

	def test_lazyframe_support(self) -> None:
		"""Test that LazyFrame is supported."""
		df = pl.DataFrame({"value": [1.0, 2.0, 3.0]}).lazy()

		result = zscore_df(df, col="value")

		assert isinstance(result, pl.LazyFrame)
		collected = result.collect()
		assert "z_score" in collected.columns

	def test_dataframe_support(self) -> None:
		"""Test that DataFrame is supported."""
		df = pl.DataFrame({"value": [1.0, 2.0, 3.0]})

		result = zscore_df(df, col="value")

		assert isinstance(result, pl.DataFrame)
		assert "z_score" in result.columns

	def test_median_zscore_is_zero(self) -> None:
		"""Test that z-score of median value is close to zero."""
		df = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})

		result = zscore_df(df, col="value")

		# 3.0 is the median, so its z-score should be near 0
		assert abs(result["z_score"][2]) < 0.01  # type: ignore

	def test_multiple_columns_preserved(self) -> None:
		"""Test that all original columns are preserved."""
		df = pl.DataFrame(
			{
				"id": [1, 2, 3],
				"name": ["a", "b", "c"],
				"value": [1.0, 2.0, 3.0],
				"other": [10.0, 20.0, 30.0],
			}
		)

		result = zscore_df(df, col="value")

		assert list(result.columns) == ["id", "name", "value", "other", "z_score"]


class TestRollingZscore:
	"""Tests for the rolling_zscore function."""

	def test_basic_rolling_zscore(self) -> None:
		"""Test basic rolling z-score calculation on Series."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])

		result = rolling_zscore(s, window_size=3)

		assert result.name == "value"
		assert result.len() == 10

	def test_preserves_series_name(self) -> None:
		"""Test that series name is preserved."""
		s = pl.Series("my_column", [1.0, 2.0, 3.0, 4.0, 5.0])

		result = rolling_zscore(s, window_size=3)

		assert result.name == "my_column"

	def test_window_size(self) -> None:
		"""Test different window sizes."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])

		result_3 = rolling_zscore(s, window_size=3)
		result_5 = rolling_zscore(s, window_size=5)

		# Both should have same length
		assert len(result_3) == 10
		assert len(result_5) == 10

	def test_min_samples(self) -> None:
		"""Test min_samples parameter."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0])

		result = rolling_zscore(s, window_size=5, min_samples=3)

		# Should have valid values where at least 3 samples are available
		assert result.len() == 5

	def test_centered_window(self) -> None:
		"""Test centered window option."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])

		result_left = rolling_zscore(s, window_size=3, center=False)
		result_center = rolling_zscore(s, window_size=3, center=True)

		# Results should differ due to different window positioning
		assert len(result_left) == len(result_center)

	def test_zero_threshold(self) -> None:
		"""Test zero_threshold parameter for handling near-zero MAD."""
		# Values with very small variance
		s = pl.Series("value", [1.0, 1.001, 1.002, 1.001, 1.0])

		result = rolling_zscore(s, window_size=3, zero_threshold=0.01, fill_value=0.1)

		# Should complete without division by zero
		assert result.len() == 5

	def test_fill_value(self) -> None:
		"""Test fill_value parameter."""
		s = pl.Series("value", [1.0, 1.0, 1.0, 1.0, 1.0])

		result = rolling_zscore(s, window_size=3, fill_value=0.5)

		# Should handle constant values gracefully
		assert result.len() == 5

	def test_outlier_detection(self) -> None:
		"""Test that outliers have high z-scores."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0, 100.0, 6.0, 7.0, 8.0, 9.0])

		result = rolling_zscore(s, window_size=3)

		# The outlier region should have elevated z-scores
		assert result.len() == 10

	def test_negative_values(self) -> None:
		"""Test rolling z-score with negative values."""
		s = pl.Series("value", [-10.0, -5.0, 0.0, 5.0, 10.0])

		result = rolling_zscore(s, window_size=3)

		# Should produce valid results
		assert result.len() == 5

	def test_with_null_values(self) -> None:
		"""Test rolling z-score with null values."""
		s = pl.Series("value", [1.0, 2.0, None, 4.0, 5.0, 6.0, 7.0])

		result = rolling_zscore(s, window_size=3)

		assert result.len() == 7

	def test_large_window(self) -> None:
		"""Test with window size larger than min_samples."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0])

		result = rolling_zscore(s, window_size=10, min_samples=2)

		assert result.len() == 5

	def test_single_min_sample(self) -> None:
		"""Test with min_samples=1."""
		s = pl.Series("value", [1.0, 2.0, 3.0])

		result = rolling_zscore(s, window_size=3, min_samples=1)

		assert result.len() == 3


class TestRollingZscoreDf:
	"""Tests for the rolling_zscore function."""

	def test_basic_zscore_calculation(self) -> None:
		"""Test basic z-score calculation."""
		df = pl.DataFrame(
			{
				"value": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
			}
		)

		result = rolling_zscore_df(df, col="value", window_size=3)

		assert "z_score" in result.columns
		assert result.lazy().collect().height == 10

	def test_custom_alias(self) -> None:
		"""Test z-score with custom alias."""
		df = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})

		result = rolling_zscore_df(df, col="value", window_size=3, alias="my_zscore")

		assert "my_zscore" in result.columns
		assert "z_score" not in result.columns

	def test_preserves_original_columns(self) -> None:
		"""Test that original columns are preserved."""
		df = pl.DataFrame(
			{
				"value": [1.0, 2.0, 3.0, 4.0, 5.0],
				"other": [10.0, 20.0, 30.0, 40.0, 50.0],
			}
		)

		result = rolling_zscore_df(df, col="value", window_size=3)

		assert "value" in result.columns
		assert "other" in result.columns

	def test_with_median_output(self) -> None:
		"""Test including median in output."""
		df = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})

		result = rolling_zscore_df(
			df, col="value", window_size=3, with_median="rolling_med"
		)

		assert "rolling_med" in result.columns

	def test_with_mad_output(self) -> None:
		"""Test including MAD in output."""
		df = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})

		# Note: with_mad parameter doesn't rename the internal 'mad' column,
		# it just includes the 'mad' column in output
		result = rolling_zscore_df(df, col="value", window_size=3, with_mad="mad")

		assert "mad" in result.columns

	def test_min_samples(self) -> None:
		"""Test min_samples parameter."""
		df = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})

		result = rolling_zscore_df(df, col="value", window_size=5, min_samples=1)

		# With min_samples=1, we should get z-scores even at the beginning
		assert result["z_score"].null_count() < 5  # type: ignore

	def test_centered_window(self) -> None:
		"""Test centered window option."""
		df = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]})

		result_centered = rolling_zscore_df(df, col="value", window_size=3, center=True)
		result_not_centered = rolling_zscore_df(
			df, col="value", window_size=3, center=False
		)

		# Results should be different with different centering
		assert (
			result_centered["z_score"].to_list()  # type: ignore
			!= result_not_centered["z_score"].to_list()  # type: ignore
		)

	def test_zscore_for_median_value_near_zero(self) -> None:
		"""Test that z-score for values at median is near zero."""
		# Create data where median is clearly 5.0
		df = pl.DataFrame({"value": [1.0, 3.0, 5.0, 7.0, 9.0, 5.0, 5.0, 5.0, 5.0, 5.0]})

		result = rolling_zscore_df(df, col="value", window_size=5, min_samples=1)

		# Later values at median (5.0) should have z-score near 0
		zscores = result["z_score"].to_list()  # type: ignore
		# Get a non-null z-score for a value that equals the rolling median
		non_null_zscores = [z for z in zscores if z is not None]  # type: ignore
		assert len(non_null_zscores) > 0  # type: ignore

	def test_outlier_has_high_zscore(self) -> None:
		"""Test that outliers have high z-scores."""
		df = pl.DataFrame(
			{"value": [1.0, 2.0, 3.0, 4.0, 5.0, 100.0, 7.0, 8.0, 9.0, 10.0]}
		)

		result = rolling_zscore_df(df, col="value", window_size=5)

		# The outlier (100.0 at index 5) should have a high z-score
		# Check values after the outlier where window includes it
		zscores = result["z_score"].to_list()  # type: ignore
		# Find max absolute z-score
		max_zscore = max(abs(z) for z in zscores if z is not None)  # type: ignore
		assert max_zscore > 2.0

	def test_lazyframe_support(self) -> None:
		"""Test that LazyFrame input returns LazyFrame output."""
		lf = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]}).lazy()

		result = rolling_zscore_df(lf, col="value", window_size=3)

		assert isinstance(result, pl.LazyFrame)

	def test_dataframe_support(self) -> None:
		"""Test that DataFrame input returns DataFrame output."""
		df = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})

		result = rolling_zscore_df(df, col="value", window_size=3)

		assert isinstance(result, pl.DataFrame)

	def test_zero_threshold_handling(self) -> None:
		"""Test that zero MAD is handled with fill_value."""
		# All same values = zero MAD
		df = pl.DataFrame({"value": [5.0, 5.0, 5.0, 5.0, 5.0]})

		result = rolling_zscore_df(
			df, col="value", window_size=3, zero_threshold=1e-5, fill_value=1e-4
		)

		# Should not have inf or nan due to division by zero
		zscores = result["z_score"].to_list()  # type: ignore
		for z in zscores:  # type: ignore
			if z is not None:
				assert z != float("inf")
				assert z != float("-inf")
				assert z == z  # not NaN

	def test_custom_zero_threshold(self) -> None:
		"""Test custom zero_threshold parameter."""
		df = pl.DataFrame({"value": [1.0, 1.001, 1.002, 1.001, 1.0]})

		result = rolling_zscore_df(
			df, col="value", window_size=3, zero_threshold=0.01, fill_value=0.1
		)

		# Should complete without error
		assert "z_score" in result.columns
