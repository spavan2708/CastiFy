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
