"""Single-symbol Yahoo ingestion with a validated, flat OHLCV schema."""
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf

COLUMNS = ["Open", "High", "Low", "Close", "Volume"]
MIN_OBSERVATIONS = 150


class MarketDataError(ValueError):
    """Expected unavailable, invalid, or insufficient market data."""


def normalize_ticker(ticker: str) -> str:
    """Normalize one symbol without rejecting Yahoo-compatible punctuation."""
    symbol = ticker.strip().upper()
    if not symbol or any(c.isspace() for c in symbol) or "," in symbol:
        raise MarketDataError("Enter one nonempty Yahoo Finance ticker.")
    return symbol


def standardize_columns(raw: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Resolve either Yahoo MultiIndex orientation without mixing symbols."""
    if raw is None or raw.empty:
        raise MarketDataError(f'Unable to retrieve usable market data for "{ticker}". '
                              'Check the ticker symbol or data availability.')
    data = raw.copy()
    if isinstance(data.columns, pd.MultiIndex):
        if data.columns.nlevels != 2:
            raise MarketDataError("Unexpected Yahoo column structure.")
        for level in (0, 1):
            if set(COLUMNS).issubset(data.columns.get_level_values(level)):
                symbol_level = 1 - level
                symbols = data.columns.get_level_values(symbol_level).unique()
                if len(symbols) != 1 or symbols[0] != ticker:
                    raise MarketDataError("Download did not contain exactly the requested symbol.")
                data.columns = data.columns.get_level_values(level)
                break
        else:
            raise MarketDataError("Required OHLCV columns are missing.")
    if not data.columns.is_unique or not set(COLUMNS).issubset(data.columns):
        raise MarketDataError("Required unique OHLCV columns are missing.")
    return data[COLUMNS].copy()


def validate_market_data(data: pd.DataFrame) -> None:
    """Reject bad observations rather than filling or silently deleting them."""
    if data.empty or not set(COLUMNS).issubset(data.columns) or not data.columns.is_unique:
        raise MarketDataError("Market data is empty or missing unique OHLCV columns.")
    if not isinstance(data.index, pd.DatetimeIndex) or data.index.hasnans:
        raise MarketDataError("Market data requires valid datetime dates.")
    if not data.index.is_monotonic_increasing or not data.index.is_unique:
        raise MarketDataError("Market dates must be ascending and unique.")
    if not all(pd.api.types.is_numeric_dtype(data[c]) for c in COLUMNS):
        raise MarketDataError("OHLCV values must be numeric.")
    if not np.isfinite(data[COLUMNS].to_numpy(dtype=float)).all():
        raise MarketDataError("OHLCV contains missing or non-finite values.")
    if not (data[COLUMNS[:4]] > 0).all().all():
        raise MarketDataError("All OHLC prices must be positive.")
    if not (data["Volume"] >= 0).all():
        raise MarketDataError("Volume must be non-negative.")
    if len(data) < MIN_OBSERVATIONS:
        raise MarketDataError(f"Insufficient historical data for CastiFy's baseline forecasting "
                              f"pipeline: {len(data)} rows; need {MIN_OBSERVATIONS}.")


def download_market_data(ticker: str, start_date: str,
                         end_date: str | None = None) -> pd.DataFrame:
    """Download adjusted daily OHLCV; exclude today's potentially partial bar.

    End dates are exclusive. None resolves to today's UTC date, conservatively
    omitting today even if that exchange's session has already completed.
    """
    ticker = normalize_ticker(ticker)
    today = datetime.now(timezone.utc).date().isoformat()
    try:
        start = pd.Timestamp(start_date)
        end = pd.Timestamp(end_date or today)
        cutoff = min(end, pd.Timestamp(today))
        if pd.isna(start) or pd.isna(end) or start >= cutoff:
            raise ValueError("Start must precede the completed-data cutoff.")
    except (ValueError, TypeError) as error:
        raise MarketDataError(f"Invalid date range: {error}") from error
    # yf.download handles provider/network failures by returning empty data.
    raw = yf.download(ticker, start=start.date().isoformat(),
                      end=cutoff.date().isoformat(), interval="1d",
                      auto_adjust=True, keepna=True, progress=False, threads=False)
    data = standardize_columns(raw, ticker)
    validate_market_data(data)
    data.attrs["effective_end_exclusive"] = cutoff.date().isoformat()
    return data


def print_data_report(data: pd.DataFrame, ticker: str, start_date: str,
                      end_date: str | None) -> None:
    """Print quality results calculated from a validated dataframe."""
    validate_market_data(data)
    print("\nCASTIFY DATA REPORT")
    print(f"Ticker: {normalize_ticker(ticker)}")
    print(f"Requested start: {start_date}; requested end: {end_date}")
    print(f"Effective exclusive end: {data.attrs.get('effective_end_exclusive')}")
    print(f"Actual dates: {data.index.min().date()} to {data.index.max().date()}")
    print(f"Trading observations: {len(data)}; columns: {list(data.columns)}")
    print(f"Duplicate dates: {data.index.duplicated().sum()}")
    print(f"Missing values: {data.isna().sum().to_dict()}")
    print("Price / volume / chronological / minimum-history validation: PASS")
    print("Overall: PASS; auto_adjust=True (adjusted OHLC; provider volume).")
