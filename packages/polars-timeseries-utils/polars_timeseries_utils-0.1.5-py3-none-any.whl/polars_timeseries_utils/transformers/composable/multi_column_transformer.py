from copy import deepcopy
from dataclasses import dataclass
from typing import Self, cast

import polars as pl
import polars.selectors as cs
from polars._typing import PolarsDataType

from ..single import BaseColumnTransformer
from .base import BaseMultiColumnTransformer


@dataclass
class ColumnTransformerMetadata:
	name: str
	transformer: BaseColumnTransformer
	columns: list[str] | list[PolarsDataType] | pl.Expr | cs.Selector | None = None


class MultiColumnTransformer(BaseMultiColumnTransformer):
	"""
	A simple column transformer for applying a sequence of transformations to a
	Polars DataFrame.

	Attributes:
		transformers (list[BaseColumnTransformer]): A list of column transformers to
			apply.
	"""

	def __init__(self, transformers: list[ColumnTransformerMetadata]) -> None:
		"""
		Initializes the ColumnTransformer with a list of transformers.

		Args:
			transformers (list[Transformer]): A list of column transformers to apply.
		"""

		if not transformers:
			raise ValueError(
				f"{self.__class__.__name__} must have at least one transformer."
			)

		self.transformers = transformers
		self.col_to_transformer: dict[str, BaseColumnTransformer] = {}
		super().__init__()

	def fit(self, df: pl.DataFrame | pl.LazyFrame) -> Self:
		"""
		Fits each transformer in the column transformer to the DataFrame.

		Args:
			df (pl.DataFrame | pl.LazyFrame): The input Polars DataFrame or LazyFrame.

		Returns:
			ColumnTransformer: The fitted column transformer.
		"""

		self.col_to_transformer = {
			col: deepcopy(transformer.transformer)
			for transformer in self.transformers
			for col in df.head(1)
			.select(self.col_selector(transformer))
			.collect_schema()
			.names()
		}

		_ = (
			df.lazy()
			.collect()
			.with_columns(
				[
					pl.col(col).map_batches(tf.fit_transform)
					for col, tf in self.col_to_transformer.items()
				]
			)
		)

		self.is_fitted = True

		return self

	def transform(self, df: pl.DataFrame | pl.LazyFrame) -> pl.DataFrame | pl.LazyFrame:
		"""
		Applies each fitted transformer in the column transformer to the DataFrame.

		Args:
			df (pl.DataFrame | pl.LazyFrame): The input Polars DataFrame or LazyFrame.

		Returns:
			pl.DataFrame | pl.LazyFrame: The transformed DataFrame or LazyFrame.
		"""

		if not self.is_fitted:
			raise RuntimeError(
				"The column transformer must be fitted before calling transform()."
			)

		cols = df.collect_schema().names()

		df = df.with_columns(cs.numeric().cast(pl.Float64)).with_columns(
			[
				pl.col(col)
				.map_batches(tf.transform, return_dtype=pl.self_dtype())
				.alias(col)
				for col, tf in self.col_to_transformer.items()
			]
		)

		return df.select(cols)

	def fit_transform(
		self, df: pl.DataFrame | pl.LazyFrame
	) -> pl.DataFrame | pl.LazyFrame:
		"""
		Fits and transforms the DataFrame using the column transformer.

		Args:
			df (pl.DataFrame | pl.LazyFrame): The input Polars DataFrame or LazyFrame.

		Returns:
			pl.DataFrame | pl.LazyFrame: The fitted and transformed DataFrame or
				LazyFrame.
		"""

		return self.fit(df).transform(df)

	def get_transformer(self, col: str) -> BaseColumnTransformer | None:
		"""
		Gets the transformer associated with a specific column.

		Args:
			col (str): The column name.
		"""

		return self.col_to_transformer.get(col)

	@staticmethod
	def col_selector(tf: ColumnTransformerMetadata) -> pl.Expr | cs.Selector:
		if tf.columns is None:
			return cs.all()
		elif isinstance(tf.columns, (pl.Expr, cs.Selector)):
			return tf.columns
		elif all(isinstance(col, str) for col in tf.columns):
			return cs.by_name(cast(list[str], tf.columns))
		elif all(
			isinstance(col, pl.DataType)
			or (isinstance(col, type) and issubclass(col, pl.DataType))
			for col in tf.columns
		):
			dtypes = [col() if isinstance(col, type) else col for col in tf.columns]
			return cs.by_dtype(dtypes)  # type: ignore
		else:
			raise ValueError(
				"Transformer columns must be all list[str] | list[pl.DataType]"
				" | pl.Expr | cs.Selector | None."
			)
