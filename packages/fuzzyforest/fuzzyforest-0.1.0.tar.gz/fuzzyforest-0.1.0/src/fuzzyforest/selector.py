from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.utils import check_random_state, check_X_y
from sklearn.utils.validation import check_is_fitted


def _is_classification_target(y: np.ndarray) -> bool:
    """Heuristically decide if the target is categorical."""
    if y.dtype.kind in {"b", "O"}:
        return True
    unique_values = np.unique(y)
    return y.dtype.kind in {"i", "u"} and unique_values.size <= 20


@dataclass
class _SelectionResult:
    importances: np.ndarray
    support_mask: np.ndarray
    ranking: List[int]
    feature_names: Optional[List[str]]


class FuzzyForestSelector(BaseEstimator, TransformerMixin):
    """Stability-focused feature selector using repeated random forests."""

    def __init__(
        self,
        n_estimators: int = 200,
        n_resamples: int = 20,
        sample_fraction: float = 0.8,
        feature_fraction: float = 0.8,
        *,
        task: str = "auto",
        top_k: Optional[int] = None,
        min_importance: float = 0.0,
        random_state: Optional[int] = None,
        n_jobs: Optional[int] = None,
    ) -> None:
        self.n_estimators = n_estimators
        self.n_resamples = n_resamples
        self.sample_fraction = sample_fraction
        self.feature_fraction = feature_fraction
        self.task = task
        self.top_k = top_k
        self.min_importance = min_importance
        self.random_state = random_state
        self.n_jobs = n_jobs

    def fit(self, X, y):
        self._validate_params()
        X, y = check_X_y(X, y, accept_sparse="csr")
        self.n_features_in_ = X.shape[1]
        rng = check_random_state(self.random_state)
        self.feature_names_in_ = self._extract_feature_names(X)

        estimator_cls = self._estimator_class(y)

        importance_sum = np.zeros(self.n_features_in_, dtype=float)
        for _ in range(self.n_resamples):
            rows = rng.choice(
                X.shape[0], max(1, int(self.sample_fraction * X.shape[0])), replace=True
            )
            cols = rng.choice(
                self.n_features_in_,
                max(1, int(self.feature_fraction * self.n_features_in_)),
                replace=False,
            )

            estimator = estimator_cls(
                n_estimators=self.n_estimators,
                random_state=rng.randint(0, 1_000_000_000),
                n_jobs=self.n_jobs,
            )
            estimator.fit(X[rows][:, cols], y[rows])
            importance_sum[cols] += estimator.feature_importances_

        self.feature_importances_ = importance_sum / float(self.n_resamples)

        selection = self._build_selection()
        self.support_mask_ = selection.support_mask
        self.ranking_ = selection.ranking
        self.selected_feature_names_ = selection.feature_names
        return self

    def transform(self, X):
        check_is_fitted(self, "support_mask_")
        if hasattr(X, "iloc"):
            # Pandas path to preserve column labels.
            return X.loc[:, self.support_mask_]
        return X[:, self.support_mask_]

    def get_support(self, indices: bool = False):
        check_is_fitted(self, "support_mask_")
        if indices:
            return np.flatnonzero(self.support_mask_)
        return self.support_mask_

    def get_feature_ranking(self):
        check_is_fitted(self, "ranking_")
        if self.feature_names_in_ is None:
            return self.ranking_
        return [self.feature_names_in_[i] for i in self.ranking_]

    def _build_selection(self) -> _SelectionResult:
        sorted_idx = np.argsort(self.feature_importances_)[::-1]
        mask = np.ones_like(self.feature_importances_, dtype=bool)

        if self.top_k is not None:
            mask = np.zeros_like(mask)
            mask[sorted_idx[: self.top_k]] = True

        if self.min_importance > 0.0:
            mask &= self.feature_importances_ >= self.min_importance

        if not np.any(mask):
            mask = np.zeros_like(mask)
            mask[sorted_idx[0]] = True

        if self.feature_names_in_ is not None:
            ranked_selected = [i for i in sorted_idx if mask[i]]
            feature_names = [self.feature_names_in_[i] for i in ranked_selected]
        else:
            feature_names = None
        return _SelectionResult(
            importances=self.feature_importances_,
            support_mask=mask,
            ranking=sorted_idx.tolist(),
            feature_names=feature_names,
        )

    def _estimator_class(self, y) -> type:
        if self.task not in {"auto", "regression", "classification"}:
            raise ValueError("task must be one of {'auto', 'regression', 'classification'}")

        if self.task == "classification":
            return RandomForestClassifier
        if self.task == "regression":
            return RandomForestRegressor
        return RandomForestClassifier if _is_classification_target(np.asarray(y)) else RandomForestRegressor

    def _extract_feature_names(self, X) -> Optional[List[str]]:
        if hasattr(X, "columns"):
            return list(X.columns)
        return None

    def _validate_params(self) -> None:
        if not (0 < self.sample_fraction <= 1):
            raise ValueError("sample_fraction must be in (0, 1].")
        if not (0 < self.feature_fraction <= 1):
            raise ValueError("feature_fraction must be in (0, 1].")
        if self.n_resamples <= 0:
            raise ValueError("n_resamples must be positive.")
        if self.n_estimators <= 0:
            raise ValueError("n_estimators must be positive.")
        if self.top_k is not None and self.top_k <= 0:
            raise ValueError("top_k must be positive when provided.")
        if self.min_importance < 0:
            raise ValueError("min_importance cannot be negative.")
