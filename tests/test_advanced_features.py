"""Independent numeric references, degenerate cases and whole-registry causality."""
import unittest
import numpy as np
import pandas as pd

from features.feature_factory import build_feature_set
from features.basic_features import build_basic_features
from features.registry import ADVANCED_FEATURES, BASIC_FEATURES, FEATURE_METADATA
from features.technical_features import technical_features
from features.audit import audit_features
from models.baseline import prepare_ml_dataset, chronological_split
from test_pipeline import sample_data


def reference_ema(values, span):
    result = [float(values[0])]
    alpha = 2 / (span + 1)
    for value in values[1:]:
        result.append(alpha * value + (1 - alpha) * result[-1])
    return np.array(result)


class AdvancedTests(unittest.TestCase):
    def setUp(self):
        self.raw = sample_data(400)
        self.raw["Open"] *= .999
        self.f = build_feature_set(self.raw)

    def test_registry_and_basic_compatibility(self):
        self.assertEqual(len(ADVANCED_FEATURES), 70)
        self.assertEqual(len(set(ADVANCED_FEATURES)), 70)
        self.assertNotIn("Tomorrow_Return", ADVANCED_FEATURES + BASIC_FEATURES)
        self.assertTrue(set(ADVANCED_FEATURES).issubset(FEATURE_METADATA))
        pd.testing.assert_frame_equal(build_feature_set(self.raw, "basic"), build_basic_features(self.raw))
        for name in BASIC_FEATURES:
            np.testing.assert_allclose(self.f[name], build_basic_features(self.raw)[name], equal_nan=True)

    def test_returns_and_price_structure(self):
        t = 80
        raw, f = self.raw, self.f
        for n in (1, 2, 3, 5, 10, 20, 60):
            self.assertAlmostEqual(f[f"Return_{n}D"].iloc[t], raw.Close.iloc[t] / raw.Close.iloc[t-n] - 1)
        self.assertAlmostEqual(f.Overnight_Gap.iloc[t], raw.Open.iloc[t] / raw.Close.iloc[t-1] - 1)
        self.assertAlmostEqual(f.Intraday_Return.iloc[t], raw.Close.iloc[t] / raw.Open.iloc[t] - 1)
        high, low = raw.High.iloc[t-19:t+1].max(), raw.Low.iloc[t-19:t+1].min()
        self.assertAlmostEqual(f.Range_Position_20.iloc[t], (raw.Close.iloc[t] - low) / (high - low))
        self.assertAlmostEqual(f.Distance_From_20D_High.iloc[t], raw.Close.iloc[t] / high - 1)
        self.assertAlmostEqual(f.Drawdown_From_20D_Peak.iloc[t], raw.Close.iloc[t] / raw.Close.iloc[t-19:t+1].max() - 1)
        for n in (20, 60, 252):
            self.assertTrue((f[f"Drawdown_From_{n}D_Peak"].dropna() <= 1e-12).all())
        self.assertAlmostEqual(f.Relative_Volume_20.iloc[t], raw.Volume.iloc[t] / raw.Volume.iloc[t-19:t+1].mean())

    def test_rsi_wilder_seed_and_recurrence(self):
        changes = np.diff(self.raw.Close.to_numpy())
        gain = np.maximum(changes[:14], 0).mean()
        loss = np.maximum(-changes[:14], 0).mean()
        self.assertTrue(self.f.RSI_14.iloc[:14].isna().all())
        for t in range(14, 40):
            if t > 14:
                gain = (13 * gain + max(changes[t-1], 0)) / 14
                loss = (13 * loss + max(-changes[t-1], 0)) / 14
            self.assertAlmostEqual(self.f.RSI_14.iloc[t], 100 - 100 / (1 + gain / loss))

    def test_macd_independent_recursion(self):
        c = self.raw.Close.to_numpy()
        macd = reference_ema(c, 12) - reference_ema(c, 26)
        signal = reference_ema(macd[25:], 9)
        t = 50
        self.assertAlmostEqual(self.f.MACD_Pct.iloc[t], macd[t] / c[t])
        self.assertAlmostEqual(self.f.MACD_Signal_Pct.iloc[t], signal[t-25] / c[t])
        self.assertAlmostEqual(self.f.MACD_Histogram_Pct.iloc[t], (macd[t] - signal[t-25]) / c[t])
        self.assertTrue(self.f.MACD_Signal_Pct.iloc[:33].isna().all())

    def test_bollinger_and_atr(self):
        self.raw.loc[self.raw.index[20], "High"] += 30
        self.f = build_feature_set(self.raw)
        t = 50
        values = self.raw.Close.iloc[t-19:t+1].to_numpy()
        mean, std = np.mean(values), np.std(values, ddof=0)
        self.assertAlmostEqual(self.f.Bollinger_Position.iloc[t], (values[-1] - mean + 2 * std) / (4 * std))
        self.assertAlmostEqual(self.f.Bollinger_Width.iloc[t], 4 * std / mean)
        tr = []
        for i in range(t + 1):
            row = self.raw.iloc[i]
            choices = [row.High - row.Low]
            if i:
                previous = self.raw.Close.iloc[i-1]
                choices += [abs(row.High - previous), abs(row.Low - previous)]
            tr.append(max(choices))
        atr = sum(tr[:14]) / 14
        for value in tr[14:]:
            atr = (atr * 13 + value) / 14
        self.assertAlmostEqual(self.f.ATR_14_Pct.iloc[t], atr / self.raw.Close.iloc[t])

    def test_flat_and_one_sided_cases(self):
        flat = self.raw.copy()
        flat[["Open", "High", "Low", "Close"]] = 100.
        flat["Volume"] = 0
        f = build_feature_set(flat)
        self.assertEqual(f.RSI_14.iloc[-1], 50)
        self.assertEqual(f.Bollinger_Position.iloc[-1], .5)
        self.assertEqual(f.Range_Position_20.iloc[-1], .5)
        self.assertEqual(f.Close_Open_Position.iloc[-1], 0)
        self.assertTrue(pd.isna(f.Relative_Volume_20.iloc[-1]))
        self.assertTrue(pd.isna(f.Downside_Volatility_20.iloc[-1]))
        self.assertFalse(np.isinf(f[ADVANCED_FEATURES].to_numpy()).any())
        for direction, expected in ((1, 100), (-1, 0)):
            data = self.raw.copy()
            data["Close"] = 500 + direction * np.arange(len(data))
            self.assertEqual(technical_features(data).RSI_14.iloc[-1], expected)

    def test_future_perturbation_all_inputs(self):
        changed = self.raw.copy()
        cutoff = 300
        rng = np.random.default_rng(42)
        changed.iloc[cutoff+1:, :4] *= rng.uniform(.5, 2, (len(changed)-cutoff-1, 1))
        changed.loc[changed.index[cutoff+1:], "Volume"] *= 3
        rebuilt = build_feature_set(changed)
        pd.testing.assert_frame_equal(self.f[ADVANCED_FEATURES].iloc[:cutoff+1],
                                      rebuilt[ADVANCED_FEATURES].iloc[:cutoff+1], check_exact=True)
        pd.testing.assert_frame_equal(self.f[ADVANCED_FEATURES].iloc[:cutoff+1],
                                      build_feature_set(self.raw.iloc[:cutoff+1])[ADVANCED_FEATURES], check_exact=True)

    def test_scale_invariance(self):
        scaled = self.raw.copy()
        scaled[["Open", "High", "Low", "Close"]] *= 11
        scaled["Volume"] *= 7
        rebuilt = build_feature_set(scaled)
        np.testing.assert_allclose(self.f[ADVANCED_FEATURES], rebuilt[ADVANCED_FEATURES],
                                   equal_nan=True, atol=1e-7, rtol=1e-7)

    def test_dataset_purge_and_finite(self):
        X, y = prepare_ml_dataset(self.f, "advanced")
        self.assertEqual(X.shape, (148, 70))
        self.assertTrue(np.isfinite(X.to_numpy()).all())
        self.assertTrue(np.isfinite(y.to_numpy()).all())
        split = chronological_split(X, y, self.raw.index)
        self.assertLess(split["latest_train_target"], split["X_test"].index.min())

    def test_distribution_obv_and_trend_references(self):
        t = 80
        returns = self.raw.Close.pct_change().iloc[t-19:t+1].to_numpy()
        negative, positive = returns[returns < 0], returns[returns > 0]
        self.assertAlmostEqual(self.f.Downside_Volatility_20.iloc[t], np.std(negative, ddof=1))
        self.assertAlmostEqual(self.f.Upside_Volatility_20.iloc[t], np.std(positive, ddof=1))
        self.assertAlmostEqual(self.f.Positive_Return_Ratio_20.iloc[t], len(positive) / 20)
        volume = self.raw.Volume.iloc[t-19:t+1].to_numpy()
        self.assertAlmostEqual(self.f.OBV_Flow_20.iloc[t], np.dot(np.sign(returns), volume) / volume.sum())
        exponential = self.raw.copy()
        exponential["Close"] = np.exp(.003 * np.arange(len(exponential)))
        actual = build_feature_set(exponential)
        self.assertAlmostEqual(actual.Log_Price_Slope_20.iloc[t], .003)
        self.assertAlmostEqual(actual.Log_Price_Slope_60.iloc[t], .003)

    def test_audit_known_flags(self):
        X = pd.DataFrame({"a": [1., 2., 3.], "duplicate": [1., 2., 3.],
                          "constant": [2., 2., 2.], "tiny": [0., 1e-8, 2e-8]})
        audit = audit_features(X)
        self.assertIn(["a", "duplicate"], audit["exact_duplicates"])
        self.assertEqual(audit["constants"], ["constant"])
        self.assertIn("tiny", audit["near_zero_variance"])
        self.assertTrue(audit["high_correlations"])


if __name__ == "__main__":
    unittest.main()
