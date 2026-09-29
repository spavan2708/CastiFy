"""Offline checks for ingestion, feature semantics, and strict holdout isolation."""
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from data.market_data import (
    COLUMNS, MarketDataError, download_market_data, normalize_ticker,
    standardize_columns, validate_market_data
)
from features.basic_features import build_basic_features
from models.baseline import (
    FEATURE_COLUMNS, chronological_split, evaluate_baseline, prepare_ml_dataset
)


def sample_data(rows=180):
    """Make positive, varying data on a non-calendar-daily trading index."""
    index = pd.bdate_range("2020-01-01", periods=rows)
    close = 100 + np.arange(rows) * 0.1 + np.sin(np.arange(rows))
    return pd.DataFrame({"Open": close, "High": close + 2, "Low": close - 2,
                         "Close": close, "Volume": 1000 + np.arange(rows)}, index=index)


class PipelineTests(unittest.TestCase):
    def test_normalization(self):
        for raw, expected in ((" aapl ", "AAPL"), ("msft", "MSFT"),
                              ("brk-b", "BRK-B"), ("7203.t", "7203.T"), ("^gspc", "^GSPC")):
            self.assertEqual(normalize_ticker(raw), expected)
        for raw in ("", "  ", "AAPL MSFT", "AAPL,MSFT"):
            with self.assertRaises(MarketDataError):
                normalize_ticker(raw)

    def test_column_formats(self):
        data = sample_data()
        pd.testing.assert_frame_equal(standardize_columns(data, "ABC"), data)
        for reverse in (False, True):
            raw = data.copy()
            raw.columns = pd.MultiIndex.from_tuples(
                [("ABC", c) if reverse else (c, "ABC") for c in COLUMNS])
            pd.testing.assert_frame_equal(standardize_columns(raw, "ABC"), data)
        with self.assertRaises(MarketDataError):
            standardize_columns(raw, "WRONG")

    def test_missing_and_duplicate_columns(self):
        for bad in (sample_data().drop(columns="Close"),
                    pd.concat([sample_data(), sample_data()[["Close"]]], axis=1)):
            with self.assertRaises(MarketDataError):
                validate_market_data(bad)

    def test_date_validation(self):
        data = sample_data()
        for bad in (data.iloc[::-1], pd.concat([data, data.iloc[[-1]]]), data.reset_index()):
            with self.assertRaises(MarketDataError):
                validate_market_data(bad)

    def test_value_validation(self):
        for column, value in (("Close", np.nan), ("High", np.inf), ("Low", 0),
                              ("Open", -1), ("Volume", np.inf), ("Volume", -1)):
            data = sample_data().astype(float)
            data.loc[data.index[3], column] = value
            with self.assertRaises(MarketDataError):
                validate_market_data(data)
        validate_market_data(sample_data())

    def test_minimum_history(self):
        with self.assertRaisesRegex(MarketDataError, "Insufficient historical data"):
            validate_market_data(sample_data(149))
        validate_market_data(sample_data(150))
        with self.assertRaisesRegex(MarketDataError, "100 usable ML rows"):
            prepare_ml_dataset(build_basic_features(sample_data(149)))

    @patch("data.market_data.yf.download", return_value=pd.DataFrame())
    def test_unavailable_download(self, download):
        with self.assertRaisesRegex(MarketDataError, "Unable to retrieve"):
            download_market_data("bad-symbol", "2010-01-01")

    @patch("data.market_data.yf.download")
    def test_download_contract(self, download):
        download.return_value = sample_data()
        data = download_market_data(" abc ", "2020-01-01", "2021-01-01")
        self.assertEqual(list(data.columns), COLUMNS)
        self.assertEqual(download.call_args.args, ("ABC",))
        self.assertTrue(download.call_args.kwargs["auto_adjust"])
        self.assertTrue(download.call_args.kwargs["keepna"])
        self.assertEqual(download.call_args.kwargs["end"], "2021-01-01")

    def test_feature_semantics_and_nonmutation(self):
        raw = sample_data()
        original = raw.copy(deep=True)
        featured = build_basic_features(raw)
        pd.testing.assert_frame_equal(raw, original)
        returns = raw.Close.pct_change()
        np.testing.assert_allclose(featured.Daily_Return, returns, equal_nan=True)
        for lag in (1, 2, 3, 5):
            np.testing.assert_allclose(featured[f"Return_Lag_{lag}"], returns.shift(lag), equal_nan=True)
        for window in (5, 20, 50):
            self.assertAlmostEqual(featured[f"MA_{window}"].iloc[window - 1],
                                   sum(raw.Close.iloc[:window]) / window)
        for window in (5, 20):
            self.assertAlmostEqual(featured[f"Volatility_{window}"].iloc[window],
                                   np.std(returns.iloc[1:window + 1], ddof=1))
        np.testing.assert_allclose(featured.Volume_Change, raw.Volume.pct_change(), equal_nan=True)
        np.testing.assert_allclose(featured.Tomorrow_Return.iloc[:-1], returns.iloc[1:])
        self.assertTrue(pd.isna(featured.Tomorrow_Return.iloc[-1]))

    def test_future_changes_do_not_change_past_features(self):
        raw = sample_data()
        changed = raw.copy()
        changed.iloc[120:] *= 2
        before, after = build_basic_features(raw), build_basic_features(changed)
        pd.testing.assert_frame_equal(before[FEATURE_COLUMNS].iloc[:120],
                                      after[FEATURE_COLUMNS].iloc[:120])

    def test_dataset_and_purge_with_missing_trading_row(self):
        raw = sample_data().drop(sample_data().index[100])
        featured = build_basic_features(raw)
        X, y = prepare_ml_dataset(featured)
        self.assertEqual(X.columns.tolist(), FEATURE_COLUMNS)
        self.assertNotIn("Tomorrow_Return", X)
        self.assertNotIn("Daily_Return", X)
        split = chronological_split(X, y, raw.index)
        self.assertEqual(len(split["removed"]), 1)
        targets = raw.index.to_series().shift(-1).loc[split["X_train"].index]
        self.assertTrue((targets < split["X_test"].index.min()).all())
        pd.testing.assert_frame_equal(split["X_test"], X.iloc[int(len(X) * .8):])

    def test_zero_volume_infinity_is_rejected(self):
        data = sample_data()
        data.loc[data.index[90], "Volume"] = 0
        validate_market_data(data)
        with self.assertRaisesRegex(MarketDataError, "Non-finite ML values"):
            prepare_ml_dataset(build_basic_features(data))

    @patch("models.baseline.RandomForestRegressor")
    def test_fit_receives_only_purged_training(self, forest):
        featured = build_basic_features(sample_data())
        X, y = prepare_ml_dataset(featured)
        split = chronological_split(X, y, featured.index)
        forest.return_value.predict.return_value = np.zeros(len(split["y_test"]))
        forest.return_value.feature_importances_ = np.full(10, .1)
        result = evaluate_baseline(split, featured)
        forest.assert_called_once_with(n_estimators=300, random_state=42, n_jobs=-1)
        args = forest.return_value.fit.call_args.args
        self.assertIs(args[0], split["X_train"])
        self.assertIs(args[1], split["y_train"])
        self.assertTrue(result["results"].index.equals(split["X_test"].index))


if __name__ == "__main__":
    unittest.main()
