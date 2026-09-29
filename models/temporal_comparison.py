"""V6 family ablation and descriptive profiles; never target-encode calendars.

Run: python -m models.temporal_comparison AAPL MSFT JPM
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from data.market_data import download_market_data, normalize_ticker
from features.audit import audit_features
from features.feature_factory import build_feature_set
from features.registry import ADVANCED_FEATURES, ADVANCED_TEMPORAL_FEATURES, TEMPORAL_FEATURES
from models.baseline import chronological_split, evaluate_baseline, prepare_ml_dataset


def return_profiles(featured: pd.DataFrame) -> dict:
    """Summarize historical same-session Daily_Return, for reporting only.

    These full-history descriptive tables are never merged into model inputs and
    never used as training targets, fitted encodings, or persistent market laws.
    """
    returns = featured["Daily_Return"].dropna()
    tables = {}
    for label, groups in (("weekday", returns.index.dayofweek), ("month", returns.index.month)):
        summary = returns.groupby(groups).agg(
            count="count", mean="mean", median="median", std="std",
            positive_fraction=lambda values: float((values > 0).mean())
        )
        summary.index.name = label
        if label == "weekday":
            summary.index = summary.index.map(dict(enumerate(
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])))
        tables[label] = summary.reset_index().to_dict(orient="records")
    return tables


def verify_calendar_causality(stock: pd.DataFrame, full: pd.DataFrame) -> list[dict]:
    """Check all inputs on three historical prefixes and future OHLCV perturbations."""
    checks = []
    for cutoff in ("2015-06-15", "2015-06-30", "2015-12-31"):
        if not (stock.index.min() <= pd.Timestamp(cutoff) < stock.index.max()):
            checks.append(dict(cutoff=cutoff, result="outside downloaded range"))
            continue
        expected = full.loc[:cutoff, ADVANCED_TEMPORAL_FEATURES]
        prefix = build_feature_set(stock.loc[:cutoff], "advanced_temporal")
        pd.testing.assert_frame_equal(expected, prefix[ADVANCED_TEMPORAL_FEATURES], check_exact=True)
        changed = stock.copy()
        future = changed.index > cutoff
        changed.loc[future, ["Open", "High", "Low", "Close"]] *= 3
        changed.loc[future, "Volume"] *= 7
        perturbed = build_feature_set(changed, "advanced_temporal")
        pd.testing.assert_frame_equal(expected, perturbed.loc[:cutoff, ADVANCED_TEMPORAL_FEATURES], check_exact=True)
        checks.append(dict(cutoff=cutoff, prefix="PASS", perturbation="PASS"))
    return checks


def compare_temporal_family(stock: pd.DataFrame) -> dict:
    """Compare the same forest with and without calendar inputs on identical dates."""
    advanced = build_feature_set(stock, "advanced")
    temporal = build_feature_set(stock, "advanced_temporal")
    pd.testing.assert_frame_equal(advanced, temporal[advanced.columns])
    Xa, ya = prepare_ml_dataset(advanced, "advanced")
    Xt, yt = prepare_ml_dataset(temporal, "advanced_temporal")
    common = Xa.index.intersection(Xt.index).sort_values()
    Xa, ya, Xt, yt = Xa.loc[common], ya.loc[common], Xt.loc[common], yt.loc[common]
    pd.testing.assert_series_equal(ya, yt)
    pd.testing.assert_frame_equal(Xa, Xt[ADVANCED_FEATURES])
    splits = {"advanced": chronological_split(Xa, ya, stock.index),
              "advanced_temporal": chronological_split(Xt, yt, stock.index)}
    a, t = splits["advanced"], splits["advanced_temporal"]
    for name in ("X_train", "X_test", "y_train", "y_test"):
        assert a[name].index.equals(t[name].index)
    for name in ("y_train", "y_test"):
        pd.testing.assert_series_equal(a[name], t[name])
    assert a["removed"].equals(t["removed"])
    train_audit = audit_features(t["X_train"])
    full_audit = audit_features(Xt)
    temporal_audit = audit_features(t["X_train"][TEMPORAL_FEATURES])
    if train_audit["exact_duplicates"] or full_audit["exact_duplicates"]:
        raise ValueError("Exact duplicate sample inputs require review before this diagnostic.")
    causal_checks = verify_calendar_causality(stock, temporal)
    scaled = stock.copy()
    scaled[["Open", "High", "Low", "Close"]] *= 7
    scaled["Volume"] *= 11
    rebuilt = build_feature_set(scaled, "advanced_temporal")
    pd.testing.assert_frame_equal(temporal[TEMPORAL_FEATURES], rebuilt[TEMPORAL_FEATURES], check_exact=True)
    np.testing.assert_allclose(temporal[ADVANCED_TEMPORAL_FEATURES], rebuilt[ADVANCED_TEMPORAL_FEATURES],
                               equal_nan=True, rtol=1e-6, atol=1e-6)
    evaluations = {
        "advanced": evaluate_baseline(a, advanced, "advanced"),
        "advanced_temporal": evaluate_baseline(t, temporal, "advanced_temporal")
    }
    before, after = evaluations["advanced"]["metrics"], evaluations["advanced_temporal"]["metrics"]
    for metric in ("zero_mae", "zero_rmse", "momentum"):
        assert before[metric] == after[metric]
    importance = evaluations["advanced_temporal"]["importance"]
    temporal_importance = importance[importance.Feature.isin(TEMPORAL_FEATURES)]
    profiles = return_profiles(advanced)
    return dict(
        raw_rows=len(stock), raw_start=str(stock.index.min().date()), raw_end=str(stock.index.max().date()),
        eligible_rows=len(common), eligible_start=str(common.min().date()), eligible_end=str(common.max().date()),
        advanced_count=len(ADVANCED_FEATURES), temporal_count=len(TEMPORAL_FEATURES), combined_count=len(ADVANCED_TEMPORAL_FEATURES),
        train_before=t["train_before"], train_rows=len(t["X_train"]), test_rows=len(t["X_test"]),
        train_start=str(t["X_train"].index.min().date()), train_end=str(t["X_train"].index.max().date()),
        test_start=str(t["X_test"].index.min().date()), test_end=str(t["X_test"].index.max().date()),
        purged_dates=[str(d.date()) for d in t["removed"]], latest_train_target=str(t["latest_train_target"].date()),
        identical_dates="PASS", advanced_unchanged="PASS", all_matrices_finite="PASS",
        advanced=before, advanced_temporal=after,
        deltas={metric: after[metric] - before[metric] for metric in ("mae", "rmse", "r2", "direction")},
        temporal_importance_total=float(temporal_importance.Importance.sum()),
        temporal_importances=temporal_importance.to_dict(orient="records"),
        top20=importance.head(20).to_dict(orient="records"),
        weekday_profile=profiles["weekday"], month_profile=profiles["month"],
        training_audit=train_audit, full_sample_audit=full_audit, temporal_training_audit=temporal_audit,
        causality_checks=causal_checks, temporal_scale_invariance="PASS", combined_scale_invariance="PASS"
    )


def main() -> None:
    """Save V6-only artifacts; leave historical V3/V4/V5 results untouched."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickers", nargs="+")
    parser.add_argument("--start", default="2010-01-01")
    parser.add_argument("--end", default=None)
    args = parser.parse_args()
    measurements = {}
    for raw_ticker in args.tickers:
        ticker = normalize_ticker(raw_ticker)
        print(f"V6 temporal ablation for {ticker}...", flush=True)
        stock = download_market_data(ticker, args.start, args.end)
        result = compare_temporal_family(stock)
        result["effective_end_exclusive"] = stock.attrs["effective_end_exclusive"]
        result["requested_start"] = args.start
        measurements[ticker] = result
        print(json.dumps(result, indent=2), flush=True)
    Path("reports").mkdir(exist_ok=True)
    Path("reports/v6_experiments.json").write_text(json.dumps(measurements, indent=2) + "\n")


if __name__ == "__main__":
    main()
