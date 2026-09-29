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
