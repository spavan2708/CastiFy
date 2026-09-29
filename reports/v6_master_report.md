# CASTIFY V6 MASTER REPORT

## 1. ARCHITECTURE CHANGES

```text
main.py                             configuration comment updated; default basic
features/
  temporal_features.py              new Gregorian date engine
  registry.py                       additive temporal registry/metadata
  feature_factory.py                third mode; retains old modes
models/
  temporal_comparison.py            new controlled V6 diagnostic and profiles
  baseline.py                       unchanged forest and purged split
 tests/
  test_temporal_features.py          new offline tests
  test_pipeline.py                   unchanged
  test_advanced_features.py          unchanged
reports/
  v6_temporal_feature_catalog.md
  v6_feature_metadata.json
  v6_experiments.json
  v6_experiments.txt
  v6_tests.txt
  v6_preservation.json
  v6_master_report.md
```

No data-ingestion, target, quantitative feature, baseline-model, dependency or
historical report changes. No new calendar package or other dependency.

## 2. FILES CREATED

- features/temporal_features.py
- models/temporal_comparison.py
- tests/test_temporal_features.py
- reports/v6_temporal_feature_catalog.md
- reports/v6_feature_metadata.json
- reports/v6_experiments.json
- reports/v6_experiments.txt
- reports/v6_tests.txt
- reports/v6_preservation.json
- reports/v6_master_report.md

## 3. FILES MODIFIED

- main.py
- features/registry.py
- features/feature_factory.py

## 4. TEMPORAL ENGINE DESIGN

The engine accepts completed-session date labels and returns 18 explicit temporal
columns. It reads no OHLCV values. Calendar arithmetic uses the index-local date;
timezone-aware labels are not converted to UTC. Invalid, unordered, duplicate or
weekend session dates are explicitly rejected in the temporal mode. This prevents
weekend rows silently receiving an all-zero weekday encoding.

TEMPORAL_FEATURES is separate from the unchanged V5 FEATURE_GROUPS and
ADVANCED_FEATURES. ADVANCED_TEMPORAL_FEATURES combines the two ordered lists.
get_feature_columns returns a copy of an explicit registry. No automatic numeric
selection or target-derived aggregate is used. FEATURE_METADATA is extended
without changing any of its 73 original records.

## 5. COMPLETE TEMPORAL FEATURE LIST

```text
DOW_Monday
DOW_Tuesday
DOW_Wednesday
DOW_Thursday
DOW_Friday
Month_Sin
Month_Cos
DayOfMonth_Sin
DayOfMonth_Cos
DayOfYear_Sin
DayOfYear_Cos
Calendar_Days_From_Month_Start
Calendar_Days_To_Month_End
Calendar_Days_From_Quarter_Start
Calendar_Days_To_Quarter_End
Is_Quarter_Start_Region
Is_Quarter_End_Region
Calendar_Days_Since_Previous_Session
```

## 6. TEMPORAL FEATURE DEFINITIONS

| Feature | Definition | Lookback | Encoding | Range |
|---|---|---|---|---|
| DOW_Monday | 1 if current session date is Monday, else 0; weekend dates rejected. | 0 | one-hot | 0 or 1 |
| DOW_Tuesday | 1 if current session date is Tuesday, else 0; weekend dates rejected. | 0 | one-hot | 0 or 1 |
| DOW_Wednesday | 1 if current session date is Wednesday, else 0; weekend dates rejected. | 0 | one-hot | 0 or 1 |
| DOW_Thursday | 1 if current session date is Thursday, else 0; weekend dates rejected. | 0 | one-hot | 0 or 1 |
| DOW_Friday | 1 if current session date is Friday, else 0; weekend dates rejected. | 0 | one-hot | 0 or 1 |
| Month_Sin | sin(2*pi*(month-1)/12); calendar phase, not an ordinal category. | 0 | cyclical | [-1, 1] |
| Month_Cos | cos(2*pi*(month-1)/12); calendar phase, not an ordinal category. | 0 | cyclical | [-1, 1] |
| DayOfMonth_Sin | sin(2*pi*(day-1)/days_in_current_month); calendar phase, not an ordinal category. | 0 | cyclical | [-1, 1] |
| DayOfMonth_Cos | cos(2*pi*(day-1)/days_in_current_month); calendar phase, not an ordinal category. | 0 | cyclical | [-1, 1] |
| DayOfYear_Sin | sin(2*pi*(day_of_year-1)/(366 if leap year else 365)); calendar phase, not an ordinal category. | 0 | cyclical | [-1, 1] |
| DayOfYear_Cos | cos(2*pi*(day_of_year-1)/(366 if leap year else 365)); calendar phase, not an ordinal category. | 0 | cyclical | [-1, 1] |
| Calendar_Days_From_Month_Start | Current date minus first calendar day of current month; first day=0. | 0 | calendar-day distance | [0, 30] |
| Calendar_Days_To_Month_End | Last calendar day of current month minus current date; last day=0. | 0 | calendar-day distance | [0, 30] |
| Calendar_Days_From_Quarter_Start | Current date minus first calendar day of Gregorian quarter; first day=0. | 0 | calendar-day distance | [0, 91] |
| Calendar_Days_To_Quarter_End | Last calendar day of Gregorian quarter minus current date; last day=0. | 0 | calendar-day distance | [0, 91] |
| Is_Quarter_Start_Region | 1 in first seven calendar days of quarter (elapsed 0..6), else 0. | 0 | binary | 0 or 1 |
| Is_Quarter_End_Region | 1 in last seven calendar days of quarter (remaining 0..6), else 0. | 0 | binary | 0 or 1 |
| Calendar_Days_Since_Previous_Session | Current date minus previous observed session date, in local calendar days; first row NaN. Gaps can include missing provider rows. | 1 | calendar-day distance | >=1, first row NaN |

All day distances are zero-based differences: the boundary date has distance 0;
the current date is not counted as an extra day. Calendar distances retain units
of days, while category/cycle features are bounded. Every temporal input is
invariant to changes in price or volume units.

## 7. FEATURE MODES

- basic: exact original baseline, still the main.py default.
- advanced: unchanged V5 quantitative features.
- advanced_temporal: V5 features plus the V6 temporal family.

Set FEATURE_SET in main.py, or call build_feature_set(stock, mode), then pass the
same mode to prepare_ml_dataset and evaluate_baseline. No earlier mode silently
acquires new columns. Existing basic/advanced defaults remain unchanged.

## 8. FEATURE COUNTS

| Mode | Inputs |
|---|---:|
| basic | 10 |
| advanced | 70 |
| advanced_temporal | 88 |

The 18 additions have explicit interpretations. The combined count exceeds 80
because it preserves all 70 V5 features and adds calendar context; the full 88-column
matrix was audited for duplicates, variance and correlation rather than padded.

## 9. CALENDAR SAFETY

- Current date: weekday one-hot and Gregorian month/date/year phases.
- Deterministic calendar arithmetic: actual month/year lengths, calendar month and
  quarter endpoints, distances and first/last seven-calendar-day quarter regions.
- Previous observed date: Calendar_Days_Since_Previous_Session only; first row NaN.

A known calendar date in the future is not an unknown future market observation.
No feature inspects the next downloaded row, future missing rows, prices, volume,
returns, realized volatility or targets. The first gap remains NaN; ordinary V5
warm-up removal already excludes it, so it adds no extra lost rows in these runs.

## 10. MONTH/WEEK/QUARTER/YEAR HANDLING

Weekday is five one-hot columns, not an ordinal number. Month phase is (month-1)/12;
day-of-month phase is (day-1)/actual_days_in_month. Quarters are Gregorian Q1–Q4,
not corporate fiscal quarters. Start/end regions mean first/last seven calendar
days and can include weekends without inventing market observations.

ISO week cycles are omitted because annual phase already describes within-year
position; there is no week-53 bug to resolve in an absent feature. Separate
Is_Monday/Is_Friday would duplicate one-hot inputs and were omitted. Quarter cycles
and year-distance pairs were omitted in favor of the implemented contexts. No
raw year or absolute observed-session counter encodes dataset age or identity.
First/last trading-day flags and future trading-session counts were not implemented;
calendar-day distances are the safe substitutes without an exchange schedule.

## 11. LEAP-YEAR HANDLING

DayOfYear uses (ordinal_day-1)/366 in leap years, otherwise /365. Tests explicitly
cover 2024-02-28, 2024-02-29 and 2024-03-01; February month length is 29. A non-leap
March 1 case uses denominator 365. All three sine/cosine pairs are finite, bounded
in [-1,1] and lie on the unit circle. December/January, month-end/start and
year-end/start geometric wrap checks passed.

## 12. HOLIDAY / EXCHANGE LIMITATIONS

No explicit US/NYSE/Tokyo holiday or exchange-calendar assumptions exist.
Generic Gregorian context generalizes across tickers. The gap describes previous
observed session dates: it may represent weekends, holidays, provider missing bars
or other absences, and is not claimed to identify holidays. Synthetic Friday-to-
Monday and Friday-to-Tuesday tests yield 3 and 4 calendar days. A DST-crossing gap
also yields 3 local dates, not fractional/elapsed UTC days.

Weekend trading exchanges are not represented by the five weekday categories;
advanced_temporal raises a clear error for those dates. Existing modes are not
changed. Exchange-specific holiday schedules and expanded trading-week support
remain future enhancements. The V4 conservative completed-bar cutoff is unchanged.

## 13. REDUNDANCY AUDIT

Exact duplicates, constants, near-zero sample variance <=1e-12 and absolute Pearson
correlation >=0.98 were measured on purged training and full eligible matrices.
Full-sample tables are descriptive only; no feature selection or tuning followed.

| Ticker | Train exact duplicates | Train constants | Train near-zero | Train high-correlation pairs | Full high-correlation pairs |
|---|---|---|---|---|---|
| AAPL | 0 | 0 | 0 | 11 | 11 |
| MSFT | 0 | 0 | 0 | 11 | 11 |
| JPM | 0 | 0 | 0 | 11 | 11 |

### AAPL: training correlation pairs

| Feature A | Feature B | Correlation |
|---|---|---|
| Return_5D | Rolling_Mean_Return_5 | 0.999455 |
| Return_20D | Rolling_Mean_Return_20 | 0.998424 |
| Return_60D | Rolling_Mean_Return_60 | 0.994300 |
| Price_to_SMA_10 | Price_to_EMA_10 | 0.981332 |
| Price_to_SMA_20 | Price_to_EMA_20 | 0.982864 |
| Price_to_SMA_50 | Price_to_EMA_50 | 0.982834 |
| Distance_From_20D_High | Drawdown_From_20D_Peak | 0.990353 |
| Distance_From_60D_High | Drawdown_From_60D_Peak | 0.996027 |
| Positive_Return_Ratio_20 | Negative_Return_Ratio_20 | -0.996483 |
| Calendar_Days_From_Month_Start | Calendar_Days_To_Month_End | -0.995780 |
| Calendar_Days_From_Quarter_Start | Calendar_Days_To_Quarter_End | -0.999569 |

### MSFT: training correlation pairs

| Feature A | Feature B | Correlation |
|---|---|---|
| Return_5D | Rolling_Mean_Return_5 | 0.999236 |
| Return_20D | Rolling_Mean_Return_20 | 0.998105 |
| Return_60D | Rolling_Mean_Return_60 | 0.994720 |
| Price_to_SMA_10 | Price_to_EMA_10 | 0.980546 |
| Price_to_SMA_20 | Price_to_EMA_20 | 0.982247 |
| Price_to_SMA_50 | Price_to_EMA_50 | 0.982550 |
| Distance_From_20D_High | Drawdown_From_20D_Peak | 0.988222 |
| Distance_From_60D_High | Drawdown_From_60D_Peak | 0.994043 |
| Positive_Return_Ratio_20 | Negative_Return_Ratio_20 | -0.980986 |
| Calendar_Days_From_Month_Start | Calendar_Days_To_Month_End | -0.995780 |
| Calendar_Days_From_Quarter_Start | Calendar_Days_To_Quarter_End | -0.999569 |

### JPM: training correlation pairs

| Feature A | Feature B | Correlation |
|---|---|---|
| Return_5D | Rolling_Mean_Return_5 | 0.998905 |
| Return_20D | Rolling_Mean_Return_20 | 0.997098 |
| Return_60D | Rolling_Mean_Return_60 | 0.995699 |
| Price_to_SMA_10 | Price_to_EMA_10 | 0.980580 |
| Price_to_SMA_20 | Price_to_EMA_20 | 0.981113 |
| Price_to_SMA_50 | Price_to_EMA_50 | 0.982625 |
| Distance_From_20D_High | Drawdown_From_20D_Peak | 0.993099 |
| Distance_From_60D_High | Drawdown_From_60D_Peak | 0.997389 |
| Positive_Return_Ratio_20 | Negative_Return_Ratio_20 | -0.987261 |
| Calendar_Days_From_Month_Start | Calendar_Days_To_Month_End | -0.995780 |
| Calendar_Days_From_Quarter_Start | Calendar_Days_To_Quarter_End | -0.999569 |

The five weekday indicators sum to one, an expected linear dependency with an
intercept, not a duplicate-column bug. From/to month and quarter distances are
highly negatively correlated, but their sums vary with actual calendar period
lengths. They are not universally affine duplicates; both boundary meanings are
retained and documented. V5 correlations are untouched. Full exact coefficients
and temporal-only audits are saved in v6_experiments.json.

## 14. DATASET RESULTS

| Ticker | Raw rows | Eligible rows | Advanced inputs | Combined inputs | Train | Test |
|---|---|---|---|---|---|---|
| AAPL | 4209 | 3957 | 70 | 88 | 3164 | 792 |
| MSFT | 4209 | 3957 | 70 | 88 | 3164 | 792 |
| JPM | 4209 | 3957 | 70 | 88 | 3164 | 792 |

| Ticker | Raw dates | Eligible dates | Train dates | Test dates | Purged feature date |
|---|---|---|---|---|---|
| AAPL | 2010-01-04 → 2026-09-28 | 2010-12-31 → 2026-09-25 | 2010-12-31 → 2023-07-28 | 2023-08-01 → 2026-09-25 | 2023-07-31 |
| MSFT | 2010-01-04 → 2026-09-28 | 2010-12-31 → 2026-09-25 | 2010-12-31 → 2023-07-28 | 2023-08-01 → 2026-09-25 | 2023-07-31 |
| JPM | 2010-01-04 → 2026-09-28 | 2010-12-31 → 2026-09-25 | 2010-12-31 → 2023-07-28 | 2023-08-01 → 2026-09-25 | 2023-07-31 |

The same raw download feeds both models for each ticker. Common eligible dates
are selected before either split; shared quantitative values and targets are asserted
identical, as are train/test indexes, purge dates and benchmark metrics. No target
redefinition occurred. Each training target realization strictly precedes the first
test feature date. All final model matrices and predictions passed finite checks.

## 15. CONTROLLED ADVANCED VS ADVANCED_TEMPORAL RESULTS

Every fit uses RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1),
all other defaults, with no tuning, preprocessing fitting or scaling. MAE/RMSE are
daily-return decimals (multiply by 100 for percentage points).

| Ticker | Mode | MAE | RMSE | R² | Direction |
|---|---|---|---|---|---|
| AAPL | advanced | 0.01185151 | 0.01748155 | -0.079970 | 53.2828% |
| AAPL | advanced_temporal | 0.01182055 | 0.01744447 | -0.075393 | 52.6515% |
| MSFT | advanced | 0.01194911 | 0.01736057 | -0.128789 | 50.5051% |
| MSFT | advanced_temporal | 0.01188745 | 0.01729816 | -0.120689 | 49.8737% |
| JPM | advanced | 0.01058725 | 0.01494138 | -0.084179 | 52.5253% |
| JPM | advanced_temporal | 0.01053072 | 0.01491034 | -0.079679 | 51.0101% |

| Ticker | Zero MAE | Zero RMSE | Previous-day direction |
|---|---|---|---|
| AAPL | 0.01148608 | 0.01684341 | 51.1364% |
| MSFT | 0.01117060 | 0.01635468 | 49.3687% |
| JPM | 0.01004296 | 0.01439549 | 50.7576% |

AAPL: temporal MAE decreased, RMSE decreased, R² increased, directional accuracy decreased. Temporal error versus zero baseline: MAE higher, RMSE higher.

MSFT: temporal MAE decreased, RMSE decreased, R² increased, directional accuracy decreased. Temporal error versus zero baseline: MAE higher, RMSE higher.

JPM: temporal MAE decreased, RMSE decreased, R² increased, directional accuracy decreased. Temporal error versus zero baseline: MAE higher, RMSE higher.

These describe this three-stock fixed-holdout experiment, not general predictive
superiority, persistent calendar laws or trading usefulness. Models were not altered
in response to the measurements. Current advanced results were rerun from the same
raw snapshot as temporal, rather than compared to old V5 measurements.

## 16. TEMPORAL ABLATION DELTAS

Delta = advanced_temporal minus advanced. Negative MAE/RMSE deltas mean lower error;
positive R²/direction deltas mean higher scores. Direction differences are percentage
points, not relative percentage changes.

| Ticker | ΔMAE | ΔRMSE | ΔR² | ΔDirection (pp) |
|---|---|---|---|---|
| AAPL | -0.00003097 | -0.00003708 | +0.004577 | -0.6313 |
| MSFT | -0.00006166 | -0.00006240 | +0.008100 | -0.6313 |
| JPM | -0.00005654 | -0.00003104 | +0.004500 | -1.5152 |

## 17. TEMPORAL FEATURE IMPORTANCE

Impurity importance is descriptive, not causation. Correlation and encoding affect
how trees distribute importance. No importance-based selection was performed.

| Ticker | Total temporal importance |
|---|---|
| AAPL | 0.092873 (9.29%) |
| MSFT | 0.090512 (9.05%) |
| JPM | 0.081598 (8.16%) |

| Temporal feature | AAPL | MSFT | JPM |
|---|---|---|---|
| DOW_Monday | 0.001205 | 0.000903 | 0.001180 |
| DOW_Tuesday | 0.002488 | 0.001485 | 0.001448 |
| DOW_Wednesday | 0.001627 | 0.001319 | 0.001213 |
| DOW_Thursday | 0.001914 | 0.002134 | 0.001486 |
| DOW_Friday | 0.003347 | 0.001242 | 0.001754 |
| Month_Sin | 0.002737 | 0.003353 | 0.002311 |
| Month_Cos | 0.003022 | 0.003167 | 0.002296 |
| DayOfMonth_Sin | 0.012977 | 0.014019 | 0.011644 |
| DayOfMonth_Cos | 0.010987 | 0.010293 | 0.010237 |
| DayOfYear_Sin | 0.011520 | 0.012275 | 0.011142 |
| DayOfYear_Cos | 0.012678 | 0.011319 | 0.011709 |
| Calendar_Days_From_Month_Start | 0.006249 | 0.006217 | 0.005622 |
| Calendar_Days_To_Month_End | 0.006661 | 0.006107 | 0.005854 |
| Calendar_Days_From_Quarter_Start | 0.006618 | 0.007220 | 0.006166 |
| Calendar_Days_To_Quarter_End | 0.006508 | 0.007582 | 0.005636 |
| Is_Quarter_Start_Region | 0.000350 | 0.000179 | 0.000117 |
| Is_Quarter_End_Region | 0.000158 | 0.000222 | 0.000202 |
| Calendar_Days_Since_Previous_Session | 0.001826 | 0.001476 | 0.001582 |

### AAPL: top 20 overall

| Rank | Feature | Importance |
|---|---|---|
| 1 | High_Low_Range | 0.027449 |
| 2 | Return_Lag_5 | 0.023354 |
| 3 | Relative_Volume_20 | 0.021409 |
| 4 | Overnight_Gap | 0.020590 |
| 5 | Return_x_VolumeChange | 0.019555 |
| 6 | Return_Lag_2 | 0.019305 |
| 7 | Price_to_SMA_10 | 0.019146 |
| 8 | Return_Lag_3 | 0.018641 |
| 9 | SMA_50_to_200 | 0.018268 |
| 10 | Momentum_x_RelativeVolume | 0.018200 |
| 11 | Return_Lag_1 | 0.018177 |
| 12 | Return_1D | 0.017933 |
| 13 | Relative_Volume_5 | 0.017801 |
| 14 | Rolling_Skew_60 | 0.017793 |
| 15 | Volume_Change | 0.017548 |
| 16 | Volatility_10 | 0.017440 |
| 17 | Upside_Volatility_20 | 0.015991 |
| 18 | Volatility_Ratio_20_60 | 0.015934 |
| 19 | OBV_Flow_20 | 0.015916 |
| 20 | ATR_14_Pct | 0.015813 |

### MSFT: top 20 overall

| Rank | Feature | Importance |
|---|---|---|
| 1 | High_Low_Range | 0.024090 |
| 2 | Return_Lag_1 | 0.023438 |
| 3 | SMA_50_to_200 | 0.021788 |
| 4 | Price_to_SMA_20 | 0.021330 |
| 5 | MACD_Histogram_Pct | 0.021250 |
| 6 | Return_Lag_5 | 0.020116 |
| 7 | Return_1D | 0.019568 |
| 8 | Return_Lag_2 | 0.019256 |
| 9 | Return_Lag_3 | 0.019145 |
| 10 | Return_x_VolumeChange | 0.018720 |
| 11 | Overnight_Gap | 0.018407 |
| 12 | Return_5D_Acceleration | 0.017988 |
| 13 | Relative_Volume_20 | 0.017915 |
| 14 | Volume_Change | 0.017556 |
| 15 | Price_to_SMA_10 | 0.016857 |
| 16 | Log_Price_Slope_20 | 0.016796 |
| 17 | Intraday_Return | 0.016618 |
| 18 | Relative_Volume_5 | 0.016395 |
| 19 | OBV_Flow_20 | 0.016289 |
| 20 | ATR_14_Pct | 0.015798 |

### JPM: top 20 overall

| Rank | Feature | Importance |
|---|---|---|
| 1 | Return_Lag_1 | 0.030035 |
| 2 | Return_Lag_3 | 0.028568 |
| 3 | Drawdown_From_252D_Peak | 0.027222 |
| 4 | Overnight_Gap | 0.025658 |
| 5 | Return_Lag_5 | 0.024973 |
| 6 | Price_to_SMA_200 | 0.021872 |
| 7 | SMA_5_to_20 | 0.019605 |
| 8 | Return_Lag_2 | 0.019220 |
| 9 | Rolling_Kurtosis_60 | 0.019056 |
| 10 | Return_5D_Acceleration | 0.018711 |
| 11 | SMA_50_to_200 | 0.018431 |
| 12 | Volatility_10 | 0.017546 |
| 13 | MACD_Histogram_Pct | 0.017256 |
| 14 | Return_1D | 0.016611 |
| 15 | Volume_Change | 0.016045 |
| 16 | Return_x_VolumeChange | 0.015955 |
| 17 | High_Low_Range | 0.015707 |
| 18 | Intraday_Return | 0.015285 |
| 19 | Price_to_SMA_5 | 0.014976 |
| 20 | Log_Price_Slope_60 | 0.014965 |

## 18. WEEKDAY RETURN PROFILE

Full raw-history same-session Daily_Return descriptive statistics; initial NaN
excluded. Std uses ddof=1. Fractions count strictly positive returns; zeros count
as nonpositive. Values are decimals except counts and positive fraction percentages.
These tables are never features, targets, target encodings or training summaries.

### AAPL

| Weekday | Count | Mean | Median | Std | Positive fraction |
|---|---|---|---|---|---|
| Monday | 787 | 0.00299964 | 0.00346245 | 0.01849576 | 59.2122% |
| Tuesday | 866 | 0.00164440 | 0.00156442 | 0.01650371 | 54.3880% |
| Wednesday | 863 | 0.00178756 | 0.00113998 | 0.01807875 | 53.9977% |
| Thursday | 848 | -0.00054031 | -0.00034094 | 0.01767792 | 48.9387% |
| Friday | 844 | -0.00028500 | -0.00027784 | 0.01756709 | 49.1706% |

### MSFT

| Weekday | Count | Mean | Median | Std | Positive fraction |
|---|---|---|---|---|---|
| Monday | 787 | 0.00072117 | 0.00082676 | 0.01609225 | 52.7319% |
| Tuesday | 866 | 0.00060686 | 0.00031608 | 0.01488680 | 50.9238% |
| Wednesday | 863 | 0.00120579 | 0.00045539 | 0.01624173 | 51.3326% |
| Thursday | 848 | 0.00082215 | 0.00119080 | 0.01736856 | 53.8915% |
| Friday | 844 | 0.00098873 | 0.00075261 | 0.01743331 | 52.7251% |

### JPM

| Weekday | Count | Mean | Median | Std | Positive fraction |
|---|---|---|---|---|---|
| Monday | 787 | 0.00044707 | 0.00046974 | 0.01784202 | 51.3342% |
| Tuesday | 866 | 0.00107548 | 0.00094407 | 0.01651672 | 52.7714% |
| Wednesday | 863 | 0.00125357 | 0.00143881 | 0.01668602 | 54.5771% |
| Thursday | 848 | 0.00048003 | 0.00057185 | 0.01694441 | 52.0047% |
| Friday | 844 | 0.00039770 | 0.00000000 | 0.01832126 | 49.8815% |

## 19. MONTH RETURN PROFILE

Same full-history descriptive conventions; month numbers below are reporting labels,
not ordinal ML inputs. These are observed historical summaries, not persistent laws.

### AAPL

| Month | Count | Mean | Median | Std | Positive fraction |
|---|---|---|---|---|---|
| 1 | 342 | -0.00021782 | 0.00017102 | 0.02081618 | 50.8772% |
| 2 | 326 | 0.00142794 | 0.00170690 | 0.01580991 | 55.5215% |
| 3 | 372 | 0.00114706 | 0.00115555 | 0.02143721 | 53.2258% |
| 4 | 352 | 0.00088765 | 0.00019965 | 0.02134598 | 50.8523% |
| 5 | 359 | 0.00144164 | 0.00039038 | 0.01717614 | 51.5320% |
| 6 | 359 | 0.00039952 | 0.00039847 | 0.01510302 | 50.9749% |
| 7 | 360 | 0.00316601 | 0.00286166 | 0.01530291 | 58.0556% |
| 8 | 376 | 0.00208448 | 0.00203987 | 0.01682189 | 56.9149% |
| 9 | 346 | -0.00005328 | 0.00088822 | 0.01792310 | 53.1792% |
| 10 | 352 | 0.00168223 | 0.00203716 | 0.01672262 | 55.6818% |
| 11 | 327 | 0.00120052 | 0.00042781 | 0.01678581 | 51.6820% |
| 12 | 337 | -0.00015502 | -0.00052881 | 0.01512588 | 47.7745% |

### MSFT

| Month | Count | Mean | Median | Std | Positive fraction |
|---|---|---|---|---|---|
| 1 | 342 | 0.00042390 | 0.00099257 | 0.01793579 | 52.6316% |
| 2 | 326 | 0.00018600 | -0.00006788 | 0.01546711 | 49.0798% |
| 3 | 372 | 0.00080397 | 0.00056397 | 0.02145091 | 52.1505% |
| 4 | 352 | 0.00203084 | 0.00087842 | 0.01883209 | 52.5568% |
| 5 | 359 | 0.00083145 | 0.00000000 | 0.01431204 | 49.8607% |
| 6 | 359 | 0.00033579 | 0.00129317 | 0.01541230 | 52.3677% |
| 7 | 360 | 0.00220701 | 0.00158959 | 0.01715023 | 56.6667% |
| 8 | 376 | 0.00069260 | 0.00066810 | 0.01457169 | 52.3936% |
| 9 | 346 | -0.00057776 | 0.00000000 | 0.01413437 | 49.1329% |
| 10 | 352 | 0.00186589 | 0.00126987 | 0.01743570 | 56.2500% |
| 11 | 327 | 0.00131585 | 0.00111115 | 0.01463144 | 54.7401% |
| 12 | 337 | 0.00025126 | 0.00000000 | 0.01338147 | 49.5549% |

### JPM

| Month | Count | Mean | Median | Std | Positive fraction |
|---|---|---|---|---|---|
| 1 | 342 | 0.00035451 | 0.00106731 | 0.01539074 | 54.3860% |
| 2 | 326 | 0.00130825 | 0.00174406 | 0.01588131 | 56.1350% |
| 3 | 372 | -0.00024451 | -0.00010235 | 0.02462663 | 49.7312% |
| 4 | 352 | 0.00066282 | 0.00071950 | 0.01916087 | 51.7045% |
| 5 | 359 | -0.00021416 | -0.00078755 | 0.01687263 | 46.2396% |
| 6 | 359 | 0.00030606 | 0.00066254 | 0.01651005 | 52.0891% |
| 7 | 360 | 0.00200825 | 0.00168782 | 0.01389826 | 55.8333% |
| 8 | 376 | -0.00044145 | 0.00004267 | 0.01555179 | 50.0000% |
| 9 | 346 | -0.00044977 | 0.00037100 | 0.01576957 | 51.4451% |
| 10 | 352 | 0.00207178 | 0.00120650 | 0.01717568 | 52.2727% |
| 11 | 327 | 0.00233883 | 0.00135386 | 0.01880176 | 53.8226% |
| 12 | 337 | 0.00145181 | 0.00091875 | 0.01422750 | 52.8190% |

## 20. FUTURE-PERTURBATION TEST

PASS. Synthetic and live tests modify OHLC and volume strictly after historical
cutoffs, rebuild all 88 inputs, and require exact equality through the cutoff,
including NaNs. Tomorrow_Return is excluded because it intentionally refers to
the following trading row. All live cutoff checks passed for all three tickers.

## 21. PREFIX-INVARIANCE TESTS

Offline cutoffs: 2021-06-15 (ordinary mid-month), 2021-06-30 (month/quarter end),
2021-12-31 (year end): all PASS for all 88 inputs. Full history and truncated-prefix
features match exactly; future OHLCV perturbation also passes at each cutoff.

Live checks:

| Ticker | Cutoff | Prefix | Perturbation |
|---|---|---|---|
| AAPL | 2015-06-15 | PASS | PASS |
| AAPL | 2015-06-30 | PASS | PASS |
| AAPL | 2015-12-31 | PASS | PASS |
| MSFT | 2015-06-15 | PASS | PASS |
| MSFT | 2015-06-30 | PASS | PASS |
| MSFT | 2015-12-31 | PASS | PASS |
| JPM | 2015-06-15 | PASS | PASS |
| JPM | 2015-06-30 | PASS | PASS |
| JPM | 2015-12-31 | PASS | PASS |

## 22. SCALE-INVARIANCE TEST

PASS. Live tests multiply all prices by 7 and volume by 11: all temporal features
remain exactly equal, including missingness. Combined 88-feature checks pass with
rtol=atol=1e-6 for existing numerical computations. An offline test uses price/volume
factors 11/7, exact temporal equality and 1e-7 tolerance for combined features.
No scale parameters are learned or fitted.

## 23. LEAKAGE AUDIT

| Check | Result |
|---|---|
| No future market observations | PASS |
| No next-row inspection in temporal inputs | PASS |
| No target-derived temporal features | PASS |
| Target absent from all registries | PASS |
| Chronological split | PASS |
| Purged realization boundary | PASS |
| No test fitting | PASS |
| No backward fill | PASS |
| No future interpolation | PASS |
| Future perturbation | PASS |
| Prefix invariance | PASS |

The separate target and purge mapping retain negative shifts by design; no temporal
input uses one. Known month/quarter/year endpoints require no future observed rows.
These checks establish computational causality on supplied data, not point-in-time
purity of retrospectively adjusted Yahoo market history.

## 24. AUTOMATED TESTS

39 tests executed; 39 passed; zero failures: 13 unchanged V4 tests, 11 unchanged
V5 tests and 15 V6 tests. Commands actually executed:

```sh
venv/bin/python -m unittest discover -s tests -v
venv/bin/python -m models.temporal_comparison AAPL MSFT JPM
```

The suite covers one-hot correctness, month/day/year cycles and wraps, leap years,
quarter/boundary arithmetic, holiday-sized gaps, local DST behavior, metadata and
registries, old-mode equality, prefix/future invariance, scale invariance, finite
matrices, training-only fitting for all modes, and reporting-only return statistics.
All six live model fits completed with their assertions. Module imports passed.

## 25. V5 REGRESSION CHECK

All 24 prior tests pass unchanged. All 70 quantitative definitions, original 10
features, RF configuration, target and ingestion remain unchanged. Basic, advanced
and advanced_temporal were constructed and their finite ML matrices exercised in
unit tests; advanced and advanced_temporal were also fitted live three times each.
The tests verify training-only calls for all three modes with the exact configuration.

All 22 protected files (prior report artifacts, ingestion, requirements and existing
quantitative feature modules) match their before-work SHA-256 hashes. All 73 original
V5 metadata entries match their saved JSON exactly. See v6_preservation.json.
Historical V3/V4/V5 report files were not regenerated. Main still defaults to basic.

## 26. DOCUMENTATION GENERATED

- v6_temporal_feature_catalog.md: all definitions, encodings, ranges, data sources,
  calendar semantics, safeguards, deliberate omissions and exchange limitations.
- v6_feature_metadata.json: complete extended feature metadata, preserving old entries.
- v6_experiments.json/.txt: exact measured diagnostics, profiles, importances and audits.
- v6_tests.txt and v6_preservation.json: executed test and preservation evidence.
- This complete report, including every changed/created source file below.

## 27. ERRORS/WARNINGS

The first restricted-network run failed Yahoo DNS resolution; an authorized
network-enabled rerun was used. A live regression assertion then detected that
concatenating new columns lost the original Yahoo column-axis name (Price), not
values. The factory now preserves this metadata; the regression test includes a
named column axis, and the full suite plus all live experiments were rerun.
Successful runs produced no numerical/model warnings. No tuning or feature removal
was performed to change metrics. Unexpected diagnostic failures remain visible.

## 28. COMPLETE SOURCE CODE

The following are complete contents of every created/modified Python source file.
Existing quantitative, ingestion and model modules were not edited for V6.

### main.py

```python
"""Terminal orchestration for the CastiFy V6 research pipeline."""
from data.market_data import (
    MarketDataError, download_market_data, normalize_ticker, print_data_report
)
from features.feature_factory import build_feature_set
from models.baseline import (
    chronological_split, evaluate_baseline, prepare_ml_dataset, print_baseline_report
)

START_DATE = "2010-01-01"
END_DATE = None
FEATURE_SET = "basic"  # Also supports "advanced" and "advanced_temporal".


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
    modes = {"basic": BASIC_FEATURES, "advanced": ADVANCED_FEATURES,
             "advanced_temporal": ADVANCED_TEMPORAL_FEATURES}
    if feature_set not in modes:
        raise ValueError("feature_set must be 'basic', 'advanced', or 'advanced_temporal'.")
    return modes[feature_set].copy()


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


# V6 is additive: do not change ADVANCED_FEATURES or its original family groups.
TEMPORAL_FEATURES = [
    "DOW_Monday", "DOW_Tuesday", "DOW_Wednesday", "DOW_Thursday", "DOW_Friday",
    "Month_Sin", "Month_Cos", "DayOfMonth_Sin", "DayOfMonth_Cos",
    "DayOfYear_Sin", "DayOfYear_Cos",
    "Calendar_Days_From_Month_Start", "Calendar_Days_To_Month_End",
    "Calendar_Days_From_Quarter_Start", "Calendar_Days_To_Quarter_End",
    "Is_Quarter_Start_Region", "Is_Quarter_End_Region",
    "Calendar_Days_Since_Previous_Session"
]
ADVANCED_TEMPORAL_FEATURES = ADVANCED_FEATURES + TEMPORAL_FEATURES
TEMPORAL_METADATA = {}


def _temporal(name, definition, encoding, value_range, lookback=0):
    metadata = dict(
        name=name, family="temporal", definition=definition, description=definition,
        lookback=lookback, minimum_raw_rows=lookback + 1,
        normalized=encoding in ("one-hot", "cyclical", "binary"), future_safe=True,
        encoding=encoding, range=value_range, uses_market_values=False,
        uses_future_observations=False, exchange_specific=False,
        calendar_semantics="Gregorian calendar; index-local session date; zero-based elapsed/remaining calendar days."
    )
    TEMPORAL_METADATA[name] = metadata
    FEATURE_METADATA[name] = metadata


for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"):
    _temporal(f"DOW_{day}", f"1 if current session date is {day}, else 0; weekend dates rejected.", "one-hot", "0 or 1")
for name, phase in (("Month", "(month-1)/12"),
                    ("DayOfMonth", "(day-1)/days_in_current_month"),
                    ("DayOfYear", "(day_of_year-1)/(366 if leap year else 365)")):
    for suffix, function in (("Sin", "sin"), ("Cos", "cos")):
        _temporal(f"{name}_{suffix}", f"{function}(2*pi*{phase}); calendar phase, not an ordinal category.", "cyclical", "[-1, 1]")
for name, definition, upper in (
    ("Calendar_Days_From_Month_Start", "Current date minus first calendar day of current month; first day=0.", 30),
    ("Calendar_Days_To_Month_End", "Last calendar day of current month minus current date; last day=0.", 30),
    ("Calendar_Days_From_Quarter_Start", "Current date minus first calendar day of Gregorian quarter; first day=0.", 91),
    ("Calendar_Days_To_Quarter_End", "Last calendar day of Gregorian quarter minus current date; last day=0.", 91)):
    _temporal(name, definition, "calendar-day distance", f"[0, {upper}]")
_temporal("Is_Quarter_Start_Region", "1 in first seven calendar days of quarter (elapsed 0..6), else 0.", "binary", "0 or 1")
_temporal("Is_Quarter_End_Region", "1 in last seven calendar days of quarter (remaining 0..6), else 0.", "binary", "0 or 1")
_temporal("Calendar_Days_Since_Previous_Session", "Current date minus previous observed session date, in local calendar days; first row NaN. Gaps can include missing provider rows.", "calendar-day distance", ">=1, first row NaN", 1)
assert len(ADVANCED_TEMPORAL_FEATURES) == len(set(ADVANCED_TEMPORAL_FEATURES))
assert "Tomorrow_Return" not in BASIC_FEATURES + ADVANCED_TEMPORAL_FEATURES
assert set(TEMPORAL_METADATA) == set(TEMPORAL_FEATURES)
```

### features/feature_factory.py

```python
"""Select the historical basic baseline or the explicit V5 advanced feature set."""
import numpy as np
import pandas as pd
from features.basic_features import build_basic_features
from features.temporal_features import temporal_features
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
    if feature_set in ("advanced", "advanced_temporal"):
        for builder in (price_features, momentum_features, volatility_features,
                        volume_features, technical_features):
            block = builder(stock)
            featured[block.columns] = block
        if feature_set == "advanced_temporal":
            column_name = featured.columns.name
            featured = pd.concat([featured, temporal_features(stock)], axis=1)
            featured.columns.name = column_name
        if np.isinf(featured[columns].to_numpy()).any():
            raise ValueError("Advanced feature generation produced infinity; inspect raw inputs.")
    assert "Tomorrow_Return" not in columns
    assert featured.index.equals(stock.index)
    return featured
```

### features/temporal_features.py

```python
"""Exchange-neutral Gregorian context for completed session-date labels.

Known calendar endpoints are allowed; future downloaded rows are never consulted.
Dates are interpreted in the index's existing timezone, without UTC conversion.
"""
import numpy as np
import pandas as pd


def temporal_features(stock: pd.DataFrame) -> pd.DataFrame:
    """Build date-only inputs and a backward-looking observed-session gap.

    Weekend rows are explicitly unsupported in this Monday-Friday representation.
    Gaps measure observed dates, not certified exchange closures or missing bars.
    """
    index = stock.index
    if not isinstance(index, pd.DatetimeIndex) or index.hasnans:
        raise ValueError("Temporal features require valid datetime session labels.")
    dates = index.tz_localize(None).normalize()
    if not dates.is_monotonic_increasing or not dates.is_unique:
        raise ValueError("Temporal features require sorted, unique session dates.")
    if (dates.dayofweek > 4).any():
        raise ValueError("Weekend session dates are unsupported by the Monday-Friday temporal encoding.")
    output = {}
    for day, name in enumerate(("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")):
        output[f"DOW_{name}"] = (dates.dayofweek == day).astype(float)
    phases = {
        "Month": (dates.month - 1) / 12,
        "DayOfMonth": (dates.day - 1) / dates.days_in_month,
        "DayOfYear": (dates.dayofyear - 1) / np.where(dates.is_leap_year, 366, 365)
    }
    for name, phase in phases.items():
        output[f"{name}_Sin"] = np.sin(2 * np.pi * phase)
        output[f"{name}_Cos"] = np.cos(2 * np.pi * phase)
    month_start = dates.to_period("M").start_time
    month_end = dates.to_period("M").end_time.normalize()
    quarter_start = dates.to_period("Q-DEC").start_time
    quarter_end = dates.to_period("Q-DEC").end_time.normalize()
    output["Calendar_Days_From_Month_Start"] = (dates - month_start).days.astype(float)
    output["Calendar_Days_To_Month_End"] = (month_end - dates).days.astype(float)
    from_quarter = (dates - quarter_start).days
    to_quarter = (quarter_end - dates).days
    output["Calendar_Days_From_Quarter_Start"] = from_quarter.astype(float)
    output["Calendar_Days_To_Quarter_End"] = to_quarter.astype(float)
    output["Is_Quarter_Start_Region"] = (from_quarter < 7).astype(float)
    output["Is_Quarter_End_Region"] = (to_quarter < 7).astype(float)
    output["Calendar_Days_Since_Previous_Session"] = pd.Series(dates, index=index).diff().dt.days
    result = pd.DataFrame(output, index=index)
    assert (result.iloc[:, :5].sum(axis=1) == 1).all()
    return result
```

### models/temporal_comparison.py

```python
"""V6 family ablation and descriptive profiles; never target-encode calendars.

Run: python -m models.temporal_comparison AAPL MSFT JPM
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from data.market_data import download_market_data, normalize_ticker
from features.audit import audit_features
from features.feature_factory import build_feature_set
from features.registry import ADVANCED_FEATURES, ADVANCED_TEMPORAL_FEATURES, TEMPORAL_FEATURES
from models.baseline import chronological_split, evaluate_baseline, prepare_ml_dataset


def return_profiles(featured: pd.DataFrame) -> dict:
    """Summarize historical same-session Daily_Return, for reporting only.

    These full-history descriptive tables are never merged into model inputs and
    never used as training targets, fitted encodings, or persistent market laws.
    """
    returns = featured["Daily_Return"].dropna()
    tables = {}
    for label, groups in (("weekday", returns.index.dayofweek), ("month", returns.index.month)):
        summary = returns.groupby(groups).agg(
            count="count", mean="mean", median="median", std="std",
            positive_fraction=lambda values: float((values > 0).mean())
        )
        summary.index.name = label
        if label == "weekday":
            summary.index = summary.index.map(dict(enumerate(
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])))
        tables[label] = summary.reset_index().to_dict(orient="records")
    return tables


def verify_calendar_causality(stock: pd.DataFrame, full: pd.DataFrame) -> list[dict]:
    """Check all inputs on three historical prefixes and future OHLCV perturbations."""
    checks = []
    for cutoff in ("2015-06-15", "2015-06-30", "2015-12-31"):
        if not (stock.index.min() <= pd.Timestamp(cutoff) < stock.index.max()):
            checks.append(dict(cutoff=cutoff, result="outside downloaded range"))
            continue
        expected = full.loc[:cutoff, ADVANCED_TEMPORAL_FEATURES]
        prefix = build_feature_set(stock.loc[:cutoff], "advanced_temporal")
        pd.testing.assert_frame_equal(expected, prefix[ADVANCED_TEMPORAL_FEATURES], check_exact=True)
        changed = stock.copy()
        future = changed.index > cutoff
        changed.loc[future, ["Open", "High", "Low", "Close"]] *= 3
        changed.loc[future, "Volume"] *= 7
        perturbed = build_feature_set(changed, "advanced_temporal")
        pd.testing.assert_frame_equal(expected, perturbed.loc[:cutoff, ADVANCED_TEMPORAL_FEATURES], check_exact=True)
        checks.append(dict(cutoff=cutoff, prefix="PASS", perturbation="PASS"))
    return checks


def compare_temporal_family(stock: pd.DataFrame) -> dict:
    """Compare the same forest with and without calendar inputs on identical dates."""
    advanced = build_feature_set(stock, "advanced")
    temporal = build_feature_set(stock, "advanced_temporal")
    pd.testing.assert_frame_equal(advanced, temporal[advanced.columns])
    Xa, ya = prepare_ml_dataset(advanced, "advanced")
    Xt, yt = prepare_ml_dataset(temporal, "advanced_temporal")
    common = Xa.index.intersection(Xt.index).sort_values()
    Xa, ya, Xt, yt = Xa.loc[common], ya.loc[common], Xt.loc[common], yt.loc[common]
    pd.testing.assert_series_equal(ya, yt)
    pd.testing.assert_frame_equal(Xa, Xt[ADVANCED_FEATURES])
    splits = {"advanced": chronological_split(Xa, ya, stock.index),
              "advanced_temporal": chronological_split(Xt, yt, stock.index)}
    a, t = splits["advanced"], splits["advanced_temporal"]
    for name in ("X_train", "X_test", "y_train", "y_test"):
        assert a[name].index.equals(t[name].index)
    for name in ("y_train", "y_test"):
        pd.testing.assert_series_equal(a[name], t[name])
    assert a["removed"].equals(t["removed"])
    train_audit = audit_features(t["X_train"])
    full_audit = audit_features(Xt)
    temporal_audit = audit_features(t["X_train"][TEMPORAL_FEATURES])
    if train_audit["exact_duplicates"] or full_audit["exact_duplicates"]:
        raise ValueError("Exact duplicate sample inputs require review before this diagnostic.")
    causal_checks = verify_calendar_causality(stock, temporal)
    scaled = stock.copy()
    scaled[["Open", "High", "Low", "Close"]] *= 7
    scaled["Volume"] *= 11
    rebuilt = build_feature_set(scaled, "advanced_temporal")
    pd.testing.assert_frame_equal(temporal[TEMPORAL_FEATURES], rebuilt[TEMPORAL_FEATURES], check_exact=True)
    np.testing.assert_allclose(temporal[ADVANCED_TEMPORAL_FEATURES], rebuilt[ADVANCED_TEMPORAL_FEATURES],
                               equal_nan=True, rtol=1e-6, atol=1e-6)
    evaluations = {
        "advanced": evaluate_baseline(a, advanced, "advanced"),
        "advanced_temporal": evaluate_baseline(t, temporal, "advanced_temporal")
    }
    before, after = evaluations["advanced"]["metrics"], evaluations["advanced_temporal"]["metrics"]
    for metric in ("zero_mae", "zero_rmse", "momentum"):
        assert before[metric] == after[metric]
    importance = evaluations["advanced_temporal"]["importance"]
    temporal_importance = importance[importance.Feature.isin(TEMPORAL_FEATURES)]
    profiles = return_profiles(advanced)
    return dict(
        raw_rows=len(stock), raw_start=str(stock.index.min().date()), raw_end=str(stock.index.max().date()),
        eligible_rows=len(common), eligible_start=str(common.min().date()), eligible_end=str(common.max().date()),
        advanced_count=len(ADVANCED_FEATURES), temporal_count=len(TEMPORAL_FEATURES), combined_count=len(ADVANCED_TEMPORAL_FEATURES),
        train_before=t["train_before"], train_rows=len(t["X_train"]), test_rows=len(t["X_test"]),
        train_start=str(t["X_train"].index.min().date()), train_end=str(t["X_train"].index.max().date()),
        test_start=str(t["X_test"].index.min().date()), test_end=str(t["X_test"].index.max().date()),
        purged_dates=[str(d.date()) for d in t["removed"]], latest_train_target=str(t["latest_train_target"].date()),
        identical_dates="PASS", advanced_unchanged="PASS", all_matrices_finite="PASS",
        advanced=before, advanced_temporal=after,
        deltas={metric: after[metric] - before[metric] for metric in ("mae", "rmse", "r2", "direction")},
        temporal_importance_total=float(temporal_importance.Importance.sum()),
        temporal_importances=temporal_importance.to_dict(orient="records"),
        top20=importance.head(20).to_dict(orient="records"),
        weekday_profile=profiles["weekday"], month_profile=profiles["month"],
        training_audit=train_audit, full_sample_audit=full_audit, temporal_training_audit=temporal_audit,
        causality_checks=causal_checks, temporal_scale_invariance="PASS", combined_scale_invariance="PASS"
    )


def main() -> None:
    """Save V6-only artifacts; leave historical V3/V4/V5 results untouched."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickers", nargs="+")
    parser.add_argument("--start", default="2010-01-01")
    parser.add_argument("--end", default=None)
    args = parser.parse_args()
    measurements = {}
    for raw_ticker in args.tickers:
        ticker = normalize_ticker(raw_ticker)
        print(f"V6 temporal ablation for {ticker}...", flush=True)
        stock = download_market_data(ticker, args.start, args.end)
        result = compare_temporal_family(stock)
        result["effective_end_exclusive"] = stock.attrs["effective_end_exclusive"]
        result["requested_start"] = args.start
        measurements[ticker] = result
        print(json.dumps(result, indent=2), flush=True)
    Path("reports").mkdir(exist_ok=True)
    Path("reports/v6_experiments.json").write_text(json.dumps(measurements, indent=2) + "\n")


if __name__ == "__main__":
    main()
```

### tests/test_temporal_features.py

```python
"""Date arithmetic, mode preservation and causality checks without a network."""
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from features.temporal_features import temporal_features
from features.feature_factory import build_feature_set
from features.registry import (
    BASIC_FEATURES, ADVANCED_FEATURES, TEMPORAL_FEATURES, ADVANCED_TEMPORAL_FEATURES,
    TEMPORAL_METADATA, FEATURE_METADATA, get_feature_columns
)
from models.baseline import prepare_ml_dataset, chronological_split, evaluate_baseline
from test_pipeline import sample_data


def dates_only(dates):
    return pd.DataFrame(index=pd.DatetimeIndex(dates))


class TemporalTests(unittest.TestCase):
    def test_weekday_one_hot(self):
        result = temporal_features(dates_only(pd.bdate_range("2024-01-08", periods=5)))
        np.testing.assert_array_equal(result[TEMPORAL_FEATURES[:5]], np.eye(5))
        np.testing.assert_array_equal(result[TEMPORAL_FEATURES[:5]].sum(axis=1), np.ones(5))

    def test_bad_dates_explicitly_rejected(self):
        for bad in (dates_only(["2024-01-06"]), dates_only(["2024-01-08", "2024-01-05"]),
                    dates_only(["2024-01-08", "2024-01-08"]), dates_only([pd.NaT]),
                    pd.DataFrame(index=[1, 2])):
            with self.assertRaises(ValueError):
                temporal_features(bad)

    def test_month_phase_and_wrap(self):
        f = temporal_features(dates_only(["2023-12-29", "2024-01-01", "2024-07-01"]))
        np.testing.assert_allclose(f[["Month_Sin", "Month_Cos"]].iloc[1], [0, 1], atol=1e-15)
        np.testing.assert_allclose(f[["Month_Sin", "Month_Cos"]].iloc[2], [0, -1], atol=1e-15)
        distance = np.linalg.norm(f[["Month_Sin", "Month_Cos"]].iloc[0] - f[["Month_Sin", "Month_Cos"]].iloc[1])
        self.assertAlmostEqual(distance, 2 * np.sin(np.pi / 12))

    def test_month_length_and_boundary(self):
        f = temporal_features(dates_only(["2024-01-31", "2024-02-01", "2024-02-29", "2024-03-01"]))
        np.testing.assert_allclose(f.DayOfMonth_Sin, np.sin(2 * np.pi * np.array([30/31, 0, 28/29, 0])))
        np.testing.assert_array_equal(f.Calendar_Days_From_Month_Start, [30, 0, 28, 0])
        np.testing.assert_array_equal(f.Calendar_Days_To_Month_End, [0, 28, 0, 30])
        phase = f[["DayOfMonth_Sin", "DayOfMonth_Cos"]]
        self.assertLess(np.linalg.norm(phase.iloc[2] - phase.iloc[3]), .22)

    def test_leap_february_28_29_march_1(self):
        f = temporal_features(dates_only(["2024-02-28", "2024-02-29", "2024-03-01"]))
        phases = np.array([58, 59, 60]) / 366
        np.testing.assert_allclose(f.DayOfYear_Sin, np.sin(2 * np.pi * phases))
        np.testing.assert_allclose(f.DayOfYear_Cos, np.cos(2 * np.pi * phases))
        nonleap = temporal_features(dates_only(["2023-03-01"]))
        self.assertAlmostEqual(nonleap.DayOfYear_Sin.iloc[0], np.sin(2 * np.pi * 59/365))

    def test_year_wrap(self):
        f = temporal_features(dates_only(["2020-12-31", "2021-01-01"]))
        np.testing.assert_allclose(f[["DayOfYear_Sin", "DayOfYear_Cos"]].iloc[1], [0, 1])
        self.assertAlmostEqual(f.DayOfYear_Sin.iloc[0], np.sin(2 * np.pi * 365/366))
        self.assertLess(np.linalg.norm(f[["DayOfYear_Sin", "DayOfYear_Cos"]].iloc[0] - [0, 1]), .018)

    def test_quarter_distances_and_regions(self):
        f = temporal_features(dates_only(["2024-01-01", "2024-01-08", "2024-03-25", "2024-03-29", "2024-04-01"]))
        np.testing.assert_array_equal(f.Calendar_Days_From_Quarter_Start, [0, 7, 84, 88, 0])
        np.testing.assert_array_equal(f.Calendar_Days_To_Quarter_End, [90, 83, 6, 2, 90])
        np.testing.assert_array_equal(f.Is_Quarter_Start_Region, [1, 0, 0, 0, 1])
        np.testing.assert_array_equal(f.Is_Quarter_End_Region, [0, 0, 1, 1, 0])

    def test_weekend_and_holiday_gaps(self):
        f = temporal_features(dates_only(["2024-01-05", "2024-01-08", "2024-01-12", "2024-01-16"]))
        self.assertTrue(pd.isna(f.Calendar_Days_Since_Previous_Session.iloc[0]))
        np.testing.assert_array_equal(f.Calendar_Days_Since_Previous_Session.iloc[1:], [3, 4, 4])

    def test_local_timezone_dst_gap(self):
        index = pd.DatetimeIndex(["2024-03-08", "2024-03-11"], tz="America/New_York")
        f = temporal_features(dates_only(index))
        self.assertEqual(f.Calendar_Days_Since_Previous_Session.iloc[1], 3)
        self.assertEqual(f.DOW_Monday.iloc[1], 1)
        self.assertTrue(f.index.equals(index))

    def test_all_cycles_finite_bounded_unit_circle(self):
        f = temporal_features(dates_only(pd.bdate_range("2019-01-01", "2025-12-31")))
        for name in ("Month", "DayOfMonth", "DayOfYear"):
            pair = f[[name + "_Sin", name + "_Cos"]].to_numpy()
            self.assertTrue(np.isfinite(pair).all())
            self.assertTrue((np.abs(pair) <= 1).all())
            np.testing.assert_allclose(np.sum(pair**2, axis=1), 1, atol=1e-14)

    def test_registries_metadata_and_mode_preservation(self):
        self.assertEqual([len(get_feature_columns(mode)) for mode in ("basic", "advanced", "advanced_temporal")], [10,70,88])
        self.assertEqual(ADVANCED_TEMPORAL_FEATURES, ADVANCED_FEATURES + TEMPORAL_FEATURES)
        self.assertNotIn("Tomorrow_Return", BASIC_FEATURES + ADVANCED_TEMPORAL_FEATURES)
        self.assertEqual(set(TEMPORAL_METADATA), set(TEMPORAL_FEATURES))
        for name in TEMPORAL_FEATURES:
            m = FEATURE_METADATA[name]
            self.assertEqual(m["family"], "temporal")
            self.assertTrue(m["future_safe"])
            self.assertFalse(m["uses_market_values"])
            self.assertFalse(m["uses_future_observations"])
            self.assertIn("calendar_semantics", m)
        raw = sample_data(400)
        raw.columns.name = "Price"
        before = raw.copy()
        old = build_feature_set(raw, "advanced")
        new = build_feature_set(raw, "advanced_temporal")
        pd.testing.assert_frame_equal(old, new[old.columns])
        pd.testing.assert_frame_equal(raw, before)

    def test_multiple_prefixes_and_future_perturbation(self):
        raw = sample_data(800)
        full = build_feature_set(raw, "advanced_temporal")
        for date in ("2021-06-15", "2021-06-30", "2021-12-31"):
            with self.subTest(cutoff=date):
                expected = full.loc[:date, ADVANCED_TEMPORAL_FEATURES]
                prefix = build_feature_set(raw.loc[:date], "advanced_temporal")
                pd.testing.assert_frame_equal(expected, prefix[ADVANCED_TEMPORAL_FEATURES], check_exact=True)
                changed = raw.copy()
                future = changed.index > date
                changed.loc[future, ["Open", "High", "Low", "Close"]] *= 3
                changed.loc[future, "Volume"] *= 7
                rebuilt = build_feature_set(changed, "advanced_temporal")
                pd.testing.assert_frame_equal(expected, rebuilt.loc[:date, ADVANCED_TEMPORAL_FEATURES], check_exact=True)

    def test_temporal_exact_scale_invariance(self):
        raw = sample_data(400)
        scaled = raw.copy()
        scaled[["Open", "High", "Low", "Close"]] *= 11
        scaled["Volume"] *= 7
        before = build_feature_set(raw, "advanced_temporal")
        after = build_feature_set(scaled, "advanced_temporal")
        pd.testing.assert_frame_equal(before[TEMPORAL_FEATURES], after[TEMPORAL_FEATURES], check_exact=True)
        np.testing.assert_allclose(before[ADVANCED_TEMPORAL_FEATURES], after[ADVANCED_TEMPORAL_FEATURES], equal_nan=True, rtol=1e-7, atol=1e-7)

    def test_profiles_are_same_day_descriptive_only(self):
        from models.temporal_comparison import return_profiles
        f = pd.DataFrame({"Daily_Return": [np.nan, .1, -.2, 0.],
                          "Tomorrow_Return": [99., 99., 99., 99.]},
                         index=pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15", "2024-02-05"]))
        profiles = return_profiles(f)
        monday = profiles["weekday"][0]
        self.assertEqual(monday["weekday"], "Monday")
        self.assertEqual(monday["count"], 3)
        self.assertAlmostEqual(monday["mean"], -.1/3)
        self.assertEqual(monday["median"], 0)
        self.assertAlmostEqual(monday["std"], np.std([.1, -.2, 0], ddof=1))
        self.assertAlmostEqual(monday["positive_fraction"], 1/3)
        january = profiles["month"][0]
        self.assertEqual(january["count"], 2)
        self.assertAlmostEqual(january["positive_fraction"], .5)

    @patch("models.baseline.RandomForestRegressor")
    def test_three_modes_finite_and_train_only_fit(self, forest):
        raw = sample_data(400)
        for mode in ("basic", "advanced", "advanced_temporal"):
            f = build_feature_set(raw, mode)
            X, y = prepare_ml_dataset(f, mode)
            self.assertTrue(np.isfinite(X.to_numpy()).all())
            split = chronological_split(X, y, raw.index)
            forest.return_value.predict.return_value = np.zeros(len(split["y_test"]))
            forest.return_value.feature_importances_ = np.full(X.shape[1], 1/X.shape[1])
            evaluate_baseline(split, f, mode)
            args = forest.return_value.fit.call_args.args
            self.assertIs(args[0], split["X_train"])
            self.assertIs(args[1], split["y_train"])
        self.assertEqual(forest.call_count, 3)
        forest.assert_called_with(n_estimators=300, random_state=42, n_jobs=-1)


if __name__ == "__main__":
    unittest.main()
```

## 29. V6 COMPLETION STATUS

V6 is complete: 18 documented calendar inputs, three explicit feature modes, additive
metadata, calendar-safe construction, full regression and causality tests, controlled
three-ticker family ablations, statistical profiles, importance and redundancy reports.
No V7 functionality was implemented.

## 30. V7 HANDOFF

Market/sector context remains absent: no market-index returns, sector ETF returns,
relative market/sector performance, VIX, rates, Treasury yields or cross-asset context.
Future integration will require timestamp/calendar alignment and availability rules
before such inputs can be added safely. No data for these sources was downloaded.

Other limitations remain: generic rather than exchange-specific calendars, explicit
weekend rejection in temporal mode, provider gaps versus certified sessions, historical
adjusted-data vintage, correlated features, one inspected holdout, no statistical
significance or walk-forward estimates. The weekday/month profiles do not establish
persistent effects. No signals, backtests, model tuning, dashboard or V7+ features.
