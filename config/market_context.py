"""Explicit US context profiles; no automatic international or sector inference."""
from data.market_data import MarketDataError, normalize_ticker

SECTOR_MAPPING = {"AAPL": "XLK", "MSFT": "XLK", "JPM": "XLF"}
MAX_CONTEXT_AGE_DAYS = 4
SOURCES = {
    "SPY": "Broad US equity market ETF",
    "QQQ": "Growth/technology-heavy US equity ETF",
    "^VIX": "Cboe implied volatility index; Yahoo points, divided by 100 for level",
    "^TNX": "Yahoo 10-year Treasury yield proxy; percentage points, divided by 100",
    "XLK": "Technology sector ETF", "XLF": "Financial sector ETF"
}


def context_profile(ticker: str) -> dict:
    """Require a configured US equity; keep non-context modes universally separate."""
    ticker = normalize_ticker(ticker)
    if ticker not in SECTOR_MAPPING:
        raise MarketDataError(f"Market context profile is not configured for {ticker}. "
                              "Use basic, advanced, or advanced_temporal instead.")
    return dict(ticker=ticker, sector=SECTOR_MAPPING[ticker], market="SPY", growth="QQQ",
                volatility="^VIX", rates="^TNX", region="US",
                timing="After completed US equity close: exact-date ETF data; strictly prior-date VIX/TNX, maximum age 4 calendar days.")
