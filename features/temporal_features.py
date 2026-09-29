"""Exchange-neutral Gregorian context for completed session-date labels.

Known calendar endpoints are allowed; future downloaded rows are never consulted.
Dates are interpreted in the index's existing timezone, without UTC conversion.
"""
import numpy as np
import pandas as pd


def temporal_features(stock: pd.DataFrame) -> pd.DataFrame:
    """Build date-only inputs and a backward-looking observed-session gap.

    Weekend rows are explicitly unsupported in this Monday-Friday representation.
    Gaps measure observed dates, not certified exchange closures or missing bars.
    """
    index = stock.index
    if not isinstance(index, pd.DatetimeIndex) or index.hasnans:
        raise ValueError("Temporal features require valid datetime session labels.")
    dates = index.tz_localize(None).normalize()
    if not dates.is_monotonic_increasing or not dates.is_unique:
        raise ValueError("Temporal features require sorted, unique session dates.")
    if (dates.dayofweek > 4).any():
        raise ValueError("Weekend session dates are unsupported by the Monday-Friday temporal encoding.")
    output = {}
    for day, name in enumerate(("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")):
        output[f"DOW_{name}"] = (dates.dayofweek == day).astype(float)
    phases = {
        "Month": (dates.month - 1) / 12,
        "DayOfMonth": (dates.day - 1) / dates.days_in_month,
        "DayOfYear": (dates.dayofyear - 1) / np.where(dates.is_leap_year, 366, 365)
    }
    for name, phase in phases.items():
        output[f"{name}_Sin"] = np.sin(2 * np.pi * phase)
        output[f"{name}_Cos"] = np.cos(2 * np.pi * phase)
    month_start = dates.to_period("M").start_time
    month_end = dates.to_period("M").end_time.normalize()
    quarter_start = dates.to_period("Q-DEC").start_time
    quarter_end = dates.to_period("Q-DEC").end_time.normalize()
    output["Calendar_Days_From_Month_Start"] = (dates - month_start).days.astype(float)
    output["Calendar_Days_To_Month_End"] = (month_end - dates).days.astype(float)
    from_quarter = (dates - quarter_start).days
    to_quarter = (quarter_end - dates).days
    output["Calendar_Days_From_Quarter_Start"] = from_quarter.astype(float)
    output["Calendar_Days_To_Quarter_End"] = to_quarter.astype(float)
    output["Is_Quarter_Start_Region"] = (from_quarter < 7).astype(float)
    output["Is_Quarter_End_Region"] = (to_quarter < 7).astype(float)
    output["Calendar_Days_Since_Previous_Session"] = pd.Series(dates, index=index).diff().dt.days
    result = pd.DataFrame(output, index=index)
    assert (result.iloc[:, :5].sum(axis=1) == 1).all()
    return result
