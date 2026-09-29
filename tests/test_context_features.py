"""Offline alignment, availability, numerical-reference and causality tests."""
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd

from config.market_context import context_profile
from data.context_data import ContextCache, download_context_bundle, align_previous
from data.market_data import MarketDataError
from features.context_features import context_features
from features.feature_factory import build_feature_set
from features.registry import get_feature_columns, FEATURE_METADATA, ADVANCED_TEMPORAL_FEATURES, ADVANCED_TEMPORAL_CONTEXT_FEATURES
from features.context_registry import CONTEXT_FEATURES
from models.baseline import prepare_ml_dataset, chronological_split, evaluate_baseline


def frame(returns, index, level=100):
    close = level*np.cumprod(1+np.asarray(returns))
    return pd.DataFrame(dict(Open=close*.999,High=close*1.01,Low=close*.99,Close=close,
                             Volume=1000+np.arange(len(index))),index=index)


def fixture(rows=600):
    index=pd.bdate_range("2020-01-01",periods=rows)
    rng=np.random.default_rng(17)
    market=rng.normal(.0003,.012,rows)
    stock=frame(2*market,index)
    sources={"SPY":frame(market,index),"QQQ":frame(market*.9+rng.normal(0,.003,rows),index),
             "XLK":frame(market*.7+rng.normal(0,.005,rows),index),
             "^VIX":frame(rng.normal(0,.015,rows),index,20),"^TNX":frame(rng.normal(0,.002,rows),index,4)}
    return stock,dict(profile=context_profile("AAPL"),series=sources,requested_start="2020-01-01",requested_end=None)


class ContextTests(unittest.TestCase):
    def test_profiles_and_unsupported(self):
        for ticker,sector in ((" aapl ","XLK"),("MSFT","XLK"),("JPM","XLF")):
            self.assertEqual(context_profile(ticker)["sector"],sector)
        with self.assertRaisesRegex(MarketDataError,"not configured"):
            context_profile("7203.T")
        stock,_=fixture()
        for mode in ("basic","advanced","advanced_temporal"):
            self.assertEqual(len(prepare_ml_dataset(build_feature_set(stock,mode),mode)[0])>0,True)

    def test_date_alignment_and_missing_interval(self):
        stock,bundle=fixture()
        missing=stock.index[20]
        bundle["series"]["SPY"]=bundle["series"]["SPY"].drop(missing)
        f=context_features(stock,bundle)
        self.assertTrue(pd.isna(f.loc[missing,"SPY_Return_1D"]))
        self.assertTrue(pd.isna(f.iloc[21].SPY_Return_1D))
        expected=bundle["series"]["SPY"].Close.loc[stock.index[22]]/bundle["series"]["SPY"].Close.loc[stock.index[21]]-1
        self.assertAlmostEqual(f.iloc[22].SPY_Return_1D,expected)
        self.assertTrue(pd.isna(f.iloc[24].SPY_Return_5D))
        self.assertTrue(f.index.equals(stock.index))

    def test_market_and_relative_returns(self):
        stock,bundle=fixture()
        f=context_features(stock,bundle);t=90
        spy,sector=bundle["series"]["SPY"].Close,bundle["series"]["XLK"].Close
        for n in (1,5,20):
            self.assertAlmostEqual(f[f"SPY_Return_{n}D"].iloc[t],spy.iloc[t]/spy.iloc[t-n]-1)
        self.assertAlmostEqual(f.Stock_vs_SPY_Return_5D.iloc[t],stock.Close.iloc[t]/stock.Close.iloc[t-5]-spy.iloc[t]/spy.iloc[t-5])
        self.assertAlmostEqual(f.Sector_Adjusted_Return_1D.iloc[t],stock.Close.pct_change().iloc[t]-sector.pct_change().iloc[t])

    def test_beta_and_correlation_known_relationship(self):
        stock,bundle=fixture()
        f=context_features(stock,bundle)
        for n in (20,60):
            np.testing.assert_allclose(f[f"Stock_SPY_Beta_{n}"].iloc[100:],2,atol=1e-10)
            np.testing.assert_allclose(f[f"Stock_SPY_Correlation_{n}"].iloc[100:],1,atol=1e-10)
        market=bundle["series"]["SPY"].Close.pct_change().fillna(0)
        inverse=frame(-market.to_numpy(),stock.index)
        negative=context_features(inverse,bundle)
        np.testing.assert_allclose(negative.Stock_SPY_Correlation_20.iloc[100:],-1,atol=1e-10)
        np.testing.assert_allclose(negative.Stock_SPY_Beta_20.iloc[100:],-1,atol=1e-10)

    def test_relative_volatility_and_zero_variance(self):
        stock,bundle=fixture()
        f=context_features(stock,bundle)
        np.testing.assert_allclose(f.Stock_to_SPY_Volatility_20.iloc[100:],2,atol=1e-10)
        bundle["series"]["SPY"]["Close"]=100.
        undefined=context_features(stock,bundle)
        self.assertTrue(undefined.Stock_SPY_Beta_20.isna().all())
        self.assertTrue(undefined.Stock_SPY_Correlation_20.isna().all())
        self.assertTrue(undefined.Stock_to_SPY_Volatility_20.isna().all())

    def test_strict_prior_staleness_and_no_backfill(self):
        values=pd.DataFrame({"rate":[4.,9.]},index=pd.to_datetime(["2024-01-05","2024-01-12"]))
        dates=pd.to_datetime(["2024-01-04","2024-01-05","2024-01-08","2024-01-09","2024-01-10","2024-01-12","2024-01-15"])
        f,d=align_previous(values,dates)
        self.assertTrue(f.iloc[:2].isna().all().all())
        self.assertEqual(f.rate.iloc[2],4)
        self.assertEqual(d.Age_Days.iloc[2],3)
        self.assertEqual(f.rate.iloc[3],4)
        self.assertTrue(pd.isna(f.rate.iloc[4]))
        self.assertTrue(pd.isna(f.rate.iloc[5])) # Same-date value not allowed.
        self.assertEqual(f.rate.iloc[6],9)
        self.assertEqual(d.Age_Days.iloc[6],3)
        self.assertTrue((d.loc[d.Usable,"Source_Date"]<dates[d.Usable]).all())

    def test_vix_rank_ties_and_future_safety(self):
        stock,bundle=fixture()
        v=bundle["series"]["^VIX"]
        v["Close"]=np.tile([10.,20.,20.,30.],150)
        f=context_features(stock,bundle);t=350
        values=v.Close.iloc[t-252:t].to_numpy();last=values[-1]
        expected=((values<last).sum()+((values==last).sum()+1)/2)/252
        self.assertAlmostEqual(f.VIX_Percentile_252.iloc[t],expected)
        self.assertTrue(pd.isna(f.VIX_Percentile_252.iloc[251]))
        v.loc[v.index>stock.index[t],"Close"]*=100
        pd.testing.assert_series_equal(f.VIX_Percentile_252.iloc[:t+1],context_features(stock,bundle).VIX_Percentile_252.iloc[:t+1],check_exact=True)

    def test_rate_units_and_lag(self):
        stock,bundle=fixture();r=bundle["series"]["^TNX"]
        r["Close"]=4.+np.arange(len(r))*.001
        f=context_features(stock,bundle);t=90
        self.assertAlmostEqual(f.Treasury_10Y_Level.iloc[t],r.Close.iloc[t-1]/100)
        self.assertAlmostEqual(f.Treasury_10Y_Change_1D.iloc[t],.001/100)
        self.assertAlmostEqual(f.Treasury_10Y_Change_5D.iloc[t],.005/100)
        self.assertAlmostEqual(f.Treasury_10Y_vs_MA_20.iloc[t],(r.Close.iloc[t-1]-r.Close.iloc[t-20:t].mean())/100)

    def test_independent_perturbations_and_prefixes(self):
        stock,bundle=fixture()
        full=build_feature_set(stock,"advanced_temporal_context",bundle)
        for pos in (300,390,520):
            date=stock.index[pos]
            for change_stock in (True,False):
                s=stock.copy();b=dict(bundle,series={k:v.copy() for k,v in bundle["series"].items()})
                if change_stock:
                    s.loc[s.index>date,:]*=2
                else:
                    for f in b["series"].values():
                        f.loc[f.index>date,:]*=3
                changed=build_feature_set(s,"advanced_temporal_context",b)
                pd.testing.assert_frame_equal(full.loc[:date,ADVANCED_TEMPORAL_CONTEXT_FEATURES],changed.loc[:date,ADVANCED_TEMPORAL_CONTEXT_FEATURES],check_exact=True)
            b=dict(bundle,series={k:v.loc[:date] for k,v in bundle["series"].items()})
            prefix=build_feature_set(stock.loc[:date],"advanced_temporal_context",b)
            pd.testing.assert_frame_equal(full.loc[:date,ADVANCED_TEMPORAL_CONTEXT_FEATURES],prefix[ADVANCED_TEMPORAL_CONTEXT_FEATURES],check_exact=True)

    def test_price_and_volume_scale(self):
        stock,bundle=fixture();a=context_features(stock,bundle)
        stock[["Open","High","Low","Close"]]*=7;stock["Volume"]*=11
        for symbol,factor in (("SPY",3),("QQQ",5),("XLK",9)):
            bundle["series"][symbol][["Open","High","Low","Close"]]*=factor
        for f in bundle["series"].values(): f["Volume"]*=13
        b=context_features(stock,bundle)
        np.testing.assert_allclose(a,b,atol=1e-8,rtol=1e-8,equal_nan=True)

    def test_registry_metadata_and_previous_mode(self):
        self.assertEqual([len(get_feature_columns(m)) for m in ("basic","advanced","advanced_temporal","advanced_temporal_context")],[10,70,88,132])
        self.assertNotIn("Tomorrow_Return",ADVANCED_TEMPORAL_CONTEXT_FEATURES)
        self.assertEqual(len(set(CONTEXT_FEATURES)),44)
        for name in CONTEXT_FEATURES:
            m=FEATURE_METADATA[name]
            self.assertEqual(m['family'],'context')
            for key in ('alignment','staleness','source','lookback','normalized','future_safe'):
                self.assertIn(key,m)
        stock,bundle=fixture();stock.columns.name="Price"
        old=build_feature_set(stock,"advanced_temporal")
        new=build_feature_set(stock,"advanced_temporal_context",bundle)
        pd.testing.assert_frame_equal(old,new[old.columns])

    @patch("data.context_data.download_context_series")
    def test_cache_download_counts(self,download):
        stock,_=fixture();download.return_value=stock
        cache=ContextCache()
        for ticker in ("AAPL","MSFT","JPM"):
            download_context_bundle(ticker,"2010-01-01",cache=cache)
        self.assertEqual(cache.logical_requests,15)
        self.assertEqual(cache.provider_downloads,6)
        self.assertEqual(download.call_count,6)

    @patch("data.context_data.download_context_series",side_effect=MarketDataError("provider unavailable"))
    def test_required_failure_names_source(self,download):
        with self.assertRaisesRegex(MarketDataError,r"\^VIX failed.*non|\^VIX failed.*Basic"):
            ContextCache().get("^VIX","2010-01-01",None)
        stock,bundle=fixture();del bundle["series"]["SPY"]
        with self.assertRaisesRegex(MarketDataError,"SPY missing"):
            context_features(stock,bundle)

    @patch("models.baseline.RandomForestRegressor")
    def test_finite_matrices_and_training_only_fit(self,forest):
        stock,bundle=fixture()
        f=build_feature_set(stock,"advanced_temporal_context",bundle)
        X,y=prepare_ml_dataset(f,"advanced_temporal_context")
        self.assertTrue(np.isfinite(X.to_numpy()).all())
        split=chronological_split(X,y,stock.index)
        forest.return_value.predict.return_value=np.zeros(len(split["y_test"]))
        forest.return_value.feature_importances_=np.full(132,1/132)
        evaluate_baseline(split,f,"advanced_temporal_context")
        forest.assert_called_once_with(n_estimators=300,random_state=42,n_jobs=-1)
        self.assertIs(forest.return_value.fit.call_args.args[0],split["X_train"])

    @patch("main.download_market_data")
    @patch("builtins.input",return_value="7203.T")
    @patch("builtins.print")
    def test_unsupported_cli_no_download(self,printing,input_mock,download):
        import main
        with patch.object(main,"FEATURE_SET","advanced_temporal_context"):
            self.assertEqual(main.main(),1)
        download.assert_not_called()


class ContextIngestionTests(unittest.TestCase):
    @patch("data.context_data.yf.download")
    def test_index_placeholders_recorded_not_filled(self,download):
        from data.context_data import download_context_series
        stock,_=fixture(200)
        raw=stock.astype(float)
        date=raw.index[20]
        raw.loc[date,["Open","High","Low","Close"]]=np.nan
        raw.loc[date,"Volume"]=0
        download.return_value=raw
        clean=download_context_series("^VIX","2020-01-01","2021-01-01")
        self.assertEqual(len(clean),199)
        self.assertNotIn(date,clean.index)
        self.assertEqual(clean.attrs["empty_quote_dates"],[str(date.date())])
        pd.testing.assert_frame_equal(clean,stock.astype(float).drop(date),check_flags=False)
        self.assertTrue(download.call_args.kwargs["auto_adjust"])
        self.assertTrue(download.call_args.kwargs["keepna"])

    @patch("data.context_data.yf.download")
    def test_partial_invalid_quote_is_rejected(self,download):
        from data.context_data import download_context_series
        stock,_=fixture(200)
        stock.loc[stock.index[20],"Close"]=np.nan
        download.return_value=stock
        with self.assertRaisesRegex(MarketDataError,"non-finite"):
            download_context_series("^TNX","2020-01-01","2021-01-01")
