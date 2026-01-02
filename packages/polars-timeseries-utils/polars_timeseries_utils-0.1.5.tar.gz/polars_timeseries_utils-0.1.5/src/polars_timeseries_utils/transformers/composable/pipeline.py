from dataclasses import dataclass
from typing import Self, override

import polars as pl

from .base import BaseMultiColumnTransformer


@dataclass
class MultiColumnTransformerMetadata:
	name: str
	transformer: BaseMultiColumnTransformer


class Pipeline(BaseMultiColumnTransformer):
	def __init__(self, steps: list[MultiColumnTransformerMetadata]) -> None:
		if not steps:
			raise ValueError(f"{self.__class__.__name__} must have at least one step.")

		self.steps = steps
		super().__init__()

	@override
	def fit(self, df: pl.DataFrame | pl.LazyFrame) -> Self:
		df = df.lazy().collect()
		for step in self.steps:
			df = step.transformer.fit_transform(df)

		self.is_fitted = all(step.transformer.is_fitted for step in self.steps)
		if not self.is_fitted:
			raise RuntimeError(
				f"{self.__class__.__name__} fitting failed; not all steps are fitted."
			)

		return self

	@override
	def transform(self, df: pl.DataFrame | pl.LazyFrame) -> pl.DataFrame | pl.LazyFrame:
		if not self.is_fitted:
			raise RuntimeError(
				f"{self.__class__.__name__} must be fitted before calling transform."
			)

		for step in self.steps:
			df = step.transformer.transform(df)
		return df
