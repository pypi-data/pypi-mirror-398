import polars as pl
import pytest

from polars_timeseries_utils.transformers.single import RollingSmoother, Smoother


class TestSmoother:
	"""Tests for the Smoother class."""

	def test_init_defaults(self) -> None:
		"""Test default initialization."""
		smoother = Smoother()
		assert smoother.max_zscore == 3.0
		assert smoother.zero_threshold == 1e-5
		assert smoother.fill_value == 1e-4

	def test_init_custom_params(self) -> None:
		"""Test custom initialization."""
		smoother = Smoother(max_zscore=2.0, zero_threshold=1e-6, fill_value=1e-5)
		assert smoother.max_zscore == 2.0
		assert smoother.zero_threshold == 1e-6
		assert smoother.fill_value == 1e-5

	def test_fit(self, series_with_outliers: pl.Series) -> None:
		"""Test fitting the smoother."""
		smoother = Smoother()
		smoother.fit(series_with_outliers)

		assert smoother.median is not None
		assert smoother.mad is not None

	def test_transform_reduces_outliers(self, series_with_outliers: pl.Series) -> None:
		"""Test that outliers are reduced after smoothing."""
		smoother = Smoother(max_zscore=2.0)
		result = smoother.fit_transform(series_with_outliers)

		# Original has extreme values 100.0 and -50.0
		# After smoothing, values should be closer to the median
		assert result.max() < 100.0  # type: ignore
		assert result.min() > -50.0  # type: ignore

	def test_normal_data_unchanged(self, series_normal_distribution: pl.Series) -> None:
		"""Test that normal data is mostly unchanged."""
		smoother = Smoother(max_zscore=3.0)
		result = smoother.fit_transform(series_normal_distribution)

		# Values should be close to original for normal distribution
		for i in range(len(result)):
			assert result[i] == pytest.approx(series_normal_distribution[i], abs=1.0)  # type: ignore

	def test_transform_without_fit_raises(
		self, series_with_outliers: pl.Series
	) -> None:
		"""Test that transform without fit raises."""
		smoother = Smoother()
		with pytest.raises(ValueError, match="has not been fitted yet."):
			smoother.transform(series_with_outliers)

	def test_preserves_dtype(self, series_with_outliers: pl.Series) -> None:
		"""Test that the original dtype is preserved."""
		smoother = Smoother()
		result = smoother.fit_transform(series_with_outliers)

		assert result.dtype == series_with_outliers.dtype

	def test_preserves_length(self, series_with_outliers: pl.Series) -> None:
		"""Test that the length is preserved."""
		smoother = Smoother()
		result = smoother.fit_transform(series_with_outliers)

		assert len(result) == len(series_with_outliers)


class TestRollingSmoother:
	"""Tests for the RollingSmoother class."""

	def test_init_defaults(self) -> None:
		"""Test default initialization."""
		smoother = RollingSmoother(window_size=5)
		assert smoother.window_size == 5
		assert smoother.min_samples == 1
		assert smoother.max_zscore == 3.0
		assert smoother.center is False

	def test_init_custom_params(self) -> None:
		"""Test custom initialization."""
		smoother = RollingSmoother(
			window_size=7,
			min_samples=3,
			max_zscore=2.0,
			center=True,
		)
		assert smoother.window_size == 7
		assert smoother.min_samples == 3
		assert smoother.max_zscore == 2.0
		assert smoother.center is True

	def test_transform_reduces_outliers(self, series_with_outliers: pl.Series) -> None:
		"""Test that rolling smoother reduces outliers."""
		smoother = RollingSmoother(window_size=5, max_zscore=2.0)
		result = smoother.fit_transform(series_with_outliers)

		# Check that extreme outliers are moderated
		assert result.max() < 100.0  # type: ignore
		assert result.min() > -50.0  # type: ignore

	def test_preserves_dtype(self, series_with_outliers: pl.Series) -> None:
		"""Test that the original dtype is preserved."""
		smoother = RollingSmoother(window_size=3)
		result = smoother.fit_transform(series_with_outliers)

		assert result.dtype == series_with_outliers.dtype

	def test_preserves_length(self, series_with_outliers: pl.Series) -> None:
		"""Test that the length is preserved."""
		smoother = RollingSmoother(window_size=3)
		result = smoother.fit_transform(series_with_outliers)

		assert len(result) == len(series_with_outliers)

	def test_centered_window(self, series_with_outliers: pl.Series) -> None:
		"""Test centered window smoothing."""
		smoother = RollingSmoother(window_size=5, center=True)
		result = smoother.fit_transform(series_with_outliers)

		assert len(result) == len(series_with_outliers)
		assert result.dtype == series_with_outliers.dtype

	def test_normal_data_mostly_unchanged(
		self, series_normal_distribution: pl.Series
	) -> None:
		"""Test that normal data is mostly unchanged."""
		smoother = RollingSmoother(window_size=3, max_zscore=3.0)
		result = smoother.fit_transform(series_normal_distribution)

		# Values should be close to original for normal distribution
		for i in range(len(result)):
			assert result[i] == pytest.approx(series_normal_distribution[i], abs=2.0)  # type: ignore
