import polars as pl
import pytest

from polars_timeseries_utils.transformers.single import (
	MinMaxScaler,
	RobustScaler,
	StandardScaler,
)


class TestMinMaxScaler:
	"""Tests for the MinMaxScaler class."""

	def test_init(self) -> None:
		"""Test initialization."""
		scaler = MinMaxScaler()
		assert scaler.min is None
		assert scaler.max is None

	def test_fit(self, series_for_scaling: pl.Series) -> None:
		"""Test fitting the scaler."""
		scaler = MinMaxScaler()
		scaler.fit(series_for_scaling)

		assert scaler.min == 0.0
		assert scaler.max == 100.0

	def test_transform_scales_to_0_1(self, series_for_scaling: pl.Series) -> None:
		"""Test that values are scaled to [0, 1] range."""
		scaler = MinMaxScaler()
		result = scaler.fit_transform(series_for_scaling)

		# [0, 25, 50, 75, 100] -> [0.0, 0.25, 0.5, 0.75, 1.0] (approximately)
		assert result[0] == pytest.approx(0.0, abs=0.01)  # type: ignore
		assert result[2] == pytest.approx(0.5, abs=0.01)  # type: ignore
		assert result[4] == pytest.approx(1.0, abs=0.01)  # type: ignore

	def test_transform_negative_values(
		self, series_with_negative_values: pl.Series
	) -> None:
		"""Test scaling with negative values."""
		scaler = MinMaxScaler()
		result = scaler.fit_transform(series_with_negative_values)

		# [-50, -25, 0, 25, 50] -> should scale to approximately [0, 0.25, 0.5, 0.75, 1]
		assert result[0] == pytest.approx(0.0, abs=0.01)  # type: ignore
		assert result[2] == pytest.approx(0.5, abs=0.01)  # type: ignore
		assert result[4] == pytest.approx(1.0, abs=0.01)  # type: ignore

	def test_transform_without_fit_raises(self, series_for_scaling: pl.Series) -> None:
		"""Test that transform without fit raises."""
		scaler = MinMaxScaler()
		with pytest.raises(ValueError, match="has not been fitted"):
			scaler.transform(series_for_scaling)

	def test_preserves_dtype(self, series_for_scaling: pl.Series) -> None:
		"""Test that the original dtype is preserved."""
		scaler = MinMaxScaler()
		result = scaler.fit_transform(series_for_scaling)

		assert result.dtype == series_for_scaling.dtype

	def test_separate_fit_transform(self, series_for_scaling: pl.Series) -> None:
		"""Test separate fit and transform calls."""
		scaler = MinMaxScaler()
		scaler.fit(series_for_scaling)
		result = scaler.transform(series_for_scaling)

		assert result[0] == pytest.approx(0.0, abs=0.01)  # type: ignore
		assert result[4] == pytest.approx(1.0, abs=0.01)  # type: ignore

	def test_transform_new_data(self, series_for_scaling: pl.Series) -> None:
		"""Test transforming new data with fitted scaler."""
		scaler = MinMaxScaler()
		scaler.fit(series_for_scaling)

		# New data with same scale
		new_series = pl.Series("value", [50.0, 75.0])
		result = scaler.transform(new_series)

		assert result[0] == pytest.approx(0.5, abs=0.01)  # type: ignore
		assert result[1] == pytest.approx(0.75, abs=0.01)  # type: ignore

	def test_inverse_transform_roundtrip(self) -> None:
		"""Test that inverse_transform reverses transform."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0])
		scaler = MinMaxScaler()
		scaler.fit(s)

		transformed = scaler.transform(s)
		inversed = scaler.inverse_transform(transformed)

		# Check values are close to original
		for orig, inv in zip(s.to_list(), inversed.to_list()):
			assert abs(orig - inv) < 1e-6

	def test_inverse_transform_preserves_nulls(self) -> None:
		"""Test that nulls are preserved through inverse transform."""
		s = pl.Series("value", [1.0, None, 3.0, None, 5.0])
		scaler = MinMaxScaler()
		scaler.fit(s)

		transformed = scaler.transform(s)
		inversed = scaler.inverse_transform(transformed)

		assert inversed.null_count() == 2
		assert inversed[1] is None
		assert inversed[3] is None

	def test_inverse_transform_not_fitted_raises(self) -> None:
		"""Test that inverse_transform raises if not fitted."""
		s = pl.Series("value", [1.0, 2.0, 3.0])
		scaler = MinMaxScaler()

		with pytest.raises(ValueError, match="has not been fitted"):
			scaler.inverse_transform(s)


class TestStandardScaler:
	"""Tests for the StandardScaler class."""

	def test_init(self) -> None:
		"""Test initialization."""
		scaler = StandardScaler()
		assert scaler.mean is None
		assert scaler.std is None

	def test_fit(self, series_for_scaling: pl.Series) -> None:
		"""Test fitting the scaler."""
		scaler = StandardScaler()
		scaler.fit(series_for_scaling)

		# [0, 25, 50, 75, 100] -> mean = 50
		assert scaler.mean == 50.0
		assert scaler.std is not None
		assert scaler.std > 0  # type: ignore

	def test_transform_centers_mean(self, series_for_scaling: pl.Series) -> None:
		"""Test that mean is approximately 0 after transform."""
		scaler = StandardScaler()
		result = scaler.fit_transform(series_for_scaling)

		# Mean should be approximately 0
		assert result.mean() == pytest.approx(0.0, abs=0.01)  # type: ignore

	def test_transform_without_fit_raises(self, series_for_scaling: pl.Series) -> None:
		"""Test that transform without fit raises."""
		scaler = StandardScaler()
		with pytest.raises(ValueError, match="has not been fitted"):
			scaler.transform(series_for_scaling)

	def test_preserves_dtype(self, series_for_scaling: pl.Series) -> None:
		"""Test that the original dtype is preserved."""
		scaler = StandardScaler()
		result = scaler.fit_transform(series_for_scaling)

		assert result.dtype == series_for_scaling.dtype

	def test_separate_fit_transform(self, series_for_scaling: pl.Series) -> None:
		"""Test separate fit and transform calls."""
		scaler = StandardScaler()
		scaler.fit(series_for_scaling)
		result = scaler.transform(series_for_scaling)

		assert result.mean() == pytest.approx(0.0, abs=0.01)  # type: ignore

	def test_transform_new_data(self, series_for_scaling: pl.Series) -> None:
		"""Test transforming new data with fitted scaler."""
		scaler = StandardScaler()
		scaler.fit(series_for_scaling)

		# Transform the mean value should give approximately 0
		new_series = pl.Series("value", [50.0])
		result = scaler.transform(new_series)

		assert result[0] == pytest.approx(0.0, abs=0.01)  # type: ignore

	def test_inverse_transform_roundtrip(self) -> None:
		"""Test that inverse_transform reverses transform."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0])
		scaler = StandardScaler()
		scaler.fit(s)

		transformed = scaler.transform(s)
		inversed = scaler.inverse_transform(transformed)

		# Check values are close to original
		for orig, inv in zip(s.to_list(), inversed.to_list()):
			assert abs(orig - inv) < 1e-6

	def test_inverse_transform_not_fitted_raises(self) -> None:
		"""Test that inverse_transform raises if not fitted."""
		s = pl.Series("value", [1.0, 2.0, 3.0])
		scaler = StandardScaler()

		with pytest.raises(ValueError, match="has not been fitted"):
			scaler.inverse_transform(s)

	def test_transform_preserves_nulls(self) -> None:
		"""Test that nulls are preserved through transform."""
		s = pl.Series("value", [1.0, None, 3.0, None, 5.0])
		scaler = StandardScaler()
		scaler.fit(s)

		transformed = scaler.transform(s)

		assert transformed.null_count() == 2
		assert transformed[1] is None
		assert transformed[3] is None


class TestRobustScaler:
	"""Tests for RobustScaler."""

	def test_fit(self) -> None:
		"""Test fitting the scaler."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0, 100.0])  # 100 is outlier
		scaler = RobustScaler()
		scaler.fit(s)

		assert scaler.is_fitted
		assert scaler.median is not None
		assert scaler.iqr is not None

	def test_transform_robust_to_outliers(self) -> None:
		"""Test that RobustScaler is less affected by outliers than StandardScaler."""
		# Data with outlier
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0, 100.0])

		robust = RobustScaler()
		standard = StandardScaler()

		robust.fit(s)
		standard.fit(s)

		# Transform a normal value (3.0 which is close to median)
		test_s = pl.Series("value", [3.0])
		robust_result = robust.transform(test_s)[0]
		standard_result = standard.transform(test_s)[0]

		# RobustScaler should give a value closer to 0 for median-like values
		assert abs(robust_result) < abs(standard_result)

	def test_inverse_transform_roundtrip(self) -> None:
		"""Test that inverse_transform reverses transform."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0])
		scaler = RobustScaler()
		scaler.fit(s)

		transformed = scaler.transform(s)
		inversed = scaler.inverse_transform(transformed)

		# Check values are close to original
		for orig, inv in zip(s.to_list(), inversed.to_list()):
			assert abs(orig - inv) < 1e-6

	def test_custom_quantile_range(self) -> None:
		"""Test RobustScaler with custom quantile range."""
		s = pl.Series("value", list(range(100)))
		scaler = RobustScaler(q_min=0.1, q_max=0.9)
		scaler.fit(s)

		assert scaler.is_fitted
		# Q10 should be ~10, Q90 should be ~90
		assert scaler.q_min_val is not None
		assert scaler.q_max_val is not None

	def test_transform_preserves_nulls(self) -> None:
		"""Test that nulls are preserved."""
		s = pl.Series("value", [1.0, None, 3.0, None, 5.0])
		scaler = RobustScaler()
		scaler.fit(s)

		transformed = scaler.transform(s)
		assert transformed.null_count() == 2

	def test_inverse_transform_not_fitted_raises(self) -> None:
		"""Test that inverse_transform raises if not fitted."""
		s = pl.Series("value", [1.0, 2.0, 3.0])
		scaler = RobustScaler()

		with pytest.raises(ValueError, match="has not been fitted"):
			scaler.inverse_transform(s)

	def test_transform_without_fit_raises(self) -> None:
		"""Test that transform without fit raises."""
		s = pl.Series("value", [1.0, 2.0, 3.0])
		scaler = RobustScaler()

		with pytest.raises(ValueError, match="has not been fitted"):
			scaler.transform(s)
