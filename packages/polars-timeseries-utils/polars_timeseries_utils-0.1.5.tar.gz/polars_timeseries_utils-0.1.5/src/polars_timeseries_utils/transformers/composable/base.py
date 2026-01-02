from abc import ABC, abstractmethod
from typing import Self

import polars as pl


class BaseMultiColumnTransformer(ABC):
	def __init__(self) -> None:
		self.is_fitted = False

	@abstractmethod
	def fit(self, df: pl.DataFrame | pl.LazyFrame) -> Self:
		"""
		Fit the transformer to the DataFrame.

		Args:
			df (pl.DataFrame | pl.LazyFrame): The input Polars DataFrame or LazyFrame.

		Returns:
			Self: The fitted transformer.
		"""

		...

	@abstractmethod
	def transform(self, df: pl.DataFrame | pl.LazyFrame) -> pl.DataFrame | pl.LazyFrame:
		"""
		Transform the DataFrame using the fitted transformer.

		Args:
			df (pl.DataFrame | pl.LazyFrame): The input Polars DataFrame or LazyFrame.

		Returns:
			pl.DataFrame | pl.LazyFrame: The transformed DataFrame or LazyFrame.
		"""

		...

	def fit_transform(
		self, df: pl.DataFrame | pl.LazyFrame
	) -> pl.DataFrame | pl.LazyFrame:
		"""
		Fit the transformer to the DataFrame and transform it.

		Args:
			df (pl.DataFrame | pl.LazyFrame): The input Polars DataFrame or LazyFrame.

		Returns:
			pl.DataFrame | pl.LazyFrame: The transformed DataFrame or LazyFrame.
		"""

		return self.fit(df).transform(df)
