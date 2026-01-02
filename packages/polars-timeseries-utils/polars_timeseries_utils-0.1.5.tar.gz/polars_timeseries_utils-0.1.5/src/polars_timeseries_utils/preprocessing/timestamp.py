from datetime import datetime

import polars as pl
from polars.datatypes.group import DATETIME_DTYPES

from .frequency import periods_to_relativedelta
from .types import TIMESTAMP_COLUMNS, Frequency


def next_timestamp_val(timestamp: datetime, freq: Frequency, step: int = 1) -> datetime:
	"""
	Calculates the next timestamp based on the given frequency and step.

	Args:
		timestamp (datetime): The starting timestamp.
		freq (Frequency): The frequency to increment by.
		step (int): The number of frequency steps to increment. Defaults to 1.

	Returns:
		datetime: The next timestamp.
	"""

	td = periods_to_relativedelta(step, freq)
	return timestamp + td


def last_timestamp(series: pl.Series) -> datetime:
	"""
	Finds the last timestamp in a Polars Series.

	Args:
		series (pl.Series): The input Polars Series containing datetime values.

	Returns:
		datetime: The last timestamp in the series.
	"""

	return series.cast(pl.Datetime("ns")).max()  # type: ignore


def next_timestamp(series: pl.Series, freq: Frequency, step: int = 1) -> datetime:
	""" "
	Calculates the next timestamp after the last timestamp in the series.

	Args:
		series (pl.Series): The input Polars Series containing datetime values.
		freq (Frequency): The frequency to increment by.
		step (int): The number of frequency steps to increment. Defaults to 1.

	Returns:
		datetime: The next timestamp after the last timestamp in the series.
	"""

	last_ts = last_timestamp(series)
	return next_timestamp_val(last_ts, freq, step=step)


def cast_to_datetime_raises_if_error(s: pl.Series) -> pl.Series:
	"""
	Tries to cast the specified column of the DataFrame to datetime.

	Args:
		df (pl.DataFrame): The input DataFrame.
		column (str): The column name to cast.

	Returns:
		pl.DataFrame: The DataFrame with the specified column cast to datetime if
			successful, else returns the original DataFrame.
	"""

	datetime_formats = [
		"%Y-%m-%d",
		"%d-%m-%Y",
		"%Y/%m/%d",
		"%d/%m/%Y",
		"%Y-%m-%d %H:%M:%S",
		"%Y/%m/%d %H:%M:%S",
		"%d-%m-%Y %H:%M:%S",
		"%d/%m/%Y %H:%M:%S",
	]
	for dt in datetime_formats:
		try:
			return s.str.to_datetime(time_unit="ns", format=dt)
		except Exception:
			continue
	raise ValueError("All datetime format casting attempts failed")


def handle_timestamp_column_raises_if_error(
	df: pl.DataFrame | pl.LazyFrame, col: str | None = None
) -> tuple[pl.DataFrame | pl.LazyFrame, str]:
	"""
	Ensures that the DataFrame has a valid timestamp column.

	Args:
		df (pl.DataFrame | pl.LazyFrame): The input DataFrame.
		col (str | None): Optional name of the file for error messages.

	Returns:
		pl.DataFrame | pl.LazyFrame: The DataFrame with a valid timestamp column.

	Raises:
		DataSerializationError: If no valid timestamp column is found.
	"""

	dt_types = list(DATETIME_DTYPES) + [pl.Date]

	if not col:
		for ts_col, dtype in df.collect_schema().items():
			matching = {ts_col} & TIMESTAMP_COLUMNS
			if matching:
				if dtype in dt_types:
					col = ts_col
					break
				elif dtype == pl.String:
					try:
						df = df.with_columns(
							cast_to_datetime_raises_if_error(
								df.select(ts_col).lazy().collect().to_series()
							)
						)
						col = ts_col
						break
					except Exception:
						continue
			elif dtype in dt_types:
				col = ts_col
				break
			elif dtype == pl.String:
				try:
					df = df.with_columns(
						cast_to_datetime_raises_if_error(
							df.select(ts_col).lazy().collect().to_series()
						)
					)
					col = ts_col
					break
				except Exception:
					continue
		else:
			raise ValueError("Timestamp column could not be determined")
	elif col not in df.collect_schema().names():
		raise ValueError(f"Timestamp column '{col}' not found")
	elif df.collect_schema().get(col) not in dt_types:
		try:
			df = df.with_columns(
				cast_to_datetime_raises_if_error(df.select(col).to_series())  # type: ignore
			)
		except Exception:
			raise ValueError(f"Timestamp column '{col}' could not be cast to datetime")

	return df, col
