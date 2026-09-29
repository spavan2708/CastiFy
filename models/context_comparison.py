"""Untuned V7 context-family ablation on identical stock dates and targets.

Run: python -m models.context_comparison AAPL MSFT JPM
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from data.market_data import download_market_data, normalize_ticker
from data.context_data import ContextCache, download_context_bundle, context_data_report, align_previous
from features.feature_factory import build_feature_set
from features.registry import ADVANCED_TEMPORAL_FEATURES, ADVANCED_TEMPORAL_CONTEXT_FEATURES
from features.context_registry import CONTEXT_FEATURES
from features.audit import audit_features
from models.baseline import prepare_ml_dataset, chronological_split, evaluate_baseline


def verify_causality(stock: pd.DataFrame, bundle: dict, full: pd.DataFrame) -> list[dict]:
    """Independent stock/context perturbations and joint history truncation."""
    checks=[]
    for cutoff in ("2015-06-15","2015-06-30","2015-12-31"):
        if not stock.index.min() <= pd.Timestamp(cutoff) < stock.index.max():
            checks.append(dict(cutoff=cutoff,status="outside sample"))
            continue
        expected=full.loc[:cutoff,ADVANCED_TEMPORAL_CONTEXT_FEATURES]
        for kind in ("stock","context","prefix"):
            raw=stock.copy()
            b=dict(bundle,series={k:v.copy() for k,v in bundle["series"].items()})
            if kind=="stock":
                raw.loc[raw.index>cutoff,:]*=2
            elif kind=="context":
                for frame in b["series"].values():
                    frame.loc[frame.index>cutoff,:]*=3
            else:
                raw=raw.loc[:cutoff]
                b["series"]={k:v.loc[:cutoff] for k,v in b["series"].items()}
            built=build_feature_set(raw,"advanced_temporal_context",b)
            pd.testing.assert_frame_equal(expected,built.loc[:cutoff,ADVANCED_TEMPORAL_CONTEXT_FEATURES],check_exact=True)
        checks.append(dict(cutoff=cutoff,stock_perturbation="PASS",context_perturbation="PASS",prefix="PASS"))
    return checks


def descriptive_context(featured: pd.DataFrame) -> dict:
    """Historical descriptions only: these aggregates never enter model inputs."""
    pairs=featured[["Daily_Return","SPY_Return_1D","Sector_Return_1D"]].dropna()
    v=featured[["Daily_Return","VIX_Percentile_252"]].dropna()
    groups={}
    for label,mask in (("low_trailing_vix",v.VIX_Percentile_252<=.25),
                       ("high_trailing_vix",v.VIX_Percentile_252>=.75)):
        rows=v.loc[mask,"Daily_Return"]
        groups[label]=dict(count=len(rows),mean=float(rows.mean()))
    return dict(paired_return_rows=len(pairs),stock_spy_correlation=float(pairs.Daily_Return.corr(pairs.SPY_Return_1D)),
                stock_sector_correlation=float(pairs.Daily_Return.corr(pairs.Sector_Return_1D)),
                vix_environments=groups,note="Reporting only; prior-date trailing VIX percentile thresholds 0.25/0.75; no causal claims.")


def compare_context(stock: pd.DataFrame, bundle: dict) -> dict:
    """Align common eligible dates before either split; hold all model settings fixed."""
    old=build_feature_set(stock,"advanced_temporal")
    full=build_feature_set(stock,"advanced_temporal_context",bundle)
    pd.testing.assert_frame_equal(old,full[old.columns])
    Xa,ya=prepare_ml_dataset(old,"advanced_temporal")
    Xb,yb=prepare_ml_dataset(full,"advanced_temporal_context")
    context_eligible=len(Xb)
    common=Xa.index.intersection(Xb.index).sort_values()
    Xa,ya,Xb,yb=Xa.loc[common],ya.loc[common],Xb.loc[common],yb.loc[common]
    pd.testing.assert_series_equal(ya,yb)
    pd.testing.assert_frame_equal(Xa,Xb[ADVANCED_TEMPORAL_FEATURES])
    a=chronological_split(Xa,ya,stock.index)
    b=chronological_split(Xb,yb,stock.index)
    for key in ("X_train","X_test","y_train","y_test"):
        assert a[key].index.equals(b[key].index)
    for key in ("y_train","y_test"):
        pd.testing.assert_series_equal(a[key],b[key])
    assert a["removed"].equals(b["removed"])
    train_audit=audit_features(b["X_train"])
    full_audit=audit_features(Xb)
    if train_audit["exact_duplicates"] or full_audit["exact_duplicates"]:
        raise ValueError("Exact duplicates detected in context inputs; review before diagnostic fitting.")
    causal=verify_causality(stock,bundle,full)
    scaled=stock.copy()
    scaled[["Open","High","Low","Close"]]*=7
    scaled["Volume"]*=11
    scaled_bundle=dict(bundle,series={k:v.copy() for k,v in bundle["series"].items()})
    for key,factor in (("market",3),("growth",5),("sector",9)):
        scaled_bundle["series"][bundle["profile"][key]][["Open","High","Low","Close"]]*=factor
    for f in scaled_bundle["series"].values(): f["Volume"]*=13
    scaled_features=build_feature_set(scaled,"advanced_temporal_context",scaled_bundle)
    np.testing.assert_allclose(full[ADVANCED_TEMPORAL_CONTEXT_FEATURES],scaled_features[ADVANCED_TEMPORAL_CONTEXT_FEATURES],equal_nan=True,rtol=1e-6,atol=1e-6)
    print("Alignment, finite matrices, causality, scale and duplicate checks: PASS. Fitting two unchanged forests...",flush=True)
    first=evaluate_baseline(a,old,"advanced_temporal")
    second=evaluate_baseline(b,full,"advanced_temporal_context")
    before,after=first["metrics"],second["metrics"]
    for metric in ("zero_mae","zero_rmse","momentum"):
        assert before[metric]==after[metric]
    importance=second["importance"]
    context_importance=importance[importance.Feature.isin(CONTEXT_FEATURES)]
    return dict(
        profile=bundle["profile"],source_reports=context_data_report(stock,bundle),
        raw_rows=len(stock),raw_start=str(stock.index.min().date()),raw_end=str(stock.index.max().date()),
        context_eligible_rows=context_eligible,common_rows=len(common),feature_count=len(Xb.columns),
        common_start=str(common.min().date()),common_end=str(common.max().date()),
        train_before=b["train_before"],train_rows=len(b["X_train"]),test_rows=len(b["X_test"]),
        train_start=str(b["X_train"].index.min().date()),train_end=str(b["X_train"].index.max().date()),
        test_start=str(b["X_test"].index.min().date()),test_end=str(b["X_test"].index.max().date()),
        purged_dates=[str(d.date()) for d in b["removed"]],latest_training_target=str(b["latest_train_target"].date()),
        temporal=before,context=after,deltas={m:after[m]-before[m] for m in ("mae","rmse","r2","direction")},
        context_importance_total=float(context_importance.Importance.sum()),
        context_importances=context_importance.to_dict(orient="records"),top25=importance.head(25).to_dict(orient="records"),
        descriptive=descriptive_context(full),training_audit=train_audit,full_sample_audit=full_audit,
        context_only_audit=audit_features(b["X_train"][CONTEXT_FEATURES]),causality_checks=causal,
        scale_invariance="PASS",identical_comparison_dates="PASS",finite_matrices="PASS"
    )


def verify_rate_units(cache: ContextCache) -> dict:
    """Independent dated unit check versus Treasury CMT, not an equality of instruments."""
    rates=next(f for (symbol,_,_),f in cache.frames.items() if symbol=="^TNX")
    reference={"2024-01-02":3.95,"2024-01-03":3.91,"2024-01-04":3.99,"2024-01-05":4.05}
    comparisons=[]
    for date,official in reference.items():
        if pd.Timestamp(date) not in rates.index:
            continue
        yahoo=float(rates.loc[date,"Close"])
        assert abs(yahoo-official)<.03, "Rate scale differs from the verified percentage-point convention."
        comparisons.append(dict(date=date,yahoo_tnx=yahoo,treasury_10y_percent=official))
    return dict(comparisons=comparisons,units="Yahoo percentage points; divide by 100 to decimal annual yield",
                reference="https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=2024",
                limitation="Cboe/Yahoo proxy and Treasury CMT are different methodologies; check establishes scale, not identical measurements.")


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickers",nargs="+")
    parser.add_argument("--start",default="2010-01-01")
    parser.add_argument("--end",default=None)
    args=parser.parse_args()
    cache=ContextCache();results={}
    for ticker in args.tickers:
        ticker=normalize_ticker(ticker)
        print(f"V7 controlled context experiment: {ticker}",flush=True)
        bundle=download_context_bundle(ticker,args.start,args.end,cache)
        stock=download_market_data(ticker,args.start,args.end)
        print(json.dumps(context_data_report(stock,bundle),indent=2),flush=True)
        results[ticker]=compare_context(stock,bundle)
        print(json.dumps(results[ticker],indent=2),flush=True)
    evidence=dict(results=results,cache=dict(logical_requests=cache.logical_requests,provider_downloads=cache.provider_downloads),
                  rate_unit_verification=verify_rate_units(cache))
    Path("reports").mkdir(exist_ok=True)
    Path("reports/v7_experiments.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print("All V7 experiments complete:",evidence["cache"],flush=True)


if __name__=="__main__":
    main()
