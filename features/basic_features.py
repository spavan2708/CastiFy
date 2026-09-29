"""Original V1 features and next-trading-row target."""
import pandas as pd


def build_basic_features(stock: pd.DataFrame) -> pd.DataFrame:
    """Return features on a copy; preserve missing warm-up and target rows."""
    stock = stock.copy()
    # Calculate daily percentage return
    stock["Daily_Return"] = stock["Close"].pct_change()
    
    # Add returns from previous trading days
    stock["Return_Lag_1"] = stock["Daily_Return"].shift(1)
    stock["Return_Lag_2"] = stock["Daily_Return"].shift(2)
    stock["Return_Lag_3"] = stock["Daily_Return"].shift(3)
    stock["Return_Lag_5"] = stock["Daily_Return"].shift(5)
    
    # Calculate moving averages including today's closing price
    stock["MA_5"] = stock["Close"].rolling(window=5).mean()
    stock["MA_20"] = stock["Close"].rolling(window=20).mean()
    stock["MA_50"] = stock["Close"].rolling(window=50).mean()
    
    # Calculate rolling daily volatility including today's return
    stock["Volatility_5"] = stock["Daily_Return"].rolling(window=5).std()
    stock["Volatility_20"] = stock["Daily_Return"].rolling(window=20).std()
    
    # Calculate percentage change from the previous trading day's volume
    stock["Volume_Change"] = stock["Volume"].pct_change()
    
    # Future target only: never include Tomorrow_Return in input features (X)
    stock["Tomorrow_Return"] = stock["Daily_Return"].shift(-1)
    
    return stock
