from datetime import datetime

import polars as pl
import pytest

# =============================================================================
# CLEAN DATAFRAMES (no missing values, proper types)
# =============================================================================


@pytest.fixture
def df_clean() -> pl.DataFrame:
	"""
	Clean DataFrame with datetime timestamp column named 'timestamp' and numeric
	columns.
	"""
	return pl.DataFrame(
		{
			"timestamp": [datetime(2023, 1, i) for i in range(1, 21)],
			"value": [float(i * 10) for i in range(1, 21)],
			"measurement": [float(i * 5 + 3) for i in range(1, 21)],
			"target": [float(i * 2 - 1) for i in range(1, 21)],
		}
	)


@pytest.fixture
def df_clean_date_col() -> pl.DataFrame:
	"""Clean DataFrame with datetime column named 'date'."""
	return pl.DataFrame(
		{
			"date": [datetime(2023, 1, i) for i in range(1, 21)],
			"value": [float(i * 10) for i in range(1, 21)],
			"y": [float(i * 5 + 3) for i in range(1, 21)],
			"extra": [float(i * 2 - 1) for i in range(1, 21)],
		}
	)


@pytest.fixture
def df_clean_ds_col() -> pl.DataFrame:
	"""Clean DataFrame with datetime column named 'ds' (Prophet format)."""
	return pl.DataFrame(
		{
			"ds": [datetime(2023, 1, i) for i in range(1, 21)],
			"y": [float(i * 10) for i in range(1, 21)],
			"value": [float(i * 5 + 3) for i in range(1, 21)],
			"extra": [float(i * 2 - 1) for i in range(1, 21)],
		}
	)


@pytest.fixture
def lf_clean() -> pl.LazyFrame:
	"""Clean LazyFrame with datetime timestamp column."""
	return pl.DataFrame(
		{
			"timestamp": [datetime(2023, 1, i) for i in range(1, 21)],
			"value": [float(i * 10) for i in range(1, 21)],
			"measurement": [float(i * 5 + 3) for i in range(1, 21)],
			"target": [float(i * 2 - 1) for i in range(1, 21)],
		}
	).lazy()


# =============================================================================
# DATAFRAMES WITH NULLS - For imputer testing
# =============================================================================


@pytest.fixture
def series_with_nulls() -> pl.Series:
	"""Series with null values for imputer testing."""
	return pl.Series("value", [1.0, None, 3.0, None, 5.0, 6.0, None, 8.0, 9.0, 10.0])


@pytest.fixture
def series_with_nulls_at_edges() -> pl.Series:
	"""Series with null values at the beginning and end."""
	return pl.Series("value", [None, None, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, None, None])


@pytest.fixture
def series_no_nulls() -> pl.Series:
	"""Series without null values."""
	return pl.Series("value", [float(i) for i in range(1, 11)])


@pytest.fixture
def series_all_nulls() -> pl.Series:
	"""Series with all null values."""
	return pl.Series("value", [None] * 10, dtype=pl.Float64)


# =============================================================================
# DATAFRAMES FOR SCALER TESTING
# =============================================================================


@pytest.fixture
def series_for_scaling() -> pl.Series:
	"""Series with known min/max for scaler testing."""
	return pl.Series("value", [0.0, 25.0, 50.0, 75.0, 100.0])


@pytest.fixture
def series_with_negative_values() -> pl.Series:
	"""Series with negative values for scaler testing."""
	return pl.Series("value", [-50.0, -25.0, 0.0, 25.0, 50.0])


@pytest.fixture
def series_constant() -> pl.Series:
	"""Series with constant values (edge case for scaling)."""
	return pl.Series("value", [5.0, 5.0, 5.0, 5.0, 5.0])


# =============================================================================
# DATAFRAMES FOR SMOOTHER TESTING
# =============================================================================


@pytest.fixture
def series_with_outliers() -> pl.Series:
	"""Series with outliers for smoother testing."""
	return pl.Series(
		"value", [10.0, 11.0, 12.0, 100.0, 13.0, 14.0, -50.0, 15.0, 16.0, 17.0]
	)


@pytest.fixture
def series_normal_distribution() -> pl.Series:
	"""Series with approximately normal distribution."""
	return pl.Series("value", [10.0, 11.0, 9.5, 10.5, 10.2, 9.8, 10.1, 9.9, 10.3, 10.0])


# =============================================================================
# DATAFRAMES FOR MULTI-COLUMN TRANSFORMER TESTING
# =============================================================================


@pytest.fixture
def df_multi_column() -> pl.DataFrame:
	"""DataFrame with multiple numeric columns for MultiColumnTransformer testing."""
	return pl.DataFrame(
		{
			"timestamp": [datetime(2023, 1, i) for i in range(1, 11)],
			"col_a": [1.0, None, 3.0, 4.0, 5.0, None, 7.0, 8.0, 9.0, 10.0],
			"col_b": [10.0, 20.0, None, 40.0, 50.0, 60.0, None, 80.0, 90.0, 100.0],
			"col_c": [
				100.0,
				200.0,
				300.0,
				400.0,
				500.0,
				600.0,
				700.0,
				800.0,
				900.0,
				1000.0,
			],
		}
	)


@pytest.fixture
def lf_multi_column() -> pl.LazyFrame:
	"""LazyFrame with multiple numeric columns for MultiColumnTransformer testing."""
	return pl.DataFrame(
		{
			"timestamp": [datetime(2023, 1, i) for i in range(1, 11)],
			"col_a": [1.0, None, 3.0, 4.0, 5.0, None, 7.0, 8.0, 9.0, 10.0],
			"col_b": [10.0, 20.0, None, 40.0, 50.0, 60.0, None, 80.0, 90.0, 100.0],
			"col_c": [
				100.0,
				200.0,
				300.0,
				400.0,
				500.0,
				600.0,
				700.0,
				800.0,
				900.0,
				1000.0,
			],
		}
	).lazy()


# =============================================================================
# UNCLEAN DATAFRAMES - String timestamps that need casting
# =============================================================================


@pytest.fixture
def df_unclean_timestamp_str_ymd_dash() -> pl.DataFrame:
	"""DataFrame with string timestamp in YYYY-MM-DD format."""
	return pl.DataFrame(
		{
			"timestamp": [f"2023-01-{i:02d}" for i in range(1, 21)],
			"value": [float(i * 10) for i in range(1, 21)],
			"measurement": [float(i * 5 + 3) for i in range(1, 21)],
			"target": [float(i * 2 - 1) for i in range(1, 21)],
		}
	)


@pytest.fixture
def df_unclean_timestamp_str_dmy_dash() -> pl.DataFrame:
	"""DataFrame with string timestamp in DD-MM-YYYY format."""
	return pl.DataFrame(
		{
			"timestamp": [f"{i:02d}-01-2023" for i in range(1, 21)],
			"value": [float(i * 10) for i in range(1, 21)],
			"measurement": [float(i * 5 + 3) for i in range(1, 21)],
			"target": [float(i * 2 - 1) for i in range(1, 21)],
		}
	)


@pytest.fixture
def df_unclean_timestamp_str_ymd_slash() -> pl.DataFrame:
	"""DataFrame with string timestamp in YYYY/MM/DD format."""
	return pl.DataFrame(
		{
			"timestamp": [f"2023/01/{i:02d}" for i in range(1, 21)],
			"value": [float(i * 10) for i in range(1, 21)],
			"measurement": [float(i * 5 + 3) for i in range(1, 21)],
			"target": [float(i * 2 - 1) for i in range(1, 21)],
		}
	)


@pytest.fixture
def df_unclean_timestamp_str_dmy_slash() -> pl.DataFrame:
	"""DataFrame with string timestamp in DD/MM/YYYY format."""
	return pl.DataFrame(
		{
			"timestamp": [f"{i:02d}/01/2023" for i in range(1, 21)],
			"value": [float(i * 10) for i in range(1, 21)],
			"measurement": [float(i * 5 + 3) for i in range(1, 21)],
			"target": [float(i * 2 - 1) for i in range(1, 21)],
		}
	)


@pytest.fixture
def df_unclean_timestamp_str_datetime_ymd_dash() -> pl.DataFrame:
	"""DataFrame with string timestamp in YYYY-MM-DD HH:MM:SS format."""
	return pl.DataFrame(
		{
			"timestamp": [f"2023-01-{i:02d} 12:30:00" for i in range(1, 21)],
			"value": [float(i * 10) for i in range(1, 21)],
			"measurement": [float(i * 5 + 3) for i in range(1, 21)],
			"target": [float(i * 2 - 1) for i in range(1, 21)],
		}
	)


@pytest.fixture
def df_unclean_timestamp_str_datetime_ymd_slash() -> pl.DataFrame:
	"""DataFrame with string timestamp in YYYY/MM/DD HH:MM:SS format."""
	return pl.DataFrame(
		{
			"timestamp": [f"2023/01/{i:02d} 12:30:00" for i in range(1, 21)],
			"value": [float(i * 10) for i in range(1, 21)],
			"measurement": [float(i * 5 + 3) for i in range(1, 21)],
			"target": [float(i * 2 - 1) for i in range(1, 21)],
		}
	)


@pytest.fixture
def df_unclean_timestamp_str_datetime_dmy_dash() -> pl.DataFrame:
	"""DataFrame with string timestamp in DD-MM-YYYY HH:MM:SS format."""
	return pl.DataFrame(
		{
			"timestamp": [f"{i:02d}-01-2023 12:30:00" for i in range(1, 21)],
			"value": [float(i * 10) for i in range(1, 21)],
			"measurement": [float(i * 5 + 3) for i in range(1, 21)],
			"target": [float(i * 2 - 1) for i in range(1, 21)],
		}
	)


@pytest.fixture
def df_unclean_timestamp_str_datetime_dmy_slash() -> pl.DataFrame:
	"""DataFrame with string timestamp in DD/MM/YYYY HH:MM:SS format."""
	return pl.DataFrame(
		{
			"timestamp": [f"{i:02d}/01/2023 12:30:00" for i in range(1, 21)],
			"value": [float(i * 10) for i in range(1, 21)],
			"measurement": [float(i * 5 + 3) for i in range(1, 21)],
			"target": [float(i * 2 - 1) for i in range(1, 21)],
		}
	)


# =============================================================================
# UNCLEAN DATAFRAMES - Value columns that need casting
# =============================================================================


@pytest.fixture
def lf_unclean_timestamp_str() -> pl.LazyFrame:
	"""LazyFrame with string timestamp that needs casting."""
	return pl.DataFrame(
		{
			"timestamp": [f"2023-01-{i:02d}" for i in range(1, 21)],
			"value": [float(i * 10) for i in range(1, 21)],
			"measurement": [float(i * 5 + 3) for i in range(1, 21)],
			"target": [float(i * 2 - 1) for i in range(1, 21)],
		}
	).lazy()


# =============================================================================
# UNCLEAN DATAFRAMES - Non-standard column names
# =============================================================================


@pytest.fixture
def df_unclean_no_standard_timestamp_name() -> pl.DataFrame:
	"""DataFrame with datetime column but non-standard name."""
	return pl.DataFrame(
		{
			"my_custom_date": [datetime(2023, 1, i) for i in range(1, 21)],
			"value": [float(i * 10) for i in range(1, 21)],
			"measurement": [float(i * 5 + 3) for i in range(1, 21)],
			"target": [float(i * 2 - 1) for i in range(1, 21)],
		}
	)


# =============================================================================
# INVALID DATAFRAMES - Should raise errors
# =============================================================================


@pytest.fixture
def df_invalid_no_datetime_col() -> pl.DataFrame:
	"""DataFrame with no datetime column at all (all strings, non-date)."""
	return pl.DataFrame(
		{
			"name": [f"item_{i}" for i in range(1, 21)],
			"value": [float(i * 10) for i in range(1, 21)],
			"measurement": [float(i * 5 + 3) for i in range(1, 21)],
			"category": [f"cat_{i % 3}" for i in range(1, 21)],
		}
	)


@pytest.fixture
def df_invalid_non_castable_timestamp() -> pl.DataFrame:
	"""DataFrame with string timestamp column that cannot be cast to datetime."""
	return pl.DataFrame(
		{
			"timestamp": [f"not_a_date_{i}" for i in range(1, 21)],
			"value": [float(i * 10) for i in range(1, 21)],
			"measurement": [float(i * 5 + 3) for i in range(1, 21)],
			"target": [float(i * 2 - 1) for i in range(1, 21)],
		}
	)


@pytest.fixture
def df_invalid_missing_specified_col() -> pl.DataFrame:
	"""DataFrame missing a specified column name."""
	return pl.DataFrame(
		{
			"date": [datetime(2023, 1, i) for i in range(1, 21)],
			"amount": [float(i * 10) for i in range(1, 21)],
			"measurement": [float(i * 5 + 3) for i in range(1, 21)],
			"target": [float(i * 2 - 1) for i in range(1, 21)],
		}
	)
