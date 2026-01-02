import polars as pl
import polars.selectors as cs
import pytest

from polars_timeseries_utils.transformers.composable import (
	ColumnTransformerMetadata,
	MultiColumnTransformer,
)
from polars_timeseries_utils.transformers.single import Imputer
from polars_timeseries_utils.transformers.single.types import Strategy


class TestMultiColumnTransformer:
	"""Tests for the MultiColumnTransformer class."""

	def test_init(self) -> None:
		"""Test initialization."""
		transformers = [
			ColumnTransformerMetadata(
				name="imputer",
				columns=["col_a", "col_b"],
				transformer=Imputer(strategy=Strategy.MEAN),
			)
		]
		mct = MultiColumnTransformer(transformers)

		assert len(mct.transformers) == 1
		assert mct.is_fitted is False

	def test_init_no_transformers(self) -> None:
		"""Test initialization with no transformers."""
		with pytest.raises(
			ValueError,
			match=f"{MultiColumnTransformer.__name__} must have at"
			" least one transformer.",
		):
			MultiColumnTransformer([])

	def test_fit(self, df_multi_column: pl.DataFrame) -> None:
		"""Test fitting the transformer."""
		transformers = [
			ColumnTransformerMetadata(
				name="imputer",
				columns=["col_a", "col_b"],
				transformer=Imputer(strategy=Strategy.MEAN),
			)
		]
		mct = MultiColumnTransformer(transformers)
		mct.fit(df_multi_column)

		assert mct.is_fitted is True
		assert len(mct.col_to_transformer) == 2
		assert "col_a" in mct.col_to_transformer
		assert "col_b" in mct.col_to_transformer

	def test_transform_fills_nulls(self, df_multi_column: pl.DataFrame) -> None:
		"""Test that transform fills nulls in specified columns."""
		transformers = [
			ColumnTransformerMetadata(
				name="imputer",
				columns=["col_a", "col_b"],
				transformer=Imputer(strategy=Strategy.MEAN),
			)
		]
		mct = MultiColumnTransformer(transformers)
		result = mct.fit_transform(df_multi_column)

		# Check nulls are filled
		assert result["col_a"].null_count() == 0  # type: ignore
		assert result["col_b"].null_count() == 0  # type: ignore

	def test_transform_without_fit_raises(self, df_multi_column: pl.DataFrame) -> None:
		"""Test that transform without fit raises."""
		transformers = [
			ColumnTransformerMetadata(
				name="imputer",
				columns=["col_a"],
				transformer=Imputer(strategy=Strategy.MEAN),
			)
		]
		mct = MultiColumnTransformer(transformers)

		with pytest.raises(RuntimeError, match="must be fitted"):
			mct.transform(df_multi_column)

	def test_preserves_column_order(self, df_multi_column: pl.DataFrame) -> None:
		"""Test that column order is preserved."""
		transformers = [
			ColumnTransformerMetadata(
				name="imputer",
				columns=["col_a", "col_b"],
				transformer=Imputer(strategy=Strategy.MEAN),
			)
		]
		mct = MultiColumnTransformer(transformers)
		result = mct.fit_transform(df_multi_column)

		assert result.columns == df_multi_column.columns

	def test_preserves_shape(self, df_multi_column: pl.DataFrame) -> None:
		"""Test that shape is preserved."""
		transformers = [
			ColumnTransformerMetadata(
				name="imputer",
				columns=["col_a", "col_b"],
				transformer=Imputer(strategy=Strategy.MEAN),
			)
		]
		mct = MultiColumnTransformer(transformers)
		result = mct.fit_transform(df_multi_column)

		assert result.shape == df_multi_column.shape  # type: ignore

	def test_untransformed_columns_unchanged(
		self, df_multi_column: pl.DataFrame
	) -> None:
		"""Test that columns not in transformers are unchanged."""
		transformers = [
			ColumnTransformerMetadata(
				name="imputer",
				columns=["col_a"],
				transformer=Imputer(strategy=Strategy.MEAN),
			)
		]
		mct = MultiColumnTransformer(transformers)
		result = mct.fit_transform(df_multi_column)

		# col_c should be unchanged
		assert result["col_c"].to_list() == df_multi_column["col_c"].to_list()  # type: ignore

	def test_by_dtype_selection(self, df_multi_column: pl.DataFrame) -> None:
		"""Test selecting columns by dtype."""
		transformers = [
			ColumnTransformerMetadata(
				name="imputer",
				columns=[pl.Float64],
				transformer=Imputer(strategy=Strategy.MEAN),
			)
		]
		mct = MultiColumnTransformer(transformers)
		mct.fit(df_multi_column)

		# Should have transformers for all float columns
		float_cols = [
			c for c, dtype in df_multi_column.schema.items() if dtype == pl.Float64
		]
		for col in float_cols:
			assert col in mct.col_to_transformer

	def test_get_transformer(self, df_multi_column: pl.DataFrame) -> None:
		"""Test getting transformer for a column."""
		transformers = [
			ColumnTransformerMetadata(
				name="imputer",
				columns=["col_a"],
				transformer=Imputer(strategy=Strategy.MEAN),
			)
		]
		mct = MultiColumnTransformer(transformers)
		mct.fit(df_multi_column)

		tf = mct.get_transformer("col_a")
		assert tf is not None
		assert isinstance(tf, Imputer)

		tf_none = mct.get_transformer("nonexistent")
		assert tf_none is None

	def test_lazyframe_support(self, lf_multi_column: pl.LazyFrame) -> None:
		"""Test that LazyFrame is supported."""
		transformers = [
			ColumnTransformerMetadata(
				name="imputer",
				columns=["col_a", "col_b"],
				transformer=Imputer(strategy=Strategy.MEAN),
			)
		]
		mct = MultiColumnTransformer(transformers)
		result = mct.fit_transform(lf_multi_column)

		assert isinstance(result, pl.LazyFrame)

		# Collect and check nulls are filled
		collected = result.collect()
		assert collected["col_a"].null_count() == 0
		assert collected["col_b"].null_count() == 0


class TestColSelector:
	"""Tests for the MultiColumnTransformer.col_selector static method."""

	def test_col_selector_none_returns_all(self) -> None:
		"""Test that None columns returns cs.all() selector."""
		tf = ColumnTransformerMetadata(
			name="test",
			columns=None,
			transformer=Imputer(strategy=Strategy.MEAN),
		)
		selector = MultiColumnTransformer.col_selector(tf)

		df = pl.DataFrame({"a": [1], "b": [2], "c": [3]})
		selected = df.select(selector).columns
		assert selected == ["a", "b", "c"]

	def test_col_selector_with_expr(self) -> None:
		"""Test that pl.Expr is returned as-is."""
		expr = pl.col("col_a")
		tf = ColumnTransformerMetadata(
			name="test",
			columns=expr,
			transformer=Imputer(strategy=Strategy.MEAN),
		)
		selector = MultiColumnTransformer.col_selector(tf)

		assert selector is expr

	def test_col_selector_with_selector(self) -> None:
		"""Test that cs.Selector is returned as-is."""
		sel = cs.numeric()
		tf = ColumnTransformerMetadata(
			name="test",
			columns=sel,
			transformer=Imputer(strategy=Strategy.MEAN),
		)
		selector = MultiColumnTransformer.col_selector(tf)

		assert selector is sel

	def test_col_selector_with_string_list(self) -> None:
		"""Test that list[str] returns cs.by_name() selector."""
		tf = ColumnTransformerMetadata(
			name="test",
			columns=["col_a", "col_b"],
			transformer=Imputer(strategy=Strategy.MEAN),
		)
		selector = MultiColumnTransformer.col_selector(tf)

		# Should select only the named columns
		df = pl.DataFrame({"col_a": [1], "col_b": [2], "col_c": [3]})
		selected = df.select(selector).columns
		assert selected == ["col_a", "col_b"]

	def test_col_selector_with_dtype_list(self) -> None:
		"""Test that list[pl.DataType] returns cs.by_dtype() selector."""
		tf = ColumnTransformerMetadata(
			name="test",
			columns=[pl.Float64],
			transformer=Imputer(strategy=Strategy.MEAN),
		)
		selector = MultiColumnTransformer.col_selector(tf)

		# Should select only Float64 columns
		df = pl.DataFrame({"a": [1.0], "b": [2], "c": [3.0]}).cast(
			{"a": pl.Float64, "b": pl.Int64, "c": pl.Float64}
		)
		selected = df.select(selector).columns
		assert selected == ["a", "c"]

	def test_col_selector_with_dtype_class(self) -> None:
		"""Test that dtype classes (not instances) work."""
		tf = ColumnTransformerMetadata(
			name="test",
			columns=[pl.Int64, pl.Float64],
			transformer=Imputer(strategy=Strategy.MEAN),
		)
		selector = MultiColumnTransformer.col_selector(tf)

		df = pl.DataFrame({"a": [1.0], "b": [2], "c": ["x"]}).cast(
			{"a": pl.Float64, "b": pl.Int64}
		)
		selected = df.select(selector).columns
		assert set(selected) == {"a", "b"}

	def test_col_selector_with_mixed_dtype_instances_and_classes(self) -> None:
		"""Test that mixed dtype instances and classes work."""
		tf = ColumnTransformerMetadata(
			name="test",
			columns=[pl.Float64(), pl.Int64],  # instance and class
			transformer=Imputer(strategy=Strategy.MEAN),
		)
		selector = MultiColumnTransformer.col_selector(tf)

		df = pl.DataFrame({"a": [1.0], "b": [2], "c": ["x"]}).cast(
			{"a": pl.Float64, "b": pl.Int64}
		)
		selected = df.select(selector).columns
		assert set(selected) == {"a", "b"}

	def test_col_selector_invalid_type_raises(self) -> None:
		"""Test that invalid column types raise ValueError."""
		tf = ColumnTransformerMetadata(
			name="test",
			columns=[1, 2, 3],  # type: ignore
			transformer=Imputer(strategy=Strategy.MEAN),
		)

		with pytest.raises(
			ValueError,
			match="Transformer columns must be all list\\[str\\] \\|"
			" list\\[pl.DataType\\]",
		):
			MultiColumnTransformer.col_selector(tf)

	def test_col_selector_mixed_str_and_dtype_raises(self) -> None:
		"""Test that mixed str and dtype raises ValueError."""
		tf = ColumnTransformerMetadata(
			name="test",
			columns=["col_a", pl.Float64],  # type: ignore
			transformer=Imputer(strategy=Strategy.MEAN),
		)

		with pytest.raises(
			ValueError,
			match="Transformer columns must be all list\\[str\\] \\|"
			" list\\[pl.DataType\\]",
		):
			MultiColumnTransformer.col_selector(tf)
