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
