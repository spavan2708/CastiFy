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
