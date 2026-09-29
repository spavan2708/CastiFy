# CASTIFY V5 MASTER REPORT

## 1. ARCHITECTURE CHANGES

```text
main.py                              modified: FEATURE_SET switch
features/
  basic_features.py                  unchanged baseline
  registry.py                        explicit families and metadata
  numerics.py                        guarded ratios, Wilder recurrence
  price_features.py                  returns, ranges, SMA structure, drawdowns
  momentum_features.py               EMA structure, log slope, acceleration
  volatility_features.py             dispersion, distribution and asymmetry
  volume_features.py                 normalized participation and interactions
  technical_features.py              RSI, MACD, Bollinger, ATR
  feature_factory.py                 basic/advanced orchestration
  audit.py                           redundancy diagnostics
models/
  baseline.py                        explicit selectable registries, unchanged RF
  feature_comparison.py              aligned controlled experiments
 tests/
  test_pipeline.py                   unchanged V4 tests
  test_advanced_features.py           V5 tests
reports/
  v5_feature_catalog.md
  v5_feature_metadata.json
  v5_experiments.json
  v5_experiments.txt
  v5_tests.txt
  v5_master_report.md
```

Data ingestion, basic feature calculations, package initializers, dependencies,
and previous V3/V4 evidence remain unchanged. No additional dependencies.

## 2. FILES CREATED

- features/registry.py
- features/numerics.py
- features/price_features.py
- features/momentum_features.py
- features/volatility_features.py
- features/volume_features.py
- features/technical_features.py
- features/feature_factory.py
- features/audit.py
- models/feature_comparison.py
- tests/test_advanced_features.py
- reports/v5_feature_catalog.md
- reports/v5_feature_metadata.json
- reports/v5_experiments.json
- reports/v5_experiments.txt
- reports/v5_tests.txt
- reports/v5_master_report.md

## 3. FILES MODIFIED

- main.py
- models/baseline.py

## 4. FEATURE FACTORY DESIGN

build_feature_set(stock, feature_set="advanced") returns a new dataframe.
get_feature_columns selects explicit BASIC_FEATURES or ADVANCED_FEATURES.
ADVANCED_FEATURES is an ordered union of six named groups; no numeric-column
inference occurs. Families can be removed from that explicit assembly for later
ablation work. The future target never enters either registry. Shared computations
may remain as intermediate columns but only registry entries enter X.

main.py retains FEATURE_SET="basic" by default for compatibility; setting it to
"advanced" selects V5 end to end. Dataset preparation and evaluation both accept
the same explicit feature_set argument and default to basic.

Controlled experiments are rerunnable with:

```sh
venv/bin/python -m models.feature_comparison AAPL MSFT JPM
```

## 5. FEATURE CATALOG SUMMARY

| Advanced family | Inputs |
|---|---|
| returns | 11 |
| price_structure | 21 |
| momentum | 7 |
| volatility | 17 |
| volume | 7 |
| technical | 7 |
| TOTAL | 70 |

The separate historical BASIC_FEATURES registry contains exactly 10 inputs.

## 6. COMPLETE ADVANCED FEATURE LIST

### returns

```text
Return_Lag_1
Return_Lag_2
Return_Lag_3
Return_Lag_5
Return_1D
Return_2D
Return_3D
Return_5D
Return_10D
Return_20D
Return_60D
```

### price_structure

```text
Intraday_Return
Overnight_Gap
High_Low_Range
Close_Open_Position
Price_to_SMA_5
Price_to_SMA_10
Price_to_SMA_20
Price_to_SMA_50
Price_to_SMA_100
Price_to_SMA_200
SMA_5_to_20
SMA_20_to_50
SMA_50_to_200
Distance_From_20D_High
Distance_From_20D_Low
Distance_From_60D_High
Distance_From_60D_Low
Range_Position_20
Drawdown_From_20D_Peak
Drawdown_From_60D_Peak
Drawdown_From_252D_Peak
```

### momentum

```text
Price_to_EMA_5
Price_to_EMA_10
Price_to_EMA_20
Price_to_EMA_50
Log_Price_Slope_20
Log_Price_Slope_60
Return_5D_Acceleration
```

### volatility

```text
Volatility_5
Volatility_10
Volatility_20
Volatility_60
Volatility_Ratio_5_20
Volatility_Ratio_20_60
Rolling_Mean_Return_5
Rolling_Mean_Return_20
Rolling_Mean_Return_60
Rolling_Skew_20
Rolling_Skew_60
Rolling_Kurtosis_20
Rolling_Kurtosis_60
Positive_Return_Ratio_20
Negative_Return_Ratio_20
Downside_Volatility_20
Upside_Volatility_20
```

### volume

```text
Volume_Change
Relative_Volume_5
Relative_Volume_20
Volume_Return_Correlation_20
OBV_Flow_20
Return_x_VolumeChange
Momentum_x_RelativeVolume
```

### technical

```text
RSI_14
MACD_Pct
MACD_Signal_Pct
MACD_Histogram_Pct
Bollinger_Position
Bollinger_Width
ATR_14_Pct
```

## 7. FEATURE DEFINITIONS

All windows count trading rows, not calendar days. Calculations use completed
current and historical bars. Minimum raw rows describe first possible availability,
not a guarantee that a conditional statistic is defined. No warm-up is backfilled.
Normalized means invariant to multiplying every OHLC price by one positive constant
and every volume by another; it does not mean standardized variance or equal units.

The basic registry retains its original 10 columns, including absolute MA_5/20/50.
The advanced registry has 70 inputs and excludes raw OHLCV, raw SMA/EMA/ATR/MACD,
raw cumulative OBV and Tomorrow_Return. Daily_Return is not selected by name;
Return_1D intentionally supplies the same current-return information once in
advanced mode. Rate-of-change Momentum_5/10/20/60 aliases are omitted because
Return_5D/10D/20D/60D already represent them. Annualized volatility copies are omitted.

RSI and ATR use arithmetic Wilder seeds, followed by alpha=1/14 recurrences. EMA
uses adjust=False, seeded with the first available price, and a span-length output
warm-up. MACD signal begins with the first valid raw MACD, with nine valid MACD
observations before publication. These initialization choices are deterministic
but may differ from external chart packages.

Bollinger uses population std (ddof=0); return volatility uses sample std (ddof=1).
Flat Bollinger/range positions are 0.5; a flat close-open bar position is 0. RSI is
50 for no movement, 100 for only gains, and 0 for only losses. Other undefined
zero-denominator ratios stay NaN. Conditional downside/upside std requires at
least two negative/positive returns inside a fully observed 20-return window.
Correlation requires both rolling standard deviations > 1e-12; otherwise it is
undefined. Valid correlations are bounded to [-1,1] for numerical roundoff.
No infinities are replaced with arbitrary constants.

Distribution features use [pandas unbiased skew and Fisher excess kurtosis](https://pandas.pydata.org/docs/reference/window.html).
Recursive EMA behavior follows [pandas EWM](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html).
High/low distances use intraday High/Low, while drawdowns use closing-price peaks,
so they are not mathematical duplicates. Arithmetic mean returns differ from
compounded multi-session returns even when their correlations are high.


The full feature-by-feature formulas, including all lookbacks, are in
v5_feature_catalog.md. Key additional definitions:

- Trailing return: Close(t)/Close(t-n)-1; historical lags retain V1 semantics.
- Intraday: Close/Open-1; overnight: Open/previous Close-1; daily range: (High-Low)/Close.
- Close_Open_Position: (Close-Open)/(High-Low), a signed within-bar displacement.
- SMA/EMA distances: Close/average-1; SMA relationships: short average/long average-1.
- Trend: rolling OLS slope of log Close against trading-row position, in log units/session.
- Acceleration: Return_5D minus the preceding row's Return_5D.
- Volatility ratios: short sample return std / long sample return std; not annualized.
- Conditional volatility: sample dispersion of only positive/negative returns in the window,
  not semideviation about zero. Positive/negative ratios count zeros in the denominator.
- OBV_Flow_20: sum(sign(return)*volume,20)/sum(volume,20), normalized trailing signed flow.
- Interactions: Daily_Return*Volume_Change and Return_5D*Relative_Volume_20, only two.

## 8. FEATURE METADATA

FEATURE_METADATA contains a record per feature: name, family, description,
minimum_raw_rows, normalized, future_safe. Assertions check full registry coverage.
A machine-readable JSON export is saved as reports/v5_feature_metadata.json.
Warm-up is a minimum: zero denominators or insufficient one-sided returns can
make later observations undefined too. EWM calculations use all preceding history,
not just their minimum output warm-up.

## 9. NUMERICAL SAFETY

Undefined ratios are NaN; valid explicitly neutral flat-case conventions are
listed above. Warm-up NaNs stay missing. No backfill, interpolation, future
initialization or arbitrary infinity replacement exists. Advanced generation
rejects infinities. Before fitting, required NaN rows are removed and any remaining
non-finite values are rejected. Every split and all predictions are checked finite.
Wilder smoothing rejects internal missing observations instead of silently skipping.
No fitted scaler or preprocessing transformation is used.

## 10. REDUNDANCY AUDIT

Thresholds: absolute Pearson correlation >=0.98; near-zero sample variance <=1e-12
(excluding separately reported constants). Exact duplicates require equal sample
values. Both purged training matrices and complete eligible matrices were audited.
Full-sample diagnostics are descriptive only and were not used to fit, tune or select.

| Ticker | Exact duplicates | Constants | Near-zero variance | High-correlation pairs (train/full) |
|---|---|---|---|---|
| AAPL | 0 | 0 | 0 | 9/9 |
| MSFT | 0 | 0 | 0 | 9/9 |
| JPM | 0 | 0 | 0 | 9/9 |

The same nine pairs were flagged for all three tickers; training correlations:

| Feature A | Feature B | AAPL | MSFT | JPM |
|---|---|---|---|---|
| Return_5D | Rolling_Mean_Return_5 | 0.999455 | 0.999236 | 0.998905 |
| Return_20D | Rolling_Mean_Return_20 | 0.998424 | 0.998105 | 0.997098 |
| Return_60D | Rolling_Mean_Return_60 | 0.994300 | 0.994720 | 0.995699 |
| Price_to_SMA_10 | Price_to_EMA_10 | 0.981332 | 0.980546 | 0.980580 |
| Price_to_SMA_20 | Price_to_EMA_20 | 0.982864 | 0.982247 | 0.981113 |
| Price_to_SMA_50 | Price_to_EMA_50 | 0.982834 | 0.982550 | 0.982625 |
| Distance_From_20D_High | Drawdown_From_20D_Peak | 0.990353 | 0.988222 | 0.993099 |
| Distance_From_60D_High | Drawdown_From_60D_Peak | 0.996027 | 0.994043 | 0.997389 |
| Positive_Return_Ratio_20 | Negative_Return_Ratio_20 | -0.996483 | -0.980526 | -0.987261 |

No features were dropped based on correlation or importance. These are not
exact mathematical duplicates: compounded versus mean returns differ; EMA and
SMA weight history differently; intraday-high distances differ from close-peak
drawdowns; positive/negative fractions need not sum to one when returns are zero.
All exact full-sample correlations and diagnostics are retained in v5_experiments.json.

## 11. DATASET RESULTS

All raw data spans 2010-01-04 through 2026-09-28; exclusive download cutoff
2026-09-29. Same raw dataframe used for both models within each ticker.

| Ticker | Raw rows | Advanced ML rows | Inputs | Warm-up rows | Train | Test |
|---|---|---|---|---|---|---|
| AAPL | 4209 | 3957 | 70 | 251 | 3164 | 792 |
| MSFT | 4209 | 3957 | 70 | 251 | 3164 | 792 |
| JPM | 4209 | 3957 | 70 | 251 | 3164 | 792 |

There are 251 initial warm-up rows for the 252-close drawdown, plus one final
missing-target row. No additional internal rows were removed in these live runs.
The full basic dataset has 4,159 rows, but controlled fitting uses the same 3,957
eligible dates as advanced. An initial 3,165 training rows becomes 3,164 after purge.
Both models test on exactly 792 identical dates, 2023-08-01 through 2026-09-25.
The final test target uses the 2026-09-28 completed return. Training target dates
are strictly earlier than 2023-08-01. Detailed train/purge dates are in the JSON.

## 12. CONTROLLED BASIC VS ADVANCED MODEL RESULTS

RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1) was used for
all six fits, without tuning. MAE/RMSE are daily-return decimals below.

| Ticker | Mode | MAE | RMSE | R² | Direction |
|---|---|---|---|---|---|
| AAPL | basic | 0.01242725 | 0.01749285 | -0.081367 | 48.6111% |
| AAPL | advanced | 0.01182928 | 0.01741998 | -0.072376 | 54.4192% |
| MSFT | basic | 0.01275085 | 0.01765425 | -0.167304 | 49.1162% |
| MSFT | advanced | 0.01195697 | 0.01732441 | -0.124093 | 48.8636% |
| JPM | basic | 0.01131783 | 0.01553298 | -0.171734 | 44.8232% |
| JPM | advanced | 0.01057899 | 0.01494533 | -0.084750 | 51.6414% |

| Ticker | Zero-return MAE | Zero-return RMSE | Previous-day direction |
|---|---|---|---|
| AAPL | 0.01148608 | 0.01684341 | 51.1364% |
| MSFT | 0.01117059 | 0.01635467 | 49.3687% |
| JPM | 0.01004296 | 0.01439549 | 50.7576% |

Advanced MAE and RMSE decreased, and R² became less negative, for each ticker
in this controlled experiment. Directional accuracy improved for AAPL and JPM but
slightly declined for MSFT. AAPL/JPM advanced direction exceeded the momentum
benchmark; MSFT did not. Every model still had negative R² and larger MAE/RMSE
than the zero-return benchmark. These results do not establish general predictive
superiority or trading usefulness. No model settings were changed after inspection.

The comparison does not reuse old V4 metrics: the old test window differs because
of warm-up. Both basic and advanced were rerun on the same raw snapshot and aligned
training/test dates. Earlier V3/V4 benchmark evidence remains untouched.

## 13. TOP ADVANCED FEATURE IMPORTANCES

Impurity-based importance is not causation. Correlated variables can share credit,
and this diagnostic was not used to remove features.

### AAPL

| Rank | Feature | Importance |
|---|---|---|
| 1 | High_Low_Range | 0.028658 |
| 2 | Return_Lag_5 | 0.025174 |
| 3 | Relative_Volume_20 | 0.023232 |
| 4 | Overnight_Gap | 0.022656 |
| 5 | Return_x_VolumeChange | 0.020992 |
| 6 | Return_Lag_2 | 0.020967 |
| 7 | Return_Lag_3 | 0.020722 |
| 8 | Price_to_SMA_10 | 0.020245 |
| 9 | Momentum_x_RelativeVolume | 0.020229 |
| 10 | SMA_50_to_200 | 0.020051 |
| 11 | Rolling_Skew_60 | 0.019967 |
| 12 | Return_Lag_1 | 0.019866 |
| 13 | Relative_Volume_5 | 0.019672 |
| 14 | Volume_Change | 0.019589 |
| 15 | Return_1D | 0.019146 |

### MSFT

| Rank | Feature | Importance |
|---|---|---|
| 1 | Return_Lag_1 | 0.025610 |
| 2 | High_Low_Range | 0.025559 |
| 3 | SMA_50_to_200 | 0.024390 |
| 4 | MACD_Histogram_Pct | 0.022827 |
| 5 | Return_Lag_5 | 0.022178 |
| 6 | Return_Lag_3 | 0.021997 |
| 7 | Return_5D_Acceleration | 0.021084 |
| 8 | Price_to_SMA_20 | 0.020948 |
| 9 | Return_Lag_2 | 0.020710 |
| 10 | Overnight_Gap | 0.020340 |
| 11 | Return_x_VolumeChange | 0.020313 |
| 12 | Return_1D | 0.020032 |
| 13 | Relative_Volume_20 | 0.020016 |
| 14 | Volume_Change | 0.019227 |
| 15 | OBV_Flow_20 | 0.018568 |

### JPM

| Rank | Feature | Importance |
|---|---|---|
| 1 | Return_Lag_1 | 0.031756 |
| 2 | Return_Lag_3 | 0.031270 |
| 3 | Drawdown_From_252D_Peak | 0.028958 |
| 4 | Overnight_Gap | 0.028209 |
| 5 | Return_Lag_5 | 0.026945 |
| 6 | Price_to_SMA_200 | 0.023348 |
| 7 | Return_Lag_2 | 0.021094 |
| 8 | SMA_5_to_20 | 0.021028 |
| 9 | Rolling_Kurtosis_60 | 0.020706 |
| 10 | SMA_50_to_200 | 0.020135 |
| 11 | Return_5D_Acceleration | 0.019902 |
| 12 | MACD_Histogram_Pct | 0.018558 |
| 13 | Volatility_10 | 0.018214 |
| 14 | High_Low_Range | 0.017951 |
| 15 | Return_x_VolumeChange | 0.017950 |

## 14. CROSS-TICKER SCALE AUDIT

All 70 advanced inputs are dimensionless, bounded indicators or per-session log
slopes. None intentionally retains raw price or raw volume scale. Absolute baseline
MA_5/20/50 remain only for historical basic compatibility. RSI's 0–100 units differ
from decimal returns; scale invariance does not imply identical statistical scales.

For each live stock, all OHLC values were multiplied by 7 and volume by 11, then
all features rebuilt. Every feature matched at rtol=atol=1e-6, with the same NaN
locations. The maximum measured absolute differences were:

| Ticker | Max absolute difference | Outcome |
|---|---|---|
| AAPL | 1.108e-11 | PASS |
| MSFT | 2.137e-11 | PASS |
| JPM | 1.320e-11 | PASS |

Per-feature median absolute magnitudes for all three tickers are also saved in
the experiment JSON; differences represent behavior, not an imposed price/volume unit.
A separate automated scaling test uses factors 11 and 7 with tighter 1e-7 tolerance.

## 15. FUTURE-PERTURBATION LEAKAGE TEST

PASS. On 400 synthetic trading rows, a historical cutoff at row 300 was selected.
All subsequent OHLC rows were multiplied by deterministic varying positive factors,
and subsequent volumes by 3. Rebuilt values for all 70 inputs at/before the cutoff
matched exactly, including NaNs. A second comparison rebuilt using only the prefix
ending at the cutoff; those features also matched exactly. Tomorrow_Return is
excluded because it intentionally references the following trading row.

## 16. LEAKAGE AUDIT

| Check | Result |
|---|---|
| Every input uses current/past information only | PASS |
| No negative shifts in inputs | PASS |
| Target isolated | PASS |
| Target absent from registry | PASS |
| Chronological split | PASS |
| Purged target-realization boundary | PASS |
| No test data fitted | PASS |
| No random row shuffling | PASS |
| No backward fill | PASS |
| No future interpolation | PASS |
| Whole-registry future perturbation test | PASS |

The only negative shift in feature construction remains Tomorrow_Return; another
maps target dates for purging. Those are not ML inputs. Raw Yahoo history remains
retrospectively adjusted rather than point-in-time; these assertions establish
causality of computations on the supplied data, not historical data-vintage purity.

## 17. AUTOMATED TESTS

24 tests executed, 24 passed, zero failures: all 13 unchanged V4 tests plus 11 V5
tests. Offline tests include independent RSI/MACD/ATR recurrences, multi-day returns,
nonzero intraday return, overnight gap, range/drawdown, relative volume, Bollinger,
conditional volatility, OBV flow, exponential-price log slopes, flat/one-sided cases,
registry coverage, basic compatibility, finite datasets, purge, scaling, duplicate
and variance detection, and the full future-perturbation check.

```sh
venv/bin/python -m unittest discover -s tests -v
```

V5 module imports also passed without running downloads. All six live fits completed
with their finite-matrix, alignment, benchmark-equality and strict-boundary assertions.

## 18. PERFORMANCE

Feature-generation wall-clock times (excludes download, audit and model training):

| Ticker | Raw rows | Seconds |
|---|---|---|
| AAPL | 4209 | 0.0526 |
| MSFT | 4209 | 0.0398 |
| JPM | 4209 | 0.0393 |

Most calculations are vectorized pandas rolling operations. Two log-price slopes
use fixed-window dot products in rolling.apply (20 and 60 rows); there is no quadratic
all-history algorithm. These are single-run timing observations, not rigorous benchmarks.

## 19. V4 REGRESSION CHECK

All 13 V4 tests still pass unchanged. Basic output matches build_basic_features
exactly; the original feature list and RF settings are preserved. Three live basic
models successfully ran on the controlled common dates. main.py still defaults to
basic. Original basic_features.py, ingestion code, requirements and historical
V3/V4 report artifacts were not modified. No new dependencies were introduced.

## 20. DOCUMENTATION

reports/v5_feature_catalog.md contains all 70 feature formulas, families, warm-ups,
normalization and causality flags, plus basic-only absolute MAs, initialization
conventions, undefined cases and intentionally omitted duplicates.
reports/v5_feature_metadata.json provides a machine-readable export.

## 21. ERRORS/WARNINGS

The initial restricted-network comparison failed Yahoo DNS resolution before model
training. The authorized network-enabled rerun completed all three tickers and six
fits successfully. The diagnostic runner leaves unexpected failures visible; the
existing main.py continues to handle expected market-data errors gracefully.
Successful model runs produced no runtime warnings. Two old pandas documentation
URLs returned 404; the current API documentation was located and used instead.
No numerical test failures occurred. No metrics were used to tune the forest.

## 22. COMPLETE SOURCE CODE

Complete contents of every created or modified Python source file follow. Basic
feature and data ingestion modules were unchanged and remain documented in V4.

### main.py

```python
"""Terminal orchestration for the CastiFy V5 research pipeline."""
from data.market_data import (
    MarketDataError, download_market_data, normalize_ticker, print_data_report
)
from features.feature_factory import build_feature_set
from models.baseline import (
    chronological_split, evaluate_baseline, prepare_ml_dataset, print_baseline_report
)

START_DATE = "2010-01-01"
END_DATE = None
FEATURE_SET = "basic"  # Set to "advanced" for the V5 diagnostic.


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
        featured = build_feature_set(stock, FEATURE_SET)
        X, y = prepare_ml_dataset(featured, FEATURE_SET)
        split = chronological_split(X, y, featured.index)
        evaluation = evaluate_baseline(split, featured, FEATURE_SET)
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

### models/baseline.py

```python
"""Explicit baseline dataset, purged holdout, and unchanged V3 forest."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from data.market_data import MarketDataError

from features.registry import BASIC_FEATURES, get_feature_columns

FEATURE_COLUMNS = BASIC_FEATURES.copy()
MIN_ML_OBSERVATIONS = 100


def prepare_ml_dataset(featured_data: pd.DataFrame, feature_set: str = "basic") -> tuple[pd.DataFrame, pd.Series]:
    """Select the requested explicit registry and target; remove required NaN rows."""
    columns = get_feature_columns(feature_set)
    data = featured_data[columns + ["Tomorrow_Return"]].dropna().copy()
    if len(data) < MIN_ML_OBSERVATIONS:
        raise MarketDataError("Insufficient historical data: need at least 100 usable ML rows.")
    # Zero preceding volume can cause infinite pct_change: do not impute it.
    if not np.isfinite(data.to_numpy()).all():
        raise MarketDataError("Non-finite ML values (possibly a percentage change from zero volume).")
    X = data[columns].copy()
    y = data["Tomorrow_Return"].copy()
    assert X.columns.tolist() == columns and X.shape[1] == len(columns)
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


def evaluate_baseline(split: dict, featured_data: pd.DataFrame, feature_set: str = "basic") -> dict:
    """Fit only purged training observations and evaluate the untouched holdout."""
    X_train, X_test = split["X_train"], split["X_test"]
    y_train, y_test = split["y_train"], split["y_test"]
    columns = get_feature_columns(feature_set)
    assert X_train.columns.tolist() == X_test.columns.tolist() == columns
    assert "Tomorrow_Return" not in columns
    assert X_train.index.max() < X_test.index.min()
    assert (featured_data.index.to_series().shift(-1).loc[X_train.index] < X_test.index.min()).all()
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
    importance = pd.DataFrame({"Feature": columns,
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

### features/registry.py

```python
"""Explicit feature families and machine-readable research definitions."""
BASIC_FEATURES = [
    "Return_Lag_1", "Return_Lag_2", "Return_Lag_3", "Return_Lag_5",
    "MA_5", "MA_20", "MA_50", "Volatility_5", "Volatility_20", "Volume_Change"
]
RETURN_FEATURES = ["Return_Lag_1", "Return_Lag_2", "Return_Lag_3", "Return_Lag_5",
                   "Return_1D", "Return_2D", "Return_3D", "Return_5D", "Return_10D", "Return_20D", "Return_60D"]
PRICE_STRUCTURE_FEATURES = [
    "Intraday_Return", "Overnight_Gap", "High_Low_Range", "Close_Open_Position",
    "Price_to_SMA_5", "Price_to_SMA_10", "Price_to_SMA_20", "Price_to_SMA_50",
    "Price_to_SMA_100", "Price_to_SMA_200", "SMA_5_to_20", "SMA_20_to_50", "SMA_50_to_200",
    "Distance_From_20D_High", "Distance_From_20D_Low", "Distance_From_60D_High",
    "Distance_From_60D_Low", "Range_Position_20",
    "Drawdown_From_20D_Peak", "Drawdown_From_60D_Peak", "Drawdown_From_252D_Peak"
]
MOMENTUM_FEATURES = ["Price_to_EMA_5", "Price_to_EMA_10", "Price_to_EMA_20", "Price_to_EMA_50",
                     "Log_Price_Slope_20", "Log_Price_Slope_60", "Return_5D_Acceleration"]
VOLATILITY_FEATURES = [
    "Volatility_5", "Volatility_10", "Volatility_20", "Volatility_60",
    "Volatility_Ratio_5_20", "Volatility_Ratio_20_60",
    "Rolling_Mean_Return_5", "Rolling_Mean_Return_20", "Rolling_Mean_Return_60",
    "Rolling_Skew_20", "Rolling_Skew_60", "Rolling_Kurtosis_20", "Rolling_Kurtosis_60",
    "Positive_Return_Ratio_20", "Negative_Return_Ratio_20",
    "Downside_Volatility_20", "Upside_Volatility_20"
]
VOLUME_FEATURES = ["Volume_Change", "Relative_Volume_5", "Relative_Volume_20",
                   "Volume_Return_Correlation_20", "OBV_Flow_20",
                   "Return_x_VolumeChange", "Momentum_x_RelativeVolume"]
TECHNICAL_FEATURES = ["RSI_14", "MACD_Pct", "MACD_Signal_Pct", "MACD_Histogram_Pct",
                      "Bollinger_Position", "Bollinger_Width", "ATR_14_Pct"]
FEATURE_GROUPS = dict(returns=RETURN_FEATURES, price_structure=PRICE_STRUCTURE_FEATURES,
                      momentum=MOMENTUM_FEATURES, volatility=VOLATILITY_FEATURES,
                      volume=VOLUME_FEATURES, technical=TECHNICAL_FEATURES)
ADVANCED_FEATURES = [name for group in FEATURE_GROUPS.values() for name in group]
assert len(ADVANCED_FEATURES) == len(set(ADVANCED_FEATURES))
assert "Tomorrow_Return" not in BASIC_FEATURES + ADVANCED_FEATURES


def get_feature_columns(feature_set: str = "basic") -> list[str]:
    """Return a fresh explicit registry; never infer inputs from dataframe dtypes."""
    if feature_set not in ("basic", "advanced"):
        raise ValueError("feature_set must be 'basic' or 'advanced'.")
    return (BASIC_FEATURES if feature_set == "basic" else ADVANCED_FEATURES).copy()


FEATURE_METADATA = {}


def _describe(name, description, rows, normalized=True):
    family = next((family for family, names in FEATURE_GROUPS.items() if name in names), "basic")
    FEATURE_METADATA[name] = dict(name=name, family=family, description=description,
                                  minimum_raw_rows=rows, normalized=normalized, future_safe=True)


for n in (1, 2, 3, 5):
    _describe(f"Return_Lag_{n}", f"Daily_Return shifted back {n} trading rows.", n + 2)
for n in (1, 2, 3, 5, 10, 20, 60):
    _describe(f"Return_{n}D", f"Close / Close.shift({n}) - 1; trailing compounded return.", n + 1)
for name, formula, rows in [
    ("Intraday_Return", "Close / Open - 1", 1),
    ("Overnight_Gap", "Open / previous Close - 1", 2),
    ("High_Low_Range", "(High - Low) / Close", 1),
    ("Close_Open_Position", "(Close - Open) / (High - Low); zero on a flat bar", 1),
    ("Range_Position_20", "(Close - rolling Low.min(20)) / (rolling High.max(20) - rolling Low.min(20)); flat range=0.5", 20)]:
    _describe(name, formula, rows)
for n in (5, 10, 20, 50, 100, 200):
    _describe(f"Price_to_SMA_{n}", f"Close / rolling mean(Close, {n}) - 1", n)
for a, b in ((5, 20), (20, 50), (50, 200)):
    _describe(f"SMA_{a}_to_{b}", f"SMA_{a} / SMA_{b} - 1", b)
for n in (20, 60):
    _describe(f"Distance_From_{n}D_High", f"Close / rolling max(High, {n}) - 1 (intraday highs)", n)
    _describe(f"Distance_From_{n}D_Low", f"Close / rolling min(Low, {n}) - 1 (intraday lows)", n)
    _describe(f"Log_Price_Slope_{n}", f"OLS slope of log Close against 0..{n-1}; log-return units per trading row", n)
for n in (20, 60, 252):
    _describe(f"Drawdown_From_{n}D_Peak", f"Close / rolling max(Close, {n}) - 1; nonpositive", n)
for n in (5, 10, 20, 50):
    _describe(f"Price_to_EMA_{n}", f"Close / EMA(span={n}, adjust=False, min_periods={n}) - 1; seeded with first close", n)
_describe("Return_5D_Acceleration", "Return_5D - previous row's Return_5D", 7)
for n in (5, 10, 20, 60):
    _describe(f"Volatility_{n}", f"Trailing {n} Daily_Return sample standard deviation, ddof=1", n + 1)
for a, b in ((5, 20), (20, 60)):
    _describe(f"Volatility_Ratio_{a}_{b}", f"Volatility_{a} / Volatility_{b}; zero denominator undefined", b + 1)
for n in (5, 20, 60):
    _describe(f"Rolling_Mean_Return_{n}", f"Arithmetic mean of last {n} daily returns", n + 1)
for n in (20, 60):
    _describe(f"Rolling_Skew_{n}", f"Pandas unbiased rolling sample skew of {n} daily returns", n + 1)
    _describe(f"Rolling_Kurtosis_{n}", f"Pandas unbiased Fisher excess kurtosis of {n} returns (normal=0)", n + 1)
for name, sign in (("Positive", "> 0"), ("Negative", "< 0")):
    _describe(f"{name}_Return_Ratio_20", f"Fraction of 20 valid daily returns {sign}; zeros count in denominator", 21)
for name, sign in (("Downside", "< 0"), ("Upside", "> 0")):
    _describe(f"{name}_Volatility_20", f"Sample std of returns {sign} inside 20-return window; NaN with fewer than 2 qualifying values", 21)
_describe("Volume_Change", "Volume / previous Volume - 1; zero denominator undefined", 2)
for n in (5, 20):
    _describe(f"Relative_Volume_{n}", f"Volume / rolling mean(Volume, {n}); zero denominator undefined", n)
_describe("Volume_Return_Correlation_20", "Pearson correlation of 20 paired Volume_Change and Daily_Return values; constant input undefined", 21)
_describe("OBV_Flow_20", "sum(sign(Daily_Return) * Volume, 20) / sum(Volume, 20); normalized trailing OBV change", 21)
_describe("Return_x_VolumeChange", "Daily_Return * Volume_Change; signed return amplified by volume change", 2)
_describe("Momentum_x_RelativeVolume", "Return_5D * Relative_Volume_20; trailing momentum weighted by volume participation", 20)
_describe("RSI_14", "Wilder gain/loss averages seeded with first 14 changes; 100 for gain-only, 0 for loss-only, 50 if both zero", 15)
for name, formula, rows in [
    ("MACD_Pct", "(EMA_12 - EMA_26) / Close", 26),
    ("MACD_Signal_Pct", "EMA_9(raw MACD) / Close", 34),
    ("MACD_Histogram_Pct", "(raw MACD - raw signal) / Close", 34),
    ("Bollinger_Position", "(Close - lower) / (upper - lower), bands=SMA_20 +/- 2 population std; flat=0.5", 20),
    ("Bollinger_Width", "(upper - lower) / SMA_20", 20),
    ("ATR_14_Pct", "Wilder mean of True Range / Close; first TR=High-Low; 14-TR arithmetic seed", 14)]:
    _describe(name, formula, rows)
for n in (5, 20, 50):
    _describe(f"MA_{n}", f"Unchanged baseline rolling mean(Close, {n}); absolute adjusted price", n, False)
assert set(BASIC_FEATURES + ADVANCED_FEATURES) == set(FEATURE_METADATA)
```

### features/numerics.py

```python
"""Explicit zero-denominator and historical smoothing conventions."""
import pandas as pd


def divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Leave undefined zero-denominator ratios missing, never substitute infinity."""
    return numerator / denominator.where(denominator != 0)


def wilder_average(values: pd.Series, window: int) -> pd.Series:
    """Seed with the first full arithmetic mean, then recur with alpha=1/window.

    Leading NaNs are allowed. Internal missing inputs are rejected: silently
    skipping them would change the meaning of the recurrence.
    """
    start = values.first_valid_index()
    if start is None:
        return values.copy()
    valid = values.loc[start:]
    if valid.isna().any():
        raise ValueError("Wilder smoothing requires contiguous valid observations.")
    seeded = values.astype(float).copy()
    seeded[:] = float("nan")
    if len(valid) >= window:
        seed_position = values.index.get_loc(start) + window - 1
        seeded.iloc[seed_position] = valid.iloc[:window].mean()
        seeded.iloc[seed_position + 1:] = values.iloc[seed_position + 1:]
    return seeded.ewm(alpha=1 / window, adjust=False, ignore_na=False).mean()
```

### features/price_features.py

```python
"""Trailing returns, normalized price structure and peak/range positions."""
import pandas as pd
from features.numerics import divide


def price_features(stock: pd.DataFrame) -> pd.DataFrame:
    """Use completed current OHLC and historical rows only."""
    c, o, h, low = (stock[name] for name in ("Close", "Open", "High", "Low"))
    features = {f"Return_{n}D": c.pct_change(n, fill_method=None) for n in (1, 2, 3, 5, 10, 20, 60)}
    features.update(Intraday_Return=divide(c, o) - 1,
                    Overnight_Gap=divide(o, c.shift(1)) - 1,
                    High_Low_Range=divide(h - low, c),
                    Close_Open_Position=divide(c - o, h - low).mask((h == low) & (c == o), 0))
    sma = {n: c.rolling(n).mean() for n in (5, 10, 20, 50, 100, 200)}
    features.update({f"Price_to_SMA_{n}": divide(c, mean) - 1 for n, mean in sma.items()})
    for a, b in ((5, 20), (20, 50), (50, 200)):
        features[f"SMA_{a}_to_{b}"] = divide(sma[a], sma[b]) - 1
    for n in (20, 60):
        features[f"Distance_From_{n}D_High"] = divide(c, h.rolling(n).max()) - 1
        features[f"Distance_From_{n}D_Low"] = divide(c, low.rolling(n).min()) - 1
    upper, lower = h.rolling(20).max(), low.rolling(20).min()
    features["Range_Position_20"] = divide(c - lower, upper - lower).mask(upper == lower, .5)
    for n in (20, 60, 252):
        drawdown = divide(c, c.rolling(n).max()) - 1
        assert (drawdown.dropna() <= 1e-12).all()
        features[f"Drawdown_From_{n}D_Peak"] = drawdown
    return pd.DataFrame(features, index=stock.index)
```

### features/momentum_features.py

```python
"""Scale-invariant EMA distance, log-price trends and return acceleration."""
import numpy as np
import pandas as pd
from features.numerics import divide


def momentum_features(stock: pd.DataFrame) -> pd.DataFrame:
    """Return per-session log slopes and price-normalized trend features."""
    c = stock["Close"]
    features = {f"Price_to_EMA_{n}": divide(c, c.ewm(span=n, adjust=False, min_periods=n).mean()) - 1
                for n in (5, 10, 20, 50)}
    for n in (20, 60):
        weights = np.arange(n) - (n - 1) / 2
        denominator = np.dot(weights, weights)
        features[f"Log_Price_Slope_{n}"] = np.log(c).rolling(n).apply(
            lambda values: np.dot(weights, values) / denominator, raw=True)
    features["Return_5D_Acceleration"] = c.pct_change(5, fill_method=None).diff()
    return pd.DataFrame(features, index=stock.index)
```

### features/volatility_features.py

```python
"""Trailing sample dispersion, distribution shape and conditional asymmetry."""
import numpy as np
import pandas as pd
from features.numerics import divide


def volatility_features(stock: pd.DataFrame) -> pd.DataFrame:
    """Use full trailing return windows; preserve undefined conditional statistics."""
    r = stock["Close"].pct_change(fill_method=None)
    vol = {n: r.rolling(n).std() for n in (5, 10, 20, 60)}
    features = {f"Volatility_{n}": values for n, values in vol.items()}
    for a, b in ((5, 20), (20, 60)):
        features[f"Volatility_Ratio_{a}_{b}"] = divide(vol[a], vol[b])
    for n in (5, 20, 60):
        features[f"Rolling_Mean_Return_{n}"] = r.rolling(n).mean()
    for n in (20, 60):
        features[f"Rolling_Skew_{n}"] = r.rolling(n).skew()
        features[f"Rolling_Kurtosis_{n}"] = r.rolling(n).kurt()
    features["Positive_Return_Ratio_20"] = (r > 0).astype(float).where(r.notna()).rolling(20).mean()
    features["Negative_Return_Ratio_20"] = (r < 0).astype(float).where(r.notna()).rolling(20).mean()
    for name, condition in (("Downside", r < 0), ("Upside", r > 0)):
        selected = r.where(condition)
        # min_periods counts qualifying observations; require a full original window too.
        features[f"{name}_Volatility_20"] = selected.rolling(20, min_periods=2).std().where(
            r.rolling(20).count() == 20)
    return pd.DataFrame(features, index=stock.index)
```

### features/volume_features.py

```python
"""Normalized participation, signed OBV flow and two interpretable interactions."""
import numpy as np
import pandas as pd
from features.numerics import divide


def volume_features(stock: pd.DataFrame) -> pd.DataFrame:
    """Normalize volume scale; leave zero-denominator and constant correlations NaN."""
    v, c = stock["Volume"], stock["Close"]
    r = c.pct_change(fill_method=None)
    change = divide(v, v.shift(1)) - 1
    relative = {n: divide(v, v.rolling(n).mean()) for n in (5, 20)}
    corr = change.rolling(20).corr(r)
    corr = corr.where((change.rolling(20).std() > 1e-12) & (r.rolling(20).std() > 1e-12))
    # Tiny roundoff excursions outside [-1,1] are bounded, not undefined values.
    corr = corr.clip(-1, 1)
    return pd.DataFrame({
        "Volume_Change": change,
        "Relative_Volume_5": relative[5], "Relative_Volume_20": relative[20],
        "Volume_Return_Correlation_20": corr,
        "OBV_Flow_20": divide((np.sign(r) * v).rolling(20).sum(), v.rolling(20).sum()),
        "Return_x_VolumeChange": r * change,
        "Momentum_x_RelativeVolume": c.pct_change(5, fill_method=None) * relative[20]
    }, index=stock.index)
```

### features/technical_features.py

```python
"""Documented RSI, MACD, Bollinger and Wilder ATR conventions."""
import pandas as pd
from features.numerics import divide, wilder_average


def technical_features(stock: pd.DataFrame) -> pd.DataFrame:
    """Compute normalized technical indicators without future initialization."""
    c, h, low = (stock[name] for name in ("Close", "High", "Low"))
    delta = c.diff()
    gain = wilder_average(delta.clip(lower=0), 14)
    loss = wilder_average(-delta.clip(upper=0), 14)
    rsi = 100 - 100 / (1 + divide(gain, loss))
    rsi = rsi.mask((loss == 0) & (gain > 0), 100).mask((gain == 0) & (loss == 0), 50)
    macd = c.ewm(span=12, adjust=False, min_periods=12).mean() - c.ewm(span=26, adjust=False, min_periods=26).mean()
    signal = macd.ewm(span=9, adjust=False, min_periods=9).mean()
    middle, std = c.rolling(20).mean(), c.rolling(20).std(ddof=0)
    width = 4 * std
    position = divide(c - (middle - 2 * std), width).mask(width == 0, .5)
    tr = pd.concat([h - low, (h - c.shift(1)).abs(), (low - c.shift(1)).abs()], axis=1).max(axis=1)
    atr = wilder_average(tr, 14)
    return pd.DataFrame({
        "RSI_14": rsi, "MACD_Pct": divide(macd, c),
        "MACD_Signal_Pct": divide(signal, c), "MACD_Histogram_Pct": divide(macd - signal, c),
        "Bollinger_Position": position, "Bollinger_Width": divide(width, middle),
        "ATR_14_Pct": divide(atr, c)
    }, index=stock.index)
```

### features/feature_factory.py

```python
"""Select the historical basic baseline or the explicit V5 advanced feature set."""
import numpy as np
import pandas as pd
from features.basic_features import build_basic_features
from features.registry import get_feature_columns
from features.price_features import price_features
from features.momentum_features import momentum_features
from features.volatility_features import volatility_features
from features.volume_features import volume_features
from features.technical_features import technical_features


def build_feature_set(stock: pd.DataFrame, feature_set: str = "advanced") -> pd.DataFrame:
    """Build on a copy. Preserve warm-up NaNs and isolate the unchanged future target."""
    columns = get_feature_columns(feature_set)
    featured = build_basic_features(stock)
    if feature_set == "advanced":
        for builder in (price_features, momentum_features, volatility_features,
                        volume_features, technical_features):
            block = builder(stock)
            featured[block.columns] = block
        if np.isinf(featured[columns].to_numpy()).any():
            raise ValueError("Advanced feature generation produced infinity; inspect raw inputs.")
    assert "Tomorrow_Return" not in columns
    assert featured.index.equals(stock.index)
    return featured
```

### features/audit.py

```python
"""Descriptive redundancy diagnostics; never fit selectors or delete columns."""
from itertools import combinations
import pandas as pd


def audit_features(X: pd.DataFrame, correlation_threshold: float = .98,
                   variance_threshold: float = 1e-12) -> dict:
    """Flag exact sample duplicates, constants, tiny variance and correlated pairs.

    Run on training data for research decisions. Near-zero variance uses absolute
    sample variance <= 1e-12 in each feature's documented units.
    """
    constants = X.columns[X.nunique() <= 1].tolist()
    variance = X.var(ddof=1)
    near_zero = variance.index[(variance <= variance_threshold) & ~variance.index.isin(constants)].tolist()
    corr = X.corr()
    duplicates, correlated = [], []
    for a, b in combinations(X.columns, 2):
        if X[a].equals(X[b]):
            duplicates.append([a, b])
        value = corr.loc[a, b]
        if pd.notna(value) and abs(value) >= correlation_threshold:
            correlated.append(dict(feature_a=a, feature_b=b, correlation=float(value)))
    return dict(exact_duplicates=duplicates, constants=constants, near_zero_variance=near_zero,
                high_correlations=correlated, correlation_threshold=correlation_threshold,
                variance_threshold=variance_threshold)
```

### models/feature_comparison.py

```python
"""Controlled basic/advanced diagnostics on identical raw data and holdout dates.

Run: python -m models.feature_comparison AAPL MSFT JPM
No model selection or tuning is performed.
"""
import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

from data.market_data import download_market_data
from features.feature_factory import build_feature_set
from features.registry import ADVANCED_FEATURES
from features.audit import audit_features
from models.baseline import prepare_ml_dataset, chronological_split, evaluate_baseline


def compare_feature_sets(stock: pd.DataFrame) -> dict:
    """Use common eligible rows, identical targets, and an identical purged split."""
    start = perf_counter()
    advanced = build_feature_set(stock, "advanced")
    feature_seconds = perf_counter() - start
    basic = build_feature_set(stock, "basic")
    Xa, ya = prepare_ml_dataset(advanced, "advanced")
    Xb, yb = prepare_ml_dataset(basic, "basic")
    common = Xa.index.intersection(Xb.index).sort_values()
    Xa, ya = Xa.loc[common], ya.loc[common]
    Xb, yb = Xb.loc[common], yb.loc[common]
    pd.testing.assert_series_equal(ya, yb)
    splits = {"basic": chronological_split(Xb, yb, stock.index),
              "advanced": chronological_split(Xa, ya, stock.index)}
    for key in ("X_train", "X_test", "y_train", "y_test"):
        assert splits["basic"][key].index.equals(splits["advanced"][key].index)
    for key in ("y_train", "y_test"):
        pd.testing.assert_series_equal(splits["basic"][key], splits["advanced"][key])
    audit = audit_features(splits["advanced"]["X_train"])
    full_audit = audit_features(Xa)
    if full_audit["exact_duplicates"] or audit["exact_duplicates"]:
        raise ValueError("Exact sample duplicate features detected; review registry before modelling.")
    # Independent dimensional check on the same ticker, not a fitted transformation.
    scaled = stock.copy()
    scaled[["Open", "High", "Low", "Close"]] *= 7
    scaled["Volume"] *= 11
    scaled_features = build_feature_set(scaled, "advanced")[ADVANCED_FEATURES]
    np.testing.assert_allclose(advanced[ADVANCED_FEATURES], scaled_features,
                               equal_nan=True, rtol=1e-6, atol=1e-6)
    evaluations = {
        "basic": evaluate_baseline(splits["basic"], basic, "basic"),
        "advanced": evaluate_baseline(splits["advanced"], advanced, "advanced")
    }
    for metric in ("zero_mae", "zero_rmse", "momentum"):
        assert evaluations["basic"]["metrics"][metric] == evaluations["advanced"]["metrics"][metric]
    valid_inputs = advanced[ADVANCED_FEATURES].notna().all(axis=1)
    first_valid = valid_inputs[valid_inputs].index[0]
    warmup = stock.index.get_loc(first_valid)
    split = splits["advanced"]
    return dict(
        raw_rows=len(stock), raw_start=str(stock.index.min().date()), raw_end=str(stock.index.max().date()),
        advanced_ml_rows=len(prepare_ml_dataset(advanced, "advanced")[0]),
        basic_ml_rows=len(prepare_ml_dataset(basic, "basic")[0]), common_rows=len(common),
        feature_count=len(ADVANCED_FEATURES), warmup_rows=warmup,
        other_removed_rows=len(stock) - warmup - len(Xa),
        train_rows=len(split["X_train"]), test_rows=len(split["X_test"]),
        train_start=str(split["X_train"].index.min().date()), train_end=str(split["X_train"].index.max().date()),
        test_start=str(split["X_test"].index.min().date()), test_end=str(split["X_test"].index.max().date()),
        purged_dates=[str(d.date()) for d in split["removed"]],
        latest_train_target=str(split["latest_train_target"].date()),
        feature_seconds=feature_seconds, scale_invariance="PASS",
        scale_max_abs_difference=float(np.nanmax(np.abs(advanced[ADVANCED_FEATURES].to_numpy() - scaled_features.to_numpy()))),
        scale_medians=Xa.abs().median().to_dict(),
        training_audit=audit, full_sample_audit=full_audit,
        basic=evaluations["basic"]["metrics"], advanced=evaluations["advanced"]["metrics"],
        top15=evaluations["advanced"]["importance"].head(15).to_dict(orient="records")
    )


def main() -> None:
    """Save diagnostic measurements without altering models or previous reports."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickers", nargs="+")
    parser.add_argument("--start", default="2010-01-01")
    parser.add_argument("--end", default=None)
    args = parser.parse_args()
    measurements = {}
    for ticker in args.tickers:
        print(f"Comparing {ticker} on one shared download...", flush=True)
        stock = download_market_data(ticker, args.start, args.end)
        result = compare_feature_sets(stock)
        result["requested_start"] = args.start
        result["effective_end_exclusive"] = stock.attrs["effective_end_exclusive"]
        measurements[ticker] = result
        print(json.dumps(result, indent=2), flush=True)
    destination = Path("reports/v5_experiments.json")
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(measurements, indent=2) + "\n")


if __name__ == "__main__":
    main()
```

### tests/test_advanced_features.py

```python
"""Independent numeric references, degenerate cases and whole-registry causality."""
import unittest
import numpy as np
import pandas as pd

from features.feature_factory import build_feature_set
from features.basic_features import build_basic_features
from features.registry import ADVANCED_FEATURES, BASIC_FEATURES, FEATURE_METADATA
from features.technical_features import technical_features
from features.audit import audit_features
from models.baseline import prepare_ml_dataset, chronological_split
from test_pipeline import sample_data


def reference_ema(values, span):
    result = [float(values[0])]
    alpha = 2 / (span + 1)
    for value in values[1:]:
        result.append(alpha * value + (1 - alpha) * result[-1])
    return np.array(result)


class AdvancedTests(unittest.TestCase):
    def setUp(self):
        self.raw = sample_data(400)
        self.raw["Open"] *= .999
        self.f = build_feature_set(self.raw)

    def test_registry_and_basic_compatibility(self):
        self.assertEqual(len(ADVANCED_FEATURES), 70)
        self.assertEqual(len(set(ADVANCED_FEATURES)), 70)
        self.assertNotIn("Tomorrow_Return", ADVANCED_FEATURES + BASIC_FEATURES)
        self.assertTrue(set(ADVANCED_FEATURES).issubset(FEATURE_METADATA))
        pd.testing.assert_frame_equal(build_feature_set(self.raw, "basic"), build_basic_features(self.raw))
        for name in BASIC_FEATURES:
            np.testing.assert_allclose(self.f[name], build_basic_features(self.raw)[name], equal_nan=True)

    def test_returns_and_price_structure(self):
        t = 80
        raw, f = self.raw, self.f
        for n in (1, 2, 3, 5, 10, 20, 60):
            self.assertAlmostEqual(f[f"Return_{n}D"].iloc[t], raw.Close.iloc[t] / raw.Close.iloc[t-n] - 1)
        self.assertAlmostEqual(f.Overnight_Gap.iloc[t], raw.Open.iloc[t] / raw.Close.iloc[t-1] - 1)
        self.assertAlmostEqual(f.Intraday_Return.iloc[t], raw.Close.iloc[t] / raw.Open.iloc[t] - 1)
        high, low = raw.High.iloc[t-19:t+1].max(), raw.Low.iloc[t-19:t+1].min()
        self.assertAlmostEqual(f.Range_Position_20.iloc[t], (raw.Close.iloc[t] - low) / (high - low))
        self.assertAlmostEqual(f.Distance_From_20D_High.iloc[t], raw.Close.iloc[t] / high - 1)
        self.assertAlmostEqual(f.Drawdown_From_20D_Peak.iloc[t], raw.Close.iloc[t] / raw.Close.iloc[t-19:t+1].max() - 1)
        for n in (20, 60, 252):
            self.assertTrue((f[f"Drawdown_From_{n}D_Peak"].dropna() <= 1e-12).all())
        self.assertAlmostEqual(f.Relative_Volume_20.iloc[t], raw.Volume.iloc[t] / raw.Volume.iloc[t-19:t+1].mean())

    def test_rsi_wilder_seed_and_recurrence(self):
        changes = np.diff(self.raw.Close.to_numpy())
        gain = np.maximum(changes[:14], 0).mean()
        loss = np.maximum(-changes[:14], 0).mean()
        self.assertTrue(self.f.RSI_14.iloc[:14].isna().all())
        for t in range(14, 40):
            if t > 14:
                gain = (13 * gain + max(changes[t-1], 0)) / 14
                loss = (13 * loss + max(-changes[t-1], 0)) / 14
            self.assertAlmostEqual(self.f.RSI_14.iloc[t], 100 - 100 / (1 + gain / loss))

    def test_macd_independent_recursion(self):
        c = self.raw.Close.to_numpy()
        macd = reference_ema(c, 12) - reference_ema(c, 26)
        signal = reference_ema(macd[25:], 9)
        t = 50
        self.assertAlmostEqual(self.f.MACD_Pct.iloc[t], macd[t] / c[t])
        self.assertAlmostEqual(self.f.MACD_Signal_Pct.iloc[t], signal[t-25] / c[t])
        self.assertAlmostEqual(self.f.MACD_Histogram_Pct.iloc[t], (macd[t] - signal[t-25]) / c[t])
        self.assertTrue(self.f.MACD_Signal_Pct.iloc[:33].isna().all())

    def test_bollinger_and_atr(self):
        self.raw.loc[self.raw.index[20], "High"] += 30
        self.f = build_feature_set(self.raw)
        t = 50
        values = self.raw.Close.iloc[t-19:t+1].to_numpy()
        mean, std = np.mean(values), np.std(values, ddof=0)
        self.assertAlmostEqual(self.f.Bollinger_Position.iloc[t], (values[-1] - mean + 2 * std) / (4 * std))
        self.assertAlmostEqual(self.f.Bollinger_Width.iloc[t], 4 * std / mean)
        tr = []
        for i in range(t + 1):
            row = self.raw.iloc[i]
            choices = [row.High - row.Low]
            if i:
                previous = self.raw.Close.iloc[i-1]
                choices += [abs(row.High - previous), abs(row.Low - previous)]
            tr.append(max(choices))
        atr = sum(tr[:14]) / 14
        for value in tr[14:]:
            atr = (atr * 13 + value) / 14
        self.assertAlmostEqual(self.f.ATR_14_Pct.iloc[t], atr / self.raw.Close.iloc[t])

    def test_flat_and_one_sided_cases(self):
        flat = self.raw.copy()
        flat[["Open", "High", "Low", "Close"]] = 100.
        flat["Volume"] = 0
        f = build_feature_set(flat)
        self.assertEqual(f.RSI_14.iloc[-1], 50)
        self.assertEqual(f.Bollinger_Position.iloc[-1], .5)
        self.assertEqual(f.Range_Position_20.iloc[-1], .5)
        self.assertEqual(f.Close_Open_Position.iloc[-1], 0)
        self.assertTrue(pd.isna(f.Relative_Volume_20.iloc[-1]))
        self.assertTrue(pd.isna(f.Downside_Volatility_20.iloc[-1]))
        self.assertFalse(np.isinf(f[ADVANCED_FEATURES].to_numpy()).any())
        for direction, expected in ((1, 100), (-1, 0)):
            data = self.raw.copy()
            data["Close"] = 500 + direction * np.arange(len(data))
            self.assertEqual(technical_features(data).RSI_14.iloc[-1], expected)

    def test_future_perturbation_all_inputs(self):
        changed = self.raw.copy()
        cutoff = 300
        rng = np.random.default_rng(42)
        changed.iloc[cutoff+1:, :4] *= rng.uniform(.5, 2, (len(changed)-cutoff-1, 1))
        changed.loc[changed.index[cutoff+1:], "Volume"] *= 3
        rebuilt = build_feature_set(changed)
        pd.testing.assert_frame_equal(self.f[ADVANCED_FEATURES].iloc[:cutoff+1],
                                      rebuilt[ADVANCED_FEATURES].iloc[:cutoff+1], check_exact=True)
        pd.testing.assert_frame_equal(self.f[ADVANCED_FEATURES].iloc[:cutoff+1],
                                      build_feature_set(self.raw.iloc[:cutoff+1])[ADVANCED_FEATURES], check_exact=True)

    def test_scale_invariance(self):
        scaled = self.raw.copy()
        scaled[["Open", "High", "Low", "Close"]] *= 11
        scaled["Volume"] *= 7
        rebuilt = build_feature_set(scaled)
        np.testing.assert_allclose(self.f[ADVANCED_FEATURES], rebuilt[ADVANCED_FEATURES],
                                   equal_nan=True, atol=1e-7, rtol=1e-7)

    def test_dataset_purge_and_finite(self):
        X, y = prepare_ml_dataset(self.f, "advanced")
        self.assertEqual(X.shape, (148, 70))
        self.assertTrue(np.isfinite(X.to_numpy()).all())
        self.assertTrue(np.isfinite(y.to_numpy()).all())
        split = chronological_split(X, y, self.raw.index)
        self.assertLess(split["latest_train_target"], split["X_test"].index.min())

    def test_distribution_obv_and_trend_references(self):
        t = 80
        returns = self.raw.Close.pct_change().iloc[t-19:t+1].to_numpy()
        negative, positive = returns[returns < 0], returns[returns > 0]
        self.assertAlmostEqual(self.f.Downside_Volatility_20.iloc[t], np.std(negative, ddof=1))
        self.assertAlmostEqual(self.f.Upside_Volatility_20.iloc[t], np.std(positive, ddof=1))
        self.assertAlmostEqual(self.f.Positive_Return_Ratio_20.iloc[t], len(positive) / 20)
        volume = self.raw.Volume.iloc[t-19:t+1].to_numpy()
        self.assertAlmostEqual(self.f.OBV_Flow_20.iloc[t], np.dot(np.sign(returns), volume) / volume.sum())
        exponential = self.raw.copy()
        exponential["Close"] = np.exp(.003 * np.arange(len(exponential)))
        actual = build_feature_set(exponential)
        self.assertAlmostEqual(actual.Log_Price_Slope_20.iloc[t], .003)
        self.assertAlmostEqual(actual.Log_Price_Slope_60.iloc[t], .003)

    def test_audit_known_flags(self):
        X = pd.DataFrame({"a": [1., 2., 3.], "duplicate": [1., 2., 3.],
                          "constant": [2., 2., 2.], "tiny": [0., 1e-8, 2e-8]})
        audit = audit_features(X)
        self.assertIn(["a", "duplicate"], audit["exact_duplicates"])
        self.assertEqual(audit["constants"], ["constant"])
        self.assertIn("tiny", audit["near_zero_variance"])
        self.assertTrue(audit["high_correlations"])


if __name__ == "__main__":
    unittest.main()
```

## 23. V5 COMPLETION STATUS

V5 is complete: 70 documented, independently grouped, deterministic advanced inputs;
basic compatibility; explicit target-safe registries; numerical and perturbation
tests; redundancy and scale audits; and controlled live comparisons for AAPL, MSFT,
and JPM. The full test suite passes. The unchanged forest was diagnostic only.

## 24. LIMITATIONS / V6 HANDOFF

No day-of-week, month, week-of-year, cyclical calendar encodings, holiday effects or
earnings-calendar intelligence exists yet. No calendar-day assumptions were added;
all feature horizons remain trading-row based. V6 should define exchange/timezone
and completed-session semantics before introducing temporal/calendar intelligence.

Other existing research limits remain: one chronological holdout, no significance
estimates or walk-forward validation, correlated inputs awaiting later ablations,
strict complete-case deletion for undefined conditional statistics, retrospective
adjusted Yahoo data, no immutable raw-data snapshot, and weak baseline error metrics.
Future repeated experiments must not tune against this inspected holdout.
No V6+ features, new models, market context, signals, backtesting or dashboard were
implemented.
