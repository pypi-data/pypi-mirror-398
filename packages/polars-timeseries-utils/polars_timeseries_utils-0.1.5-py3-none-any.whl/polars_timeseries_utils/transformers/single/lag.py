from typing import Self, override

import polars as pl

from .base import BaseColumnTransformer


class LagTransformer(BaseColumnTransformer):
	"""
	Creates lag features from a time series.

	This transformer shifts the series by specified lag periods, useful for
	creating features for time series forecasting models.

	Attributes:
		lags (list[int]): The lag periods to create (e.g., [1, 2, 3] for t-1, t-2, t-3).
		fill_value: The value to fill for positions where lag is not available.
	"""

	def __init__(
		self,
		lags: list[int] | int = 1,
		fill_value: float | None = None,
	):
		"""
		Initializes the LagTransformer.

		Args:
			lags: Single lag value or list of lag values. Positive values shift
				backward (past values), negative values shift forward (future values).
			fill_value: Value to fill for positions where lag creates nulls.
				If None, nulls are preserved.
		"""

		self.lags = [lags] if isinstance(lags, int) else lags
		self.fill_value = fill_value
		super().__init__()
		self.is_fitted = True

	@override
	def fit(self, s: pl.Series) -> Self:
		"""
		Fit method for compatibility. No fitting is required for lag transformation.

		Args:
			s (pl.Series): The input series to fit.

		Returns:
			Self: The fitted transformer.
		"""

		self.is_fitted = True
		return self

	@override
	def transform(self, s: pl.Series) -> pl.Series:
		"""
		Transform the series by applying the first lag only.

		For multiple lags, use transform_multi() which returns a DataFrame.

		Args:
			s (pl.Series): The input series to transform.

		Returns:
			pl.Series: The lagged series (using first lag value).
		"""

		if not self.is_fitted:
			raise ValueError(f"{self.__class__.__name__} has not been fitted yet.")

		lag = self.lags[0]
		result = s.shift(lag)

		if self.fill_value is not None:
			result = result.fill_null(self.fill_value)

		return result
