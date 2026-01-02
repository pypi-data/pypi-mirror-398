from enum import StrEnum


class Frequency(StrEnum):
	"""
	StrEnum for different frequency strings used in time series data.
	"""

	HOURLY = "H"
	DAILY = "D"
	MONTHLY = "MS"
	YEARLY = "Y"
	UNKNOWN = "unknown"


TIMESTAMP_COLUMNS = {"timestamp", "date", "datetime", "time", "ds"}
