"""Reusable validated context bundles and explicit availability alignment."""
from datetime import datetime, timezone
import pandas as pd
import yfinance as yf

from config.market_context import SOURCES, MAX_CONTEXT_AGE_DAYS, context_profile
from data.market_data import MarketDataError, download_market_data, standardize_columns, validate_market_data


def download_context_series(symbol: str, start: str, end: str | None = None) -> pd.DataFrame:
    """Reuse V4 ingestion for ETFs; handle empty Yahoo index quote placeholders.

    For VIX/TNX only, remove rows where every OHLC is missing and volume is zero
    or missing. Record the dates, never impute them. Partial bad rows still fail
    the unchanged V4 validator. All retained timestamps are provider originals.
    """
    if symbol not in ("^VIX", "^TNX"):
        return download_market_data(symbol, start, end)
    today = datetime.now(timezone.utc).date().isoformat()
    try:
        begin = pd.Timestamp(start)
        finish = min(pd.Timestamp(end or today), pd.Timestamp(today))
        if pd.isna(begin) or pd.isna(finish) or begin >= finish:
            raise ValueError("Start must precede completed-data cutoff.")
    except (TypeError, ValueError) as error:
        raise MarketDataError(f"Invalid context date range: {error}") from error
    raw = yf.download(symbol, start=begin.date().isoformat(), end=finish.date().isoformat(),
                      interval="1d", auto_adjust=True, keepna=True, progress=False, threads=False)
    data = standardize_columns(raw, symbol)
    placeholders = data[["Open", "High", "Low", "Close"]].isna().all(axis=1) & (data.Volume.isna() | data.Volume.eq(0))
    removed = [str(date.date()) for date in data.index[placeholders]]
    clean = data.loc[~placeholders].copy()
    validate_market_data(clean)
    clean.attrs.update(effective_end_exclusive=finish.date().isoformat(),
                       provider_rows=len(data), empty_quote_dates=removed)
    return clean


class ContextCache:
    """Small per-run cache keyed by symbol and requested date range."""
    def __init__(self):
        self.frames = {}
        self.logical_requests = 0
        self.provider_downloads = 0

    def get(self, symbol: str, start: str, end: str | None) -> pd.DataFrame:
        """Reuse the V4 standardized, adjusted, finite OHLCV download contract."""
        self.logical_requests += 1
        key = (symbol, start, end)
        if key not in self.frames:
            self.provider_downloads += 1
            try:
                self.frames[key] = download_context_series(symbol, start, end)
            except MarketDataError as error:
                raise MarketDataError(f"Required context source {symbol} failed: {error} "
                                      "Context mode cannot proceed. Basic, advanced and advanced_temporal remain available.") from error
        return self.frames[key].copy()


def download_context_bundle(ticker: str, start: str, end: str | None = None,
                            cache: ContextCache | None = None) -> dict:
    """Fetch a profile's five required sources; never silently omit a failed source."""
    profile = context_profile(ticker)
    cache = cache if cache is not None else ContextCache()
    symbols = [profile[k] for k in ("market", "growth", "volatility", "rates", "sector")]
    series = {symbol: cache.get(symbol, start, end) for symbol in symbols}
    return dict(profile=profile, series=series, requested_start=start, requested_end=end)


def validate_daily_index(index: pd.Index) -> None:
    """Require unambiguous US daily session labels; do not silently convert timezones."""
    if (not isinstance(index, pd.DatetimeIndex) or index.hasnans or index.tz is not None
            or not index.is_unique or not index.is_monotonic_increasing
            or not index.equals(index.normalize())):
        raise MarketDataError("Context alignment requires unique sorted timezone-naive midnight session dates.")


def align_previous(values: pd.DataFrame, dates: pd.DatetimeIndex) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Strict backward as-of, not same-date; reject values older than four days.

    Preserve source dates and diagnostic ages even when rejecting stale values.
    Never search backwards for a non-NaN feature: the newest source row controls.
    """
    validate_daily_index(values.index)
    validate_daily_index(dates)
    left = pd.DataFrame({"Stock_Date": dates})
    right = values.rename_axis("Source_Date").reset_index()
    joined = pd.merge_asof(left, right, left_on="Stock_Date", right_on="Source_Date",
                           direction="backward", allow_exact_matches=False)
    joined.index = dates
    age = (joined.Stock_Date - joined.Source_Date).dt.days
    usable = age.between(1, MAX_CONTEXT_AGE_DAYS)
    aligned = joined[values.columns].where(usable, axis=0)
    diagnostics = pd.DataFrame({"Source_Date": joined.Source_Date, "Age_Days": age,
                                "Usable": usable}, index=dates)
    assert (diagnostics.loc[usable, "Source_Date"] < dates[usable]).all()
    return aligned, diagnostics


def context_data_report(stock: pd.DataFrame, bundle: dict) -> list[dict]:
    """Report actual ranges, exact-date misses and bounded previous-date ages."""
    reports = []
    for symbol, frame in bundle["series"].items():
        item = dict(symbol=symbol, purpose=SOURCES.get(symbol, "Configured context source"),
                    requested_start=bundle["requested_start"], requested_end=bundle["requested_end"],
                    actual_start=str(frame.index.min().date()), actual_end=str(frame.index.max().date()),
                    observations=len(frame), missing_values=int(frame.isna().sum().sum()),
                    duplicate_dates=int(frame.index.duplicated().sum()), validation="PASS (V4 validated)",
                    auto_adjust=True, provider_rows=frame.attrs.get("provider_rows",len(frame)),
                    empty_quote_dates=frame.attrs.get("empty_quote_dates",[]), same_date_missing=int((~stock.index.isin(frame.index)).sum()))
        if symbol in (bundle["profile"]["volatility"], bundle["profile"]["rates"]):
            _, diagnostics = align_previous(frame[["Close"]], stock.index)
            item.update(alignment="Strictly previous date; max age 4 calendar days",
                        unavailable_rows=int((~diagnostics.Usable).sum()),
                        stale_rows=int((diagnostics.Age_Days > MAX_CONTEXT_AGE_DAYS).sum()),
                        max_accepted_age=float(diagnostics.loc[diagnostics.Usable, "Age_Days"].max()))
        else:
            item["alignment"] = "Exact stock date; missing stays NaN, no fill"
        reports.append(item)
    return reports
