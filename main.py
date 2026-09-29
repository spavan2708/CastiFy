"""Terminal orchestration for the CastiFy V7 research pipeline."""
from data.market_data import (
    MarketDataError, download_market_data, normalize_ticker, print_data_report
)
from features.feature_factory import build_feature_set
from data.context_data import download_context_bundle, context_data_report
from config.market_context import context_profile
from models.baseline import (
    chronological_split, evaluate_baseline, prepare_ml_dataset, print_baseline_report
)

START_DATE = "2010-01-01"
END_DATE = None
FEATURE_SET = "basic"  # Also: advanced, advanced_temporal, advanced_temporal_context.


def main() -> int:
    """Run one user-selected ticker; expected data failures get readable errors."""
    print("============================================\n"
          "                 CASTIFY\n"
          "      Quantitative Forecasting Engine\n"
          "============================================")
    try:
        ticker = normalize_ticker(input("Enter stock ticker: "))
        print(f"Analyzing {ticker}...")
        if FEATURE_SET == "advanced_temporal_context":
            context_profile(ticker)  # Fail clearly before downloading an unsupported ticker.
        stock = download_market_data(ticker, START_DATE, END_DATE)
        print_data_report(stock, ticker, START_DATE, END_DATE)
        bundle = None
        if FEATURE_SET == "advanced_temporal_context":
            bundle = download_context_bundle(ticker, START_DATE, END_DATE)
            for source in context_data_report(stock, bundle):
                print(source)
        featured = build_feature_set(stock, FEATURE_SET, context_bundle=bundle)
        X, y = prepare_ml_dataset(featured, FEATURE_SET)
        split = chronological_split(X, y, featured.index)
        evaluation = evaluate_baseline(split, featured, FEATURE_SET)
        print_baseline_report(X, split, evaluation)
    except MarketDataError as error:
        print(f"CastiFy: {error}")
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nInput cancelled.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
