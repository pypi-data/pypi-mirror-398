from abc import ABC, abstractmethod
from typing import Self

import polars as pl


class BaseColumnTransformer(ABC):
	"""
	Base class for all column transformers.
	"""

	def __init__(self) -> None:
		self.is_fitted = False

	@abstractmethod
	def fit(self, s: pl.Series) -> Self:
		"""
		Fit the imputer by computing the fill value from training data.

		Args:
			s (pl.Series): The input series to fit.

		Returns:
			Self: The fitted imputer.
		"""

		...

	@abstractmethod
	def transform(self, s: pl.Series) -> pl.Series:
		"""
		Transform the data using the fitted transformer.

		Args:
			s (pl.Series): The input series to transform.

		Returns:
			pl.Series: The transformed series.
		"""

		...

	def fit_transform(self, s: pl.Series) -> pl.Series:
		"""
		Fit the transformer to the data and transform it.

		Args:
			s (pl.Series): The input series to fit and transform.

		Returns:
			pl.Series: The transformed series.
		"""

		return self.fit(s).transform(s)


class InverseTransformerMixin(ABC):
	"""Base class for transformers that reverse transformations."""

	def __init__(self) -> None:
		self.is_fitted = False

	@abstractmethod
	def inverse_transform(self, s: pl.Series) -> pl.Series:
		"""
		Inverse transform the data back to original scale.

		Args:
			s (pl.Series): The transformed series to reverse transform.

		Returns:
			pl.Series: The reverse transformed series.
		"""

		...
