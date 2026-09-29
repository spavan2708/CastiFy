# CastiFy

A machine learning research platform for next-session equity return forecasting using price, technical, temporal, market, sector, volatility, and rate context.

CastiFy emphasizes leakage prevention, controlled experiments, modular feature engineering, and realistic evaluation. Its current implementation builds and evaluates historical forecasting datasets, with explicit benchmarks and recorded experimental evidence.

## Current Status

**Active development — complete through V7: Market, Sector & Macro Context Engine.**

| Version | Component | Status |
| --- | --- | --- |
| V0 | Project setup | Complete |
| V1 | Basic feature engineering | Complete |
| V2 | Leakage-safe ML dataset | Complete |
| V3 | Random Forest baseline | Complete |
| V4 | Multi-ticker market data engine | Complete |
| V5 | Advanced quantitative features | Complete |
| V6 | Temporal/calendar intelligence | Complete |
| V7 | Market, sector, volatility, and rate context | Complete |
| V8 | Market regime intelligence | Planned |
| V9 | Model tournament | Planned |
| V10 | Walk-forward validation | Planned |

Further modeling, NLP, backtesting, risk analysis, Monte Carlo, and dashboard work is planned.

## Why CastiFy?

Next-session stock returns are noisy. CastiFy makes experimental discipline central: avoiding look-ahead bias, preserving chronological validation, comparing feature families against explicit benchmarks, and recording reproducible configurations. Current mode comparisons examine the effect of market context; broader feature-family ablations remain planned.

## Current Pipeline

```text
Ticker -> Yahoo Finance -> OHLCV normalization and validation
                                      |
                  +-------------------+--------------------+
                  |                                        |
           Stock features                  Optional context downloads
                  |                         SPY / QQQ / sector ETF
                  |                         VIX / Treasury proxy
                  |                         Validation + date alignment
                  +-------------------+--------------------+
                                      |
                               Feature factory
                                      |
                       Explicit inputs + next-session target
                       Required-NaN filtering / finite checks
                                      |
                      Chronological 80/20 split + label purge
                                      |
                            Fixed Random Forest
                                      |
                     Holdout metrics + benchmark comparisons
```

The terminal entry point analyzes one chosen ticker per run; experiment modules compare multiple tickers.

## Feature Engineering

| Family | Representative features |
| --- | --- |
| Basic | Lagged returns, moving averages, rolling volatility, volume change |
| Returns | Multi-horizon returns and return lags |
| Price structure | Relative SMA positions, rolling high/low distances, drawdown |
| Momentum | Relative EMA positions, log-price slopes, return acceleration |
| Volatility | Rolling standard deviation, volatility ratios, skew, kurtosis |
| Volume | Relative volume, normalized OBV flow, volume/return correlation |
| Technical indicators | RSI, normalized MACD, Bollinger position/width, normalized ATR |
| Temporal/calendar | Weekday indicators, cyclical calendar encodings, session gaps |
| Market context | SPY/QQQ returns and trend, market volatility, VIX context |
| Sector context | Sector ETF returns, trend, volatility |
| Cross-asset relationships | Relative strength, rolling beta/correlation, relative volatility |
| Rates | Treasury yield level, changes, deviation from trailing mean |

Explicit registries and metadata define model inputs. Formula details are in the [V5 quantitative catalog](reports/v5_feature_catalog.md), [V6 temporal catalog](reports/v6_temporal_feature_catalog.md), and [V7 context catalog](reports/v7_context_feature_catalog.md).

## Feature Modes

| Mode | Inputs | Composition |
| --- | ---: | --- |
| `basic` | 10 | Original baseline features |
| `advanced` | 70 | Quantitative feature families |
| `advanced_temporal` | 88 | Advanced + 18 calendar features |
| `advanced_temporal_context` | 132 | Advanced + calendar + 44 context features |

Modes support controlled comparisons. The advanced registry replaces the basic registry; the counts are not cumulatively added across all four modes.

## Leakage Prevention

- **Target isolation:** `Tomorrow_Return = Daily_Return.shift(-1)` represents the next original trading session's adjusted close-to-close return. It never enters an input registry.
- **Chronological evaluation:** an 80/20 split uses no random shuffling. Training labels realizing on or after the first test feature date are purged using the original trading index.
- **Information timing:** stock features use completed current-session or earlier observations. Context is aligned by actual dates, with no backward filling or future interpolation.
- **Causality checks:** future-perturbation tests change later observations and check earlier inputs; prefix-invariance tests compare full-history calculations with truncated histories.

These checks address computation and alignment. Yahoo's retrospective revisions and adjusted prices remain limitations: the data is **not a certified point-in-time archive**.

## Context Engine

V7 combines SPY, QQQ, sector ETFs, `^VIX`, and the `^TNX` 10-year Treasury yield proxy. Current sector mappings include **AAPL → XLK**, **MSFT → XLK**, and **JPM → XLF**.

ETF observations require exact stock-date matches. VIX and Treasury context use strictly earlier source dates, with a maximum age of four calendar days. Missing or stale observations remain unavailable. Features include relative strength, rolling correlation/beta, relative volatility, and market-/sector-adjusted returns.

Context profiles cover selected US equities; they are not universal across international tickers or exchanges. See [profile configuration](config/market_context.py).

## Baseline Model

```python
RandomForestRegressor(
    n_estimators=300,
    random_state=42,
    n_jobs=-1,
)
```

This configuration stays fixed while the data and feature pipeline develops. No hyperparameter optimization is implemented. Evaluation reports MAE, RMSE, R², direction accuracy, a zero-return error baseline, and a current-return-direction benchmark.

## Current Experimental Results

The [saved V7 experiment](reports/v7_experiments.json) compares 88-input temporal and 132-input context modes on identical eligible dates within each ticker. Each uses 3,163 training rows after purging and 791 test rows. Errors below are in **daily-return decimal units**; `0.01` equals one percentage point.

| Ticker | Mode | MAE | RMSE | R² |
| --- | --- | ---: | ---: | ---: |
| AAPL | Temporal | 0.011877 | 0.017444 | -0.0753 |
| AAPL | Context | 0.011741 | 0.017050 | -0.0273 |
| MSFT | Temporal | 0.011953 | 0.017492 | -0.1484 |
| MSFT | Context | 0.026548 | 0.032744 | -3.0245 |
| JPM | Temporal | 0.010455 | 0.014825 | -0.0670 |
| JPM | Context | 0.010752 | 0.015025 | -0.0960 |

| Zero-return benchmark | MAE | RMSE |
| --- | ---: | ---: |
| AAPL | 0.011481 | 0.016845 |
| MSFT | 0.011151 | 0.016338 |
| JPM | 0.010041 | 0.014399 |

Context improves AAPL, worsens JPM, and substantially worsens MSFT. **Neither model beats the zero-return baseline on MAE or RMSE for any of these tickers.** These outcomes motivate stronger validation, feature selection, model comparison, and regime-aware research; they do not demonstrate predictive superiority or profitability.

## Testing

**56 automated tests pass at V7.** Run:

```bash
python -m unittest discover -s tests -v
```

Coverage includes feature calculations, numerical safety, target isolation and purging, mismatched calendars, date alignment, future perturbation, prefix invariance, rolling beta/correlation, scale invariance, unsupported profiles, and preservation of earlier feature modes. Provider interactions in the unit suite are mocked.

## Project Structure

```text
CastiFy/
├── main.py                         # Interactive pipeline entry point
├── requirements.txt                # Pinned dependencies
├── config/market_context.py        # Context profiles and timing policy
├── data/                           # Stock/context ingestion and validation
├── features/                       # Feature families, registries, metadata, audits
│   └── feature_factory.py          # Feature-mode orchestration
├── models/
│   ├── baseline.py                 # Dataset, purged split, forest, metrics
│   ├── feature_comparison.py       # Basic vs advanced experiments
│   ├── temporal_comparison.py      # Temporal comparisons
│   └── context_comparison.py       # V7 context comparisons
├── tests/                          # Four unittest modules
└── reports/                        # Catalogs and milestone evidence
```

## Installation

Use Python 3.12 or newer. The repository's `.python-version` specifies 3.12.10; the current test suite was verified with Python 3.14.7.

```bash
git clone https://github.com/spavan2708/CastiFy.git
cd CastiFy
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

For Windows PowerShell, activate with `venv\Scripts\Activate.ps1`.

Pinned dependencies: `yfinance==1.7.0`, `pandas==3.0.6`, `numpy==2.5.3`, and `scikit-learn==1.9.1`. Live runs require network access to Yahoo Finance.

## Running CastiFy

```bash
python main.py
```

Enter a ticker such as `AAPL` when prompted. In [main.py](main.py), choose `FEATURE_SET` from the modes above; it currently defaults to `"basic"`. Dates are also configured there: `START_DATE = "2010-01-01"`, `END_DATE = None`. The downloader resolves an unspecified end to today's UTC date, exclusive.

The command prints data diagnostics and historical holdout evaluation. It does not provide a deployed next-session forecast service.

## Research Reports

The [reports directory](reports/) records milestone evidence, including negative results: the [V3 baseline](reports/v3_baseline.json), [V4 master report](reports/v4_master_report.md), [V5 master report](reports/v5_master_report.md), [V6 master report](reports/v6_master_report.md), and [V7 master report](reports/v7_master_report.md). Feature catalogs are linked above; JSON metadata and experiment results support deeper inspection.

Milestone-specific files preserve development history. Experiment runners can overwrite their corresponding result files when rerun; live provider revisions can also change results.

## Roadmap

All items below are **planned, not implemented**:

- **V8–V10:** market regime intelligence, model tournament, walk-forward validation.
- **V11–V13:** feature selection/ablation, news/NLP, fundamental/event features.
- **V14–V15:** ensembles with uncertainty, explainability.
- **V16–V19:** trading signals, backtesting, risk analysis, Monte Carlo.
- **V20:** dashboard.

## Limitations

Next-session returns remain highly noisy, and the Random Forest is a baseline. Evaluation currently uses a fixed holdout, with no walk-forward framework or transaction-cost-aware backtest. Yahoo histories may be revised retrospectively, and context profiles are not universal across exchanges. Current V7 experiments have not demonstrated superiority over the naive zero-return error benchmark.

## Disclaimer

CastiFy is an educational and research project, not financial advice. Results do not establish future returns or guarantee trading performance.
