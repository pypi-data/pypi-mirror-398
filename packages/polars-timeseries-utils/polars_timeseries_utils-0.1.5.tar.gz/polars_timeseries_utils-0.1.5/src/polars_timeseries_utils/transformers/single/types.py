from __future__ import annotations

from enum import StrEnum


class Strategy(StrEnum):
	FORWARD = "forward"
	BACKWARD = "backward"
	MIN = "min"
	MAX = "max"
	MEAN = "mean"
	MEDIAN = "median"
	ZERO = "zero"
	ONE = "one"


class RollingStrategy(StrEnum):
	MIN = "min"
	MAX = "max"
	MEAN = "mean"
	MEDIAN = "median"
