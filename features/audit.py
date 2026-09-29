"""Descriptive redundancy diagnostics; never fit selectors or delete columns."""
from itertools import combinations
import pandas as pd


def audit_features(X: pd.DataFrame, correlation_threshold: float = .98,
                   variance_threshold: float = 1e-12) -> dict:
    """Flag exact sample duplicates, constants, tiny variance and correlated pairs.

    Run on training data for research decisions. Near-zero variance uses absolute
    sample variance <= 1e-12 in each feature's documented units.
    """
    constants = X.columns[X.nunique() <= 1].tolist()
    variance = X.var(ddof=1)
    near_zero = variance.index[(variance <= variance_threshold) & ~variance.index.isin(constants)].tolist()
    corr = X.corr()
    duplicates, correlated = [], []
    for a, b in combinations(X.columns, 2):
        if X[a].equals(X[b]):
            duplicates.append([a, b])
        value = corr.loc[a, b]
        if pd.notna(value) and abs(value) >= correlation_threshold:
            correlated.append(dict(feature_a=a, feature_b=b, correlation=float(value)))
    return dict(exact_duplicates=duplicates, constants=constants, near_zero_variance=near_zero,
                high_correlations=correlated, correlation_threshold=correlation_threshold,
                variance_threshold=variance_threshold)
