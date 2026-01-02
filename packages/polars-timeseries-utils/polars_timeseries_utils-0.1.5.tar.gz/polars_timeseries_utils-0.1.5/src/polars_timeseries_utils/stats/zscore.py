import polars as pl

from ..transformers.single.types import RollingStrategy


def zscore(
	s: pl.Series,
) -> pl.Series:
	"""
	Calculate the median based z-score of a Polars Series.

	Args:
		s (pl.Series): The input Series.

	Returns:
		pl.Series: The Series with the z-score values.
	"""

	col = s.name

	temp_df = s.to_frame().select(
		((pl.col(col) - pl.col(col).median()) / pl.col(col).std())
	)

	return temp_df.select(pl.col(col)).to_series()


def zscore_df(
	df: pl.DataFrame | pl.LazyFrame,
	col: str,
	alias: str = "z_score",
	with_median: str | None = None,
	with_std: str | None = None,
) -> pl.DataFrame | pl.LazyFrame:
	"""
	Calculate the z-score of a Polars Series col. Can return median and std columns.

	Args:
		df (pl.DataFrame | pl.LazyFrame): The input DataFrame.
		col (str): The name of the column to calculate the z-score for.
		alias (str): The name of the output z-score column.
		with_median (str | None): If provided, include the median column with this name
			in the output.
		with_std (str | None): If provided, include the std column with this name in
			the output.

	Returns:
		pl.DataFrame | pl.LazyFrame: The DataFrame with the z-score column added
	"""

	med = with_median or "median"
	std = with_std or "std"

	cols = (
		df.collect_schema().names()
		+ [alias]
		+ ([with_median] if with_median else [])
		+ ([with_std] if with_std else [])
	)

	return (
		df.with_columns(pl.col(col).median().alias(med), pl.col(col).std().alias(std))
		.with_columns(((pl.col(col) - pl.col(med)) / pl.col(std)).alias(alias))
		.select(cols)
	)


def rolling_zscore(
	s: pl.Series,
	window_size: int,
	min_samples: int = 1,
	center: bool = False,
	zero_threshold: float = 1e-5,
	fill_value: float = 1e-4,
) -> pl.Series:
	"""
	Calculate the rolling z-score of a Polars Series.

	Args:
		s (pl.Series): The input Series.
		window_size (int): The size of the rolling window.
		min_samples (int): The minimum number of samples required in the window to
			compute the statistics.
		center (bool): Whether to set the labels at the center of the window.
		zero_threshold (float): The threshold below which MAD is considered zero.
		fill_value (float): The value to replace zero MADs with.

	Returns:
		pl.Series: The Series with the rolling z-score values.
	"""

	mad = "mad"
	med = "median"
	col = s.name

	temp_df = (
		s.to_frame()
		.with_columns(
			pl.col(col)
			.rolling_median(window_size, min_samples=min_samples, center=center)
			.alias(med)
		)
		.with_columns(
			(pl.col(col) - pl.col(med))
			.abs()
			.rolling_median(window_size, min_samples=min_samples, center=center)
			.alias(mad)
		)
		.with_columns(
			pl.when(pl.col(mad).is_between(-zero_threshold, zero_threshold))
			.then(fill_value)
			.otherwise(pl.col(mad))
		)
		.with_columns(
			((pl.col(col) - pl.col(med)) / (pl.col(mad) * 1.4826 + 1e-8)).alias(col)
		)
	)

	return temp_df.select(pl.col(col)).to_series()


def rolling_zscore_df(
	df: pl.DataFrame | pl.LazyFrame,
	col: str,
	window_size: int,
	min_samples: int = 1,
	center: bool = False,
	zero_threshold: float = 1e-5,
	fill_value: float = 1e-4,
	alias: str = "z_score",
	with_median: str | None = None,
	with_mad: str | None = None,
) -> pl.DataFrame | pl.LazyFrame:
	"""
	Calculate the rolling z-score of a Polars Series col. Can ret

	Args:
		df (pl.DataFrame | pl.LazyFrame): The input DataFrame.
		col (str): The name of the column to calculate the z-score for.
		window_size (int): The size of the rolling window.
		min_samples (int): The minimum number of samples required in the window to
			compute the statistics.
		center (bool): Whether to set the labels at the center of the window.
		zero_threshold (float): The threshold below which MAD is considered zero.
		fill_value (float): The value to replace zero MADs with.
		alias (str): The name of the output z-score column.
		with_median (str | None): If provided, include the rolling median column with
			this name in the output.
		with_mad (str | None): If provided, include the rolling MAD column with this
			name in the output.

	Returns:
		pl.DataFrame | pl.LazyFrame: The DataFrame with the rolling z-score column
			added.
	"""

	mad = "mad"
	cols = (
		df.collect_schema().names()
		+ [alias]
		+ ([with_median] if with_median else [])
		+ ([with_mad] if with_mad else [])
	)
	with_median = with_median if with_median else RollingStrategy.MEDIAN
	return (
		df.with_columns(
			pl.col(col)
			.rolling_median(window_size, min_samples=min_samples, center=center)
			.alias(with_median)
		)
		.with_columns(
			(pl.col(col) - pl.col(with_median))
			.abs()
			.rolling_median(window_size, min_samples=min_samples, center=center)
			.alias(mad)
		)
		.with_columns(
			pl.when(pl.col(mad).is_between(-zero_threshold, zero_threshold))
			.then(fill_value)
			.otherwise(pl.col(mad))
		)
		.with_columns(
			((pl.col(col) - pl.col(with_median)) / (pl.col(mad) * 1.4826 + 1e-8)).alias(
				alias
			)
		)
		.select(cols)
	)
