import polars as pl
import pytest

from polars_timeseries_utils.transformers.composable import (
	ColumnTransformerMetadata,
	MultiColumnTransformer,
	MultiColumnTransformerMetadata,
	Pipeline,
)
from polars_timeseries_utils.transformers.single import Imputer, MinMaxScaler
from polars_timeseries_utils.transformers.single.types import Strategy


class TestPipeline:
	"""Tests for the Pipeline class."""

	def test_init(self) -> None:
		"""Test initialization."""
		step1 = MultiColumnTransformer(
			[
				ColumnTransformerMetadata(
					name="imputer",
					columns=["col_a"],
					transformer=Imputer(strategy=Strategy.MEAN),
				)
			]
		)
		steps = [MultiColumnTransformerMetadata(name="step1", transformer=step1)]
		pipeline = Pipeline(steps)

		assert len(pipeline.steps) == 1

	def test_single_step(self, df_multi_column: pl.DataFrame) -> None:
		"""Test pipeline with single step."""
		step1 = MultiColumnTransformer(
			[
				ColumnTransformerMetadata(
					name="imputer",
					columns=["col_a", "col_b"],
					transformer=Imputer(strategy=Strategy.MEAN),
				)
			]
		)
		steps = [MultiColumnTransformerMetadata(name="step1", transformer=step1)]
		pipeline = Pipeline(steps)
		result = pipeline.fit_transform(df_multi_column)

		assert result["col_a"].null_count() == 0  # type: ignore
		assert result["col_b"].null_count() == 0  # type: ignore

	def test_multi_step(self, df_multi_column: pl.DataFrame) -> None:
		"""Test pipeline with multiple steps."""
		step1 = MultiColumnTransformer(
			[
				ColumnTransformerMetadata(
					name="imputer",
					columns=["col_a", "col_b"],
					transformer=Imputer(strategy=Strategy.MEAN),
				)
			]
		)
		step2 = MultiColumnTransformer(
			[
				ColumnTransformerMetadata(
					name="scaler",
					columns=["col_c"],
					transformer=MinMaxScaler(),
				)
			]
		)
		steps = [
			MultiColumnTransformerMetadata(name="step1", transformer=step1),
			MultiColumnTransformerMetadata(name="step2", transformer=step2),
		]
		pipeline = Pipeline(steps)
		result = pipeline.fit_transform(df_multi_column)

		# Check imputation happened
		assert result["col_a"].null_count() == 0  # type: ignore
		assert result["col_b"].null_count() == 0  # type: ignore

		# Check scaling happened (col_c should be in [0, 1] range approximately)
		assert result["col_c"].min() >= -0.1  # type: ignore
		assert result["col_c"].max() <= 1.1  # type: ignore

	def test_preserves_shape(self, df_multi_column: pl.DataFrame) -> None:
		"""Test that shape is preserved through pipeline."""
		step1 = MultiColumnTransformer(
			[
				ColumnTransformerMetadata(
					name="imputer",
					columns=["col_a"],
					transformer=Imputer(strategy=Strategy.MEAN),
				)
			]
		)
		steps = [MultiColumnTransformerMetadata(name="step1", transformer=step1)]
		pipeline = Pipeline(steps)
		result = pipeline.fit_transform(df_multi_column)

		assert result.shape == df_multi_column.shape  # type: ignore

	def test_preserves_columns(self, df_multi_column: pl.DataFrame) -> None:
		"""Test that columns are preserved through pipeline."""
		step1 = MultiColumnTransformer(
			[
				ColumnTransformerMetadata(
					name="imputer",
					columns=["col_a"],
					transformer=Imputer(strategy=Strategy.MEAN),
				)
			]
		)
		steps = [MultiColumnTransformerMetadata(name="step1", transformer=step1)]
		pipeline = Pipeline(steps)
		result = pipeline.fit_transform(df_multi_column)

		assert result.columns == df_multi_column.columns

	def test_lazyframe_support(self, lf_multi_column: pl.LazyFrame) -> None:
		"""Test that LazyFrame is supported."""
		step1 = MultiColumnTransformer(
			[
				ColumnTransformerMetadata(
					name="imputer",
					columns=["col_a", "col_b"],
					transformer=Imputer(strategy=Strategy.MEAN),
				)
			]
		)
		steps = [MultiColumnTransformerMetadata(name="step1", transformer=step1)]
		pipeline = Pipeline(steps)
		result = pipeline.fit_transform(lf_multi_column)

		assert isinstance(result, pl.LazyFrame)

		collected = result.collect()
		assert collected["col_a"].null_count() == 0

	def test_empty_pipeline_raises(self) -> None:
		"""Test that empty pipeline raises ValueError."""
		with pytest.raises(ValueError, match="must have at least one step"):
			Pipeline([])

	def test_transform_without_fit_raises(self, df_multi_column: pl.DataFrame) -> None:
		"""Test that transform without fit raises."""
		step1 = MultiColumnTransformer(
			[
				ColumnTransformerMetadata(
					name="imputer",
					columns=["col_a"],
					transformer=Imputer(strategy=Strategy.MEAN),
				)
			]
		)
		steps = [MultiColumnTransformerMetadata(name="step1", transformer=step1)]
		pipeline = Pipeline(steps)

		with pytest.raises(RuntimeError, match="must be fitted"):
			pipeline.transform(df_multi_column)
