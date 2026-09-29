"""Select the historical basic baseline or the explicit V5 advanced feature set."""
import numpy as np
import pandas as pd
from features.basic_features import build_basic_features
from features.temporal_features import temporal_features
from features.context_features import context_features
from data.market_data import MarketDataError
from features.registry import get_feature_columns
from features.price_features import price_features
from features.momentum_features import momentum_features
from features.volatility_features import volatility_features
from features.volume_features import volume_features
from features.technical_features import technical_features


def build_feature_set(stock: pd.DataFrame, feature_set: str = "advanced", context_bundle: dict | None = None) -> pd.DataFrame:
    """Build on a copy. Preserve warm-up NaNs and isolate the unchanged future target."""
    columns = get_feature_columns(feature_set)
    featured = build_basic_features(stock)
    if feature_set in ("advanced", "advanced_temporal", "advanced_temporal_context"):
        for builder in (price_features, momentum_features, volatility_features,
                        volume_features, technical_features):
            block = builder(stock)
            featured[block.columns] = block
        if feature_set in ("advanced_temporal", "advanced_temporal_context"):
            column_name = featured.columns.name
            featured = pd.concat([featured, temporal_features(stock)], axis=1)
            featured.columns.name = column_name
        if feature_set == "advanced_temporal_context":
            if context_bundle is None:
                raise MarketDataError("Context mode requires an explicitly configured context bundle.")
            column_name = featured.columns.name
            featured = pd.concat([featured, context_features(stock, context_bundle)], axis=1)
            featured.columns.name = column_name
        if np.isinf(featured[columns].to_numpy()).any():
            raise ValueError("Advanced feature generation produced infinity; inspect raw inputs.")
    assert "Tomorrow_Return" not in columns
    assert featured.index.equals(stock.index)
    return featured
