# CastiFy V7 context feature catalog

## Timing and source contract

US-only configured profiles: AAPL/XLK, MSFT/XLK, JPM/XLF. SPY and QQQ are common
market sources. All sources use Yahoo/yfinance daily data with auto_adjust=True;
ETF OHLC are dividend/split-adjusted. VIX and TNX are indexes, not adjusted equity
returns or traded volumes. Volume is not a context input. Treasury ^TNX Yahoo closes
are percentage-point yields (e.g. 3.946 means about 3.946%), not bond prices.

Stock predictions use the completed US equity session. Same-date ETF closes are
allowed. VIX and TNX daily timestamps do not prove they were available at exactly
16:00 Eastern: their entire feature vectors are conservatively aligned from a
strictly earlier source date. No same-date VIX/rate value is used. Source age must
be 1–4 calendar days; anything older is unavailable. Historical revisions and provider
publication vintages remain unverified; this implements causal alignment, not a
certified point-in-time archival feed.

ETF prices are first aligned to the exact stock-date grid. Missing dates remain
NaN. Returns require every close in the interval, so a missing Wednesday cannot
silently convert Thursday's market return into a Tuesday-to-Thursday return paired
with Wednesday-to-Thursday stock performance. All paired windows require complete
observations; target dates remain on the original, unfiltered stock index.

VIX/TNX calculations use their native observed source rows, then strict backward
as-of alignment. The newest previous source row controls; NaN features on it are
not replaced by older valid features. Alignment diagnostics preserve Source_Date,
Age_Days and Usable; their ages are not added as duplicate ML inputs.

Yahoo index rows containing no OHLC quote and zero/missing volume are recorded and
removed before validating source observations. No value is invented. Partial bad
quotes are rejected. Removed placeholder dates remain in source-quality diagnostics.
This does not change V4 stock ingestion or any earlier feature mode.

[Official Treasury 2024 rates](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=2024)
provide the independent rate-scale check. Yahoo ^TNX is a proxy with a different
methodology, not a claim to reproduce Treasury CMT exactly. A yield curve is deferred:
no second maturity was verified or added.

## Feature definitions

Normalized below means price-unit invariant; VIX levels and all decimal-yield rate
features intentionally retain economic unit dependence. Minimum rows are native
source/stock-window requirements before availability lag, not guaranteed first ML
rows. All feature families are context; subfamilies are listed below.

| Feature | Subfamily | Definition | Source | Minimum rows | Alignment | Normalized? | Future-safe? | Staleness |
|---|---|---|---|---|---|---|---|---|
| SPY_Return_1D | market | Close / Close.shift(1) - 1; require all 2 aligned closes | SPY | 2 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| SPY_Return_5D | market | Close / Close.shift(5) - 1; require all 6 aligned closes | SPY | 6 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| SPY_Return_20D | market | Close / Close.shift(20) - 1; require all 21 aligned closes | SPY | 21 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| QQQ_Return_1D | market | Close / Close.shift(1) - 1; require all 2 aligned closes | QQQ | 2 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| QQQ_Return_5D | market | Close / Close.shift(5) - 1; require all 6 aligned closes | QQQ | 6 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| QQQ_Return_20D | market | Close / Close.shift(20) - 1; require all 21 aligned closes | QQQ | 21 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| SPY_Price_to_SMA_20 | market | Close / mean(20 aligned closes) - 1 | SPY | 20 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| SPY_Price_to_SMA_50 | market | Close / mean(50 aligned closes) - 1 | SPY | 50 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| SPY_Price_to_SMA_200 | market | Close / mean(200 aligned closes) - 1 | SPY | 200 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| QQQ_Price_to_SMA_20 | market | Close / mean(20 aligned closes) - 1 | QQQ | 20 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| QQQ_Price_to_SMA_50 | market | Close / mean(50 aligned closes) - 1 | QQQ | 50 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| SPY_Volatility_5 | market | Std of 5 aligned returns, ddof=1 | SPY | 6 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| SPY_Volatility_20 | market | Std of 20 aligned returns, ddof=1 | SPY | 21 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| SPY_Volatility_60 | market | Std of 60 aligned returns, ddof=1 | SPY | 61 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| SPY_Volatility_Ratio_5_20 | market | SPY sample volatility 5 / 20; denominator >1e-12 | SPY | 21 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| VIX_Level_Normalized | volatility_context | Prior VIX Close / 100; implied annualized volatility decimal, not realized return | ^VIX | 1 | Strict previous source date after native trailing calculation | False | True | 1 to 4 calendar days, otherwise NaN; source dates and ages reported |
| VIX_Return_1D | volatility_context | VIX Close / previous native source Close - 1 | ^VIX | 2 | Strict previous source date after native trailing calculation | True | True | 1 to 4 calendar days, otherwise NaN; source dates and ages reported |
| VIX_Return_5D | volatility_context | VIX Close / native source Close 5 rows earlier - 1 | ^VIX | 6 | Strict previous source date after native trailing calculation | True | True | 1 to 4 calendar days, otherwise NaN; source dates and ages reported |
| VIX_Price_to_SMA_20 | volatility_context | VIX Close / trailing 20-source-row mean - 1 | ^VIX | 20 | Strict previous source date after native trailing calculation | True | True | 1 to 4 calendar days, otherwise NaN; source dates and ages reported |
| VIX_Percentile_252 | volatility_context | Current VIX rank within trailing 252 source closes / 252; average ranks for ties, includes current source close | ^VIX | 252 | Strict previous source date after native trailing calculation | True | True | 1 to 4 calendar days, otherwise NaN; source dates and ages reported |
| Sector_Return_1D | sector | Close / Close.shift(1) - 1; require all 2 aligned closes | configured sector ETF (XLK/XLF) | 2 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Sector_Return_5D | sector | Close / Close.shift(5) - 1; require all 6 aligned closes | configured sector ETF (XLK/XLF) | 6 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Sector_Return_20D | sector | Close / Close.shift(20) - 1; require all 21 aligned closes | configured sector ETF (XLK/XLF) | 21 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Sector_Price_to_SMA_20 | sector | Close / mean(20 aligned closes) - 1 | configured sector ETF (XLK/XLF) | 20 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Sector_Volatility_20 | sector | Std of 20 aligned returns, ddof=1 | configured sector ETF (XLK/XLF) | 21 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Stock_vs_SPY_Return_5D | relative | Stock trailing 5-row return minus aligned SPY return | stock + SPY | 6 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Stock_vs_SPY_Return_20D | relative | Stock trailing 20-row return minus aligned SPY return | stock + SPY | 21 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Stock_vs_Sector_Return_5D | relative | Stock trailing 5-row return minus aligned Sector return | stock + Sector | 6 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Stock_vs_Sector_Return_20D | relative | Stock trailing 20-row return minus aligned Sector return | stock + Sector | 21 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Stock_vs_QQQ_Return_20D | relative | Stock trailing 20-row return minus aligned QQQ return | stock + QQQ | 21 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Stock_SPY_Correlation_20 | relative | Pearson correlation over 20 matched return pairs; full window, std >1e-12 | stock + SPY | 21 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Stock_SPY_Correlation_60 | relative | Pearson correlation over 60 matched return pairs; full window, std >1e-12 | stock + SPY | 61 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Stock_Sector_Correlation_20 | relative | Pearson correlation over 20 matched return pairs; full window, std >1e-12 | stock + Sector | 21 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Stock_Sector_Correlation_60 | relative | Pearson correlation over 60 matched return pairs; full window, std >1e-12 | stock + Sector | 61 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Stock_SPY_Beta_20 | relative | Sample cov(stock, SPY)/sample var(SPY), ddof=1 over 20 pairs; variance >1e-12 | stock + SPY | 21 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Stock_SPY_Beta_60 | relative | Sample cov(stock, SPY)/sample var(SPY), ddof=1 over 60 pairs; variance >1e-12 | stock + SPY | 61 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Market_Adjusted_Return_1D | relative | Stock current return minus aligned SPY current return; not estimated alpha | stock + SPY | 2 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Sector_Adjusted_Return_1D | relative | Stock current return minus aligned Sector current return; not estimated alpha | stock + Sector | 2 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Stock_to_SPY_Volatility_20 | relative | Stock / SPY 20-return sample std; denominator >1e-12 | stock + SPY | 21 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Stock_to_Sector_Volatility_20 | relative | Stock / Sector 20-return sample std; denominator >1e-12 | stock + Sector | 21 | Exact stock-date grid, complete trailing windows | True | True | Same date only; no fill |
| Treasury_10Y_Level | rates | Prior Yahoo ^TNX Close / 100; decimal annual yield | ^TNX | 1 | Strict previous source date after native trailing calculation | False | True | 1 to 4 calendar days, otherwise NaN; source dates and ages reported |
| Treasury_10Y_Change_1D | rates | ^TNX Close.diff(1) / 100; absolute decimal-yield change across source rows | ^TNX | 2 | Strict previous source date after native trailing calculation | False | True | 1 to 4 calendar days, otherwise NaN; source dates and ages reported |
| Treasury_10Y_Change_5D | rates | ^TNX Close.diff(5) / 100; absolute decimal-yield change across source rows | ^TNX | 6 | Strict previous source date after native trailing calculation | False | True | 1 to 4 calendar days, otherwise NaN; source dates and ages reported |
| Treasury_10Y_vs_MA_20 | rates | (^TNX Close - trailing mean 20) / 100; decimal-yield deviation | ^TNX | 20 | Strict previous source date after native trailing calculation | False | True | 1 to 4 calendar days, otherwise NaN; source dates and ages reported |

## Numerical and interpretation notes

Beta uses sample covariance and variance (ddof=1) on identical paired windows;
SPY variance must exceed 1e-12. Correlation requires both standard deviations above
1e-12 and is bounded to [-1,1] for roundoff. Relative-volatility denominators must
exceed 1e-12. Undefined values remain NaN; required-row deletion precedes fitting,
and every final matrix must be finite. No backward fill, interpolation, target
encoding, fitted preprocessing, or future distribution rank exists.

VIX_Percentile_252 is the current source close's average-tie rank within its last
252 observed closes, divided by 252; after calculation it follows the prior-date
availability rule. VIX levels divided by 100 describe implied annual volatility.
VIX returns are percentage changes of that index, not stock returns.

Treasury level is Close/100. Changes and deviation from 20-row mean are absolute
decimal-yield differences, not percentage price returns; 0.0001 is one basis point.
Source rows need not have the stock's holiday calendar. All source dates and bounded
ages remain visible in diagnostics.

Market/sector-adjusted returns are simple differences, not estimated alpha.
Five-day and twenty-day relative strength differ from one-day adjusted returns;
there are no extra one-day aliases. Correlated context features are reported, not
selected or tuned away. No regime classification, new models or strategy is included.
