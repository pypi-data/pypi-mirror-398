from typing import Any, Self, override

import polars as pl
from polars._typing import PythonLiteral

from .base import BaseColumnTransformer
from .types import RollingStrategy, Strategy


class Imputer(BaseColumnTransformer):
	"""
	Simple imputer for handling missing values in a Polars Series.

	Attributes:
		value: The value to replace missing values with.
		strategy: The imputation strategy to use.
		fitted_value: The computed value during fit (for statistical strategies).
	"""

	def __init__(
		self,
		value: Any | None = None,
		strategy: Strategy | None = None,
	):
		"""
		Initialize the imputer with a value or strategy.

		Args:
			value: The value to replace missing values with. If provided, 'strategy'
				must be None.
			strategy: The imputation strategy to use. If provided, 'value' must be None.
		"""

		if value is not None and strategy is not None:
			raise ValueError("Exactly one of value or strategy must be not None.")
		elif value is None and strategy is None:
			raise ValueError("Exactly one of value or strategy must be not None.")
		self.strategy = strategy
		self.value = value
		self.fitted_value: PythonLiteral | None = None
		super().__init__()

	@override
	def fit(self, s: pl.Series) -> Self:
		match self.strategy:
			case None | Strategy.FORWARD | Strategy.BACKWARD:
				self.fitted_value = None
			case Strategy.MEDIAN:
				self.fitted_value = s.median()
			case Strategy.MEAN:
				self.fitted_value = s.mean()
			case Strategy.MIN:
				self.fitted_value = s.min()
			case Strategy.MAX:
				self.fitted_value = s.max()
			case Strategy.ZERO:
				if s.dtype == pl.String or s.dtype == pl.Categorical:
					self.fitted_value = "0"
				else:
					self.fitted_value = 0
			case Strategy.ONE:
				if s.dtype == pl.String or s.dtype == pl.Categorical:
					self.fitted_value = "1"
				else:
					self.fitted_value = 1

		self.is_fitted = any(
			[
				(
					self.fitted_value is None
					and self.strategy in [Strategy.FORWARD, Strategy.BACKWARD, None]
				),
				(self.value is not None),
				(
					self.fitted_value is not None
					and self.strategy not in [Strategy.FORWARD, Strategy.BACKWARD, None]
				),
			]
		)
		if not self.is_fitted:
			raise RuntimeError(
				f"{self.__class__.__name__} could not be fitted with strategy"
				f" {self.strategy}."
			)

		return self

	@override
	def transform(self, s: pl.Series) -> pl.Series:
		if not self.is_fitted:
			raise ValueError(f"{self.__class__.__name__} has not been fitted yet.")

		if self.value is not None:
			fill_val = self.value
			temp_df = s.to_frame().with_columns(
				pl.col(s.name).fill_null(value=fill_val)
			)
		elif self.strategy in [Strategy.FORWARD, Strategy.BACKWARD]:
			temp_df = s.to_frame().with_columns(
				pl.col(s.name).fill_null(strategy=self.strategy)  # type: ignore
			)
		else:
			if self.fitted_value is None:
				raise ValueError(f"{self.__class__.__name__} has not been fitted yet.")
			temp_df = s.to_frame().with_columns(
				pl.col(s.name).fill_null(value=self.fitted_value)
			)

		return temp_df.select(pl.col(s.name).cast(s.dtype)).to_series()


class RollingImputer(BaseColumnTransformer):
	"""
	Impute missing values using rolling statistics.

	Attributes:
		strategy (Literal): The rolling statistic to use ('rolling_min', 'rolling_max',
			'rolling_mean', 'rolling_median').
		window_size (int): The size of the rolling window.
		weights (list[float] | None): The weights for the rolling mean. Only used if
			strategy is 'rolling_mean'.
		min_samples (int | None): The minimum number of samples required in the window
			to compute the statistic.
			If None, it defaults to window_size.
		center (bool): Whether to set the labels at the center of the window.
	"""

	def __init__(
		self,
		window_size: int,
		strategy: RollingStrategy = RollingStrategy.MEAN,
		min_samples: int = 1,
		weights: list[float] | None = None,
		center: bool = False,
	):
		self.strategy = strategy
		self.window_size = window_size
		self.weights = weights
		self.min_samples = min_samples or window_size
		self.center = center
		self.is_fitted = True

	@override
	def fit(self, s: pl.Series) -> Self:
		"""
		Fit method for compatibility. No fitting is required for rolling imputation.

		Args:
			s (pl.Series): The input series to fit.

		Returns:
			Self: The fitted imputer.
		"""

		self.is_fitted = True

		return self

	@override
	def transform(self, s: pl.Series) -> pl.Series:
		if not self.is_fitted:
			raise ValueError(f"{self.__class__.__name__} has not been fitted yet.")

		stat = "stat"
		match self.strategy:
			case RollingStrategy.MIN:
				temp_df = pl.LazyFrame({s.name: s}).with_columns(
					pl.col(s.name)
					.rolling_min(
						self.window_size,
						min_samples=self.min_samples,
						center=self.center,
					)
					.alias(stat)
				)
			case RollingStrategy.MAX:
				temp_df = pl.LazyFrame({s.name: s}).with_columns(
					pl.col(s.name)
					.rolling_max(
						self.window_size,
						min_samples=self.min_samples,
						center=self.center,
					)
					.alias(stat)
				)
			case RollingStrategy.MEAN:
				temp_df = pl.LazyFrame({s.name: s}).with_columns(
					pl.col(s.name)
					.rolling_mean(
						self.window_size,
						min_samples=self.min_samples,
						center=self.center,
					)
					.alias(stat)
				)
			case RollingStrategy.MEDIAN:
				temp_df = pl.LazyFrame({s.name: s}).with_columns(
					pl.col(s.name)
					.rolling_median(
						self.window_size,
						min_samples=self.min_samples,
						center=self.center,
					)
					.alias(stat)
				)

		temp_df = temp_df.with_columns(
			pl.coalesce(pl.col(s.name), pl.col(stat))
			.interpolate("linear")
			.fill_null(strategy="forward")
			.fill_null(0)
			.cast(s.dtype)
			.alias(s.name)
		)

		return temp_df.select(s.name).collect().to_series()
