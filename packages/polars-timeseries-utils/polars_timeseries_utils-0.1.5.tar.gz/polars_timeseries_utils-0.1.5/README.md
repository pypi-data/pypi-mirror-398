# polars-timeseries-utils

A Python library providing scikit-learn style transformers and utilities for time series data processing with [Polars](https://pola.rs/).

[![PyPI version](https://badge.fury.io/py/polars-timeseries-utils.svg)](https://badge.fury.io/py/polars-timeseries-utils)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

## Features

- **Single Transformers**: Scikit-learn style `fit`/`transform` API for Polars Series
- **Composable Transformers**: Apply transformers to DataFrames and chain them in pipelines
- **Preprocessing Utilities**: Frequency detection, timestamp handling, and ETL functions
- **Statistics**: Rolling and static z-score calculations for anomaly detection
- **Full Polars Integration**: Works with both `DataFrame` and `LazyFrame`

## Installation

```bash
pip install polars-timeseries-utils
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add polars-timeseries-utils
```

## Package Structure

```
polars_timeseries_utils/
├── transformers/
│   ├── single/        # Series-level transformers (fit/transform on pl.Series)
│   └── composable/    # DataFrame-level transformers (MultiColumnTransformer, Pipeline)
├── preprocessing/     # ETL, frequency detection, timestamp handling
└── stats/            # Z-score functions for anomaly detection
```

## Quick Start

### Single Transformers

All single transformers follow the scikit-learn `fit`/`transform` pattern and operate on `pl.Series`:

```python
import polars as pl
from polars_timeseries_utils.transformers.single import (
    Imputer,
    MinMaxScaler,
    StandardScaler,
    RobustScaler,
    Smoother,
    LagTransformer,
    DiffTransformer,
    Strategy,
)

# Impute missing values
series = pl.Series("value", [1.0, None, 3.0, None, 5.0])
imputer = Imputer(strategy=Strategy.MEAN)
filled = imputer.fit_transform(series)
# Result: [1.0, 3.0, 3.0, 3.0, 5.0]

# Scale to [0, 1] range
series = pl.Series("value", [0.0, 25.0, 50.0, 75.0, 100.0])
scaler = MinMaxScaler()
scaled = scaler.fit_transform(series)
# Result: [0.0, 0.25, 0.5, 0.75, 1.0]

# Inverse transform to get original values back
original = scaler.inverse_transform(scaled)
# Result: [0.0, 25.0, 50.0, 75.0, 100.0]
```

### Available Single Transformers

| Transformer | Description |
|-------------|-------------|
| `Imputer` | Fill missing values with a constant or strategy (mean, median, min, max, forward, backward) |
| `RollingImputer` | Fill missing values using rolling window statistics |
| `MinMaxScaler` | Scale values to [0, 1] range |
| `StandardScaler` | Standardize to zero mean and unit variance |
| `RobustScaler` | Scale using median and IQR (robust to outliers) |
| `Smoother` | Clip outliers based on z-score threshold |
| `RollingSmoother` | Clip outliers using rolling z-score |
| `LagTransformer` | Create lag features for time series |
| `DiffTransformer` | Apply differencing for stationarity |

### Imputation Strategies

```python
from polars_timeseries_utils.transformers.single import (
    Imputer,
    RollingImputer,
    Strategy,
    RollingStrategy,
)

# Static strategies
Imputer(strategy=Strategy.MEAN)      # Fill with column mean
Imputer(strategy=Strategy.MEDIAN)    # Fill with column median
Imputer(strategy=Strategy.FORWARD)   # Forward fill
Imputer(strategy=Strategy.BACKWARD)  # Backward fill
Imputer(value=0)                     # Fill with constant value

# Rolling strategies
RollingImputer(window_size=5, strategy=RollingStrategy.MEAN)
RollingImputer(window_size=5, strategy=RollingStrategy.MEDIAN)
```

### Composable Transformers

Apply single transformers to multiple DataFrame columns at once:

```python
import polars as pl
from polars_timeseries_utils.transformers.single import Imputer, MinMaxScaler, Strategy
from polars_timeseries_utils.transformers.composable import (
    MultiColumnTransformer,
    ColumnTransformerMetadata,
)

df = pl.DataFrame({
    "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
    "temperature": [20.0, None, 22.0],
    "humidity": [50.0, 55.0, None],
})

# Define transformers for specific columns
transformer = MultiColumnTransformer([
    ColumnTransformerMetadata(
        name="imputer",
        columns=["temperature", "humidity"],
        transformer=Imputer(strategy=Strategy.MEAN),
    ),
])

result = transformer.fit_transform(df)
```

You can also select columns by dtype:

```python
import polars as pl
from polars_timeseries_utils.transformers.single import MinMaxScaler
from polars_timeseries_utils.transformers.composable import (
    MultiColumnTransformer,
    ColumnTransformerMetadata,
)

transformer = MultiColumnTransformer([
    ColumnTransformerMetadata(
        name="scale_floats",
        columns=[pl.Float64],  # Apply to all Float64 columns
        transformer=MinMaxScaler(),
    ),
])
```

### Pipelines

Chain multiple transformation steps:

```python
from polars_timeseries_utils.transformers.single import Imputer, MinMaxScaler, Strategy
from polars_timeseries_utils.transformers.composable import (
    Pipeline,
    MultiColumnTransformer,
    MultiColumnTransformerMetadata,
    ColumnTransformerMetadata,
)

# Create pipeline steps
impute_step = MultiColumnTransformer([
    ColumnTransformerMetadata(
        name="imputer",
        columns=["value"],
        transformer=Imputer(strategy=Strategy.MEAN),
    ),
])

scale_step = MultiColumnTransformer([
    ColumnTransformerMetadata(
        name="scaler",
        columns=["value"],
        transformer=MinMaxScaler(),
    ),
])

# Build and run pipeline
pipeline = Pipeline([
    MultiColumnTransformerMetadata(name="impute", transformer=impute_step),
    MultiColumnTransformerMetadata(name="scale", transformer=scale_step),
])

result = pipeline.fit_transform(df)
```

### Preprocessing Utilities

#### Clean Time Series Data

```python
from datetime import datetime
import polars as pl
from polars_timeseries_utils.preprocessing import clean_timeseries_df

df = pl.DataFrame({
    "timestamp": [datetime(2023, 1, 3), datetime(2023, 1, 1), datetime(2023, 1, 2)],
    "value": [3.0, None, 100.0],  # Contains null and outlier
})

# Sorts, removes duplicates, imputes nulls, and smooths outliers
cleaned = clean_timeseries_df(df, ts_col="timestamp", window_size=3, max_zscore=2.0)
```

#### Frequency Detection

```python
from datetime import datetime
import polars as pl
from polars_timeseries_utils.preprocessing import determine_frequency, Frequency

series = pl.Series("ts", [datetime(2023, 1, i) for i in range(1, 11)])
freq = determine_frequency(series)
# Result: Frequency.DAILY
```

#### Timestamp Handling

```python
from polars_timeseries_utils.preprocessing import (
    handle_timestamp_column_raises_if_error,
    next_timestamp,
    last_timestamp,
    Frequency,
)

# Auto-detect and cast timestamp column
df, ts_col = handle_timestamp_column_raises_if_error(df)

# Get next timestamp in sequence
next_ts = next_timestamp(df[ts_col], Frequency.DAILY)
```

### Statistics

Calculate z-scores for anomaly detection:

```python
from polars_timeseries_utils.stats import zscore_df, rolling_zscore_df

# Static z-score
result = zscore_df(df, col="value", with_median="med", with_std="std")

# Rolling z-score (uses MAD for robustness)
result = rolling_zscore_df(
    df,
    col="value",
    window_size=10,
    alias="z_score",
    with_median="rolling_med",
    with_mad="rolling_mad",
)
```

## LazyFrame Support

All functions work with both `DataFrame` and `LazyFrame`:

```python
import polars as pl
from polars_timeseries_utils.transformers.single import MinMaxScaler
from polars_timeseries_utils.transformers.composable import (
    MultiColumnTransformer,
    ColumnTransformerMetadata,
)

lf = pl.LazyFrame({"value": [1.0, 2.0, 3.0]})

transformer = MultiColumnTransformer([
    ColumnTransformerMetadata(
        name="scaler",
        columns=["value"],
        transformer=MinMaxScaler(),
    ),
])

# Returns LazyFrame
result = transformer.fit_transform(lf)

# Collect when ready
df = result.collect()
```

## API Reference

### Single Transformers (`transformers.single`)

All transformers inherit from `BaseColumnTransformer` and implement:

- `fit(series: pl.Series) -> Self` - Learn parameters from data
- `transform(series: pl.Series) -> pl.Series` - Apply transformation
- `fit_transform(series: pl.Series) -> pl.Series` - Fit and transform in one step

Scalers also implement `InverseTransformerMixin`:

- `inverse_transform(series: pl.Series) -> pl.Series` - Reverse the transformation

### Composable Transformers (`transformers.composable`)

- `MultiColumnTransformer` - Apply single transformers to DataFrame columns
- `Pipeline` - Chain multiple `MultiColumnTransformer` steps
- `ColumnTransformerMetadata` - Configuration for column-transformer mapping
- `MultiColumnTransformerMetadata` - Configuration for pipeline steps

### Statistics (`stats`)

- `zscore(series)` - Calculate z-score of a Series
- `zscore_df(df, col, ...)` - Calculate z-score with optional median/std columns
- `rolling_zscore(series, window_size, ...)` - Rolling z-score of a Series
- `rolling_zscore_df(df, col, window_size, ...)` - Rolling z-score with optional outputs

### Preprocessing (`preprocessing`)

- `clean_timeseries_df(df, ts_col, ...)` - Sort, dedupe, impute, and smooth
- `determine_frequency(series)` - Detect time series frequency
- `handle_timestamp_column_raises_if_error(df, col)` - Auto-detect and cast timestamps
- `next_timestamp(series, frequency)` - Get next timestamp in sequence
- `last_timestamp(series)` - Get maximum timestamp
- `Frequency` - Enum for time series frequencies (HOURLY, DAILY, MONTHLY, YEARLY)

## License

MIT

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/LeonDavidZipp/polars-timeseries-utils).
