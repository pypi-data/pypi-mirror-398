from typing import Self, override

import polars as pl
from polars._typing import PythonLiteral

from ...stats import rolling_zscore_df
from .base import BaseColumnTransformer
from .types import RollingStrategy


class Smoother(BaseColumnTransformer):
	"""
	A class to smooth outliers in a Polars Series using the median and MAD approach.

	Attributes:
		max_zscore (float): The maximum z-score threshold to identify outliers.
	"""

	def __init__(
		self,
		max_zscore: float = 3.0,
		zero_threshold: float = 1e-5,
		fill_value: float = 1e-4,
	):
		"""
		Args:
			max_zscore (float): The maximum z-score threshold to identify outliers.
				Defaults to 3.0.
			zero_threshold (float): The threshold below which MAD is considered zero.
				Defaults to 1e-5.
			fill_value (float): The value to replace zero MADs with. Defaults to 1e-4.
		"""

		self.max_zscore = max_zscore
		self.zero_threshold = zero_threshold
		self.fill_value = fill_value
		self.median: PythonLiteral | None = None
		self.mad: PythonLiteral | None = None
		super().__init__()

	@override
	def fit(self, s: pl.Series) -> Self:
		self.median = s.median()
		mad = (s - self.median).abs().median()
		if mad < self.zero_threshold:  # type: ignore
			mad = self.fill_value
		self.mad = mad

		self.is_fitted = self.median is not None and mad is not None
		if not self.is_fitted:
			raise RuntimeError(
				f"{self.__class__.__name__} could not be fitted due to None median or"
				" mad values."
			)

		return self

	@override
	def transform(self, s: pl.Series) -> pl.Series:
		if not self.is_fitted:
			raise ValueError(f"{self.__class__.__name__} has not been fitted yet.")

		z_score = "z_score"
		temp_df = (
			s.to_frame()
			.with_columns(
				((pl.col(s.name) - self.median) / (self.mad * 1.4826 + 1e-8)).alias(  # type: ignore
					z_score
				)
			)
			.with_columns(
				pl.when(pl.col(z_score) >= self.max_zscore)
				.then(self.median + self.max_zscore * self.mad)  # type: ignore
				.when(pl.col(z_score) <= -self.max_zscore)
				.then(self.median - self.max_zscore * self.mad)  # type: ignore
				.otherwise(pl.col(s.name))
				.cast(s.dtype)
				.alias(s.name)
			)
		)
		return temp_df.select(s.name).to_series()


class RollingSmoother(BaseColumnTransformer):
	"""
	A class to smooth outliers in a Polars Series using a rolling median and MAD
	approach.

	Attributes:
		window_size (int): The size of the rolling window.
		min_samples (int): The minimum number of samples required in the window to
			compute the statistics.
		max_zscore (float): The maximum z-score threshold to identify outliers.
		center (bool): Whether to set the labels at the center of the window.
	"""

	def __init__(
		self,
		window_size: int,
		min_samples: int = 1,
		max_zscore: float = 3.0,
		zero_threshold: float = 1e-5,
		fill_value: float = 1e-4,
		center: bool = False,
	):
		"""
		Args:
			window_size (int): The size of the rolling window.
			min_samples (int | None): The minimum number of samples required in the
				window to compute the statistics. Defaults to 1.
			max_zscore (float): The maximum z-score threshold to identify outliers.
				Defaults to 3.0.
			zero_threshold (float): The threshold below which MAD is considered zero.
				Defaults to 1e-5.
			fill_value (float): The value to replace zero MADs with. Defaults to 1e-4.
			center (bool): Whether to set the labels at the center of the window.
				Default is False, because it is safe for time series data.
		"""

		self.window_size = window_size
		self.min_samples = min_samples or window_size
		self.max_zscore = max_zscore
		self.zero_threshold = zero_threshold
		self.fill_value = fill_value
		self.center = center
		self.is_fitted = True

	@override
	def fit(self, s: pl.Series) -> Self:
		"""
		Fit method for compatibility. No fitting is required for rolling smoothing.

		Args:
			s (pl.Series): The input series to fit.

		Returns:
			Self: The fitted smoother.
		"""

		self.is_fitted = True

		return self

	@override
	def transform(self, s: pl.Series) -> pl.Series:
		if not self.is_fitted:
			raise ValueError(f"{self.__class__.__name__} has not been fitted yet.")

		mad = "mad"
		z_score = "z_score"
		temp_df = rolling_zscore_df(
			df=pl.LazyFrame({s.name: s}),
			col=s.name,
			window_size=self.window_size,
			min_samples=self.min_samples,
			center=self.center,
			zero_threshold=self.zero_threshold,
			fill_value=self.fill_value,
			alias=z_score,
			with_median=RollingStrategy.MEDIAN,
			with_mad=mad,
		).with_columns(
			pl.when(pl.col(z_score) >= self.max_zscore)
			.then(pl.col(RollingStrategy.MEDIAN) + self.max_zscore * pl.col(mad))
			.when(pl.col(z_score) <= -self.max_zscore)
			.then(pl.col(RollingStrategy.MEDIAN) - self.max_zscore * pl.col(mad))
			.otherwise(pl.col(s.name))
			.cast(s.dtype)
			.alias(s.name)
		)

		return temp_df.select(s.name).lazy().collect().to_series()
