"""Explicit zero-denominator and historical smoothing conventions."""
import pandas as pd


def divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Leave undefined zero-denominator ratios missing, never substitute infinity."""
    return numerator / denominator.where(denominator != 0)


def wilder_average(values: pd.Series, window: int) -> pd.Series:
    """Seed with the first full arithmetic mean, then recur with alpha=1/window.

    Leading NaNs are allowed. Internal missing inputs are rejected: silently
    skipping them would change the meaning of the recurrence.
    """
    start = values.first_valid_index()
    if start is None:
        return values.copy()
    valid = values.loc[start:]
    if valid.isna().any():
        raise ValueError("Wilder smoothing requires contiguous valid observations.")
    seeded = values.astype(float).copy()
    seeded[:] = float("nan")
    if len(valid) >= window:
        seed_position = values.index.get_loc(start) + window - 1
        seeded.iloc[seed_position] = valid.iloc[:window].mean()
        seeded.iloc[seed_position + 1:] = values.iloc[seed_position + 1:]
    return seeded.ewm(alpha=1 / window, adjust=False, ignore_na=False).mean()
