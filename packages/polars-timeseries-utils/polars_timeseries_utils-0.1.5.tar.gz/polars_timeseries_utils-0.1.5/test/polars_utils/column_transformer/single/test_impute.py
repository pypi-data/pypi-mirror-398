import polars as pl
import pytest

from polars_timeseries_utils.transformers.single import Imputer, RollingImputer
from polars_timeseries_utils.transformers.single.types import RollingStrategy, Strategy


class TestImputer:
	"""Tests for the Imputer class."""

	def test_init_with_value(self) -> None:
		"""Test initialization with a fill value."""
		imputer = Imputer(value=0)
		assert imputer.value == 0
		assert imputer.strategy is None

	def test_init_with_strategy(self) -> None:
		"""Test initialization with a strategy."""
		imputer = Imputer(strategy=Strategy.MEAN)
		assert imputer.value is None
		assert imputer.strategy == Strategy.MEAN

	def test_init_both_params_raises(self) -> None:
		"""Test that providing both value and strategy raises ValueError."""
		with pytest.raises(
			ValueError, match="Exactly one of value or strategy must be not None."
		):
			Imputer(value=0, strategy=Strategy.MEAN)

	def test_init_neither_param_raises(self) -> None:
		"""Test that providing neither value nor strategy raises ValueError."""
		with pytest.raises(
			ValueError, match="Exactly one of value or strategy must be not None."
		):
			Imputer()

	def test_fill_with_value(self, series_with_nulls: pl.Series) -> None:
		"""Test filling nulls with a constant value."""
		imputer = Imputer(value=999)
		result = imputer.fit_transform(series_with_nulls)

		assert result.null_count() == 0
		# Check that non-null values are preserved
		assert result[0] == 1.0
		assert result[2] == 3.0
		# Check that nulls are filled with 999
		assert result[1] == 999
		assert result[3] == 999

	def test_fill_with_mean_strategy(self, series_with_nulls: pl.Series) -> None:
		"""Test filling nulls with mean strategy."""
		imputer = Imputer(strategy=Strategy.MEAN)
		result = imputer.fit_transform(series_with_nulls)

		assert result.null_count() == 0
		# Mean of [1, 3, 5, 6, 8, 9, 10] = 42/7 = 6.0
		expected_mean = 6.0
		assert result[1] == expected_mean
		assert result[3] == expected_mean

	def test_fill_with_median_strategy(self, series_with_nulls: pl.Series) -> None:
		"""Test filling nulls with median strategy."""
		imputer = Imputer(strategy=Strategy.MEDIAN)
		result = imputer.fit_transform(series_with_nulls)

		assert result.null_count() == 0
		# Median of [1, 3, 5, 6, 8, 9, 10] = 6.0
		expected_median = 6.0
		assert result[1] == expected_median
		assert result[3] == expected_median

	def test_fill_with_min_strategy(self, series_with_nulls: pl.Series) -> None:
		"""Test filling nulls with min strategy."""
		imputer = Imputer(strategy=Strategy.MIN)
		result = imputer.fit_transform(series_with_nulls)

		assert result.null_count() == 0
		assert result[1] == 1.0
		assert result[3] == 1.0

	def test_fill_with_max_strategy(self, series_with_nulls: pl.Series) -> None:
		"""Test filling nulls with max strategy."""
		imputer = Imputer(strategy=Strategy.MAX)
		result = imputer.fit_transform(series_with_nulls)

		assert result.null_count() == 0
		assert result[1] == 10.0
		assert result[3] == 10.0

	def test_fill_with_zero_strategy(self, series_with_nulls: pl.Series) -> None:
		"""Test filling nulls with zero strategy."""
		imputer = Imputer(strategy=Strategy.ZERO)
		result = imputer.fit_transform(series_with_nulls)

		assert result.null_count() == 0
		assert result[1] == 0
		assert result[3] == 0

	def test_fill_with_one_strategy(self, series_with_nulls: pl.Series) -> None:
		"""Test filling nulls with one strategy."""
		imputer = Imputer(strategy=Strategy.ONE)
		result = imputer.fit_transform(series_with_nulls)

		assert result.null_count() == 0
		assert result[1] == 1
		assert result[3] == 1

	def test_fill_with_forward_strategy(self, series_with_nulls: pl.Series) -> None:
		"""Test filling nulls with forward fill strategy."""
		imputer = Imputer(strategy=Strategy.FORWARD)
		result = imputer.fit_transform(series_with_nulls)

		# [1.0, None, 3.0, None, 5.0, 6.0, None, 8.0, 9.0, 10.0]
		# Forward fill: [1.0, 1.0, 3.0, 3.0, 5.0, 6.0, 6.0, 8.0, 9.0, 10.0]
		assert result[1] == 1.0
		assert result[3] == 3.0
		assert result[6] == 6.0

	def test_fill_with_backward_strategy(self, series_with_nulls: pl.Series) -> None:
		"""Test filling nulls with backward fill strategy."""
		imputer = Imputer(strategy=Strategy.BACKWARD)
		result = imputer.fit_transform(series_with_nulls)

		# [1.0, None, 3.0, None, 5.0, 6.0, None, 8.0, 9.0, 10.0]
		# Backward fill: [1.0, 3.0, 3.0, 5.0, 5.0, 6.0, 8.0, 8.0, 9.0, 10.0]
		assert result[1] == 3.0
		assert result[3] == 5.0
		assert result[6] == 8.0

	def test_no_nulls_unchanged(self, series_no_nulls: pl.Series) -> None:
		"""Test that series without nulls is unchanged."""
		imputer = Imputer(strategy=Strategy.MEAN)
		result = imputer.fit_transform(series_no_nulls)

		assert result.to_list() == series_no_nulls.to_list()

	def test_preserves_dtype(self, series_with_nulls: pl.Series) -> None:
		"""Test that the original dtype is preserved."""
		imputer = Imputer(strategy=Strategy.MEAN)
		result = imputer.fit_transform(series_with_nulls)

		assert result.dtype == series_with_nulls.dtype

	def test_transform_without_fit_raises(self, series_with_nulls: pl.Series) -> None:
		"""Test that transform without fit raises for statistical strategies."""
		imputer = Imputer(strategy=Strategy.MEAN)
		with pytest.raises(ValueError, match="has not been fitted yet."):
			imputer.transform(series_with_nulls)

	def test_fit_then_transform(self, series_with_nulls: pl.Series) -> None:
		"""Test separate fit and transform calls."""
		imputer = Imputer(strategy=Strategy.MEAN)
		imputer.fit(series_with_nulls)
		result = imputer.transform(series_with_nulls)

		assert result.null_count() == 0


class TestRollingImputer:
	"""Tests for the RollingImputer class."""

	def test_init_defaults(self) -> None:
		"""Test default initialization."""
		imputer = RollingImputer(window_size=3)
		assert imputer.window_size == 3
		assert imputer.strategy == RollingStrategy.MEAN
		assert imputer.min_samples == 1
		assert imputer.center is False

	def test_rolling_mean_imputation(self, series_with_nulls: pl.Series) -> None:
		"""Test rolling mean imputation."""
		imputer = RollingImputer(window_size=3, strategy=RollingStrategy.MEAN)
		result = imputer.fit_transform(series_with_nulls)

		assert result.null_count() == 0
		assert len(result) == len(series_with_nulls)

	def test_rolling_median_imputation(self, series_with_nulls: pl.Series) -> None:
		"""Test rolling median imputation."""
		imputer = RollingImputer(window_size=3, strategy=RollingStrategy.MEDIAN)
		result = imputer.fit_transform(series_with_nulls)

		assert result.null_count() == 0
		assert len(result) == len(series_with_nulls)

	def test_rolling_min_imputation(self, series_with_nulls: pl.Series) -> None:
		"""Test rolling min imputation."""
		imputer = RollingImputer(window_size=3, strategy=RollingStrategy.MIN)
		result = imputer.fit_transform(series_with_nulls)

		assert result.null_count() == 0
		assert len(result) == len(series_with_nulls)

	def test_rolling_max_imputation(self, series_with_nulls: pl.Series) -> None:
		"""Test rolling max imputation."""
		imputer = RollingImputer(window_size=3, strategy=RollingStrategy.MAX)
		result = imputer.fit_transform(series_with_nulls)

		assert result.null_count() == 0
		assert len(result) == len(series_with_nulls)

	def test_edge_nulls(self, series_with_nulls_at_edges: pl.Series) -> None:
		"""Test imputation with nulls at edges."""
		imputer = RollingImputer(window_size=3, strategy=RollingStrategy.MEAN)
		result = imputer.fit_transform(series_with_nulls_at_edges)

		assert result.null_count() == 0
		assert len(result) == len(series_with_nulls_at_edges)

	def test_preserves_dtype(self, series_with_nulls: pl.Series) -> None:
		"""Test that the original dtype is preserved."""
		imputer = RollingImputer(window_size=3)
		result = imputer.fit_transform(series_with_nulls)

		assert result.dtype == series_with_nulls.dtype

	def test_centered_window(self, series_with_nulls: pl.Series) -> None:
		"""Test centered window imputation."""
		imputer = RollingImputer(window_size=3, center=True)
		result = imputer.fit_transform(series_with_nulls)

		assert result.null_count() == 0
		assert len(result) == len(series_with_nulls)
