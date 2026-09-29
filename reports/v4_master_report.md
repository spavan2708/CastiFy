# CASTIFY V4 MASTER REPORT

## 1. ARCHITECTURE

```text
CastiFy/
├── main.py
├── requirements.txt
├── data/
│   ├── __init__.py
│   └── market_data.py
├── features/
│   ├── __init__.py
│   └── basic_features.py
├── models/
│   ├── __init__.py
│   └── baseline.py
├── tests/
│   └── test_pipeline.py
└── reports/
    ├── v3_baseline.json
    ├── v4_aapl.txt
    ├── v4_msft.txt
    ├── v4_jpm.txt
    ├── v4_international.txt
    ├── v4_invalid.txt
    ├── v4_tests.txt
    └── v4_master_report.md
```
Existing virtual environment and generated Python caches omitted. The requested
module structure was used, with one focused offline test module and saved evidence.

## 2. FILES CREATED

Every file in the tree above except main.py is new. The three package initializers
contain package docstrings. The reports directory preserves benchmark evidence,
actual terminal outputs, and this complete report.

## 3. FILES MODIFIED

main.py only. Virtual-environment configuration was not changed.

## 4. DATA ENGINE

Symbols are stripped and uppercased. Empty input, whitespace-separated multiple
symbols, and comma-separated lists are rejected; punctuation such as -, ., and ^
is permitted. No supported-symbol list exists.

The reusable download_market_data(ticker, start_date, end_date=None) uses daily
Yahoo data and returns exactly Open, High, Low, Close, Volume with flat columns.
Both orientations of a two-level Yahoo column index are handled, with a check
that exactly the requested symbol is present. Ambiguous schemas are rejected.

The explicit setting is auto_adjust=True. OHLC values use Yahoo/yfinance's
split/dividend-adjusted price series; Volume remains the provider's volume series.
This keeps the existing adjusted-price return and moving-average pipeline
consistent and avoids mixing raw OHLC with adjusted Close. No separate raw-price
or Adj Close column enters the pipeline. This is historical adjusted research data,
not a point-in-time corporate-action database.

The API documents adjusted OHLC and an exclusive end date:
[yfinance download documentation](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html).

START_DATE is 2010-01-01 and END_DATE is None in main.py. None resolves to today's
UTC date as an exclusive cutoff: this run used 2026-09-29. Explicit future end
dates are also capped there. This deliberately excludes a potentially incomplete
current daily bar. It can omit an already completed session on today's date;
an exchange-calendar-aware latest-close policy remains a limitation.

## 5. ERROR HANDLING

Expected empty/invalid/insufficient data raises MarketDataError, which the CLI
prints with exit status 1. yfinance handles provider download failures and returns
empty data; the data layer turns that into a readable message. No blanket catch
suppresses programming errors. EOF and keyboard cancellation are handled separately.

Bad rows are rejected, not silently repaired. Zero volume is valid raw data, but
if a later percentage change becomes infinite, dataset construction rejects it
with a specific message rather than imputing a value.

## 6. DATA QUALITY VALIDATION

AAPL, MSFT, JPM and ingestion-only 7203.T passed each of these executed validations:

| Validation | Result |
|---|---|
| Nonempty dataframe | PASS |
| Required unique OHLCV columns | PASS |
| Valid datetime index | PASS |
| Ascending dates | PASS |
| Unique dates | PASS |
| Numeric, finite OHLC | PASS |
| Numeric, finite Volume | PASS |
| Strictly positive OHLC | PASS |
| Non-negative Volume | PASS |
| At least 150 raw observations | PASS |

All four downloads had zero duplicate dates and zero missing OHLCV values.
No calendar rows are invented, and no forward fill or interpolation is applied.

## 7. FEATURE FACTORY

build_basic_features returns a copy and preserves Daily_Return, Return_Lag_1,
Return_Lag_2, Return_Lag_3, Return_Lag_5, MA_5, MA_20, MA_50, Volatility_5,
Volatility_20, Volume_Change, and Tomorrow_Return exactly as calculated in V3.
Positive lag shifts, trailing rolling means, pandas sample standard deviations,
and next-trading-row target alignment remain unchanged. No new features were added.

## 8. ML DATASET

The explicit 10 input features are Return_Lag_1, Return_Lag_2, Return_Lag_3,
Return_Lag_5, MA_5, MA_20, MA_50, Volatility_5, Volatility_20, Volume_Change.
Tomorrow_Return is y only. Daily_Return and raw OHLCV are excluded from X.
Required-column NaNs are dropped in a separate copy; the original data is intact.
Non-finite ML values are rejected. At least 100 usable observations are required.
Each live US run removed 49 warm-up rows plus the final missing-target row.

## 9. TIME-SERIES SPLIT

The first floor(0.8 * N) observations initially train, and the rest test. Target
realization dates come from the unfiltered trading index shifted by one row.
Training rows with target dates on or after the first test feature date are purged.
The test set remains unchanged. Date ordering, alignment, disjointness, target
boundaries, finite values, and sample accounting are asserted.

For each US stock: 3,327 initial training rows became 3,326; the feature date
2023-06-01 was purged because its target realizes on 2023-06-02, the first test
date. Retained training feature dates: 2010-03-16 through 2023-05-31. Latest
training target date: 2023-06-01. Test feature dates: 2023-06-02 through 2026-09-25.

## 10. BASELINE MODEL

RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1), with all
other sklearn defaults. No tuning or scaling. Only purged training data is fitted.
Evaluation retains MAE, RMSE, R², zero-return MAE/RMSE, exact-sign directional
accuracy, today's-return direction benchmark, three-column prediction results,
and all ten sorted impurity-based feature importances. Importance is not causation.

## 11. MULTI-STOCK TEST RESULTS

All three full CLI runs succeeded, with actual raw dates 2010-01-04 to 2026-09-28.
The requested exclusive cutoff was 2026-09-29. Error metrics below are decimals.

| Ticker | Raw | ML | Train | Test | MAE | RMSE | R² | Direction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| AAPL | 4209 | 4159 | 3326 | 832 | 0.01279743 | 0.01777521 | -0.157389 | 46.6346% |
| MSFT | 4209 | 4159 | 3326 | 832 | 0.01539333 | 0.01983571 | -0.473194 | 47.3558% |
| JPM | 4209 | 4159 | 3326 | 832 | 0.01111377 | 0.01526024 | -0.158444 | 45.9135% |

| Ticker | Zero MAE | Zero RMSE | Momentum direction |
|---|---:|---:|---:|
| AAPL | 0.01127568 | 0.01654731 | 50.9615% |
| MSFT | 0.01127009 | 0.01635599 | 49.6394% |
| JPM | 0.00993859 | 0.01423232 | 50.8413% |

All forests had higher errors than zero-return predictions, negative R², and
lower direction accuracy than both 50% and their momentum benchmarks. These
are architecture validation results, not evidence of predictive usefulness.

## 12. INTERNATIONAL SYMBOL SMOKE TEST

7203.T ingestion succeeded: 4,112 rows, 2010-01-04 through 2026-09-28, all data
checks passed. This was deliberately ingestion-only, without additional model fitting.

## 13. INVALID TICKER TEST

THISDOESNOTEXIST123 produced provider 404/unavailable diagnostics, followed by:

```text
CastiFy: Unable to retrieve usable market data for "THISDOESNOTEXIST123". Check the ticker symbol or data availability.
```

Expected exit status 1; no Python traceback.

## 14. MINIMUM-HISTORY TEST

Executed offline tests reject 149 raw rows, accept 150 valid raw rows, and reject
fewer than 100 usable ML rows. At the 150-row boundary, 50 warm-up/target rows
leave 100 ML rows: normally 79 retained training observations and 20 test
observations after one purge. This is an operational safeguard, not a claim of
statistical adequacy, and does not require years of data from newly listed stocks.

## 15. LEAKAGE AUDIT

| Requested check | Result and evidence |
|---|---|
| 1. Historical lag rows only | PASS: positive shifts; offline checks |
| 2. Current/past rolling inputs only | PASS: trailing windows; future-perturbation test |
| 3. Current/previous volume only | PASS: unchanged pct_change |
| 4. Tomorrow_Return target only | PASS: explicit dataset construction |
| 5. Target absent from X | PASS: assertion and offline test |
| 6. Chronological split | PASS: ordered slices and index assertions |
| 7. Strict target boundary | PASS: mapped actual trading dates and purge assertion |
| 8. No test data fitted | PASS: sole fit(X_train, y_train), verified by mock |
| 9. No random shuffling | PASS: no row-shuffling step |
| 10. No future values from cleaning | PASS: required-row deletion only |
| 11. Generalization preserves semantics | PASS: original calculations moved intact and tested |
| 12. No interpolation/forward fill | PASS: none added; pandas 3 pct_change does not fill |

These checks concern pipeline operations on the supplied series. Yahoo's retrospectively
adjusted history is not a point-in-time historical data snapshot; a stricter future
research system should explicitly address data vintage and corporate actions.

## 16. AUTOMATED TESTS

13 tests created in tests/test_pipeline.py; all 13 executed and passed, zero failures.
Tests are independent of live Yahoo availability. They cover normalization, schema
orientations, invalid columns/dates/values, minimum history, unavailable downloads,
download settings, original feature semantics/nonmutation, future-input perturbation,
calendar-aware purge, infinite volume changes, and exact training-only model calls.
The test log is saved as reports/v4_tests.txt. All application modules also imported
successfully without prompting for input or downloading data. No ticker hardcoding
was found in main.py or feature/model/data logic.

## 17. TERMINAL OUTPUT

The full live outputs are saved in reports/v4_aapl.txt, v4_msft.txt, v4_jpm.txt,
v4_international.txt, and v4_invalid.txt. Representative AAPL output:

```text
Actual dates: 2010-01-04 to 2026-09-28
Trading observations: 4209
ML observations: 4159; features: 10
Training before purge: 3327
Removed dates: ['2023-06-01']
Training: 3326 rows; 2010-03-16 to 2023-05-31
Testing: 832 rows; 2023-06-02 to 2026-09-25
Latest training target: 2023-06-01
mae: 0.01279743 (1.2797%)
rmse: 0.01777521 (1.7775%)
R²: -0.157389
All dataset, target-boundary, and prediction assertions: PASS
```

```text
Ran 13 tests in 0.104s
OK
Module imports: PASS
```

## 18. ERRORS / WARNINGS

The initial sandboxed AAPL request failed DNS resolution. It exited gracefully;
the authorized network-enabled rerun succeeded, as did MSFT, JPM, and 7203.T.
The invalid-symbol provider diagnostics were expected and are preserved in its log.
No dependencies needed installing, no runtime warnings appeared in successful runs,
and no model was changed in response to its metrics. Unexpected programming errors
are intentionally not hidden.

## 19. DEPENDENCIES

Pinned to the actual installed versions used in the verified runs:

```text
yfinance==1.7.0
pandas==3.0.6
numpy==2.5.3
scikit-learn==1.9.1
```

Tests use the standard-library unittest package; no new test dependency is needed.

## 20. COMPLETE SOURCE CODE

The following are complete, unabridged contents of every created or modified Python
source file, including package initializers and the test file. Requirements and
historical benchmark evidence are included after the Python files.

### main.py

```python
"""Terminal orchestration for the CastiFy V4 research pipeline."""
from data.market_data import (
    MarketDataError, download_market_data, normalize_ticker, print_data_report
)
from features.basic_features import build_basic_features
from models.baseline import (
    chronological_split, evaluate_baseline, prepare_ml_dataset, print_baseline_report
)

START_DATE = "2010-01-01"
END_DATE = None


def main() -> int:
    """Run one user-selected ticker; expected data failures get readable errors."""
    print("============================================\n"
          "                 CASTIFY\n"
          "      Quantitative Forecasting Engine\n"
          "============================================")
    try:
        ticker = normalize_ticker(input("Enter stock ticker: "))
        print(f"Analyzing {ticker}...")
        stock = download_market_data(ticker, START_DATE, END_DATE)
        print_data_report(stock, ticker, START_DATE, END_DATE)
        featured = build_basic_features(stock)
        X, y = prepare_ml_dataset(featured)
        split = chronological_split(X, y, featured.index)
        evaluation = evaluate_baseline(split, featured)
        print_baseline_report(X, split, evaluation)
    except MarketDataError as error:
        print(f"CastiFy: {error}")
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nInput cancelled.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### data/__init__.py

```python
"""CastiFy data utilities."""
```

### data/market_data.py

```python
"""Single-symbol Yahoo ingestion with a validated, flat OHLCV schema."""
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf

COLUMNS = ["Open", "High", "Low", "Close", "Volume"]
MIN_OBSERVATIONS = 150


class MarketDataError(ValueError):
    """Expected unavailable, invalid, or insufficient market data."""


def normalize_ticker(ticker: str) -> str:
    """Normalize one symbol without rejecting Yahoo-compatible punctuation."""
    symbol = ticker.strip().upper()
    if not symbol or any(c.isspace() for c in symbol) or "," in symbol:
        raise MarketDataError("Enter one nonempty Yahoo Finance ticker.")
    return symbol


def standardize_columns(raw: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Resolve either Yahoo MultiIndex orientation without mixing symbols."""
    if raw is None or raw.empty:
        raise MarketDataError(f'Unable to retrieve usable market data for "{ticker}". '
                              'Check the ticker symbol or data availability.')
    data = raw.copy()
    if isinstance(data.columns, pd.MultiIndex):
        if data.columns.nlevels != 2:
            raise MarketDataError("Unexpected Yahoo column structure.")
        for level in (0, 1):
            if set(COLUMNS).issubset(data.columns.get_level_values(level)):
                symbol_level = 1 - level
                symbols = data.columns.get_level_values(symbol_level).unique()
                if len(symbols) != 1 or symbols[0] != ticker:
                    raise MarketDataError("Download did not contain exactly the requested symbol.")
                data.columns = data.columns.get_level_values(level)
                break
        else:
            raise MarketDataError("Required OHLCV columns are missing.")
    if not data.columns.is_unique or not set(COLUMNS).issubset(data.columns):
        raise MarketDataError("Required unique OHLCV columns are missing.")
    return data[COLUMNS].copy()


def validate_market_data(data: pd.DataFrame) -> None:
    """Reject bad observations rather than filling or silently deleting them."""
    if data.empty or not set(COLUMNS).issubset(data.columns) or not data.columns.is_unique:
        raise MarketDataError("Market data is empty or missing unique OHLCV columns.")
    if not isinstance(data.index, pd.DatetimeIndex) or data.index.hasnans:
        raise MarketDataError("Market data requires valid datetime dates.")
    if not data.index.is_monotonic_increasing or not data.index.is_unique:
        raise MarketDataError("Market dates must be ascending and unique.")
    if not all(pd.api.types.is_numeric_dtype(data[c]) for c in COLUMNS):
        raise MarketDataError("OHLCV values must be numeric.")
    if not np.isfinite(data[COLUMNS].to_numpy(dtype=float)).all():
        raise MarketDataError("OHLCV contains missing or non-finite values.")
    if not (data[COLUMNS[:4]] > 0).all().all():
        raise MarketDataError("All OHLC prices must be positive.")
    if not (data["Volume"] >= 0).all():
        raise MarketDataError("Volume must be non-negative.")
    if len(data) < MIN_OBSERVATIONS:
        raise MarketDataError(f"Insufficient historical data for CastiFy's baseline forecasting "
                              f"pipeline: {len(data)} rows; need {MIN_OBSERVATIONS}.")


def download_market_data(ticker: str, start_date: str,
                         end_date: str | None = None) -> pd.DataFrame:
    """Download adjusted daily OHLCV; exclude today's potentially partial bar.

    End dates are exclusive. None resolves to today's UTC date, conservatively
    omitting today even if that exchange's session has already completed.
    """
    ticker = normalize_ticker(ticker)
    today = datetime.now(timezone.utc).date().isoformat()
    try:
        start = pd.Timestamp(start_date)
        end = pd.Timestamp(end_date or today)
        cutoff = min(end, pd.Timestamp(today))
        if pd.isna(start) or pd.isna(end) or start >= cutoff:
            raise ValueError("Start must precede the completed-data cutoff.")
    except (ValueError, TypeError) as error:
        raise MarketDataError(f"Invalid date range: {error}") from error
    # yf.download handles provider/network failures by returning empty data.
    raw = yf.download(ticker, start=start.date().isoformat(),
                      end=cutoff.date().isoformat(), interval="1d",
                      auto_adjust=True, keepna=True, progress=False, threads=False)
    data = standardize_columns(raw, ticker)
    validate_market_data(data)
    data.attrs["effective_end_exclusive"] = cutoff.date().isoformat()
    return data


def print_data_report(data: pd.DataFrame, ticker: str, start_date: str,
                      end_date: str | None) -> None:
    """Print quality results calculated from a validated dataframe."""
    validate_market_data(data)
    print("\nCASTIFY DATA REPORT")
    print(f"Ticker: {normalize_ticker(ticker)}")
    print(f"Requested start: {start_date}; requested end: {end_date}")
    print(f"Effective exclusive end: {data.attrs.get('effective_end_exclusive')}")
    print(f"Actual dates: {data.index.min().date()} to {data.index.max().date()}")
    print(f"Trading observations: {len(data)}; columns: {list(data.columns)}")
    print(f"Duplicate dates: {data.index.duplicated().sum()}")
    print(f"Missing values: {data.isna().sum().to_dict()}")
    print("Price / volume / chronological / minimum-history validation: PASS")
    print("Overall: PASS; auto_adjust=True (adjusted OHLC; provider volume).")
```

### features/__init__.py

```python
"""CastiFy features utilities."""
```

### features/basic_features.py

```python
"""Original V1 features and next-trading-row target."""
import pandas as pd


def build_basic_features(stock: pd.DataFrame) -> pd.DataFrame:
    """Return features on a copy; preserve missing warm-up and target rows."""
    stock = stock.copy()
    # Calculate daily percentage return
    stock["Daily_Return"] = stock["Close"].pct_change()
    
    # Add returns from previous trading days
    stock["Return_Lag_1"] = stock["Daily_Return"].shift(1)
    stock["Return_Lag_2"] = stock["Daily_Return"].shift(2)
    stock["Return_Lag_3"] = stock["Daily_Return"].shift(3)
    stock["Return_Lag_5"] = stock["Daily_Return"].shift(5)
    
    # Calculate moving averages including today's closing price
    stock["MA_5"] = stock["Close"].rolling(window=5).mean()
    stock["MA_20"] = stock["Close"].rolling(window=20).mean()
    stock["MA_50"] = stock["Close"].rolling(window=50).mean()
    
    # Calculate rolling daily volatility including today's return
    stock["Volatility_5"] = stock["Daily_Return"].rolling(window=5).std()
    stock["Volatility_20"] = stock["Daily_Return"].rolling(window=20).std()
    
    # Calculate percentage change from the previous trading day's volume
    stock["Volume_Change"] = stock["Volume"].pct_change()
    
    # Future target only: never include Tomorrow_Return in input features (X)
    stock["Tomorrow_Return"] = stock["Daily_Return"].shift(-1)
    
    return stock
```

### models/__init__.py

```python
"""CastiFy models utilities."""
```

### models/baseline.py

```python
"""Explicit baseline dataset, purged holdout, and unchanged V3 forest."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from data.market_data import MarketDataError

FEATURE_COLUMNS = [
    "Return_Lag_1", "Return_Lag_2", "Return_Lag_3", "Return_Lag_5",
    "MA_5", "MA_20", "MA_50", "Volatility_5", "Volatility_20", "Volume_Change"
]
MIN_ML_OBSERVATIONS = 100


def prepare_ml_dataset(featured_data: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Select only the original features and target; remove required NaN rows."""
    data = featured_data[FEATURE_COLUMNS + ["Tomorrow_Return"]].dropna().copy()
    if len(data) < MIN_ML_OBSERVATIONS:
        raise MarketDataError("Insufficient historical data: need at least 100 usable ML rows.")
    # Zero preceding volume can cause infinite pct_change: do not impute it.
    if not np.isfinite(data.to_numpy()).all():
        raise MarketDataError("Non-finite ML values (possibly a percentage change from zero volume).")
    X = data[FEATURE_COLUMNS].copy()
    y = data["Tomorrow_Return"].copy()
    assert X.columns.tolist() == FEATURE_COLUMNS and X.shape[1] == 10
    assert "Tomorrow_Return" not in X.columns
    assert X.index.equals(y.index) and len(X) == len(y)
    assert X.index.is_unique and X.index.is_monotonic_increasing
    return X, y


def chronological_split(X: pd.DataFrame, y: pd.Series,
                        trading_index: pd.DatetimeIndex) -> dict:
    """Split 80/20 and purge labels reaching the test feature-date boundary."""
    assert X.index.equals(y.index)
    assert trading_index.is_unique and trading_index.is_monotonic_increasing
    split_index = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_index].copy(), X.iloc[split_index:].copy()
    y_train, y_test = y.iloc[:split_index].copy(), y.iloc[split_index:].copy()
    assert len(X_train) and len(X_test)
    target_dates = trading_index.to_series().shift(-1).loc[X_train.index]
    assert target_dates.notna().all()
    keep = target_dates < X_test.index.min()
    removed = X_train.index[~keep]
    X_train, y_train = X_train.loc[keep].copy(), y_train.loc[keep].copy()
    assert len(X_train) and len(X_train) == len(y_train)
    assert len(X_test) == len(y_test)
    assert X_train.index.equals(y_train.index) and X_test.index.equals(y_test.index)
    assert X_train.index.max() < X_test.index.min()
    assert X_train.index.intersection(X_test.index).empty
    assert (target_dates.loc[keep] < X_test.index.min()).all()
    assert X_test.equals(X.iloc[split_index:]) and y_test.equals(y.iloc[split_index:])
    assert len(X_train) + len(X_test) + len(removed) == len(X)
    for part in (X_train, X_test, y_train, y_test):
        assert np.isfinite(part.to_numpy()).all()
    return dict(X_train=X_train, X_test=X_test, y_train=y_train, y_test=y_test,
                train_before=split_index, removed=removed,
                latest_train_target=target_dates.loc[keep].max())


def evaluate_baseline(split: dict, featured_data: pd.DataFrame) -> dict:
    """Fit only purged training observations and evaluate the untouched holdout."""
    X_train, X_test = split["X_train"], split["X_test"]
    y_train, y_test = split["y_train"], split["y_test"]
    assert X_train.columns.tolist() == X_test.columns.tolist() == FEATURE_COLUMNS
    model = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    assert len(y_pred) == len(y_test) and np.isfinite(y_pred).all()
    today_returns = featured_data.loc[X_test.index, "Daily_Return"]
    assert today_returns.index.equals(y_test.index)
    assert np.isfinite(today_returns.to_numpy()).all()
    zero = np.zeros(len(y_test))
    metrics = dict(
        mae=mean_absolute_error(y_test, y_pred),
        rmse=float(np.sqrt(mean_squared_error(y_test, y_pred))),
        r2=r2_score(y_test, y_pred),
        zero_mae=mean_absolute_error(y_test, zero),
        zero_rmse=float(np.sqrt(mean_squared_error(y_test, zero))),
        direction=float(np.mean(np.sign(y_pred) == np.sign(y_test.to_numpy()))),
        momentum=float(np.mean(np.sign(today_returns.to_numpy()) == np.sign(y_test.to_numpy())))
    )
    results = pd.DataFrame({"Actual_Return": y_test, "Predicted_Return": y_pred,
                            "Prediction_Error": y_test - y_pred}, index=X_test.index)
    assert len(results) == len(y_test) and results.index.equals(X_test.index)
    assert np.isfinite(results.to_numpy()).all()
    importance = pd.DataFrame({"Feature": FEATURE_COLUMNS,
                               "Importance": model.feature_importances_})
    return dict(metrics=metrics, results=results,
                importance=importance.sort_values("Importance", ascending=False))


def print_baseline_report(X: pd.DataFrame, split: dict, evaluation: dict) -> None:
    """Display dataset sizes, boundary dates, and factual baseline comparisons."""
    print(f"\nML observations: {len(X)}; features: {X.shape[1]}")
    print(f"ML dates: {X.index.min().date()} to {X.index.max().date()}")
    print(f"Training before purge: {split['train_before']}")
    print(f"Removed dates: {[d.date().isoformat() for d in split['removed']]}")
    print("Removed labels realize on or after the first test feature date.")
    for label, key in (("Training", "X_train"), ("Testing", "X_test")):
        part = split[key]
        print(f"{label}: {len(part)} rows; {part.index.min().date()} to {part.index.max().date()}")
    print(f"Latest training target: {split['latest_train_target'].date()}")
    m = evaluation["metrics"]
    for name in ("mae", "rmse", "zero_mae", "zero_rmse"):
        print(f"{name}: {m[name]:.8f} ({m[name]:.4%})")
    print(f"R²: {m['r2']:.6f}")
    print(f"Direction: {m['direction']:.4%}; momentum baseline: {m['momentum']:.4%}; reference: 50%")
    print(f"RF minus zero MAE: {m['mae'] - m['zero_mae']:+.8f}")
    print(f"RF minus zero RMSE: {m['rmse'] - m['zero_rmse']:+.8f}")
    print(evaluation["results"].head(10).to_string())
    print("Feature importance (not causation):")
    print(evaluation["importance"].to_string(index=False))
    print("All dataset, target-boundary, and prediction assertions: PASS")
```

### tests/test_pipeline.py

```python
"""Offline checks for ingestion, feature semantics, and strict holdout isolation."""
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from data.market_data import (
    COLUMNS, MarketDataError, download_market_data, normalize_ticker,
    standardize_columns, validate_market_data
)
from features.basic_features import build_basic_features
from models.baseline import (
    FEATURE_COLUMNS, chronological_split, evaluate_baseline, prepare_ml_dataset
)


def sample_data(rows=180):
    """Make positive, varying data on a non-calendar-daily trading index."""
    index = pd.bdate_range("2020-01-01", periods=rows)
    close = 100 + np.arange(rows) * 0.1 + np.sin(np.arange(rows))
    return pd.DataFrame({"Open": close, "High": close + 2, "Low": close - 2,
                         "Close": close, "Volume": 1000 + np.arange(rows)}, index=index)


class PipelineTests(unittest.TestCase):
    def test_normalization(self):
        for raw, expected in ((" aapl ", "AAPL"), ("msft", "MSFT"),
                              ("brk-b", "BRK-B"), ("7203.t", "7203.T"), ("^gspc", "^GSPC")):
            self.assertEqual(normalize_ticker(raw), expected)
        for raw in ("", "  ", "AAPL MSFT", "AAPL,MSFT"):
            with self.assertRaises(MarketDataError):
                normalize_ticker(raw)

    def test_column_formats(self):
        data = sample_data()
        pd.testing.assert_frame_equal(standardize_columns(data, "ABC"), data)
        for reverse in (False, True):
            raw = data.copy()
            raw.columns = pd.MultiIndex.from_tuples(
                [("ABC", c) if reverse else (c, "ABC") for c in COLUMNS])
            pd.testing.assert_frame_equal(standardize_columns(raw, "ABC"), data)
        with self.assertRaises(MarketDataError):
            standardize_columns(raw, "WRONG")

    def test_missing_and_duplicate_columns(self):
        for bad in (sample_data().drop(columns="Close"),
                    pd.concat([sample_data(), sample_data()[["Close"]]], axis=1)):
            with self.assertRaises(MarketDataError):
                validate_market_data(bad)

    def test_date_validation(self):
        data = sample_data()
        for bad in (data.iloc[::-1], pd.concat([data, data.iloc[[-1]]]), data.reset_index()):
            with self.assertRaises(MarketDataError):
                validate_market_data(bad)

    def test_value_validation(self):
        for column, value in (("Close", np.nan), ("High", np.inf), ("Low", 0),
                              ("Open", -1), ("Volume", np.inf), ("Volume", -1)):
            data = sample_data().astype(float)
            data.loc[data.index[3], column] = value
            with self.assertRaises(MarketDataError):
                validate_market_data(data)
        validate_market_data(sample_data())

    def test_minimum_history(self):
        with self.assertRaisesRegex(MarketDataError, "Insufficient historical data"):
            validate_market_data(sample_data(149))
        validate_market_data(sample_data(150))
        with self.assertRaisesRegex(MarketDataError, "100 usable ML rows"):
            prepare_ml_dataset(build_basic_features(sample_data(149)))

    @patch("data.market_data.yf.download", return_value=pd.DataFrame())
    def test_unavailable_download(self, download):
        with self.assertRaisesRegex(MarketDataError, "Unable to retrieve"):
            download_market_data("bad-symbol", "2010-01-01")

    @patch("data.market_data.yf.download")
    def test_download_contract(self, download):
        download.return_value = sample_data()
        data = download_market_data(" abc ", "2020-01-01", "2021-01-01")
        self.assertEqual(list(data.columns), COLUMNS)
        self.assertEqual(download.call_args.args, ("ABC",))
        self.assertTrue(download.call_args.kwargs["auto_adjust"])
        self.assertTrue(download.call_args.kwargs["keepna"])
        self.assertEqual(download.call_args.kwargs["end"], "2021-01-01")

    def test_feature_semantics_and_nonmutation(self):
        raw = sample_data()
        original = raw.copy(deep=True)
        featured = build_basic_features(raw)
        pd.testing.assert_frame_equal(raw, original)
        returns = raw.Close.pct_change()
        np.testing.assert_allclose(featured.Daily_Return, returns, equal_nan=True)
        for lag in (1, 2, 3, 5):
            np.testing.assert_allclose(featured[f"Return_Lag_{lag}"], returns.shift(lag), equal_nan=True)
        for window in (5, 20, 50):
            self.assertAlmostEqual(featured[f"MA_{window}"].iloc[window - 1],
                                   sum(raw.Close.iloc[:window]) / window)
        for window in (5, 20):
            self.assertAlmostEqual(featured[f"Volatility_{window}"].iloc[window],
                                   np.std(returns.iloc[1:window + 1], ddof=1))
        np.testing.assert_allclose(featured.Volume_Change, raw.Volume.pct_change(), equal_nan=True)
        np.testing.assert_allclose(featured.Tomorrow_Return.iloc[:-1], returns.iloc[1:])
        self.assertTrue(pd.isna(featured.Tomorrow_Return.iloc[-1]))

    def test_future_changes_do_not_change_past_features(self):
        raw = sample_data()
        changed = raw.copy()
        changed.iloc[120:] *= 2
        before, after = build_basic_features(raw), build_basic_features(changed)
        pd.testing.assert_frame_equal(before[FEATURE_COLUMNS].iloc[:120],
                                      after[FEATURE_COLUMNS].iloc[:120])

    def test_dataset_and_purge_with_missing_trading_row(self):
        raw = sample_data().drop(sample_data().index[100])
        featured = build_basic_features(raw)
        X, y = prepare_ml_dataset(featured)
        self.assertEqual(X.columns.tolist(), FEATURE_COLUMNS)
        self.assertNotIn("Tomorrow_Return", X)
        self.assertNotIn("Daily_Return", X)
        split = chronological_split(X, y, raw.index)
        self.assertEqual(len(split["removed"]), 1)
        targets = raw.index.to_series().shift(-1).loc[split["X_train"].index]
        self.assertTrue((targets < split["X_test"].index.min()).all())
        pd.testing.assert_frame_equal(split["X_test"], X.iloc[int(len(X) * .8):])

    def test_zero_volume_infinity_is_rejected(self):
        data = sample_data()
        data.loc[data.index[90], "Volume"] = 0
        validate_market_data(data)
        with self.assertRaisesRegex(MarketDataError, "Non-finite ML values"):
            prepare_ml_dataset(build_basic_features(data))

    @patch("models.baseline.RandomForestRegressor")
    def test_fit_receives_only_purged_training(self, forest):
        featured = build_basic_features(sample_data())
        X, y = prepare_ml_dataset(featured)
        split = chronological_split(X, y, featured.index)
        forest.return_value.predict.return_value = np.zeros(len(split["y_test"]))
        forest.return_value.feature_importances_ = np.full(10, .1)
        result = evaluate_baseline(split, featured)
        forest.assert_called_once_with(n_estimators=300, random_state=42, n_jobs=-1)
        args = forest.return_value.fit.call_args.args
        self.assertIs(args[0], split["X_train"])
        self.assertIs(args[1], split["y_train"])
        self.assertTrue(result["results"].index.equals(split["X_test"].index))


if __name__ == "__main__":
    unittest.main()
```

### requirements.txt

```text
yfinance==1.7.0
pandas==3.0.6
numpy==2.5.3
scikit-learn==1.9.1
```

### reports/v3_baseline.json

```json
{
  "description": "Historical V3 run recorded before V4; not a new measurement",
  "ticker": "AAPL",
  "requested_start": "2020-01-01",
  "requested_end_exclusive": "2025-01-01",
  "raw_rows": 1258,
  "ml_rows": 1208,
  "train_rows_after_purge": 965,
  "test_rows": 242,
  "model": {"n_estimators": 300, "random_state": 42, "n_jobs": -1},
  "mae": 0.01303128,
  "rmse": 0.01669322,
  "r2": -0.381892,
  "directional_accuracy": 0.433884,
  "zero_mae": 0.01042097,
  "zero_rmse": 0.01426964,
  "momentum_accuracy": 0.533058
}
```

## 21. V3 BASELINE PRESERVATION

reports/v3_baseline.json records the original AAPL V3 measurement, explicitly
labelled historical evidence rather than a new run:
MAE 0.01303128; RMSE 0.01669322; R² -0.381892; directional accuracy 43.3884%.
The zero and momentum benchmarks outperformed it. The original feature formulas,
10-column selection, strict split, forest settings and evaluation formulas remain.

V4 AAPL metrics differ because the requested data window changed from
2020-01-01–2025-01-01 to 2010-01-01–2026-09-29 (exclusive ends). The training
and testing dates and observations therefore changed. Yahoo data can also be
revised or readjusted between downloads, and no original raw-data snapshot was
available to isolate those effects. This is not a controlled model-improvement
comparison; the original experiment was not retuned or relabelled successful.

## 22. V4 COMPLETION STATUS

V4 is complete: reusable ingestion, validation, features, dataset construction,
purged splitting and the unchanged forest execute successfully for AAPL, MSFT,
and JPM. International ingestion and expected invalid-symbol handling were checked.
No V5 indicators, new models, signals, backtests, or dashboard were implemented.

## 23. NEXT ARCHITECTURAL LIMITATIONS

- Yahoo/network availability, revised data and absence of immutable raw-data snapshots.
- Conservative UTC cutoff instead of exchange-session-aware latest completed data.
- Retrospective adjusted prices rather than point-in-time corporate-action data.
- One ticker per CLI invocation; no batching, caching or persisted model artifacts.
- One fixed chronological holdout; no walk-forward validation or uncertainty analysis.
- Bad/missing raw bars and infinite volume changes are rejected rather than repaired.
- Operational history thresholds do not establish statistically reliable forecasts.
- Baseline predictive performance remains weak; architecture success is not model efficacy.

These limitations are documented only, not implemented as additional scope.
