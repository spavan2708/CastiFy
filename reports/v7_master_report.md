# CASTIFY V7 MASTER REPORT

## 1. ARCHITECTURE CHANGES

```text
main.py                              fourth mode orchestration
config/
  __init__.py
  market_context.py                  centralized profiles, symbols, age policy
data/
  market_data.py                     unchanged V4 ingestion
  context_data.py                    shared cache, index quote adapter, alignment
features/
  registry.py                        additive combined mode
  feature_factory.py                 optional explicit context bundle
  context_registry.py                44 context definitions/metadata
  context_features.py                date-safe context calculations
models/
  baseline.py                        unchanged forest, split and target handling
  context_comparison.py              V7 controlled experiment and reports
 tests/
  test_context_features.py           17 new offline tests
reports/
  v7_context_feature_catalog.md
  v7_feature_metadata.json
  v7_experiments.json
  v7_experiments.txt
  v7_tests.txt
  v7_preservation.json
  v7_rate_probe.txt
  v7_master_report.md
```

No new dependencies, predictive models, regime classification or database.

## 2. FILES CREATED

- config/__init__.py
- config/market_context.py
- data/context_data.py
- features/context_registry.py
- features/context_features.py
- models/context_comparison.py
- tests/test_context_features.py
- reports/v7_context_feature_catalog.md
- reports/v7_feature_metadata.json
- reports/v7_experiments.json
- reports/v7_experiments.txt
- reports/v7_tests.txt
- reports/v7_preservation.json
- reports/v7_rate_probe.txt
- reports/v7_master_report.md

## 3. FILES MODIFIED

- main.py
- features/registry.py
- features/feature_factory.py

## 4. CONTEXT ENGINE DESIGN

A configured US ticker selects SPY, QQQ, VIX, TNX and its explicit sector ETF.
ContextCache downloads each distinct symbol/date request once per experiment run.
ETF data uses the original V4 downloader. For Yahoo index quote placeholders only,
a small adapter reuses V4 standardization/validation after recording and removing
rows with no OHLC quotes and zero/missing volume. Partial invalid observations fail.
Stock ingestion is unchanged. No prices are fabricated or filled at ingestion.

The feature factory accepts an explicit context bundle. Context computations produce
44 named inputs; no automatic numeric selection. Original stock rows and target
semantics remain intact. Missing features are removed only in the separate ML
matrix, so Tomorrow_Return still references the next original stock trading row.

## 5. EXTERNAL DATA SOURCES

| Symbol | Purpose | Actual first date | Actual last date | Validated observations | Provider rows | Empty quote placeholders |
|---|---|---|---|---|---|---|
| SPY | Broad US equity market ETF | 2010-01-04 | 2026-09-28 | 4209 | 4209 | 0 |
| QQQ | Growth/technology-heavy US equity ETF | 2010-01-04 | 2026-09-28 | 4209 | 4209 | 0 |
| ^VIX | Cboe implied volatility index; Yahoo points, divided by 100 for level | 2010-01-04 | 2026-09-28 | 4211 | 4366 | 155 |
| ^TNX | Yahoo 10-year Treasury yield proxy; percentage points, divided by 100 | 2010-01-04 | 2026-09-28 | 4207 | 4209 | 2 |
| XLK | Technology sector ETF | 2010-01-04 | 2026-09-28 | 4209 | 4209 | 0 |
| XLF | Financial sector ETF | 2010-01-04 | 2026-09-28 | 4209 | 4209 | 0 |

All requests start 2010-01-01, end=None resolved to exclusive 2026-09-29. Every
source uses daily interval and explicit auto_adjust=True. ETF OHLC are split/dividend
adjusted; VIX/TNX are index levels, not equity prices or tradable volume. Adjusted
historical data is not a certified point-in-time vintage archive. Source dates are
retained exactly; no positional pairing or timezone conversion is applied.

## 6. SECTOR MAPPING

| Stock | Sector ETF |
|---|---|
| AAPL | XLK |
| MSFT | XLK |
| JPM | XLF |

These mappings are centralized in config/market_context.py and were all exercised.
Sector features retain generic Sector_* names. No automatic sector discovery or
international US-profile fallback exists.

## 7. COMPLETE CONTEXT FEATURE LIST

### market: 15

```text
SPY_Return_1D
SPY_Return_5D
SPY_Return_20D
QQQ_Return_1D
QQQ_Return_5D
QQQ_Return_20D
SPY_Price_to_SMA_20
SPY_Price_to_SMA_50
SPY_Price_to_SMA_200
QQQ_Price_to_SMA_20
QQQ_Price_to_SMA_50
SPY_Volatility_5
SPY_Volatility_20
SPY_Volatility_60
SPY_Volatility_Ratio_5_20
```

### volatility_context: 5

```text
VIX_Level_Normalized
VIX_Return_1D
VIX_Return_5D
VIX_Price_to_SMA_20
VIX_Percentile_252
```

### sector: 5

```text
Sector_Return_1D
Sector_Return_5D
Sector_Return_20D
Sector_Price_to_SMA_20
Sector_Volatility_20
```

### relative: 15

```text
Stock_vs_SPY_Return_5D
Stock_vs_SPY_Return_20D
Stock_vs_Sector_Return_5D
Stock_vs_Sector_Return_20D
Stock_vs_QQQ_Return_20D
Stock_SPY_Correlation_20
Stock_SPY_Correlation_60
Stock_Sector_Correlation_20
Stock_Sector_Correlation_60
Stock_SPY_Beta_20
Stock_SPY_Beta_60
Market_Adjusted_Return_1D
Sector_Adjusted_Return_1D
Stock_to_SPY_Volatility_20
Stock_to_Sector_Volatility_20
```

### rates: 4

```text
Treasury_10Y_Level
Treasury_10Y_Change_1D
Treasury_10Y_Change_5D
Treasury_10Y_vs_MA_20
```

## 8. CONTEXT FEATURE DEFINITIONS

| Feature | Definition | Source | Minimum source/window rows | Alignment |
|---|---|---|---|---|
| SPY_Return_1D | Close / Close.shift(1) - 1; require all 2 aligned closes | SPY | 2 | Exact stock-date grid, complete trailing windows |
| SPY_Return_5D | Close / Close.shift(5) - 1; require all 6 aligned closes | SPY | 6 | Exact stock-date grid, complete trailing windows |
| SPY_Return_20D | Close / Close.shift(20) - 1; require all 21 aligned closes | SPY | 21 | Exact stock-date grid, complete trailing windows |
| SPY_Price_to_SMA_20 | Close / mean(20 aligned closes) - 1 | SPY | 20 | Exact stock-date grid, complete trailing windows |
| SPY_Price_to_SMA_50 | Close / mean(50 aligned closes) - 1 | SPY | 50 | Exact stock-date grid, complete trailing windows |
| SPY_Price_to_SMA_200 | Close / mean(200 aligned closes) - 1 | SPY | 200 | Exact stock-date grid, complete trailing windows |
| SPY_Volatility_5 | Std of 5 aligned returns, ddof=1 | SPY | 6 | Exact stock-date grid, complete trailing windows |
| SPY_Volatility_20 | Std of 20 aligned returns, ddof=1 | SPY | 21 | Exact stock-date grid, complete trailing windows |
| SPY_Volatility_60 | Std of 60 aligned returns, ddof=1 | SPY | 61 | Exact stock-date grid, complete trailing windows |
| QQQ_Return_1D | Close / Close.shift(1) - 1; require all 2 aligned closes | QQQ | 2 | Exact stock-date grid, complete trailing windows |
| QQQ_Return_5D | Close / Close.shift(5) - 1; require all 6 aligned closes | QQQ | 6 | Exact stock-date grid, complete trailing windows |
| QQQ_Return_20D | Close / Close.shift(20) - 1; require all 21 aligned closes | QQQ | 21 | Exact stock-date grid, complete trailing windows |
| QQQ_Price_to_SMA_20 | Close / mean(20 aligned closes) - 1 | QQQ | 20 | Exact stock-date grid, complete trailing windows |
| QQQ_Price_to_SMA_50 | Close / mean(50 aligned closes) - 1 | QQQ | 50 | Exact stock-date grid, complete trailing windows |
| Sector_Return_1D | Close / Close.shift(1) - 1; require all 2 aligned closes | configured sector ETF (XLK/XLF) | 2 | Exact stock-date grid, complete trailing windows |
| Sector_Return_5D | Close / Close.shift(5) - 1; require all 6 aligned closes | configured sector ETF (XLK/XLF) | 6 | Exact stock-date grid, complete trailing windows |
| Sector_Return_20D | Close / Close.shift(20) - 1; require all 21 aligned closes | configured sector ETF (XLK/XLF) | 21 | Exact stock-date grid, complete trailing windows |
| Sector_Price_to_SMA_20 | Close / mean(20 aligned closes) - 1 | configured sector ETF (XLK/XLF) | 20 | Exact stock-date grid, complete trailing windows |
| Sector_Volatility_20 | Std of 20 aligned returns, ddof=1 | configured sector ETF (XLK/XLF) | 21 | Exact stock-date grid, complete trailing windows |
| SPY_Volatility_Ratio_5_20 | SPY sample volatility 5 / 20; denominator >1e-12 | SPY | 21 | Exact stock-date grid, complete trailing windows |
| VIX_Level_Normalized | Prior VIX Close / 100; implied annualized volatility decimal, not realized return | ^VIX | 1 | Strict previous source date after native trailing calculation |
| VIX_Return_1D | VIX Close / previous native source Close - 1 | ^VIX | 2 | Strict previous source date after native trailing calculation |
| VIX_Return_5D | VIX Close / native source Close 5 rows earlier - 1 | ^VIX | 6 | Strict previous source date after native trailing calculation |
| VIX_Price_to_SMA_20 | VIX Close / trailing 20-source-row mean - 1 | ^VIX | 20 | Strict previous source date after native trailing calculation |
| VIX_Percentile_252 | Current VIX rank within trailing 252 source closes / 252; average ranks for ties, includes current source close | ^VIX | 252 | Strict previous source date after native trailing calculation |
| Stock_vs_SPY_Return_5D | Stock trailing 5-row return minus aligned SPY return | stock + SPY | 6 | Exact stock-date grid, complete trailing windows |
| Stock_vs_SPY_Return_20D | Stock trailing 20-row return minus aligned SPY return | stock + SPY | 21 | Exact stock-date grid, complete trailing windows |
| Stock_vs_Sector_Return_5D | Stock trailing 5-row return minus aligned Sector return | stock + Sector | 6 | Exact stock-date grid, complete trailing windows |
| Stock_vs_Sector_Return_20D | Stock trailing 20-row return minus aligned Sector return | stock + Sector | 21 | Exact stock-date grid, complete trailing windows |
| Stock_vs_QQQ_Return_20D | Stock trailing 20-row return minus aligned QQQ return | stock + QQQ | 21 | Exact stock-date grid, complete trailing windows |
| Stock_SPY_Correlation_20 | Pearson correlation over 20 matched return pairs; full window, std >1e-12 | stock + SPY | 21 | Exact stock-date grid, complete trailing windows |
| Stock_SPY_Correlation_60 | Pearson correlation over 60 matched return pairs; full window, std >1e-12 | stock + SPY | 61 | Exact stock-date grid, complete trailing windows |
| Stock_Sector_Correlation_20 | Pearson correlation over 20 matched return pairs; full window, std >1e-12 | stock + Sector | 21 | Exact stock-date grid, complete trailing windows |
| Stock_Sector_Correlation_60 | Pearson correlation over 60 matched return pairs; full window, std >1e-12 | stock + Sector | 61 | Exact stock-date grid, complete trailing windows |
| Stock_SPY_Beta_20 | Sample cov(stock, SPY)/sample var(SPY), ddof=1 over 20 pairs; variance >1e-12 | stock + SPY | 21 | Exact stock-date grid, complete trailing windows |
| Stock_SPY_Beta_60 | Sample cov(stock, SPY)/sample var(SPY), ddof=1 over 60 pairs; variance >1e-12 | stock + SPY | 61 | Exact stock-date grid, complete trailing windows |
| Market_Adjusted_Return_1D | Stock current return minus aligned SPY current return; not estimated alpha | stock + SPY | 2 | Exact stock-date grid, complete trailing windows |
| Sector_Adjusted_Return_1D | Stock current return minus aligned Sector current return; not estimated alpha | stock + Sector | 2 | Exact stock-date grid, complete trailing windows |
| Stock_to_SPY_Volatility_20 | Stock / SPY 20-return sample std; denominator >1e-12 | stock + SPY | 21 | Exact stock-date grid, complete trailing windows |
| Stock_to_Sector_Volatility_20 | Stock / Sector 20-return sample std; denominator >1e-12 | stock + Sector | 21 | Exact stock-date grid, complete trailing windows |
| Treasury_10Y_Level | Prior Yahoo ^TNX Close / 100; decimal annual yield | ^TNX | 1 | Strict previous source date after native trailing calculation |
| Treasury_10Y_Change_1D | ^TNX Close.diff(1) / 100; absolute decimal-yield change across source rows | ^TNX | 2 | Strict previous source date after native trailing calculation |
| Treasury_10Y_Change_5D | ^TNX Close.diff(5) / 100; absolute decimal-yield change across source rows | ^TNX | 6 | Strict previous source date after native trailing calculation |
| Treasury_10Y_vs_MA_20 | (^TNX Close - trailing mean 20) / 100; decimal-yield deviation | ^TNX | 20 | Strict previous source date after native trailing calculation |


Beta uses ddof=1 covariance and variance; denominator variance must exceed 1e-12.
Correlations require a full window and both standard deviations >1e-12. Ratios with
undefined denominators remain NaN. Simple market/sector-adjusted returns are not
estimated alpha. No redundant one-day relative-strength aliases were included.
Source-window counts precede the prior-date availability lag for VIX/TNX.

## 9. FEATURE MODES

basic, advanced, advanced_temporal, advanced_temporal_context all operate through
explicit registries. Existing modes and their defaults are unchanged. main.py still
defaults to basic; set FEATURE_SET to advanced_temporal_context to request V7.
A context bundle is required for that mode; absent/unsupported sources fail clearly.

## 10. FEATURE COUNTS

| Mode | Inputs |
|---|---:|
| basic | 10 |
| advanced | 70 |
| advanced_temporal | 88 |
| advanced_temporal_context | 132 |

Context adds 44 focused inputs: 15 market, 5 VIX, 5 sector, 15 relative and 4 rates.
The entire combined matrix was audited, with no exact duplicate columns found.

## 11. DATE ALIGNMENT STRATEGY

ETF closes are reindexed by exact stock dates before calculations. Missing dates
stay NaN. Returns require complete n+1 aligned-close intervals; rolling statistics
require full paired windows. This prevents a context series missing Wednesday from
pairing a Tuesday–Thursday return with a Wednesday–Thursday stock return. No row
number is ever used to align sources. Current completed ETF session data is allowed.

VIX and rates are conservatively delayed: calculate trailing features on native
observed source rows, then use backward as-of with allow_exact_matches=False.
Source_Date must be strictly earlier than the stock date, with age 1–4 calendar days.
This avoids assuming the VIX/TNX final daily value was available at exactly the
stock's closing time. Cboe describes a VIX calculation session extending past the
ordinary US equity close: [Cboe VIX FAQ](https://www.cboe.com/tradable_products/vix/faqs).
Provider publication timestamps and historical vintages are not independently verified;
this is conservative observation-date safety, not certification of archival availability.

## 12. MISSING DATA / STALENESS POLICY

No ETF filling, backward filling or interpolation. The latest previous VIX/rate
source row controls; an undefined feature on that row is not replaced by an older
valid feature. Values older than four calendar days are unavailable. Source dates,
Age_Days and Usable are explicit alignment diagnostics, not extra ML features.
The four-day maximum accommodates common three-/four-day closure gaps without
indefinitely carrying observations. It is a calendar-day limit, not an inferred
exchange holiday schedule. Synthetic tests cover before-first-source, exact-date
exclusion, accepted ages 3/4, stale ages 5/7, and future-value rejection.

Yahoo all-empty index quote rows are recorded and excluded as absent observations;
retained quote timestamps do not change. No missing quote is assigned a value.

## 13. CONTEXT DATA QUALITY REPORT

All retained observations passed V4 checks: schema, nonempty/minimum history,
datetime/ascending/unique dates, finite positive OHLC and finite nonnegative volume.
No non-finite values remain in final matrices. Index placeholders are fully recorded
by date in the experiment JSON. The following alignment diagnostics apply to every
stock in this run (their stock calendars are identical):

| Symbol | Stock dates without same-date quote | Stale prior rows | Unavailable prior rows | Max accepted age |
|---|---|---|---|---|
| SPY | 0 | N/A exact-date | N/A exact-date | 0 (exact date) |
| QQQ | 0 | N/A exact-date | N/A exact-date | 0 (exact date) |
| ^VIX | 0 | 1 | 2 | 4.0 |
| ^TNX | 2 | 1 | 2 | 4.0 |
| XLK | 0 | N/A exact-date | N/A exact-date | 0 (exact date) |
| XLF | 0 | N/A exact-date | N/A exact-date | 0 (exact date) |

These availability counts precede feature warm-up. Required missing features later
remove rows from both compared models' common eligible set. Empty/unusable required
sources prevent context fitting and identify the failed symbol; they are not omitted
from the schema. Non-context modes remain available.

## 14. DATASET RESULTS

| Ticker | Raw rows | Common eligible | Features old/new | Train | Test |
|---|---|---|---|---|---|
| AAPL | 4209 | 3955 | 88 / 132 | 3163 | 791 |
| MSFT | 4209 | 3955 | 88 / 132 | 3163 | 791 |
| JPM | 4209 | 3955 | 88 / 132 | 3163 | 791 |

| Ticker | Raw dates | Common eligible dates | Training dates | Testing dates | Purged feature date | Latest training target date |
|---|---|---|---|---|---|---|
| AAPL | 2010-01-04 → 2026-09-28 | 2011-01-03 → 2026-09-25 | 2011-01-03 → 2023-07-31 | 2023-08-02 → 2026-09-25 | 2023-08-01 | 2023-08-01 |
| MSFT | 2010-01-04 → 2026-09-28 | 2011-01-03 → 2026-09-25 | 2011-01-03 → 2023-07-31 | 2023-08-02 → 2026-09-25 | 2023-08-01 | 2023-08-01 |
| JPM | 2010-01-04 → 2026-09-28 | 2011-01-03 → 2026-09-25 | 2011-01-03 → 2023-07-31 | 2023-08-02 → 2026-09-25 | 2023-08-01 | 2023-08-01 |

Both models use the same stock download, eligible rows, shared features, target
values, training/test dates and purged boundary. These equalities were asserted
before every fit. All features are built before ML filtering; the target and its
realization dates remain tied to the unfiltered stock history.

## 15. CONTROLLED TEMPORAL VS CONTEXT RESULTS

RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1), other defaults,
for all six fits. No tuning, feature selection, fitted scaler or model changes.
MAE/RMSE below are daily-return decimals; multiply by 100 for percentage points.

| Ticker | Mode | MAE | RMSE | R² | Direction |
|---|---|---|---|---|---|
| AAPL | temporal | 0.01187735 | 0.01744397 | -0.075257 | 51.5803% |
| AAPL | context | 0.01174076 | 0.01705047 | -0.027293 | 53.2238% |
| MSFT | temporal | 0.01195325 | 0.01749152 | -0.148391 | 52.2124% |
| MSFT | context | 0.02654806 | 0.03274436 | -3.024462 | 47.2819% |
| JPM | temporal | 0.01045489 | 0.01482510 | -0.067040 | 50.9482% |
| JPM | context | 0.01075193 | 0.01502468 | -0.095963 | 47.9140% |

| Ticker | Zero MAE | Zero RMSE | Previous-day direction |
|---|---|---|---|
| AAPL | 0.01148102 | 0.01684505 | 51.0746% |
| MSFT | 0.01115149 | 0.01633831 | 49.4311% |
| JPM | 0.01004135 | 0.01439896 | 50.6953% |

AAPL: context MAE decreased, RMSE decreased, R² increased, directional accuracy increased. Against zero-return predictions, context MAE is higher and RMSE is higher.

MSFT: context MAE increased, RMSE increased, R² decreased, directional accuracy decreased. Against zero-return predictions, context MAE is higher and RMSE is higher.

JPM: context MAE increased, RMSE increased, R² decreased, directional accuracy decreased. Against zero-return predictions, context MAE is higher and RMSE is higher.

These are this experiment's results, not general predictive superiority, causal
effects or trading performance. Earlier V6 scores were not reused: both models
were rerun on the same current raw data and common dates.

## 16. CONTEXT ABLATION DELTAS

Delta = context minus temporal. Negative error differences indicate lower error;
positive R²/direction differences indicate higher scores. Direction uses percentage
points, not relative percentage change.

| Ticker | ΔMAE | ΔRMSE | ΔR² | ΔDirection (pp) |
|---|---|---|---|---|
| AAPL | -0.00013659 | -0.00039351 | +0.047965 | +1.6435 |
| MSFT | +0.01459481 | +0.01525285 | -2.876071 | -4.9305 |
| JPM | +0.00029704 | +0.00019958 | -0.028923 | -3.0341 |

## 17. CONTEXT FEATURE IMPORTANCE

Importance is impurity-based and descriptive, not causation. Correlated features
share credit. No low-importance features were removed and no models were tuned.

| Ticker | Total context importance |
|---|---|
| AAPL | 0.398044 (39.80%) |
| MSFT | 0.431542 (43.15%) |
| JPM | 0.433598 (43.36%) |

| Context feature | AAPL | MSFT | JPM |
|---|---|---|---|
| SPY_Return_1D | 0.010394 | 0.011651 | 0.010783 |
| SPY_Return_5D | 0.009970 | 0.010829 | 0.011899 |
| SPY_Return_20D | 0.008923 | 0.010613 | 0.007529 |
| QQQ_Return_1D | 0.010131 | 0.011323 | 0.015980 |
| QQQ_Return_5D | 0.008877 | 0.008879 | 0.017404 |
| QQQ_Return_20D | 0.010833 | 0.009245 | 0.006617 |
| SPY_Price_to_SMA_20 | 0.011342 | 0.015815 | 0.012619 |
| SPY_Price_to_SMA_50 | 0.007865 | 0.009153 | 0.007791 |
| SPY_Price_to_SMA_200 | 0.008827 | 0.011004 | 0.007648 |
| QQQ_Price_to_SMA_20 | 0.009048 | 0.008051 | 0.007658 |
| QQQ_Price_to_SMA_50 | 0.009798 | 0.015739 | 0.010011 |
| SPY_Volatility_5 | 0.008558 | 0.008811 | 0.010554 |
| SPY_Volatility_20 | 0.005275 | 0.005449 | 0.006560 |
| SPY_Volatility_60 | 0.005795 | 0.005036 | 0.007784 |
| SPY_Volatility_Ratio_5_20 | 0.009674 | 0.008584 | 0.007350 |
| VIX_Level_Normalized | 0.010689 | 0.011191 | 0.016120 |
| VIX_Return_1D | 0.015770 | 0.008671 | 0.009254 |
| VIX_Return_5D | 0.008415 | 0.012575 | 0.008481 |
| VIX_Price_to_SMA_20 | 0.011094 | 0.015043 | 0.011817 |
| VIX_Percentile_252 | 0.007721 | 0.009231 | 0.006577 |
| Sector_Return_1D | 0.008859 | 0.012775 | 0.021705 |
| Sector_Return_5D | 0.009521 | 0.009945 | 0.008100 |
| Sector_Return_20D | 0.008016 | 0.007904 | 0.010959 |
| Sector_Price_to_SMA_20 | 0.011068 | 0.013523 | 0.015882 |
| Sector_Volatility_20 | 0.007067 | 0.007377 | 0.007196 |
| Stock_vs_SPY_Return_5D | 0.007515 | 0.007541 | 0.006829 |
| Stock_vs_SPY_Return_20D | 0.005748 | 0.006129 | 0.005846 |
| Stock_vs_Sector_Return_5D | 0.008454 | 0.010500 | 0.010649 |
| Stock_vs_Sector_Return_20D | 0.006895 | 0.006060 | 0.008461 |
| Stock_vs_QQQ_Return_20D | 0.007116 | 0.006856 | 0.006892 |
| Stock_SPY_Correlation_20 | 0.006514 | 0.006086 | 0.006917 |
| Stock_SPY_Correlation_60 | 0.006437 | 0.008716 | 0.006330 |
| Stock_Sector_Correlation_20 | 0.006663 | 0.007476 | 0.006426 |
| Stock_Sector_Correlation_60 | 0.005566 | 0.006758 | 0.006505 |
| Stock_SPY_Beta_20 | 0.007306 | 0.006003 | 0.006437 |
| Stock_SPY_Beta_60 | 0.008492 | 0.007766 | 0.007473 |
| Market_Adjusted_Return_1D | 0.009639 | 0.008912 | 0.010795 |
| Sector_Adjusted_Return_1D | 0.010516 | 0.010227 | 0.009288 |
| Stock_to_SPY_Volatility_20 | 0.005555 | 0.005593 | 0.005798 |
| Stock_to_Sector_Volatility_20 | 0.006264 | 0.006534 | 0.006027 |
| Treasury_10Y_Level | 0.016292 | 0.019054 | 0.009173 |
| Treasury_10Y_Change_1D | 0.014367 | 0.011798 | 0.008837 |
| Treasury_10Y_Change_5D | 0.011040 | 0.012733 | 0.017227 |
| Treasury_10Y_vs_MA_20 | 0.014136 | 0.018383 | 0.023411 |

### AAPL: top 25 overall

| Rank | Feature | Importance |
|---|---|---|
| 1 | High_Low_Range | 0.019334 |
| 2 | Treasury_10Y_Level | 0.016292 |
| 3 | VIX_Return_1D | 0.015770 |
| 4 | Treasury_10Y_Change_1D | 0.014367 |
| 5 | Treasury_10Y_vs_MA_20 | 0.014136 |
| 6 | Return_Lag_5 | 0.013927 |
| 7 | Relative_Volume_20 | 0.013732 |
| 8 | Overnight_Gap | 0.013221 |
| 9 | SMA_50_to_200 | 0.012904 |
| 10 | Return_Lag_3 | 0.012406 |
| 11 | Return_x_VolumeChange | 0.012240 |
| 12 | Return_Lag_2 | 0.012179 |
| 13 | Volume_Change | 0.012174 |
| 14 | Relative_Volume_5 | 0.011724 |
| 15 | Return_Lag_1 | 0.011544 |
| 16 | SPY_Price_to_SMA_20 | 0.011342 |
| 17 | VIX_Price_to_SMA_20 | 0.011094 |
| 18 | Sector_Price_to_SMA_20 | 0.011068 |
| 19 | Treasury_10Y_Change_5D | 0.011040 |
| 20 | Rolling_Skew_60 | 0.010996 |
| 21 | QQQ_Return_20D | 0.010833 |
| 22 | VIX_Level_Normalized | 0.010689 |
| 23 | Sector_Adjusted_Return_1D | 0.010516 |
| 24 | SPY_Return_1D | 0.010394 |
| 25 | MACD_Signal_Pct | 0.010372 |

### MSFT: top 25 overall

| Rank | Feature | Importance |
|---|---|---|
| 1 | Treasury_10Y_Level | 0.019054 |
| 2 | Treasury_10Y_vs_MA_20 | 0.018383 |
| 3 | SPY_Price_to_SMA_20 | 0.015815 |
| 4 | QQQ_Price_to_SMA_50 | 0.015739 |
| 5 | VIX_Price_to_SMA_20 | 0.015043 |
| 6 | SMA_50_to_200 | 0.014220 |
| 7 | Sector_Price_to_SMA_20 | 0.013523 |
| 8 | Return_Lag_5 | 0.013124 |
| 9 | High_Low_Range | 0.013079 |
| 10 | Return_Lag_3 | 0.012985 |
| 11 | Return_Lag_1 | 0.012867 |
| 12 | Sector_Return_1D | 0.012775 |
| 13 | Treasury_10Y_Change_5D | 0.012733 |
| 14 | VIX_Return_5D | 0.012575 |
| 15 | Price_to_SMA_20 | 0.012197 |
| 16 | Relative_Volume_20 | 0.012187 |
| 17 | Return_5D_Acceleration | 0.012130 |
| 18 | Overnight_Gap | 0.011939 |
| 19 | Treasury_10Y_Change_1D | 0.011798 |
| 20 | Volume_Change | 0.011725 |
| 21 | SPY_Return_1D | 0.011651 |
| 22 | Return_x_VolumeChange | 0.011378 |
| 23 | QQQ_Return_1D | 0.011323 |
| 24 | VIX_Level_Normalized | 0.011191 |
| 25 | SPY_Price_to_SMA_200 | 0.011004 |

### JPM: top 25 overall

| Rank | Feature | Importance |
|---|---|---|
| 1 | Treasury_10Y_vs_MA_20 | 0.023411 |
| 2 | Drawdown_From_252D_Peak | 0.022534 |
| 3 | Sector_Return_1D | 0.021705 |
| 4 | Return_Lag_5 | 0.018254 |
| 5 | QQQ_Return_5D | 0.017404 |
| 6 | Treasury_10Y_Change_5D | 0.017227 |
| 7 | Return_Lag_3 | 0.016265 |
| 8 | VIX_Level_Normalized | 0.016120 |
| 9 | QQQ_Return_1D | 0.015980 |
| 10 | Sector_Price_to_SMA_20 | 0.015882 |
| 11 | Overnight_Gap | 0.014556 |
| 12 | Return_5D_Acceleration | 0.014365 |
| 13 | Return_Lag_1 | 0.013734 |
| 14 | SMA_50_to_200 | 0.012991 |
| 15 | Price_to_SMA_200 | 0.012903 |
| 16 | SPY_Price_to_SMA_20 | 0.012619 |
| 17 | SPY_Return_5D | 0.011899 |
| 18 | VIX_Price_to_SMA_20 | 0.011817 |
| 19 | Sector_Return_20D | 0.010959 |
| 20 | Market_Adjusted_Return_1D | 0.010795 |
| 21 | SPY_Return_1D | 0.010783 |
| 22 | Volume_Change | 0.010672 |
| 23 | Stock_vs_Sector_Return_5D | 0.010649 |
| 24 | SPY_Volatility_5 | 0.010554 |
| 25 | Return_Lag_2 | 0.010364 |

## 18. DESCRIPTIVE CONTEXT ANALYSIS

Reporting-only full-history same-session Daily_Return summaries. High/low VIX
conditions use the available prior-date trailing percentile >=0.75 / <=0.25, not a
full-sample VIX rank. They are never model inputs, fitted encodings or causal claims.

| Ticker | Paired return rows | Stock–SPY correlation | Stock–sector correlation | Low VIX count / mean return | High VIX count / mean return |
|---|---|---|---|---|---|
| AAPL | 4208 | 0.677271 | 0.743323 | 1347 / 0.00090123 | 902 / 0.00074643 |
| MSFT | 4208 | 0.725545 | 0.783346 | 1347 / 0.00080751 | 902 / 0.00145833 |
| JPM | 4208 | 0.727232 | 0.906285 | 1347 / 0.00071890 | 902 / 0.00053588 |

## 19. REDUNDANCY AUDIT

Thresholds: exact sample equality; constants; sample variance <=1e-12; absolute
Pearson correlation >=0.98. Both purged training and full eligible data were audited.
Full-sample diagnostics are reporting-only and did not drive model selection.

| Ticker | Exact duplicates | Constants | Near-zero variance | Train correlation pairs | Full correlation pairs |
|---|---|---|---|---|---|
| AAPL | 0 | 0 | 0 | 11 | 11 |
| MSFT | 0 | 0 | 0 | 11 | 11 |
| JPM | 0 | 0 | 0 | 11 | 11 |

### AAPL: all training correlations >=0.98 in magnitude

| Feature A | Feature B | Correlation |
|---|---|---|
| Return_5D | Rolling_Mean_Return_5 | 0.999454 |
| Return_20D | Rolling_Mean_Return_20 | 0.998423 |
| Return_60D | Rolling_Mean_Return_60 | 0.994300 |
| Price_to_SMA_10 | Price_to_EMA_10 | 0.981316 |
| Price_to_SMA_20 | Price_to_EMA_20 | 0.982850 |
| Price_to_SMA_50 | Price_to_EMA_50 | 0.982825 |
| Distance_From_20D_High | Drawdown_From_20D_Peak | 0.990348 |
| Distance_From_60D_High | Drawdown_From_60D_Peak | 0.996026 |
| Positive_Return_Ratio_20 | Negative_Return_Ratio_20 | -0.996482 |
| Calendar_Days_From_Month_Start | Calendar_Days_To_Month_End | -0.995776 |
| Calendar_Days_From_Quarter_Start | Calendar_Days_To_Quarter_End | -0.999569 |

### MSFT: all training correlations >=0.98 in magnitude

| Feature A | Feature B | Correlation |
|---|---|---|
| Return_5D | Rolling_Mean_Return_5 | 0.999236 |
| Return_20D | Rolling_Mean_Return_20 | 0.998104 |
| Return_60D | Rolling_Mean_Return_60 | 0.994718 |
| Price_to_SMA_10 | Price_to_EMA_10 | 0.980540 |
| Price_to_SMA_20 | Price_to_EMA_20 | 0.982249 |
| Price_to_SMA_50 | Price_to_EMA_50 | 0.982535 |
| Distance_From_20D_High | Drawdown_From_20D_Peak | 0.988209 |
| Distance_From_60D_High | Drawdown_From_60D_Peak | 0.994036 |
| Positive_Return_Ratio_20 | Negative_Return_Ratio_20 | -0.980523 |
| Calendar_Days_From_Month_Start | Calendar_Days_To_Month_End | -0.995776 |
| Calendar_Days_From_Quarter_Start | Calendar_Days_To_Quarter_End | -0.999569 |

### JPM: all training correlations >=0.98 in magnitude

| Feature A | Feature B | Correlation |
|---|---|---|
| Return_5D | Rolling_Mean_Return_5 | 0.998904 |
| Return_20D | Rolling_Mean_Return_20 | 0.997098 |
| Return_60D | Rolling_Mean_Return_60 | 0.995699 |
| Price_to_SMA_10 | Price_to_EMA_10 | 0.980580 |
| Price_to_SMA_20 | Price_to_EMA_20 | 0.981119 |
| Price_to_SMA_50 | Price_to_EMA_50 | 0.982631 |
| Distance_From_20D_High | Drawdown_From_20D_Peak | 0.993101 |
| Distance_From_60D_High | Drawdown_From_60D_Peak | 0.997390 |
| Positive_Return_Ratio_20 | Negative_Return_Ratio_20 | -0.987280 |
| Calendar_Days_From_Month_Start | Calendar_Days_To_Month_End | -0.995776 |
| Calendar_Days_From_Quarter_Start | Calendar_Days_To_Quarter_End | -0.999569 |

All exact full-sample coefficients and context-only audits are in v7_experiments.json.
No mathematically identical one-day adjusted/relative-return aliases were created.
Correlated but distinct SPY, QQQ, sector, beta and relative-strength representations
remain available for later ablation, without selection during this checkpoint.

## 20. STOCK FUTURE-PERTURBATION TEST

PASS. Change stock OHLCV strictly after the cutoff with context unchanged; rebuild
all 132 inputs. Every historical input through the cutoff matches exactly, including
NaNs. Target columns are excluded because they intentionally reference future returns.

## 21. CONTEXT FUTURE-PERTURBATION TEST

PASS. Independently change every context source after the cutoff with stock data
unchanged; all historical inputs match exactly. This includes prior-rate/VIX,
rolling percentile, market/sector returns, correlations and betas.

## 22. PREFIX-INVARIANCE TEST

Offline tests use three cutoffs at rows 300, 390 and 520 of a 600-row synthetic
history. Both stock and all context histories are truncated, then all 132 inputs
compared exactly. Live checks:

| Ticker | Cutoff | Stock perturbation | Context perturbation | Joint prefix |
|---|---|---|---|---|
| AAPL | 2015-06-15 | PASS | PASS | PASS |
| AAPL | 2015-06-30 | PASS | PASS | PASS |
| AAPL | 2015-12-31 | PASS | PASS | PASS |
| MSFT | 2015-06-15 | PASS | PASS | PASS |
| MSFT | 2015-06-30 | PASS | PASS | PASS |
| MSFT | 2015-12-31 | PASS | PASS | PASS |
| JPM | 2015-06-15 | PASS | PASS | PASS |
| JPM | 2015-06-30 | PASS | PASS | PASS |
| JPM | 2015-12-31 | PASS | PASS | PASS |

## 23. ALIGNMENT TESTS

PASS. A synthetic missing SPY date remains missing on that stock date; the next
one-day return is also unavailable when its required preceding close is missing.
The following complete interval uses its exact dates and correct values. Longer
returns also reject intervals containing missing closes. The stock index and all
pre-existing features/targets are retained unchanged before dataset construction.
As-of tests verify strict earlier-source dates, no future backfill and a four-day cap.

## 24. BETA/CORRELATION TESTS

PASS. Synthetic stock returns equal to twice market returns produce beta 2,
correlation +1 and relative volatility 2 after warm-up. An inverse relationship
produces correlation -1 and beta -1. Constant market prices produce undefined
beta/correlation/relative volatility rather than infinity or fabricated numbers.
Sample covariance/variance both use ddof=1 on matched complete windows.

## 25. VIX PERCENTILE SAFETY

PASS. rolling(252).rank(method="average", pct=True) uses only the source window
ending at the current source date, then follows prior-date availability. A tied
synthetic sequence matches a manually counted average-rank reference. Perturbing
later VIX observations cannot change earlier percentiles. No full_series.rank is used.

## 26. RATE DATA SEMANTICS

^TNX was actually downloaded and compared with official Treasury 10-year reference
values on four dates. The Yahoo convention is percentage-point yield, not a bond
price or a ten-times-scaled value in this feed. Dividing by 100 gives annual decimal
yield. Differences are absolute decimal-yield changes; 0.0001 equals one basis point.

| Date | Yahoo ^TNX Close | Official Treasury 10-year (%) |
|---|---|---|
| 2024-01-02 | 3.946000 | 3.95 |
| 2024-01-03 | 3.907000 | 3.91 |
| 2024-01-04 | 3.991000 | 3.99 |
| 2024-01-05 | 4.042000 | 4.05 |

Reference: [US Treasury daily yield curves, 2024](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=2024).
The sources use different methodologies; their small differences are expected.
This verifies scale, not instrument identity or historical publication timestamps.
The prior-date/four-calendar-day rule applies to all rate-derived inputs. No second
maturity was verified; yield-curve features are deliberately deferred.

## 27. SCALE / UNIT AUDIT

PASS. Live tests independently multiply stock prices by 7 and SPY/QQQ/sector prices
by 3/5/9, with stock/source volumes multiplied by 11/13. All 132 features match at
rtol=atol=1e-6, because VIX/rate levels are intentionally left in their physical units.
Offline context checks use 1e-8 tolerance. Volume has no role in context calculations.
VIX level and rate level/changes intentionally depend on verified economic units;
other context ratios/correlations/betas are price-scale invariant. This is a diagnostic,
not a fitted scaler or transformation learned from test data.

## 28. INTERNATIONAL / UNSUPPORTED CONTEXT BEHAVIOR

PASS. 7203.T is rejected by the context profile with an explicit message and no
provider download. Non-context modes remain available. Unmapped US stocks also
receive an unavailable-profile message rather than an invented sector. Profiles
can be extended centrally later. V6's Monday–Friday temporal restriction remains.
A missing required source names the failure and prevents malformed context training.

## 29. LEAKAGE AUDIT

| Check | Result |
|---|---|
| Date alignment | PASS |
| No position alignment | PASS |
| Current/past context only | PASS |
| No future fill | PASS |
| Target isolation | PASS |
| Target absent from registry | PASS |
| Trailing rolling features | PASS |
| Historical VIX percentile | PASS |
| Chronological split | PASS |
| Purged target boundary | PASS |
| No test fitting | PASS |
| Independent future perturbations | PASS |
| Joint prefix invariance | PASS |

Prior observed dates are availability proxies; provider revisions and retroactive
adjustments remain a limitation. No test-fitted preprocessing, target encoding,
calendar-label inference from future rows, or future-value interpolation is present.

## 30. AUTOMATED TESTS

56 executed, 56 passed, zero failures: all 39 V4/V5/V6 tests plus 17 V7 tests.
The earlier suites and their source files were unchanged. Tests cover alignment,
market/relative/sector returns, known beta/correlation/volatility relationships,
zero variance, stale as-of handling, historical VIX rank/ties, rate units, registry,
metadata, target exclusion, independent perturbations, prefixes, scaling, profiles,
cache counters, required-source failure, train-only fitting, unsupported CLI behavior,
and index placeholder handling versus partial invalid observations.

Executed commands:

```sh
venv/bin/python -m unittest discover -s tests -v
venv/bin/python -m models.context_comparison AAPL MSFT JPM
```

All six live forest fits completed with common-date, target, finite-matrix and
purged-boundary assertions. All application modules imported successfully.

## 31. DOWNLOAD/CACHE EFFICIENCY

Final successful experiment: **15 logical context requests**, **6 actual context downloads**.

The six symbols are SPY, QQQ, ^VIX, ^TNX, XLK and XLF. AAPL/MSFT share XLK, and
all stocks share the four common sources. Each stock is separately downloaded once
in the successful run. These counters exclude earlier failed attempts and the two
separate diagnostic probes (^TNX unit sample and VIX empty-row inspection). No database,
persistent cache or automatic retry loop was added.

## 32. V6 REGRESSION CHECK

All 39 previous tests still pass. Three earlier modes retain counts 10/70/88 and
can build finite datasets; old training-only tests exercise them. All 88 existing
columns match their context-frame counterparts on the same raw data. The baseline
model file, target, V5/V6 definitions, V4 ingestion and requirements are unchanged.
All 36 protected files match their pre-work hashes, and all 91 prior metadata entries
match their saved V6 JSON. Historical reports were not regenerated. Main defaults basic.

## 33. DOCUMENTATION GENERATED

- v7_context_feature_catalog.md: all 44 formulas, sources, lookbacks, availability,
  unit/normalization rules, staleness, placeholder policy and limitations.
- v7_feature_metadata.json: complete additive machine-readable metadata.
- v7_experiments.json/.txt: measured metrics, all importances, audits and quality reports.
- v7_tests.txt, v7_preservation.json and v7_rate_probe.txt: execution evidence.
- This report with complete created/modified source code.

## 34. ERRORS/WARNINGS

Initial restricted-network requests failed DNS resolution; authorized network-enabled
runs were used. The first live context attempt rejected Yahoo VIX all-empty quote rows
under strict V4 validation. Inspection showed missing OHLC with zero volume, largely
on closure dates. A context-only adapter now records/excludes such placeholders and
then applies unchanged V4 validation; partial invalid quotes still fail. Two tests
cover this behavior. The entire suite and live experiment were rerun successfully.
No stock ingestion rules, historical features or model settings were relaxed or tuned.

No numerical/model warnings appeared in the successful run. The research runner
keeps unexpected failures diagnosable; the interactive main catches expected data
errors and explains which required source is unavailable.

## 35. COMPLETE SOURCE CODE

Complete contents of every created/modified source file follow. Unchanged files,
including baseline.py, retain their previous implementation and historical reports.

### main.py

```python
"""Terminal orchestration for the CastiFy V7 research pipeline."""
from data.market_data import (
    MarketDataError, download_market_data, normalize_ticker, print_data_report
)
from features.feature_factory import build_feature_set
from data.context_data import download_context_bundle, context_data_report
from config.market_context import context_profile
from models.baseline import (
    chronological_split, evaluate_baseline, prepare_ml_dataset, print_baseline_report
)

START_DATE = "2010-01-01"
END_DATE = None
FEATURE_SET = "basic"  # Also: advanced, advanced_temporal, advanced_temporal_context.


def main() -> int:
    """Run one user-selected ticker; expected data failures get readable errors."""
    print("============================================\n"
          "                 CASTIFY\n"
          "      Quantitative Forecasting Engine\n"
          "============================================")
    try:
        ticker = normalize_ticker(input("Enter stock ticker: "))
        print(f"Analyzing {ticker}...")
        if FEATURE_SET == "advanced_temporal_context":
            context_profile(ticker)  # Fail clearly before downloading an unsupported ticker.
        stock = download_market_data(ticker, START_DATE, END_DATE)
        print_data_report(stock, ticker, START_DATE, END_DATE)
        bundle = None
        if FEATURE_SET == "advanced_temporal_context":
            bundle = download_context_bundle(ticker, START_DATE, END_DATE)
            for source in context_data_report(stock, bundle):
                print(source)
        featured = build_feature_set(stock, FEATURE_SET, context_bundle=bundle)
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
             "advanced_temporal": ADVANCED_TEMPORAL_FEATURES,
             "advanced_temporal_context": ADVANCED_TEMPORAL_CONTEXT_FEATURES}
    if feature_set not in modes:
        raise ValueError("Unknown feature_set; use basic, advanced, advanced_temporal or advanced_temporal_context.")
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


# V7 extends the registry without altering earlier input lists or metadata.
from features.context_registry import CONTEXT_FEATURES, CONTEXT_METADATA
ADVANCED_TEMPORAL_CONTEXT_FEATURES = ADVANCED_TEMPORAL_FEATURES + CONTEXT_FEATURES
FEATURE_METADATA.update(CONTEXT_METADATA)
assert len(ADVANCED_TEMPORAL_CONTEXT_FEATURES) == len(set(ADVANCED_TEMPORAL_CONTEXT_FEATURES))
assert "Tomorrow_Return" not in ADVANCED_TEMPORAL_CONTEXT_FEATURES
```

### features/feature_factory.py

```python
"""Select the historical basic baseline or the explicit V5 advanced feature set."""
import numpy as np
import pandas as pd
from features.basic_features import build_basic_features
from features.temporal_features import temporal_features
from features.context_features import context_features
from data.market_data import MarketDataError
from features.registry import get_feature_columns
from features.price_features import price_features
from features.momentum_features import momentum_features
from features.volatility_features import volatility_features
from features.volume_features import volume_features
from features.technical_features import technical_features


def build_feature_set(stock: pd.DataFrame, feature_set: str = "advanced", context_bundle: dict | None = None) -> pd.DataFrame:
    """Build on a copy. Preserve warm-up NaNs and isolate the unchanged future target."""
    columns = get_feature_columns(feature_set)
    featured = build_basic_features(stock)
    if feature_set in ("advanced", "advanced_temporal", "advanced_temporal_context"):
        for builder in (price_features, momentum_features, volatility_features,
                        volume_features, technical_features):
            block = builder(stock)
            featured[block.columns] = block
        if feature_set in ("advanced_temporal", "advanced_temporal_context"):
            column_name = featured.columns.name
            featured = pd.concat([featured, temporal_features(stock)], axis=1)
            featured.columns.name = column_name
        if feature_set == "advanced_temporal_context":
            if context_bundle is None:
                raise MarketDataError("Context mode requires an explicitly configured context bundle.")
            column_name = featured.columns.name
            featured = pd.concat([featured, context_features(stock, context_bundle)], axis=1)
            featured.columns.name = column_name
        if np.isinf(featured[columns].to_numpy()).any():
            raise ValueError("Advanced feature generation produced infinity; inspect raw inputs.")
    assert "Tomorrow_Return" not in columns
    assert featured.index.equals(stock.index)
    return featured
```

### config/__init__.py

```python
"""Centralized CastiFy research configurations."""
```

### config/market_context.py

```python
"""Explicit US context profiles; no automatic international or sector inference."""
from data.market_data import MarketDataError, normalize_ticker

SECTOR_MAPPING = {"AAPL": "XLK", "MSFT": "XLK", "JPM": "XLF"}
MAX_CONTEXT_AGE_DAYS = 4
SOURCES = {
    "SPY": "Broad US equity market ETF",
    "QQQ": "Growth/technology-heavy US equity ETF",
    "^VIX": "Cboe implied volatility index; Yahoo points, divided by 100 for level",
    "^TNX": "Yahoo 10-year Treasury yield proxy; percentage points, divided by 100",
    "XLK": "Technology sector ETF", "XLF": "Financial sector ETF"
}


def context_profile(ticker: str) -> dict:
    """Require a configured US equity; keep non-context modes universally separate."""
    ticker = normalize_ticker(ticker)
    if ticker not in SECTOR_MAPPING:
        raise MarketDataError(f"Market context profile is not configured for {ticker}. "
                              "Use basic, advanced, or advanced_temporal instead.")
    return dict(ticker=ticker, sector=SECTOR_MAPPING[ticker], market="SPY", growth="QQQ",
                volatility="^VIX", rates="^TNX", region="US",
                timing="After completed US equity close: exact-date ETF data; strictly prior-date VIX/TNX, maximum age 4 calendar days.")
```

### data/context_data.py

```python
"""Reusable validated context bundles and explicit availability alignment."""
from datetime import datetime, timezone
import pandas as pd
import yfinance as yf

from config.market_context import SOURCES, MAX_CONTEXT_AGE_DAYS, context_profile
from data.market_data import MarketDataError, download_market_data, standardize_columns, validate_market_data


def download_context_series(symbol: str, start: str, end: str | None = None) -> pd.DataFrame:
    """Reuse V4 ingestion for ETFs; handle empty Yahoo index quote placeholders.

    For VIX/TNX only, remove rows where every OHLC is missing and volume is zero
    or missing. Record the dates, never impute them. Partial bad rows still fail
    the unchanged V4 validator. All retained timestamps are provider originals.
    """
    if symbol not in ("^VIX", "^TNX"):
        return download_market_data(symbol, start, end)
    today = datetime.now(timezone.utc).date().isoformat()
    try:
        begin = pd.Timestamp(start)
        finish = min(pd.Timestamp(end or today), pd.Timestamp(today))
        if pd.isna(begin) or pd.isna(finish) or begin >= finish:
            raise ValueError("Start must precede completed-data cutoff.")
    except (TypeError, ValueError) as error:
        raise MarketDataError(f"Invalid context date range: {error}") from error
    raw = yf.download(symbol, start=begin.date().isoformat(), end=finish.date().isoformat(),
                      interval="1d", auto_adjust=True, keepna=True, progress=False, threads=False)
    data = standardize_columns(raw, symbol)
    placeholders = data[["Open", "High", "Low", "Close"]].isna().all(axis=1) & (data.Volume.isna() | data.Volume.eq(0))
    removed = [str(date.date()) for date in data.index[placeholders]]
    clean = data.loc[~placeholders].copy()
    validate_market_data(clean)
    clean.attrs.update(effective_end_exclusive=finish.date().isoformat(),
                       provider_rows=len(data), empty_quote_dates=removed)
    return clean


class ContextCache:
    """Small per-run cache keyed by symbol and requested date range."""
    def __init__(self):
        self.frames = {}
        self.logical_requests = 0
        self.provider_downloads = 0

    def get(self, symbol: str, start: str, end: str | None) -> pd.DataFrame:
        """Reuse the V4 standardized, adjusted, finite OHLCV download contract."""
        self.logical_requests += 1
        key = (symbol, start, end)
        if key not in self.frames:
            self.provider_downloads += 1
            try:
                self.frames[key] = download_context_series(symbol, start, end)
            except MarketDataError as error:
                raise MarketDataError(f"Required context source {symbol} failed: {error} "
                                      "Context mode cannot proceed. Basic, advanced and advanced_temporal remain available.") from error
        return self.frames[key].copy()


def download_context_bundle(ticker: str, start: str, end: str | None = None,
                            cache: ContextCache | None = None) -> dict:
    """Fetch a profile's five required sources; never silently omit a failed source."""
    profile = context_profile(ticker)
    cache = cache if cache is not None else ContextCache()
    symbols = [profile[k] for k in ("market", "growth", "volatility", "rates", "sector")]
    series = {symbol: cache.get(symbol, start, end) for symbol in symbols}
    return dict(profile=profile, series=series, requested_start=start, requested_end=end)


def validate_daily_index(index: pd.Index) -> None:
    """Require unambiguous US daily session labels; do not silently convert timezones."""
    if (not isinstance(index, pd.DatetimeIndex) or index.hasnans or index.tz is not None
            or not index.is_unique or not index.is_monotonic_increasing
            or not index.equals(index.normalize())):
        raise MarketDataError("Context alignment requires unique sorted timezone-naive midnight session dates.")


def align_previous(values: pd.DataFrame, dates: pd.DatetimeIndex) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Strict backward as-of, not same-date; reject values older than four days.

    Preserve source dates and diagnostic ages even when rejecting stale values.
    Never search backwards for a non-NaN feature: the newest source row controls.
    """
    validate_daily_index(values.index)
    validate_daily_index(dates)
    left = pd.DataFrame({"Stock_Date": dates})
    right = values.rename_axis("Source_Date").reset_index()
    joined = pd.merge_asof(left, right, left_on="Stock_Date", right_on="Source_Date",
                           direction="backward", allow_exact_matches=False)
    joined.index = dates
    age = (joined.Stock_Date - joined.Source_Date).dt.days
    usable = age.between(1, MAX_CONTEXT_AGE_DAYS)
    aligned = joined[values.columns].where(usable, axis=0)
    diagnostics = pd.DataFrame({"Source_Date": joined.Source_Date, "Age_Days": age,
                                "Usable": usable}, index=dates)
    assert (diagnostics.loc[usable, "Source_Date"] < dates[usable]).all()
    return aligned, diagnostics


def context_data_report(stock: pd.DataFrame, bundle: dict) -> list[dict]:
    """Report actual ranges, exact-date misses and bounded previous-date ages."""
    reports = []
    for symbol, frame in bundle["series"].items():
        item = dict(symbol=symbol, purpose=SOURCES.get(symbol, "Configured context source"),
                    requested_start=bundle["requested_start"], requested_end=bundle["requested_end"],
                    actual_start=str(frame.index.min().date()), actual_end=str(frame.index.max().date()),
                    observations=len(frame), missing_values=int(frame.isna().sum().sum()),
                    duplicate_dates=int(frame.index.duplicated().sum()), validation="PASS (V4 validated)",
                    auto_adjust=True, provider_rows=frame.attrs.get("provider_rows",len(frame)),
                    empty_quote_dates=frame.attrs.get("empty_quote_dates",[]), same_date_missing=int((~stock.index.isin(frame.index)).sum()))
        if symbol in (bundle["profile"]["volatility"], bundle["profile"]["rates"]):
            _, diagnostics = align_previous(frame[["Close"]], stock.index)
            item.update(alignment="Strictly previous date; max age 4 calendar days",
                        unavailable_rows=int((~diagnostics.Usable).sum()),
                        stale_rows=int((diagnostics.Age_Days > MAX_CONTEXT_AGE_DAYS).sum()),
                        max_accepted_age=float(diagnostics.loc[diagnostics.Usable, "Age_Days"].max()))
        else:
            item["alignment"] = "Exact stock date; missing stays NaN, no fill"
        reports.append(item)
    return reports
```

### features/context_registry.py

```python
"""Focused explicit V7 registry; level units and availability are documented."""
MARKET_CONTEXT_FEATURES = [
    "SPY_Return_1D", "SPY_Return_5D", "SPY_Return_20D",
    "QQQ_Return_1D", "QQQ_Return_5D", "QQQ_Return_20D",
    "SPY_Price_to_SMA_20", "SPY_Price_to_SMA_50", "SPY_Price_to_SMA_200",
    "QQQ_Price_to_SMA_20", "QQQ_Price_to_SMA_50",
    "SPY_Volatility_5", "SPY_Volatility_20", "SPY_Volatility_60", "SPY_Volatility_Ratio_5_20"
]
VIX_CONTEXT_FEATURES = ["VIX_Level_Normalized", "VIX_Return_1D", "VIX_Return_5D",
                        "VIX_Price_to_SMA_20", "VIX_Percentile_252"]
SECTOR_CONTEXT_FEATURES = ["Sector_Return_1D", "Sector_Return_5D", "Sector_Return_20D",
                          "Sector_Price_to_SMA_20", "Sector_Volatility_20"]
RELATIVE_CONTEXT_FEATURES = [
    "Stock_vs_SPY_Return_5D", "Stock_vs_SPY_Return_20D",
    "Stock_vs_Sector_Return_5D", "Stock_vs_Sector_Return_20D", "Stock_vs_QQQ_Return_20D",
    "Stock_SPY_Correlation_20", "Stock_SPY_Correlation_60",
    "Stock_Sector_Correlation_20", "Stock_Sector_Correlation_60",
    "Stock_SPY_Beta_20", "Stock_SPY_Beta_60", "Market_Adjusted_Return_1D", "Sector_Adjusted_Return_1D",
    "Stock_to_SPY_Volatility_20", "Stock_to_Sector_Volatility_20"
]
RATE_CONTEXT_FEATURES = ["Treasury_10Y_Level", "Treasury_10Y_Change_1D", "Treasury_10Y_Change_5D", "Treasury_10Y_vs_MA_20"]
CONTEXT_GROUPS = dict(market=MARKET_CONTEXT_FEATURES, volatility_context=VIX_CONTEXT_FEATURES,
                      sector=SECTOR_CONTEXT_FEATURES, relative=RELATIVE_CONTEXT_FEATURES, rates=RATE_CONTEXT_FEATURES)
CONTEXT_FEATURES = [name for group in CONTEXT_GROUPS.values() for name in group]
CONTEXT_METADATA = {}


def _add(name, description, source, rows, unit_dependent=False):
    subfamily = next(group for group, names in CONTEXT_GROUPS.items() if name in names)
    prior = subfamily in ("rates", "volatility_context")
    CONTEXT_METADATA[name] = dict(
        name=name, family="context", subfamily=subfamily, description=description,
        source=source, minimum_raw_rows=rows, lookback=rows-1,
        normalized=not unit_dependent, unit_dependent=unit_dependent, future_safe=True,
        alignment="Strict previous source date after native trailing calculation" if prior else "Exact stock-date grid, complete trailing windows",
        staleness="1 to 4 calendar days, otherwise NaN; source dates and ages reported" if prior else "Same date only; no fill",
        timing="Available by completed stock session; prior-date policy for VIX/TNX"
    )


for source in ("SPY", "QQQ", "Sector"):
    symbol = "configured sector ETF (XLK/XLF)" if source == "Sector" else source
    for n in (1, 5, 20):
        _add(f"{source}_Return_{n}D", f"Close / Close.shift({n}) - 1; require all {n+1} aligned closes", symbol, n+1)
    for n in ((20,50,200) if source=="SPY" else (20,50) if source=="QQQ" else (20,)):
        _add(f"{source}_Price_to_SMA_{n}", f"Close / mean({n} aligned closes) - 1", symbol, n)
    for n in ((5,20,60) if source=="SPY" else (20,) if source=="Sector" else ()):
        _add(f"{source}_Volatility_{n}", f"Std of {n} aligned returns, ddof=1", symbol, n+1)
_add("SPY_Volatility_Ratio_5_20", "SPY sample volatility 5 / 20; denominator >1e-12", "SPY", 21)
for name, desc, rows, unit in [
    ("VIX_Level_Normalized", "Prior VIX Close / 100; implied annualized volatility decimal, not realized return",1,True),
    ("VIX_Return_1D", "VIX Close / previous native source Close - 1",2,False),
    ("VIX_Return_5D", "VIX Close / native source Close 5 rows earlier - 1",6,False),
    ("VIX_Price_to_SMA_20", "VIX Close / trailing 20-source-row mean - 1",20,False),
    ("VIX_Percentile_252", "Current VIX rank within trailing 252 source closes / 252; average ranks for ties, includes current source close",252,False)]:
    _add(name,desc,"^VIX",rows,unit)
for source,n in (("SPY",5),("SPY",20),("Sector",5),("Sector",20),("QQQ",20)):
    _add(f"Stock_vs_{source}_Return_{n}D", f"Stock trailing {n}-row return minus aligned {source} return", f"stock + {source}",n+1)
for source in ("SPY","Sector"):
    for n in (20,60):
        _add(f"Stock_{source}_Correlation_{n}", f"Pearson correlation over {n} matched return pairs; full window, std >1e-12",f"stock + {source}",n+1)
for n in (20,60):
    _add(f"Stock_SPY_Beta_{n}",f"Sample cov(stock, SPY)/sample var(SPY), ddof=1 over {n} pairs; variance >1e-12", "stock + SPY",n+1)
for name,source in (("Market_Adjusted_Return_1D","SPY"),("Sector_Adjusted_Return_1D","Sector")):
    _add(name,f"Stock current return minus aligned {source} current return; not estimated alpha",f"stock + {source}",2)
for source in ("SPY","Sector"):
    _add(f"Stock_to_{source}_Volatility_20",f"Stock / {source} 20-return sample std; denominator >1e-12",f"stock + {source}",21)
for name,desc,rows in [
    ("Treasury_10Y_Level","Prior Yahoo ^TNX Close / 100; decimal annual yield",1),
    ("Treasury_10Y_Change_1D","^TNX Close.diff(1) / 100; absolute decimal-yield change across source rows",2),
    ("Treasury_10Y_Change_5D","^TNX Close.diff(5) / 100; absolute decimal-yield change across source rows",6),
    ("Treasury_10Y_vs_MA_20","(^TNX Close - trailing mean 20) / 100; decimal-yield deviation",20)]:
    _add(name,desc,"^TNX",rows,True)
assert len(CONTEXT_FEATURES)==len(set(CONTEXT_FEATURES))==44
assert set(CONTEXT_METADATA)==set(CONTEXT_FEATURES)
assert "Tomorrow_Return" not in CONTEXT_FEATURES
```

### features/context_features.py

```python
"""Date-aligned market, sector, VIX and rate features without future observations."""
import numpy as np
import pandas as pd

from data.market_data import MarketDataError
from data.context_data import align_previous, validate_daily_index
from features.context_registry import CONTEXT_FEATURES
from features.numerics import divide


def _return(close: pd.Series, n: int) -> pd.Series:
    """Full stock-grid window prevents missing dates becoming unequal return spans."""
    return (divide(close, close.shift(n)) - 1).where(close.rolling(n+1).count() == n+1)


def context_features(stock: pd.DataFrame, bundle: dict) -> pd.DataFrame:
    """Keep the stock index intact; missing context removes ML rows, never target rows.

    ETF closes are first reindexed to actual stock dates, with no filling, before
    trailing computations. VIX/rates use native trailing windows then strict-prior
    as-of alignment capped at four calendar days. Unknown source vintages are not
    represented as historically verified publication timestamps.
    """
    validate_daily_index(stock.index)
    profile, sources = bundle["profile"], bundle["series"]
    for key in ("market", "growth", "sector", "volatility", "rates"):
        symbol = profile[key]
        if symbol not in sources:
            raise MarketDataError(f"Required context source {symbol} missing. Context mode cannot proceed; non-context modes remain available.")
        frame = sources[symbol]
        validate_daily_index(frame.index)
        if "Close" not in frame or frame.empty or not np.isfinite(frame.Close).all() or not (frame.Close>0).all():
            raise MarketDataError(f"Invalid required context Close data for {symbol}.")
    stock_close = stock.Close
    stock_return = stock_close.pct_change(fill_method=None)
    output, returns, vols = {}, {}, {}
    for label,key in (("SPY","market"),("QQQ","growth"),("Sector","sector")):
        close = sources[profile[key]].Close.reindex(stock.index)
        returns[label] = {n:_return(close,n) for n in (1,5,20)}
        output.update({f"{label}_Return_{n}D":values for n,values in returns[label].items()})
        for n in ((20,50,200) if label=="SPY" else (20,50) if label=="QQQ" else (20,)):
            output[f"{label}_Price_to_SMA_{n}"] = divide(close,close.rolling(n).mean())-1
        vols[label] = {}
        for n in ((5,20,60) if label=="SPY" else (20,) if label=="Sector" else ()):
            vols[label][n] = returns[label][1].rolling(n).std()
            output[f"{label}_Volatility_{n}"] = vols[label][n]
    output["SPY_Volatility_Ratio_5_20"] = divide(vols["SPY"][5],vols["SPY"][20].where(vols["SPY"][20]>1e-12))
    for label,n in (("SPY",5),("SPY",20),("Sector",5),("Sector",20),("QQQ",20)):
        output[f"Stock_vs_{label}_Return_{n}D"] = _return(stock_close,n)-returns[label][n]
    for label in ("SPY","Sector"):
        market = returns[label][1]
        for n in (20,60):
            corr = stock_return.rolling(n).corr(market)
            usable = (stock_return.rolling(n).std()>1e-12) & (market.rolling(n).std()>1e-12)
            output[f"Stock_{label}_Correlation_{n}"] = corr.where(usable).clip(-1,1)
    for n in (20,60):
        variance = returns["SPY"][1].rolling(n).var(ddof=1)
        output[f"Stock_SPY_Beta_{n}"] = divide(stock_return.rolling(n).cov(returns["SPY"][1],ddof=1),variance.where(variance>1e-12))
    output["Market_Adjusted_Return_1D"] = stock_return-returns["SPY"][1]
    output["Sector_Adjusted_Return_1D"] = stock_return-returns["Sector"][1]
    for label in ("SPY","Sector"):
        output[f"Stock_to_{label}_Volatility_20"] = divide(stock_return.rolling(20).std(),vols[label][20].where(vols[label][20]>1e-12))
    vix = sources[profile["volatility"]].Close
    vix_native = pd.DataFrame({
        "VIX_Level_Normalized":vix/100, "VIX_Return_1D":vix.pct_change(fill_method=None),
        "VIX_Return_5D":vix.pct_change(5,fill_method=None),
        "VIX_Price_to_SMA_20":divide(vix,vix.rolling(20).mean())-1,
        "VIX_Percentile_252":vix.rolling(252).rank(method="average",pct=True)
    })
    rates = sources[profile["rates"]].Close
    rate_native = pd.DataFrame({
        "Treasury_10Y_Level":rates/100, "Treasury_10Y_Change_1D":rates.diff()/100,
        "Treasury_10Y_Change_5D":rates.diff(5)/100,
        "Treasury_10Y_vs_MA_20":(rates-rates.rolling(20).mean())/100
    })
    vix_aligned,_ = align_previous(vix_native,stock.index)
    rates_aligned,_ = align_previous(rate_native,stock.index)
    result = pd.concat([pd.DataFrame(output,index=stock.index),vix_aligned,rates_aligned],axis=1)[CONTEXT_FEATURES]
    if np.isinf(result.to_numpy()).any():
        raise MarketDataError("Context features contain infinity; cannot fit context mode.")
    return result
```

### models/context_comparison.py

```python
"""Untuned V7 context-family ablation on identical stock dates and targets.

Run: python -m models.context_comparison AAPL MSFT JPM
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from data.market_data import download_market_data, normalize_ticker
from data.context_data import ContextCache, download_context_bundle, context_data_report, align_previous
from features.feature_factory import build_feature_set
from features.registry import ADVANCED_TEMPORAL_FEATURES, ADVANCED_TEMPORAL_CONTEXT_FEATURES
from features.context_registry import CONTEXT_FEATURES
from features.audit import audit_features
from models.baseline import prepare_ml_dataset, chronological_split, evaluate_baseline


def verify_causality(stock: pd.DataFrame, bundle: dict, full: pd.DataFrame) -> list[dict]:
    """Independent stock/context perturbations and joint history truncation."""
    checks=[]
    for cutoff in ("2015-06-15","2015-06-30","2015-12-31"):
        if not stock.index.min() <= pd.Timestamp(cutoff) < stock.index.max():
            checks.append(dict(cutoff=cutoff,status="outside sample"))
            continue
        expected=full.loc[:cutoff,ADVANCED_TEMPORAL_CONTEXT_FEATURES]
        for kind in ("stock","context","prefix"):
            raw=stock.copy()
            b=dict(bundle,series={k:v.copy() for k,v in bundle["series"].items()})
            if kind=="stock":
                raw.loc[raw.index>cutoff,:]*=2
            elif kind=="context":
                for frame in b["series"].values():
                    frame.loc[frame.index>cutoff,:]*=3
            else:
                raw=raw.loc[:cutoff]
                b["series"]={k:v.loc[:cutoff] for k,v in b["series"].items()}
            built=build_feature_set(raw,"advanced_temporal_context",b)
            pd.testing.assert_frame_equal(expected,built.loc[:cutoff,ADVANCED_TEMPORAL_CONTEXT_FEATURES],check_exact=True)
        checks.append(dict(cutoff=cutoff,stock_perturbation="PASS",context_perturbation="PASS",prefix="PASS"))
    return checks


def descriptive_context(featured: pd.DataFrame) -> dict:
    """Historical descriptions only: these aggregates never enter model inputs."""
    pairs=featured[["Daily_Return","SPY_Return_1D","Sector_Return_1D"]].dropna()
    v=featured[["Daily_Return","VIX_Percentile_252"]].dropna()
    groups={}
    for label,mask in (("low_trailing_vix",v.VIX_Percentile_252<=.25),
                       ("high_trailing_vix",v.VIX_Percentile_252>=.75)):
        rows=v.loc[mask,"Daily_Return"]
        groups[label]=dict(count=len(rows),mean=float(rows.mean()))
    return dict(paired_return_rows=len(pairs),stock_spy_correlation=float(pairs.Daily_Return.corr(pairs.SPY_Return_1D)),
                stock_sector_correlation=float(pairs.Daily_Return.corr(pairs.Sector_Return_1D)),
                vix_environments=groups,note="Reporting only; prior-date trailing VIX percentile thresholds 0.25/0.75; no causal claims.")


def compare_context(stock: pd.DataFrame, bundle: dict) -> dict:
    """Align common eligible dates before either split; hold all model settings fixed."""
    old=build_feature_set(stock,"advanced_temporal")
    full=build_feature_set(stock,"advanced_temporal_context",bundle)
    pd.testing.assert_frame_equal(old,full[old.columns])
    Xa,ya=prepare_ml_dataset(old,"advanced_temporal")
    Xb,yb=prepare_ml_dataset(full,"advanced_temporal_context")
    context_eligible=len(Xb)
    common=Xa.index.intersection(Xb.index).sort_values()
    Xa,ya,Xb,yb=Xa.loc[common],ya.loc[common],Xb.loc[common],yb.loc[common]
    pd.testing.assert_series_equal(ya,yb)
    pd.testing.assert_frame_equal(Xa,Xb[ADVANCED_TEMPORAL_FEATURES])
    a=chronological_split(Xa,ya,stock.index)
    b=chronological_split(Xb,yb,stock.index)
    for key in ("X_train","X_test","y_train","y_test"):
        assert a[key].index.equals(b[key].index)
    for key in ("y_train","y_test"):
        pd.testing.assert_series_equal(a[key],b[key])
    assert a["removed"].equals(b["removed"])
    train_audit=audit_features(b["X_train"])
    full_audit=audit_features(Xb)
    if train_audit["exact_duplicates"] or full_audit["exact_duplicates"]:
        raise ValueError("Exact duplicates detected in context inputs; review before diagnostic fitting.")
    causal=verify_causality(stock,bundle,full)
    scaled=stock.copy()
    scaled[["Open","High","Low","Close"]]*=7
    scaled["Volume"]*=11
    scaled_bundle=dict(bundle,series={k:v.copy() for k,v in bundle["series"].items()})
    for key,factor in (("market",3),("growth",5),("sector",9)):
        scaled_bundle["series"][bundle["profile"][key]][["Open","High","Low","Close"]]*=factor
    for f in scaled_bundle["series"].values(): f["Volume"]*=13
    scaled_features=build_feature_set(scaled,"advanced_temporal_context",scaled_bundle)
    np.testing.assert_allclose(full[ADVANCED_TEMPORAL_CONTEXT_FEATURES],scaled_features[ADVANCED_TEMPORAL_CONTEXT_FEATURES],equal_nan=True,rtol=1e-6,atol=1e-6)
    print("Alignment, finite matrices, causality, scale and duplicate checks: PASS. Fitting two unchanged forests...",flush=True)
    first=evaluate_baseline(a,old,"advanced_temporal")
    second=evaluate_baseline(b,full,"advanced_temporal_context")
    before,after=first["metrics"],second["metrics"]
    for metric in ("zero_mae","zero_rmse","momentum"):
        assert before[metric]==after[metric]
    importance=second["importance"]
    context_importance=importance[importance.Feature.isin(CONTEXT_FEATURES)]
    return dict(
        profile=bundle["profile"],source_reports=context_data_report(stock,bundle),
        raw_rows=len(stock),raw_start=str(stock.index.min().date()),raw_end=str(stock.index.max().date()),
        context_eligible_rows=context_eligible,common_rows=len(common),feature_count=len(Xb.columns),
        common_start=str(common.min().date()),common_end=str(common.max().date()),
        train_before=b["train_before"],train_rows=len(b["X_train"]),test_rows=len(b["X_test"]),
        train_start=str(b["X_train"].index.min().date()),train_end=str(b["X_train"].index.max().date()),
        test_start=str(b["X_test"].index.min().date()),test_end=str(b["X_test"].index.max().date()),
        purged_dates=[str(d.date()) for d in b["removed"]],latest_training_target=str(b["latest_train_target"].date()),
        temporal=before,context=after,deltas={m:after[m]-before[m] for m in ("mae","rmse","r2","direction")},
        context_importance_total=float(context_importance.Importance.sum()),
        context_importances=context_importance.to_dict(orient="records"),top25=importance.head(25).to_dict(orient="records"),
        descriptive=descriptive_context(full),training_audit=train_audit,full_sample_audit=full_audit,
        context_only_audit=audit_features(b["X_train"][CONTEXT_FEATURES]),causality_checks=causal,
        scale_invariance="PASS",identical_comparison_dates="PASS",finite_matrices="PASS"
    )


def verify_rate_units(cache: ContextCache) -> dict:
    """Independent dated unit check versus Treasury CMT, not an equality of instruments."""
    rates=next(f for (symbol,_,_),f in cache.frames.items() if symbol=="^TNX")
    reference={"2024-01-02":3.95,"2024-01-03":3.91,"2024-01-04":3.99,"2024-01-05":4.05}
    comparisons=[]
    for date,official in reference.items():
        if pd.Timestamp(date) not in rates.index:
            continue
        yahoo=float(rates.loc[date,"Close"])
        assert abs(yahoo-official)<.03, "Rate scale differs from the verified percentage-point convention."
        comparisons.append(dict(date=date,yahoo_tnx=yahoo,treasury_10y_percent=official))
    return dict(comparisons=comparisons,units="Yahoo percentage points; divide by 100 to decimal annual yield",
                reference="https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=2024",
                limitation="Cboe/Yahoo proxy and Treasury CMT are different methodologies; check establishes scale, not identical measurements.")


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickers",nargs="+")
    parser.add_argument("--start",default="2010-01-01")
    parser.add_argument("--end",default=None)
    args=parser.parse_args()
    cache=ContextCache();results={}
    for ticker in args.tickers:
        ticker=normalize_ticker(ticker)
        print(f"V7 controlled context experiment: {ticker}",flush=True)
        bundle=download_context_bundle(ticker,args.start,args.end,cache)
        stock=download_market_data(ticker,args.start,args.end)
        print(json.dumps(context_data_report(stock,bundle),indent=2),flush=True)
        results[ticker]=compare_context(stock,bundle)
        print(json.dumps(results[ticker],indent=2),flush=True)
    evidence=dict(results=results,cache=dict(logical_requests=cache.logical_requests,provider_downloads=cache.provider_downloads),
                  rate_unit_verification=verify_rate_units(cache))
    Path("reports").mkdir(exist_ok=True)
    Path("reports/v7_experiments.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print("All V7 experiments complete:",evidence["cache"],flush=True)


if __name__=="__main__":
    main()
```

### tests/test_context_features.py

```python
"""Offline alignment, availability, numerical-reference and causality tests."""
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd

from config.market_context import context_profile
from data.context_data import ContextCache, download_context_bundle, align_previous
from data.market_data import MarketDataError
from features.context_features import context_features
from features.feature_factory import build_feature_set
from features.registry import get_feature_columns, FEATURE_METADATA, ADVANCED_TEMPORAL_FEATURES, ADVANCED_TEMPORAL_CONTEXT_FEATURES
from features.context_registry import CONTEXT_FEATURES
from models.baseline import prepare_ml_dataset, chronological_split, evaluate_baseline


def frame(returns, index, level=100):
    close = level*np.cumprod(1+np.asarray(returns))
    return pd.DataFrame(dict(Open=close*.999,High=close*1.01,Low=close*.99,Close=close,
                             Volume=1000+np.arange(len(index))),index=index)


def fixture(rows=600):
    index=pd.bdate_range("2020-01-01",periods=rows)
    rng=np.random.default_rng(17)
    market=rng.normal(.0003,.012,rows)
    stock=frame(2*market,index)
    sources={"SPY":frame(market,index),"QQQ":frame(market*.9+rng.normal(0,.003,rows),index),
             "XLK":frame(market*.7+rng.normal(0,.005,rows),index),
             "^VIX":frame(rng.normal(0,.015,rows),index,20),"^TNX":frame(rng.normal(0,.002,rows),index,4)}
    return stock,dict(profile=context_profile("AAPL"),series=sources,requested_start="2020-01-01",requested_end=None)


class ContextTests(unittest.TestCase):
    def test_profiles_and_unsupported(self):
        for ticker,sector in ((" aapl ","XLK"),("MSFT","XLK"),("JPM","XLF")):
            self.assertEqual(context_profile(ticker)["sector"],sector)
        with self.assertRaisesRegex(MarketDataError,"not configured"):
            context_profile("7203.T")
        stock,_=fixture()
        for mode in ("basic","advanced","advanced_temporal"):
            self.assertEqual(len(prepare_ml_dataset(build_feature_set(stock,mode),mode)[0])>0,True)

    def test_date_alignment_and_missing_interval(self):
        stock,bundle=fixture()
        missing=stock.index[20]
        bundle["series"]["SPY"]=bundle["series"]["SPY"].drop(missing)
        f=context_features(stock,bundle)
        self.assertTrue(pd.isna(f.loc[missing,"SPY_Return_1D"]))
        self.assertTrue(pd.isna(f.iloc[21].SPY_Return_1D))
        expected=bundle["series"]["SPY"].Close.loc[stock.index[22]]/bundle["series"]["SPY"].Close.loc[stock.index[21]]-1
        self.assertAlmostEqual(f.iloc[22].SPY_Return_1D,expected)
        self.assertTrue(pd.isna(f.iloc[24].SPY_Return_5D))
        self.assertTrue(f.index.equals(stock.index))

    def test_market_and_relative_returns(self):
        stock,bundle=fixture()
        f=context_features(stock,bundle);t=90
        spy,sector=bundle["series"]["SPY"].Close,bundle["series"]["XLK"].Close
        for n in (1,5,20):
            self.assertAlmostEqual(f[f"SPY_Return_{n}D"].iloc[t],spy.iloc[t]/spy.iloc[t-n]-1)
        self.assertAlmostEqual(f.Stock_vs_SPY_Return_5D.iloc[t],stock.Close.iloc[t]/stock.Close.iloc[t-5]-spy.iloc[t]/spy.iloc[t-5])
        self.assertAlmostEqual(f.Sector_Adjusted_Return_1D.iloc[t],stock.Close.pct_change().iloc[t]-sector.pct_change().iloc[t])

    def test_beta_and_correlation_known_relationship(self):
        stock,bundle=fixture()
        f=context_features(stock,bundle)
        for n in (20,60):
            np.testing.assert_allclose(f[f"Stock_SPY_Beta_{n}"].iloc[100:],2,atol=1e-10)
            np.testing.assert_allclose(f[f"Stock_SPY_Correlation_{n}"].iloc[100:],1,atol=1e-10)
        market=bundle["series"]["SPY"].Close.pct_change().fillna(0)
        inverse=frame(-market.to_numpy(),stock.index)
        negative=context_features(inverse,bundle)
        np.testing.assert_allclose(negative.Stock_SPY_Correlation_20.iloc[100:],-1,atol=1e-10)
        np.testing.assert_allclose(negative.Stock_SPY_Beta_20.iloc[100:],-1,atol=1e-10)

    def test_relative_volatility_and_zero_variance(self):
        stock,bundle=fixture()
        f=context_features(stock,bundle)
        np.testing.assert_allclose(f.Stock_to_SPY_Volatility_20.iloc[100:],2,atol=1e-10)
        bundle["series"]["SPY"]["Close"]=100.
        undefined=context_features(stock,bundle)
        self.assertTrue(undefined.Stock_SPY_Beta_20.isna().all())
        self.assertTrue(undefined.Stock_SPY_Correlation_20.isna().all())
        self.assertTrue(undefined.Stock_to_SPY_Volatility_20.isna().all())

    def test_strict_prior_staleness_and_no_backfill(self):
        values=pd.DataFrame({"rate":[4.,9.]},index=pd.to_datetime(["2024-01-05","2024-01-12"]))
        dates=pd.to_datetime(["2024-01-04","2024-01-05","2024-01-08","2024-01-09","2024-01-10","2024-01-12","2024-01-15"])
        f,d=align_previous(values,dates)
        self.assertTrue(f.iloc[:2].isna().all().all())
        self.assertEqual(f.rate.iloc[2],4)
        self.assertEqual(d.Age_Days.iloc[2],3)
        self.assertEqual(f.rate.iloc[3],4)
        self.assertTrue(pd.isna(f.rate.iloc[4]))
        self.assertTrue(pd.isna(f.rate.iloc[5])) # Same-date value not allowed.
        self.assertEqual(f.rate.iloc[6],9)
        self.assertEqual(d.Age_Days.iloc[6],3)
        self.assertTrue((d.loc[d.Usable,"Source_Date"]<dates[d.Usable]).all())

    def test_vix_rank_ties_and_future_safety(self):
        stock,bundle=fixture()
        v=bundle["series"]["^VIX"]
        v["Close"]=np.tile([10.,20.,20.,30.],150)
        f=context_features(stock,bundle);t=350
        values=v.Close.iloc[t-252:t].to_numpy();last=values[-1]
        expected=((values<last).sum()+((values==last).sum()+1)/2)/252
        self.assertAlmostEqual(f.VIX_Percentile_252.iloc[t],expected)
        self.assertTrue(pd.isna(f.VIX_Percentile_252.iloc[251]))
        v.loc[v.index>stock.index[t],"Close"]*=100
        pd.testing.assert_series_equal(f.VIX_Percentile_252.iloc[:t+1],context_features(stock,bundle).VIX_Percentile_252.iloc[:t+1],check_exact=True)

    def test_rate_units_and_lag(self):
        stock,bundle=fixture();r=bundle["series"]["^TNX"]
        r["Close"]=4.+np.arange(len(r))*.001
        f=context_features(stock,bundle);t=90
        self.assertAlmostEqual(f.Treasury_10Y_Level.iloc[t],r.Close.iloc[t-1]/100)
        self.assertAlmostEqual(f.Treasury_10Y_Change_1D.iloc[t],.001/100)
        self.assertAlmostEqual(f.Treasury_10Y_Change_5D.iloc[t],.005/100)
        self.assertAlmostEqual(f.Treasury_10Y_vs_MA_20.iloc[t],(r.Close.iloc[t-1]-r.Close.iloc[t-20:t].mean())/100)

    def test_independent_perturbations_and_prefixes(self):
        stock,bundle=fixture()
        full=build_feature_set(stock,"advanced_temporal_context",bundle)
        for pos in (300,390,520):
            date=stock.index[pos]
            for change_stock in (True,False):
                s=stock.copy();b=dict(bundle,series={k:v.copy() for k,v in bundle["series"].items()})
                if change_stock:
                    s.loc[s.index>date,:]*=2
                else:
                    for f in b["series"].values():
                        f.loc[f.index>date,:]*=3
                changed=build_feature_set(s,"advanced_temporal_context",b)
                pd.testing.assert_frame_equal(full.loc[:date,ADVANCED_TEMPORAL_CONTEXT_FEATURES],changed.loc[:date,ADVANCED_TEMPORAL_CONTEXT_FEATURES],check_exact=True)
            b=dict(bundle,series={k:v.loc[:date] for k,v in bundle["series"].items()})
            prefix=build_feature_set(stock.loc[:date],"advanced_temporal_context",b)
            pd.testing.assert_frame_equal(full.loc[:date,ADVANCED_TEMPORAL_CONTEXT_FEATURES],prefix[ADVANCED_TEMPORAL_CONTEXT_FEATURES],check_exact=True)

    def test_price_and_volume_scale(self):
        stock,bundle=fixture();a=context_features(stock,bundle)
        stock[["Open","High","Low","Close"]]*=7;stock["Volume"]*=11
        for symbol,factor in (("SPY",3),("QQQ",5),("XLK",9)):
            bundle["series"][symbol][["Open","High","Low","Close"]]*=factor
        for f in bundle["series"].values(): f["Volume"]*=13
        b=context_features(stock,bundle)
        np.testing.assert_allclose(a,b,atol=1e-8,rtol=1e-8,equal_nan=True)

    def test_registry_metadata_and_previous_mode(self):
        self.assertEqual([len(get_feature_columns(m)) for m in ("basic","advanced","advanced_temporal","advanced_temporal_context")],[10,70,88,132])
        self.assertNotIn("Tomorrow_Return",ADVANCED_TEMPORAL_CONTEXT_FEATURES)
        self.assertEqual(len(set(CONTEXT_FEATURES)),44)
        for name in CONTEXT_FEATURES:
            m=FEATURE_METADATA[name]
            self.assertEqual(m['family'],'context')
            for key in ('alignment','staleness','source','lookback','normalized','future_safe'):
                self.assertIn(key,m)
        stock,bundle=fixture();stock.columns.name="Price"
        old=build_feature_set(stock,"advanced_temporal")
        new=build_feature_set(stock,"advanced_temporal_context",bundle)
        pd.testing.assert_frame_equal(old,new[old.columns])

    @patch("data.context_data.download_context_series")
    def test_cache_download_counts(self,download):
        stock,_=fixture();download.return_value=stock
        cache=ContextCache()
        for ticker in ("AAPL","MSFT","JPM"):
            download_context_bundle(ticker,"2010-01-01",cache=cache)
        self.assertEqual(cache.logical_requests,15)
        self.assertEqual(cache.provider_downloads,6)
        self.assertEqual(download.call_count,6)

    @patch("data.context_data.download_context_series",side_effect=MarketDataError("provider unavailable"))
    def test_required_failure_names_source(self,download):
        with self.assertRaisesRegex(MarketDataError,r"\^VIX failed.*non|\^VIX failed.*Basic"):
            ContextCache().get("^VIX","2010-01-01",None)
        stock,bundle=fixture();del bundle["series"]["SPY"]
        with self.assertRaisesRegex(MarketDataError,"SPY missing"):
            context_features(stock,bundle)

    @patch("models.baseline.RandomForestRegressor")
    def test_finite_matrices_and_training_only_fit(self,forest):
        stock,bundle=fixture()
        f=build_feature_set(stock,"advanced_temporal_context",bundle)
        X,y=prepare_ml_dataset(f,"advanced_temporal_context")
        self.assertTrue(np.isfinite(X.to_numpy()).all())
        split=chronological_split(X,y,stock.index)
        forest.return_value.predict.return_value=np.zeros(len(split["y_test"]))
        forest.return_value.feature_importances_=np.full(132,1/132)
        evaluate_baseline(split,f,"advanced_temporal_context")
        forest.assert_called_once_with(n_estimators=300,random_state=42,n_jobs=-1)
        self.assertIs(forest.return_value.fit.call_args.args[0],split["X_train"])

    @patch("main.download_market_data")
    @patch("builtins.input",return_value="7203.T")
    @patch("builtins.print")
    def test_unsupported_cli_no_download(self,printing,input_mock,download):
        import main
        with patch.object(main,"FEATURE_SET","advanced_temporal_context"):
            self.assertEqual(main.main(),1)
        download.assert_not_called()


class ContextIngestionTests(unittest.TestCase):
    @patch("data.context_data.yf.download")
    def test_index_placeholders_recorded_not_filled(self,download):
        from data.context_data import download_context_series
        stock,_=fixture(200)
        raw=stock.astype(float)
        date=raw.index[20]
        raw.loc[date,["Open","High","Low","Close"]]=np.nan
        raw.loc[date,"Volume"]=0
        download.return_value=raw
        clean=download_context_series("^VIX","2020-01-01","2021-01-01")
        self.assertEqual(len(clean),199)
        self.assertNotIn(date,clean.index)
        self.assertEqual(clean.attrs["empty_quote_dates"],[str(date.date())])
        pd.testing.assert_frame_equal(clean,stock.astype(float).drop(date),check_flags=False)
        self.assertTrue(download.call_args.kwargs["auto_adjust"])
        self.assertTrue(download.call_args.kwargs["keepna"])

    @patch("data.context_data.yf.download")
    def test_partial_invalid_quote_is_rejected(self,download):
        from data.context_data import download_context_series
        stock,_=fixture(200)
        stock.loc[stock.index[20],"Close"]=np.nan
        download.return_value=stock
        with self.assertRaisesRegex(MarketDataError,"non-finite"):
            download_context_series("^TNX","2020-01-01","2021-01-01")
```

## 36. V7 COMPLETION STATUS

V7 is complete: explicit US profiles and cache, verified rate units, context data
validation, exact-date/bounded-prior alignment, 44 documented context features,
four preserved/additive modes, deterministic tests, controlled three-stock fits,
descriptive reports, feature importance and redundancy evidence. No V8 functionality.

## 37. V8 HANDOFF

Market regime intelligence remains absent: no regime labels, clustering, Hidden
Markov Models, Gaussian mixtures or regime-conditioned forecasts. Future work must
avoid fitting regime transformations on test data or classifying historical rows
using future observations. No PCA, selection, new predictive models, news, signals,
backtesting, portfolio simulation or dashboard was added.

Remaining research limitations include retrospectively adjusted/revised provider
history, observation-date availability assumptions, explicit US-only profiles,
four-day index carry limits, correlated inputs, a single inspected holdout and no
statistical-significance or trading-performance evidence. Additional maturities,
real-time publication metadata and exchange-specific international context are deferred.
