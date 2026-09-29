"""Date-aligned market, sector, VIX and rate features without future observations."""
import numpy as np
import pandas as pd

from data.market_data import MarketDataError
from data.context_data import align_previous, validate_daily_index
from features.context_registry import CONTEXT_FEATURES
from features.numerics import divide


def _return(close: pd.Series, n: int) -> pd.Series:
    """Full stock-grid window prevents missing dates becoming unequal return spans."""
    return (divide(close, close.shift(n)) - 1).where(close.rolling(n+1).count() == n+1)


def context_features(stock: pd.DataFrame, bundle: dict) -> pd.DataFrame:
    """Keep the stock index intact; missing context removes ML rows, never target rows.

    ETF closes are first reindexed to actual stock dates, with no filling, before
    trailing computations. VIX/rates use native trailing windows then strict-prior
    as-of alignment capped at four calendar days. Unknown source vintages are not
    represented as historically verified publication timestamps.
    """
    validate_daily_index(stock.index)
    profile, sources = bundle["profile"], bundle["series"]
    for key in ("market", "growth", "sector", "volatility", "rates"):
        symbol = profile[key]
        if symbol not in sources:
            raise MarketDataError(f"Required context source {symbol} missing. Context mode cannot proceed; non-context modes remain available.")
        frame = sources[symbol]
        validate_daily_index(frame.index)
        if "Close" not in frame or frame.empty or not np.isfinite(frame.Close).all() or not (frame.Close>0).all():
            raise MarketDataError(f"Invalid required context Close data for {symbol}.")
    stock_close = stock.Close
    stock_return = stock_close.pct_change(fill_method=None)
    output, returns, vols = {}, {}, {}
    for label,key in (("SPY","market"),("QQQ","growth"),("Sector","sector")):
        close = sources[profile[key]].Close.reindex(stock.index)
        returns[label] = {n:_return(close,n) for n in (1,5,20)}
        output.update({f"{label}_Return_{n}D":values for n,values in returns[label].items()})
        for n in ((20,50,200) if label=="SPY" else (20,50) if label=="QQQ" else (20,)):
            output[f"{label}_Price_to_SMA_{n}"] = divide(close,close.rolling(n).mean())-1
        vols[label] = {}
        for n in ((5,20,60) if label=="SPY" else (20,) if label=="Sector" else ()):
            vols[label][n] = returns[label][1].rolling(n).std()
            output[f"{label}_Volatility_{n}"] = vols[label][n]
    output["SPY_Volatility_Ratio_5_20"] = divide(vols["SPY"][5],vols["SPY"][20].where(vols["SPY"][20]>1e-12))
    for label,n in (("SPY",5),("SPY",20),("Sector",5),("Sector",20),("QQQ",20)):
        output[f"Stock_vs_{label}_Return_{n}D"] = _return(stock_close,n)-returns[label][n]
    for label in ("SPY","Sector"):
        market = returns[label][1]
        for n in (20,60):
            corr = stock_return.rolling(n).corr(market)
            usable = (stock_return.rolling(n).std()>1e-12) & (market.rolling(n).std()>1e-12)
            output[f"Stock_{label}_Correlation_{n}"] = corr.where(usable).clip(-1,1)
    for n in (20,60):
        variance = returns["SPY"][1].rolling(n).var(ddof=1)
        output[f"Stock_SPY_Beta_{n}"] = divide(stock_return.rolling(n).cov(returns["SPY"][1],ddof=1),variance.where(variance>1e-12))
    output["Market_Adjusted_Return_1D"] = stock_return-returns["SPY"][1]
    output["Sector_Adjusted_Return_1D"] = stock_return-returns["Sector"][1]
    for label in ("SPY","Sector"):
        output[f"Stock_to_{label}_Volatility_20"] = divide(stock_return.rolling(20).std(),vols[label][20].where(vols[label][20]>1e-12))
    vix = sources[profile["volatility"]].Close
    vix_native = pd.DataFrame({
        "VIX_Level_Normalized":vix/100, "VIX_Return_1D":vix.pct_change(fill_method=None),
        "VIX_Return_5D":vix.pct_change(5,fill_method=None),
        "VIX_Price_to_SMA_20":divide(vix,vix.rolling(20).mean())-1,
        "VIX_Percentile_252":vix.rolling(252).rank(method="average",pct=True)
    })
    rates = sources[profile["rates"]].Close
    rate_native = pd.DataFrame({
        "Treasury_10Y_Level":rates/100, "Treasury_10Y_Change_1D":rates.diff()/100,
        "Treasury_10Y_Change_5D":rates.diff(5)/100,
        "Treasury_10Y_vs_MA_20":(rates-rates.rolling(20).mean())/100
    })
    vix_aligned,_ = align_previous(vix_native,stock.index)
    rates_aligned,_ = align_previous(rate_native,stock.index)
    result = pd.concat([pd.DataFrame(output,index=stock.index),vix_aligned,rates_aligned],axis=1)[CONTEXT_FEATURES]
    if np.isinf(result.to_numpy()).any():
        raise MarketDataError("Context features contain infinity; cannot fit context mode.")
    return result
