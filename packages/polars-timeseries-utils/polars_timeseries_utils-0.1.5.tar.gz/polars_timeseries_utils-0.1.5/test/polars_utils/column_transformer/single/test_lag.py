import polars as pl

from polars_timeseries_utils.transformers.single import (
	LagTransformer,
)


class TestLagTransformer:
	"""Tests for LagTransformer."""

	def test_single_lag(self) -> None:
		"""Test single lag transformation."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0])
		transformer = LagTransformer(lags=1)

		result = transformer.transform(s)

		assert result[0] is None
		assert result[1] == 1.0
		assert result[2] == 2.0
		assert result[3] == 3.0
		assert result[4] == 4.0

	def test_negative_lag(self) -> None:
		"""Test negative lag (future values)."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0])
		transformer = LagTransformer(lags=-1)

		result = transformer.transform(s)

		assert result[0] == 2.0
		assert result[1] == 3.0
		assert result[4] is None

	def test_fill_value(self) -> None:
		"""Test fill_value parameter."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0])
		transformer = LagTransformer(lags=1, fill_value=0.0)

		result = transformer.transform(s)

		assert result[0] == 0.0
		assert result[1] == 1.0

	def test_fit_transform(self) -> None:
		"""Test fit_transform convenience method."""
		s = pl.Series("value", [1.0, 2.0, 3.0, 4.0, 5.0])
		transformer = LagTransformer(lags=1)

		result = transformer.fit_transform(s)

		assert result[0] is None
		assert result[1] == 1.0
