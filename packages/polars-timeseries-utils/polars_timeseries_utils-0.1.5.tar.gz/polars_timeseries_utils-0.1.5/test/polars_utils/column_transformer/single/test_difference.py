import polars as pl
import pytest

from polars_timeseries_utils.transformers.single import (
	DiffTransformer,
)


class TestDiffTransformer:
	"""Tests for DiffTransformer."""

	def test_first_order_diff(self) -> None:
		"""Test first-order differencing."""
		s = pl.Series("value", [1.0, 3.0, 6.0, 10.0, 15.0])
		transformer = DiffTransformer(order=1)

		result = transformer.fit_transform(s)

		assert result[0] is None
		assert result[1] == 2.0  # 3 - 1
		assert result[2] == 3.0  # 6 - 3
		assert result[3] == 4.0  # 10 - 6
		assert result[4] == 5.0  # 15 - 10

	def test_second_order_diff(self) -> None:
		"""Test second-order differencing."""
		s = pl.Series("value", [1.0, 3.0, 6.0, 10.0, 15.0])
		transformer = DiffTransformer(order=2)

		result = transformer.fit_transform(s)

		# First diff: [None, 2, 3, 4, 5]
		# Second diff: [None, None, 1, 1, 1]
		assert result[0] is None
		assert result[1] is None
		assert result[2] == 1.0
		assert result[3] == 1.0
		assert result[4] == 1.0

	def test_seasonal_diff(self) -> None:
		"""Test seasonal differencing with periods > 1."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
		transformer = DiffTransformer(order=1, periods=2)

		result = transformer.fit_transform(s)

		assert result[0] is None
		assert result[1] is None
		assert result[2] == 2.0  # 3 - 1
		assert result[3] == 2.0  # 4 - 2

	def test_invalid_order_raises(self) -> None:
		"""Test that invalid order raises ValueError."""
		with pytest.raises(ValueError, match="Order must be at least 1"):
			DiffTransformer(order=0)

	def test_invalid_periods_raises(self) -> None:
		"""Test that invalid periods raises ValueError."""
		with pytest.raises(ValueError, match="Periods must be at least 1"):
			DiffTransformer(periods=0)

	def test_not_fitted_raises(self) -> None:
		"""Test that transform without fit raises."""
		s = pl.Series("value", [1.0, 2.0, 3.0])
		transformer = DiffTransformer()
		transformer.is_fitted = False

		with pytest.raises(ValueError, match="has not been fitted"):
			transformer.transform(s)
