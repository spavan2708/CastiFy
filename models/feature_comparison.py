"""Controlled basic/advanced diagnostics on identical raw data and holdout dates.

Run: python -m models.feature_comparison AAPL MSFT JPM
No model selection or tuning is performed.
"""
import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

from data.market_data import download_market_data
from features.feature_factory import build_feature_set
from features.registry import ADVANCED_FEATURES
from features.audit import audit_features
from models.baseline import prepare_ml_dataset, chronological_split, evaluate_baseline


def compare_feature_sets(stock: pd.DataFrame) -> dict:
    """Use common eligible rows, identical targets, and an identical purged split."""
    start = perf_counter()
    advanced = build_feature_set(stock, "advanced")
    feature_seconds = perf_counter() - start
    basic = build_feature_set(stock, "basic")
    Xa, ya = prepare_ml_dataset(advanced, "advanced")
    Xb, yb = prepare_ml_dataset(basic, "basic")
    common = Xa.index.intersection(Xb.index).sort_values()
    Xa, ya = Xa.loc[common], ya.loc[common]
    Xb, yb = Xb.loc[common], yb.loc[common]
    pd.testing.assert_series_equal(ya, yb)
    splits = {"basic": chronological_split(Xb, yb, stock.index),
              "advanced": chronological_split(Xa, ya, stock.index)}
    for key in ("X_train", "X_test", "y_train", "y_test"):
        assert splits["basic"][key].index.equals(splits["advanced"][key].index)
    for key in ("y_train", "y_test"):
        pd.testing.assert_series_equal(splits["basic"][key], splits["advanced"][key])
    audit = audit_features(splits["advanced"]["X_train"])
    full_audit = audit_features(Xa)
    if full_audit["exact_duplicates"] or audit["exact_duplicates"]:
        raise ValueError("Exact sample duplicate features detected; review registry before modelling.")
    # Independent dimensional check on the same ticker, not a fitted transformation.
    scaled = stock.copy()
    scaled[["Open", "High", "Low", "Close"]] *= 7
    scaled["Volume"] *= 11
    scaled_features = build_feature_set(scaled, "advanced")[ADVANCED_FEATURES]
    np.testing.assert_allclose(advanced[ADVANCED_FEATURES], scaled_features,
                               equal_nan=True, rtol=1e-6, atol=1e-6)
    evaluations = {
        "basic": evaluate_baseline(splits["basic"], basic, "basic"),
        "advanced": evaluate_baseline(splits["advanced"], advanced, "advanced")
    }
    for metric in ("zero_mae", "zero_rmse", "momentum"):
        assert evaluations["basic"]["metrics"][metric] == evaluations["advanced"]["metrics"][metric]
    valid_inputs = advanced[ADVANCED_FEATURES].notna().all(axis=1)
    first_valid = valid_inputs[valid_inputs].index[0]
    warmup = stock.index.get_loc(first_valid)
    split = splits["advanced"]
    return dict(
        raw_rows=len(stock), raw_start=str(stock.index.min().date()), raw_end=str(stock.index.max().date()),
        advanced_ml_rows=len(prepare_ml_dataset(advanced, "advanced")[0]),
        basic_ml_rows=len(prepare_ml_dataset(basic, "basic")[0]), common_rows=len(common),
        feature_count=len(ADVANCED_FEATURES), warmup_rows=warmup,
        other_removed_rows=len(stock) - warmup - len(Xa),
        train_rows=len(split["X_train"]), test_rows=len(split["X_test"]),
        train_start=str(split["X_train"].index.min().date()), train_end=str(split["X_train"].index.max().date()),
        test_start=str(split["X_test"].index.min().date()), test_end=str(split["X_test"].index.max().date()),
        purged_dates=[str(d.date()) for d in split["removed"]],
        latest_train_target=str(split["latest_train_target"].date()),
        feature_seconds=feature_seconds, scale_invariance="PASS",
        scale_max_abs_difference=float(np.nanmax(np.abs(advanced[ADVANCED_FEATURES].to_numpy() - scaled_features.to_numpy()))),
        scale_medians=Xa.abs().median().to_dict(),
        training_audit=audit, full_sample_audit=full_audit,
        basic=evaluations["basic"]["metrics"], advanced=evaluations["advanced"]["metrics"],
        top15=evaluations["advanced"]["importance"].head(15).to_dict(orient="records")
    )


def main() -> None:
    """Save diagnostic measurements without altering models or previous reports."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickers", nargs="+")
    parser.add_argument("--start", default="2010-01-01")
    parser.add_argument("--end", default=None)
    args = parser.parse_args()
    measurements = {}
    for ticker in args.tickers:
        print(f"Comparing {ticker} on one shared download...", flush=True)
        stock = download_market_data(ticker, args.start, args.end)
        result = compare_feature_sets(stock)
        result["requested_start"] = args.start
        result["effective_end_exclusive"] = stock.attrs["effective_end_exclusive"]
        measurements[ticker] = result
        print(json.dumps(result, indent=2), flush=True)
    destination = Path("reports/v5_experiments.json")
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(measurements, indent=2) + "\n")


if __name__ == "__main__":
    main()
