from typing import Self, override

import polars as pl
from polars._typing import PythonLiteral

from .base import BaseColumnTransformer, InverseTransformerMixin


class MinMaxScaler(BaseColumnTransformer, InverseTransformerMixin):
	"""
	Scales a Polars Series to a given range [0, 1] using Min-Max scaling.

	Attributes:
		min (float | None): The minimum value of the series.
		max (float | None): The maximum value of the series.
	"""

	def __init__(self):
		"""
		Initializes the MinMaxScaler.
		"""

		self.min: PythonLiteral | None = None
		self.max: PythonLiteral | None = None
		super().__init__()

	@override
	def fit(self, s: pl.Series) -> Self:
		self.min = s.min()
		self.max = s.max()

		self.is_fitted = self.min is not None and self.max is not None
		if not self.is_fitted:
			raise RuntimeError(
				f"{self.__class__.__name__} could not be fitted due to None min or"
				" max values."
			)

		return self

	@override
	def transform(self, s: pl.Series) -> pl.Series:
		if not self.is_fitted:
			raise ValueError(f"{self.__class__.__name__} has not been fitted yet.")

		temp_df = s.to_frame().with_columns(
			pl.when(pl.col(s.name).is_null())
			.then(None)
			.otherwise((pl.col(s.name) - self.min) / (self.max - self.min + 1e-8))  # type: ignore
			.cast(s.dtype)
			.alias(s.name)
		)

		return temp_df.select(s.name).to_series()

	@override
	def inverse_transform(self, s: pl.Series) -> pl.Series:
		"""
		Inverse transform scaled values back to original scale.

		Args:
			s (pl.Series): The scaled series to inverse transform.

		Returns:
			pl.Series: The inverse transformed series in original scale.
		"""

		if not self.is_fitted:
			raise ValueError(f"{self.__class__.__name__} has not been fitted yet.")

		temp_df = s.to_frame().with_columns(
			pl.when(pl.col(s.name).is_null())
			.then(None)
			.otherwise(pl.col(s.name) * (self.max - self.min + 1e-8) + self.min)  # type: ignore
			.cast(s.dtype)
			.alias(s.name)
		)

		return temp_df.select(s.name).to_series()


class StandardScaler(BaseColumnTransformer, InverseTransformerMixin):
	"""
	Scales a Polars Series to have zero mean and unit variance using Standard scaling.
	"""

	def __init__(self):
		"""
		Initializes the StandardScaler.
		"""

		self.mean: PythonLiteral | None = None
		self.std: PythonLiteral | None = None
		super().__init__()

	@override
	def fit(self, s: pl.Series) -> Self:
		self.mean = s.mean()
		self.std = s.std()

		self.is_fitted = self.mean is not None and self.std is not None
		if not self.is_fitted:
			raise RuntimeError(
				f"{self.__class__.__name__} could not be fitted due to None mean or"
				" std values."
			)

		return self

	@override
	def transform(self, s: pl.Series) -> pl.Series:
		if not self.is_fitted:
			raise ValueError(f"{self.__class__.__name__} has not been fitted yet.")

		temp_df = s.to_frame().with_columns(
			((pl.col(s.name) - self.mean) / self.std).cast(s.dtype).alias(s.name)
		)
		return temp_df.select(s.name).to_series()

	@override
	def inverse_transform(self, s: pl.Series) -> pl.Series:
		"""
		Inverse transform standardized values back to original scale.

		Args:
			s (pl.Series): The standardized series to inverse transform.

		Returns:
			pl.Series: The inverse transformed series in original scale.
		"""

		if not self.is_fitted:
			raise ValueError(f"{self.__class__.__name__} has not been fitted yet.")

		temp_df = s.to_frame().with_columns(
			(pl.col(s.name) * self.std + self.mean).cast(s.dtype).alias(s.name)
		)
		return temp_df.select(s.name).to_series()


class RobustScaler(BaseColumnTransformer, InverseTransformerMixin):
	"""
	Scales a Polars Series using statistics that are robust to outliers.

	Uses the median and interquartile range (IQR) instead of mean and standard
	deviation, making it robust to outliers.

	Attributes:
		median (float | None): The median of the series.
		iqr (float | None): The interquartile range (Q3 - Q1) of the series.
		q_min (float): The lower quantile for IQR calculation.
		q_max (float): The upper quantile for IQR calculation.
		q_min_val (float | None): The lower quantile value.
		q_max_val (float | None): The upper quantile value.
	"""

	def __init__(self, q_min: float = 0.25, q_max: float = 0.75):
		"""
		Initializes the RobustScaler.

		Args:
			q_min (float): The lower quantile for IQR calculation.
				Default is 0.25.
			q_max (float): The upper quantile for IQR calculation.
				Default is 0.75.
		"""

		self.q_min = q_min
		self.q_max = q_max
		self.median: PythonLiteral | None = None
		self.q_min_val: PythonLiteral | None = None
		self.q_max_val: PythonLiteral | None = None
		self.iqr: PythonLiteral | None = None
		super().__init__()

	@override
	def fit(self, s: pl.Series) -> Self:
		self.median = s.median()
		self.q_min_val = s.quantile(self.q_min)
		self.q_max_val = s.quantile(self.q_max)

		if self.q_min_val is not None and self.q_max_val is not None:
			self.iqr = self.q_max_val - self.q_min_val  # type: ignore

		self.is_fitted = (
			self.median is not None and self.iqr is not None and self.iqr != 0
		)
		if not self.is_fitted:
			raise RuntimeError(
				f"{self.__class__.__name__} could not be fitted due to None median,"
				" IQR, or zero IQR values."
			)

		return self

	@override
	def transform(self, s: pl.Series) -> pl.Series:
		if not self.is_fitted:
			raise ValueError(f"{self.__class__.__name__} has not been fitted yet.")

		temp_df = s.to_frame().with_columns(
			pl.when(pl.col(s.name).is_null())
			.then(None)
			.otherwise((pl.col(s.name) - self.median) / (self.iqr + 1e-8))  # type: ignore
			.cast(s.dtype)
			.alias(s.name)
		)

		return temp_df.select(s.name).to_series()

	@override
	def inverse_transform(self, s: pl.Series) -> pl.Series:
		"""
		Inverse transform robust-scaled values back to original scale.

		Args:
			s (pl.Series): The scaled series to inverse transform.

		Returns:
			pl.Series: The inverse transformed series in original scale.
		"""

		if not self.is_fitted:
			raise ValueError(f"{self.__class__.__name__} has not been fitted yet.")

		temp_df = s.to_frame().with_columns(
			pl.when(pl.col(s.name).is_null())
			.then(None)
			.otherwise(pl.col(s.name) * (self.iqr + 1e-8) + self.median)  # type: ignore
			.cast(s.dtype)
			.alias(s.name)
		)

		return temp_df.select(s.name).to_series()
