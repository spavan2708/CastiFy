# CastiFy V5 feature catalog

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

## Advanced inputs

| Feature | Family | Definition / interpretation | Minimum raw rows | Normalized? | Future-safe? |
|---|---|---|---|---|---|
| Return_Lag_1 | returns | Daily_Return shifted back 1 trading rows. | 3 | Yes | Yes |
| Return_Lag_2 | returns | Daily_Return shifted back 2 trading rows. | 4 | Yes | Yes |
| Return_Lag_3 | returns | Daily_Return shifted back 3 trading rows. | 5 | Yes | Yes |
| Return_Lag_5 | returns | Daily_Return shifted back 5 trading rows. | 7 | Yes | Yes |
| Return_1D | returns | Close / Close.shift(1) - 1; trailing compounded return. | 2 | Yes | Yes |
| Return_2D | returns | Close / Close.shift(2) - 1; trailing compounded return. | 3 | Yes | Yes |
| Return_3D | returns | Close / Close.shift(3) - 1; trailing compounded return. | 4 | Yes | Yes |
| Return_5D | returns | Close / Close.shift(5) - 1; trailing compounded return. | 6 | Yes | Yes |
| Return_10D | returns | Close / Close.shift(10) - 1; trailing compounded return. | 11 | Yes | Yes |
| Return_20D | returns | Close / Close.shift(20) - 1; trailing compounded return. | 21 | Yes | Yes |
| Return_60D | returns | Close / Close.shift(60) - 1; trailing compounded return. | 61 | Yes | Yes |
| Intraday_Return | price_structure | Close / Open - 1 | 1 | Yes | Yes |
| Overnight_Gap | price_structure | Open / previous Close - 1 | 2 | Yes | Yes |
| High_Low_Range | price_structure | (High - Low) / Close | 1 | Yes | Yes |
| Close_Open_Position | price_structure | (Close - Open) / (High - Low); zero on a flat bar | 1 | Yes | Yes |
| Price_to_SMA_5 | price_structure | Close / rolling mean(Close, 5) - 1 | 5 | Yes | Yes |
| Price_to_SMA_10 | price_structure | Close / rolling mean(Close, 10) - 1 | 10 | Yes | Yes |
| Price_to_SMA_20 | price_structure | Close / rolling mean(Close, 20) - 1 | 20 | Yes | Yes |
| Price_to_SMA_50 | price_structure | Close / rolling mean(Close, 50) - 1 | 50 | Yes | Yes |
| Price_to_SMA_100 | price_structure | Close / rolling mean(Close, 100) - 1 | 100 | Yes | Yes |
| Price_to_SMA_200 | price_structure | Close / rolling mean(Close, 200) - 1 | 200 | Yes | Yes |
| SMA_5_to_20 | price_structure | SMA_5 / SMA_20 - 1 | 20 | Yes | Yes |
| SMA_20_to_50 | price_structure | SMA_20 / SMA_50 - 1 | 50 | Yes | Yes |
| SMA_50_to_200 | price_structure | SMA_50 / SMA_200 - 1 | 200 | Yes | Yes |
| Distance_From_20D_High | price_structure | Close / rolling max(High, 20) - 1 (intraday highs) | 20 | Yes | Yes |
| Distance_From_20D_Low | price_structure | Close / rolling min(Low, 20) - 1 (intraday lows) | 20 | Yes | Yes |
| Distance_From_60D_High | price_structure | Close / rolling max(High, 60) - 1 (intraday highs) | 60 | Yes | Yes |
| Distance_From_60D_Low | price_structure | Close / rolling min(Low, 60) - 1 (intraday lows) | 60 | Yes | Yes |
| Range_Position_20 | price_structure | (Close - rolling Low.min(20)) / (rolling High.max(20) - rolling Low.min(20)); flat range=0.5 | 20 | Yes | Yes |
| Drawdown_From_20D_Peak | price_structure | Close / rolling max(Close, 20) - 1; nonpositive | 20 | Yes | Yes |
| Drawdown_From_60D_Peak | price_structure | Close / rolling max(Close, 60) - 1; nonpositive | 60 | Yes | Yes |
| Drawdown_From_252D_Peak | price_structure | Close / rolling max(Close, 252) - 1; nonpositive | 252 | Yes | Yes |
| Price_to_EMA_5 | momentum | Close / EMA(span=5, adjust=False, min_periods=5) - 1; seeded with first close | 5 | Yes | Yes |
| Price_to_EMA_10 | momentum | Close / EMA(span=10, adjust=False, min_periods=10) - 1; seeded with first close | 10 | Yes | Yes |
| Price_to_EMA_20 | momentum | Close / EMA(span=20, adjust=False, min_periods=20) - 1; seeded with first close | 20 | Yes | Yes |
| Price_to_EMA_50 | momentum | Close / EMA(span=50, adjust=False, min_periods=50) - 1; seeded with first close | 50 | Yes | Yes |
| Log_Price_Slope_20 | momentum | OLS slope of log Close against 0..19; log-return units per trading row | 20 | Yes | Yes |
| Log_Price_Slope_60 | momentum | OLS slope of log Close against 0..59; log-return units per trading row | 60 | Yes | Yes |
| Return_5D_Acceleration | momentum | Return_5D - previous row's Return_5D | 7 | Yes | Yes |
| Volatility_5 | volatility | Trailing 5 Daily_Return sample standard deviation, ddof=1 | 6 | Yes | Yes |
| Volatility_10 | volatility | Trailing 10 Daily_Return sample standard deviation, ddof=1 | 11 | Yes | Yes |
| Volatility_20 | volatility | Trailing 20 Daily_Return sample standard deviation, ddof=1 | 21 | Yes | Yes |
| Volatility_60 | volatility | Trailing 60 Daily_Return sample standard deviation, ddof=1 | 61 | Yes | Yes |
| Volatility_Ratio_5_20 | volatility | Volatility_5 / Volatility_20; zero denominator undefined | 21 | Yes | Yes |
| Volatility_Ratio_20_60 | volatility | Volatility_20 / Volatility_60; zero denominator undefined | 61 | Yes | Yes |
| Rolling_Mean_Return_5 | volatility | Arithmetic mean of last 5 daily returns | 6 | Yes | Yes |
| Rolling_Mean_Return_20 | volatility | Arithmetic mean of last 20 daily returns | 21 | Yes | Yes |
| Rolling_Mean_Return_60 | volatility | Arithmetic mean of last 60 daily returns | 61 | Yes | Yes |
| Rolling_Skew_20 | volatility | Pandas unbiased rolling sample skew of 20 daily returns | 21 | Yes | Yes |
| Rolling_Skew_60 | volatility | Pandas unbiased rolling sample skew of 60 daily returns | 61 | Yes | Yes |
| Rolling_Kurtosis_20 | volatility | Pandas unbiased Fisher excess kurtosis of 20 returns (normal=0) | 21 | Yes | Yes |
| Rolling_Kurtosis_60 | volatility | Pandas unbiased Fisher excess kurtosis of 60 returns (normal=0) | 61 | Yes | Yes |
| Positive_Return_Ratio_20 | volatility | Fraction of 20 valid daily returns > 0; zeros count in denominator | 21 | Yes | Yes |
| Negative_Return_Ratio_20 | volatility | Fraction of 20 valid daily returns < 0; zeros count in denominator | 21 | Yes | Yes |
| Downside_Volatility_20 | volatility | Sample std of returns < 0 inside 20-return window; NaN with fewer than 2 qualifying values | 21 | Yes | Yes |
| Upside_Volatility_20 | volatility | Sample std of returns > 0 inside 20-return window; NaN with fewer than 2 qualifying values | 21 | Yes | Yes |
| Volume_Change | volume | Volume / previous Volume - 1; zero denominator undefined | 2 | Yes | Yes |
| Relative_Volume_5 | volume | Volume / rolling mean(Volume, 5); zero denominator undefined | 5 | Yes | Yes |
| Relative_Volume_20 | volume | Volume / rolling mean(Volume, 20); zero denominator undefined | 20 | Yes | Yes |
| Volume_Return_Correlation_20 | volume | Pearson correlation of 20 paired Volume_Change and Daily_Return values; constant input undefined | 21 | Yes | Yes |
| OBV_Flow_20 | volume | sum(sign(Daily_Return) * Volume, 20) / sum(Volume, 20); normalized trailing OBV change | 21 | Yes | Yes |
| Return_x_VolumeChange | volume | Daily_Return * Volume_Change; signed return amplified by volume change | 2 | Yes | Yes |
| Momentum_x_RelativeVolume | volume | Return_5D * Relative_Volume_20; trailing momentum weighted by volume participation | 20 | Yes | Yes |
| RSI_14 | technical | Wilder gain/loss averages seeded with first 14 changes; 100 for gain-only, 0 for loss-only, 50 if both zero | 15 | Yes | Yes |
| MACD_Pct | technical | (EMA_12 - EMA_26) / Close | 26 | Yes | Yes |
| MACD_Signal_Pct | technical | EMA_9(raw MACD) / Close | 34 | Yes | Yes |
| MACD_Histogram_Pct | technical | (raw MACD - raw signal) / Close | 34 | Yes | Yes |
| Bollinger_Position | technical | (Close - lower) / (upper - lower), bands=SMA_20 +/- 2 population std; flat=0.5 | 20 | Yes | Yes |
| Bollinger_Width | technical | (upper - lower) / SMA_20 | 20 | Yes | Yes |
| ATR_14_Pct | technical | Wilder mean of True Range / Close; first TR=High-Low; 14-TR arithmetic seed | 14 | Yes | Yes |


## Basic-only absolute moving averages

| Feature | Definition | Minimum raw rows | Normalized? |
|---|---|---|---|
| MA_5 | Unchanged baseline rolling mean(Close, 5); absolute adjusted price | 5 | No |
| MA_20 | Unchanged baseline rolling mean(Close, 20); absolute adjusted price | 20 | No |
| MA_50 | Unchanged baseline rolling mean(Close, 50); absolute adjusted price | 50 | No |

