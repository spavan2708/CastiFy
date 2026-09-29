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
