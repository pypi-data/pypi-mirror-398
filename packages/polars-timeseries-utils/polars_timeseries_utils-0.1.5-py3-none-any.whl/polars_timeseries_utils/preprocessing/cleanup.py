import polars as pl
import polars.selectors as cs

from ..transformers.single import RollingImputer, RollingSmoother


def clean_timeseries_df(
	df: pl.DataFrame | pl.LazyFrame,
	ts_col: str,
	window_size: int = 5,
	max_zscore: float = 3.0,
	round: int = 2,
) -> pl.DataFrame | pl.LazyFrame:
	"""
	Cleans the time series DataFrame by sorting, removing duplicates, and handling
	missing values.

	Args:
		df (pl.DataFrame | pl.LazyFrame): The input time series DataFrame.

	Returns:
		pl.DataFrame | pl.LazyFrame: The cleaned time series DataFrame.
	"""

	original_cols = df.collect_schema().names()
	imputer = RollingImputer(window_size=window_size, min_samples=1, center=False)
	smoother = RollingSmoother(
		window_size=window_size, min_samples=1, max_zscore=max_zscore, center=False
	)

	return (
		df.sort(ts_col, descending=False)
		.unique(subset=[ts_col])
		.with_columns(
			cs.numeric().map_batches(
				imputer.fit_transform, return_dtype=pl.self_dtype()
			)
		)
		.with_columns(
			cs.numeric()
			.map_batches(smoother.fit_transform, return_dtype=pl.self_dtype())
			.round(round)
		)
		.select(original_cols)
	)
