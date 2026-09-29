"""Date arithmetic, mode preservation and causality checks without a network."""
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from features.temporal_features import temporal_features
from features.feature_factory import build_feature_set
from features.registry import (
    BASIC_FEATURES, ADVANCED_FEATURES, TEMPORAL_FEATURES, ADVANCED_TEMPORAL_FEATURES,
    TEMPORAL_METADATA, FEATURE_METADATA, get_feature_columns
)
from models.baseline import prepare_ml_dataset, chronological_split, evaluate_baseline
from test_pipeline import sample_data


def dates_only(dates):
    return pd.DataFrame(index=pd.DatetimeIndex(dates))


class TemporalTests(unittest.TestCase):
    def test_weekday_one_hot(self):
        result = temporal_features(dates_only(pd.bdate_range("2024-01-08", periods=5)))
        np.testing.assert_array_equal(result[TEMPORAL_FEATURES[:5]], np.eye(5))
        np.testing.assert_array_equal(result[TEMPORAL_FEATURES[:5]].sum(axis=1), np.ones(5))

    def test_bad_dates_explicitly_rejected(self):
        for bad in (dates_only(["2024-01-06"]), dates_only(["2024-01-08", "2024-01-05"]),
                    dates_only(["2024-01-08", "2024-01-08"]), dates_only([pd.NaT]),
                    pd.DataFrame(index=[1, 2])):
            with self.assertRaises(ValueError):
                temporal_features(bad)

    def test_month_phase_and_wrap(self):
        f = temporal_features(dates_only(["2023-12-29", "2024-01-01", "2024-07-01"]))
        np.testing.assert_allclose(f[["Month_Sin", "Month_Cos"]].iloc[1], [0, 1], atol=1e-15)
        np.testing.assert_allclose(f[["Month_Sin", "Month_Cos"]].iloc[2], [0, -1], atol=1e-15)
        distance = np.linalg.norm(f[["Month_Sin", "Month_Cos"]].iloc[0] - f[["Month_Sin", "Month_Cos"]].iloc[1])
        self.assertAlmostEqual(distance, 2 * np.sin(np.pi / 12))

    def test_month_length_and_boundary(self):
        f = temporal_features(dates_only(["2024-01-31", "2024-02-01", "2024-02-29", "2024-03-01"]))
        np.testing.assert_allclose(f.DayOfMonth_Sin, np.sin(2 * np.pi * np.array([30/31, 0, 28/29, 0])))
        np.testing.assert_array_equal(f.Calendar_Days_From_Month_Start, [30, 0, 28, 0])
        np.testing.assert_array_equal(f.Calendar_Days_To_Month_End, [0, 28, 0, 30])
        phase = f[["DayOfMonth_Sin", "DayOfMonth_Cos"]]
        self.assertLess(np.linalg.norm(phase.iloc[2] - phase.iloc[3]), .22)

    def test_leap_february_28_29_march_1(self):
        f = temporal_features(dates_only(["2024-02-28", "2024-02-29", "2024-03-01"]))
        phases = np.array([58, 59, 60]) / 366
        np.testing.assert_allclose(f.DayOfYear_Sin, np.sin(2 * np.pi * phases))
        np.testing.assert_allclose(f.DayOfYear_Cos, np.cos(2 * np.pi * phases))
        nonleap = temporal_features(dates_only(["2023-03-01"]))
        self.assertAlmostEqual(nonleap.DayOfYear_Sin.iloc[0], np.sin(2 * np.pi * 59/365))

    def test_year_wrap(self):
        f = temporal_features(dates_only(["2020-12-31", "2021-01-01"]))
        np.testing.assert_allclose(f[["DayOfYear_Sin", "DayOfYear_Cos"]].iloc[1], [0, 1])
        self.assertAlmostEqual(f.DayOfYear_Sin.iloc[0], np.sin(2 * np.pi * 365/366))
        self.assertLess(np.linalg.norm(f[["DayOfYear_Sin", "DayOfYear_Cos"]].iloc[0] - [0, 1]), .018)

    def test_quarter_distances_and_regions(self):
        f = temporal_features(dates_only(["2024-01-01", "2024-01-08", "2024-03-25", "2024-03-29", "2024-04-01"]))
        np.testing.assert_array_equal(f.Calendar_Days_From_Quarter_Start, [0, 7, 84, 88, 0])
        np.testing.assert_array_equal(f.Calendar_Days_To_Quarter_End, [90, 83, 6, 2, 90])
        np.testing.assert_array_equal(f.Is_Quarter_Start_Region, [1, 0, 0, 0, 1])
        np.testing.assert_array_equal(f.Is_Quarter_End_Region, [0, 0, 1, 1, 0])

    def test_weekend_and_holiday_gaps(self):
        f = temporal_features(dates_only(["2024-01-05", "2024-01-08", "2024-01-12", "2024-01-16"]))
        self.assertTrue(pd.isna(f.Calendar_Days_Since_Previous_Session.iloc[0]))
        np.testing.assert_array_equal(f.Calendar_Days_Since_Previous_Session.iloc[1:], [3, 4, 4])

    def test_local_timezone_dst_gap(self):
        index = pd.DatetimeIndex(["2024-03-08", "2024-03-11"], tz="America/New_York")
        f = temporal_features(dates_only(index))
        self.assertEqual(f.Calendar_Days_Since_Previous_Session.iloc[1], 3)
        self.assertEqual(f.DOW_Monday.iloc[1], 1)
        self.assertTrue(f.index.equals(index))

    def test_all_cycles_finite_bounded_unit_circle(self):
        f = temporal_features(dates_only(pd.bdate_range("2019-01-01", "2025-12-31")))
        for name in ("Month", "DayOfMonth", "DayOfYear"):
            pair = f[[name + "_Sin", name + "_Cos"]].to_numpy()
            self.assertTrue(np.isfinite(pair).all())
            self.assertTrue((np.abs(pair) <= 1).all())
            np.testing.assert_allclose(np.sum(pair**2, axis=1), 1, atol=1e-14)

    def test_registries_metadata_and_mode_preservation(self):
        self.assertEqual([len(get_feature_columns(mode)) for mode in ("basic", "advanced", "advanced_temporal")], [10,70,88])
        self.assertEqual(ADVANCED_TEMPORAL_FEATURES, ADVANCED_FEATURES + TEMPORAL_FEATURES)
        self.assertNotIn("Tomorrow_Return", BASIC_FEATURES + ADVANCED_TEMPORAL_FEATURES)
        self.assertEqual(set(TEMPORAL_METADATA), set(TEMPORAL_FEATURES))
        for name in TEMPORAL_FEATURES:
            m = FEATURE_METADATA[name]
            self.assertEqual(m["family"], "temporal")
            self.assertTrue(m["future_safe"])
            self.assertFalse(m["uses_market_values"])
            self.assertFalse(m["uses_future_observations"])
            self.assertIn("calendar_semantics", m)
        raw = sample_data(400)
        raw.columns.name = "Price"
        before = raw.copy()
        old = build_feature_set(raw, "advanced")
        new = build_feature_set(raw, "advanced_temporal")
        pd.testing.assert_frame_equal(old, new[old.columns])
        pd.testing.assert_frame_equal(raw, before)

    def test_multiple_prefixes_and_future_perturbation(self):
        raw = sample_data(800)
        full = build_feature_set(raw, "advanced_temporal")
        for date in ("2021-06-15", "2021-06-30", "2021-12-31"):
            with self.subTest(cutoff=date):
                expected = full.loc[:date, ADVANCED_TEMPORAL_FEATURES]
                prefix = build_feature_set(raw.loc[:date], "advanced_temporal")
                pd.testing.assert_frame_equal(expected, prefix[ADVANCED_TEMPORAL_FEATURES], check_exact=True)
                changed = raw.copy()
                future = changed.index > date
                changed.loc[future, ["Open", "High", "Low", "Close"]] *= 3
                changed.loc[future, "Volume"] *= 7
                rebuilt = build_feature_set(changed, "advanced_temporal")
                pd.testing.assert_frame_equal(expected, rebuilt.loc[:date, ADVANCED_TEMPORAL_FEATURES], check_exact=True)

    def test_temporal_exact_scale_invariance(self):
        raw = sample_data(400)
        scaled = raw.copy()
        scaled[["Open", "High", "Low", "Close"]] *= 11
        scaled["Volume"] *= 7
        before = build_feature_set(raw, "advanced_temporal")
        after = build_feature_set(scaled, "advanced_temporal")
        pd.testing.assert_frame_equal(before[TEMPORAL_FEATURES], after[TEMPORAL_FEATURES], check_exact=True)
        np.testing.assert_allclose(before[ADVANCED_TEMPORAL_FEATURES], after[ADVANCED_TEMPORAL_FEATURES], equal_nan=True, rtol=1e-7, atol=1e-7)

    def test_profiles_are_same_day_descriptive_only(self):
        from models.temporal_comparison import return_profiles
        f = pd.DataFrame({"Daily_Return": [np.nan, .1, -.2, 0.],
                          "Tomorrow_Return": [99., 99., 99., 99.]},
                         index=pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-15", "2024-02-05"]))
        profiles = return_profiles(f)
        monday = profiles["weekday"][0]
        self.assertEqual(monday["weekday"], "Monday")
        self.assertEqual(monday["count"], 3)
        self.assertAlmostEqual(monday["mean"], -.1/3)
        self.assertEqual(monday["median"], 0)
        self.assertAlmostEqual(monday["std"], np.std([.1, -.2, 0], ddof=1))
        self.assertAlmostEqual(monday["positive_fraction"], 1/3)
        january = profiles["month"][0]
        self.assertEqual(january["count"], 2)
        self.assertAlmostEqual(january["positive_fraction"], .5)

    @patch("models.baseline.RandomForestRegressor")
    def test_three_modes_finite_and_train_only_fit(self, forest):
        raw = sample_data(400)
        for mode in ("basic", "advanced", "advanced_temporal"):
            f = build_feature_set(raw, mode)
            X, y = prepare_ml_dataset(f, mode)
            self.assertTrue(np.isfinite(X.to_numpy()).all())
            split = chronological_split(X, y, raw.index)
            forest.return_value.predict.return_value = np.zeros(len(split["y_test"]))
            forest.return_value.feature_importances_ = np.full(X.shape[1], 1/X.shape[1])
            evaluate_baseline(split, f, mode)
            args = forest.return_value.fit.call_args.args
            self.assertIs(args[0], split["X_train"])
            self.assertIs(args[1], split["y_train"])
        self.assertEqual(forest.call_count, 3)
        forest.assert_called_with(n_estimators=300, random_state=42, n_jobs=-1)


if __name__ == "__main__":
    unittest.main()
