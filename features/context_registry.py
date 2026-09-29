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
