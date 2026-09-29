"""Documented RSI, MACD, Bollinger and Wilder ATR conventions."""
import pandas as pd
from features.numerics import divide, wilder_average


def technical_features(stock: pd.DataFrame) -> pd.DataFrame:
    """Compute normalized technical indicators without future initialization."""
    c, h, low = (stock[name] for name in ("Close", "High", "Low"))
    delta = c.diff()
    gain = wilder_average(delta.clip(lower=0), 14)
    loss = wilder_average(-delta.clip(upper=0), 14)
    rsi = 100 - 100 / (1 + divide(gain, loss))
    rsi = rsi.mask((loss == 0) & (gain > 0), 100).mask((gain == 0) & (loss == 0), 50)
    macd = c.ewm(span=12, adjust=False, min_periods=12).mean() - c.ewm(span=26, adjust=False, min_periods=26).mean()
    signal = macd.ewm(span=9, adjust=False, min_periods=9).mean()
    middle, std = c.rolling(20).mean(), c.rolling(20).std(ddof=0)
    width = 4 * std
    position = divide(c - (middle - 2 * std), width).mask(width == 0, .5)
    tr = pd.concat([h - low, (h - c.shift(1)).abs(), (low - c.shift(1)).abs()], axis=1).max(axis=1)
    atr = wilder_average(tr, 14)
    return pd.DataFrame({
        "RSI_14": rsi, "MACD_Pct": divide(macd, c),
        "MACD_Signal_Pct": divide(signal, c), "MACD_Histogram_Pct": divide(macd - signal, c),
        "Bollinger_Position": position, "Bollinger_Width": divide(width, middle),
        "ATR_14_Pct": divide(atr, c)
    }, index=stock.index)
