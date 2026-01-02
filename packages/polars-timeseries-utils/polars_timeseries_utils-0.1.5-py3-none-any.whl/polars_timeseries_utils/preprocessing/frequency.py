import pandas as pd
import polars as pl
from dateutil.relativedelta import relativedelta

from .types import Frequency


def frequency_to_interval(freq: Frequency) -> str:
	"""
	Converts a Frequency enum to a Polars interval string.

	Use this for pl.datetime_range() to get calendar-aware intervals.

	Args:
		freq (Frequency): The frequency to convert.

	Returns:
		str: The Polars interval string (e.g., "1h", "1d", "1mo", "1y").
	"""

	match freq:
		case Frequency.HOURLY:
			return "1h"
		case Frequency.DAILY:
			return "1d"
		case Frequency.MONTHLY:
			return "1mo"
		case Frequency.YEARLY:
			return "1y"
		case _:
			raise ValueError(f"Unsupported frequency: {freq}")


def periods_to_relativedelta(n_periods: int, freq: Frequency) -> relativedelta:
	"""
	Calculates the timestamp after adding n_periods of the given frequency.

	Args:
		n_periods (int): The number of periods to add.
		freq (Frequency): The frequency of the periods.

	Returns:
		relativedelta: The resulting relativedelta after adding the periods.
	"""

	match freq:
		case Frequency.HOURLY:
			return relativedelta(hours=n_periods)
		case Frequency.DAILY:
			return relativedelta(days=n_periods)
		case Frequency.MONTHLY:
			return relativedelta(months=n_periods)
		case Frequency.YEARLY:
			return relativedelta(years=n_periods)
		case _:
			raise ValueError("Unknown frequency")


def determine_frequency(s: pl.Series) -> Frequency:
	"""
	Determines the frequency of a timestamp series using pandas' infer_freq.

	Args:
		s (pl.Series): The input Polars Series containing datetime values.

	Returns:
		Frequency: The determined frequency (HOURLY, DAILY, MONTHLY, YEARLY).
	"""

	freq = pd.infer_freq(s.to_pandas())

	if freq is None or freq == "":
		return Frequency.UNKNOWN

	freq_upper = freq.upper()

	if freq_upper.startswith(("YS", "YE", "AS", "A-", "BYS", "BYE", "Y")):
		return Frequency.YEARLY
	elif freq_upper.startswith(("QS", "QE", "BQS", "BQE", "Q")):
		return Frequency.MONTHLY
	elif freq_upper.startswith(("MS", "ME", "BMS", "BME", "M")):
		return Frequency.MONTHLY
	elif freq_upper.startswith(("W-", "W")) or freq_upper == "W":
		return Frequency.DAILY
	elif freq_upper in ("D", "B", "C") or freq_upper.endswith("D"):
		return Frequency.DAILY
	elif freq_upper in ("H", "BH") or freq_upper.endswith("H"):
		return Frequency.HOURLY
	elif freq_upper.endswith(("T", "MIN", "S", "MS", "US", "NS", "L", "U", "N")):
		return Frequency.HOURLY
	elif freq_upper.startswith("WOM"):
		return Frequency.MONTHLY

	return Frequency.UNKNOWN
