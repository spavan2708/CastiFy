"""Explicit baseline dataset, purged holdout, and unchanged V3 forest."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from data.market_data import MarketDataError

from features.registry import BASIC_FEATURES, get_feature_columns

FEATURE_COLUMNS = BASIC_FEATURES.copy()
MIN_ML_OBSERVATIONS = 100


def prepare_ml_dataset(featured_data: pd.DataFrame, feature_set: str = "basic") -> tuple[pd.DataFrame, pd.Series]:
    """Select the requested explicit registry and target; remove required NaN rows."""
    columns = get_feature_columns(feature_set)
    data = featured_data[columns + ["Tomorrow_Return"]].dropna().copy()
    if len(data) < MIN_ML_OBSERVATIONS:
        raise MarketDataError("Insufficient historical data: need at least 100 usable ML rows.")
    # Zero preceding volume can cause infinite pct_change: do not impute it.
    if not np.isfinite(data.to_numpy()).all():
        raise MarketDataError("Non-finite ML values (possibly a percentage change from zero volume).")
    X = data[columns].copy()
    y = data["Tomorrow_Return"].copy()
    assert X.columns.tolist() == columns and X.shape[1] == len(columns)
    assert "Tomorrow_Return" not in X.columns
    assert X.index.equals(y.index) and len(X) == len(y)
    assert X.index.is_unique and X.index.is_monotonic_increasing
    return X, y


def chronological_split(X: pd.DataFrame, y: pd.Series,
                        trading_index: pd.DatetimeIndex) -> dict:
    """Split 80/20 and purge labels reaching the test feature-date boundary."""
    assert X.index.equals(y.index)
    assert trading_index.is_unique and trading_index.is_monotonic_increasing
    split_index = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_index].copy(), X.iloc[split_index:].copy()
    y_train, y_test = y.iloc[:split_index].copy(), y.iloc[split_index:].copy()
    assert len(X_train) and len(X_test)
    target_dates = trading_index.to_series().shift(-1).loc[X_train.index]
    assert target_dates.notna().all()
    keep = target_dates < X_test.index.min()
    removed = X_train.index[~keep]
    X_train, y_train = X_train.loc[keep].copy(), y_train.loc[keep].copy()
    assert len(X_train) and len(X_train) == len(y_train)
    assert len(X_test) == len(y_test)
    assert X_train.index.equals(y_train.index) and X_test.index.equals(y_test.index)
    assert X_train.index.max() < X_test.index.min()
    assert X_train.index.intersection(X_test.index).empty
    assert (target_dates.loc[keep] < X_test.index.min()).all()
    assert X_test.equals(X.iloc[split_index:]) and y_test.equals(y.iloc[split_index:])
    assert len(X_train) + len(X_test) + len(removed) == len(X)
    for part in (X_train, X_test, y_train, y_test):
        assert np.isfinite(part.to_numpy()).all()
    return dict(X_train=X_train, X_test=X_test, y_train=y_train, y_test=y_test,
                train_before=split_index, removed=removed,
                latest_train_target=target_dates.loc[keep].max())


def evaluate_baseline(split: dict, featured_data: pd.DataFrame, feature_set: str = "basic") -> dict:
    """Fit only purged training observations and evaluate the untouched holdout."""
    X_train, X_test = split["X_train"], split["X_test"]
    y_train, y_test = split["y_train"], split["y_test"]
    columns = get_feature_columns(feature_set)
    assert X_train.columns.tolist() == X_test.columns.tolist() == columns
    assert "Tomorrow_Return" not in columns
    assert X_train.index.max() < X_test.index.min()
    assert (featured_data.index.to_series().shift(-1).loc[X_train.index] < X_test.index.min()).all()
    model = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    assert len(y_pred) == len(y_test) and np.isfinite(y_pred).all()
    today_returns = featured_data.loc[X_test.index, "Daily_Return"]
    assert today_returns.index.equals(y_test.index)
    assert np.isfinite(today_returns.to_numpy()).all()
    zero = np.zeros(len(y_test))
    metrics = dict(
        mae=mean_absolute_error(y_test, y_pred),
        rmse=float(np.sqrt(mean_squared_error(y_test, y_pred))),
        r2=r2_score(y_test, y_pred),
        zero_mae=mean_absolute_error(y_test, zero),
        zero_rmse=float(np.sqrt(mean_squared_error(y_test, zero))),
        direction=float(np.mean(np.sign(y_pred) == np.sign(y_test.to_numpy()))),
        momentum=float(np.mean(np.sign(today_returns.to_numpy()) == np.sign(y_test.to_numpy())))
    )
    results = pd.DataFrame({"Actual_Return": y_test, "Predicted_Return": y_pred,
                            "Prediction_Error": y_test - y_pred}, index=X_test.index)
    assert len(results) == len(y_test) and results.index.equals(X_test.index)
    assert np.isfinite(results.to_numpy()).all()
    importance = pd.DataFrame({"Feature": columns,
                               "Importance": model.feature_importances_})
    return dict(metrics=metrics, results=results,
                importance=importance.sort_values("Importance", ascending=False))


def print_baseline_report(X: pd.DataFrame, split: dict, evaluation: dict) -> None:
    """Display dataset sizes, boundary dates, and factual baseline comparisons."""
    print(f"\nML observations: {len(X)}; features: {X.shape[1]}")
    print(f"ML dates: {X.index.min().date()} to {X.index.max().date()}")
    print(f"Training before purge: {split['train_before']}")
    print(f"Removed dates: {[d.date().isoformat() for d in split['removed']]}")
    print("Removed labels realize on or after the first test feature date.")
    for label, key in (("Training", "X_train"), ("Testing", "X_test")):
        part = split[key]
        print(f"{label}: {len(part)} rows; {part.index.min().date()} to {part.index.max().date()}")
    print(f"Latest training target: {split['latest_train_target'].date()}")
    m = evaluation["metrics"]
    for name in ("mae", "rmse", "zero_mae", "zero_rmse"):
        print(f"{name}: {m[name]:.8f} ({m[name]:.4%})")
    print(f"R²: {m['r2']:.6f}")
    print(f"Direction: {m['direction']:.4%}; momentum baseline: {m['momentum']:.4%}; reference: 50%")
    print(f"RF minus zero MAE: {m['mae'] - m['zero_mae']:+.8f}")
    print(f"RF minus zero RMSE: {m['rmse'] - m['zero_rmse']:+.8f}")
    print(evaluation["results"].head(10).to_string())
    print("Feature importance (not causation):")
    print(evaluation["importance"].to_string(index=False))
    print("All dataset, target-boundary, and prediction assertions: PASS")
