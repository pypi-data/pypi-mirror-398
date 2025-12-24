from __future__ import annotations

from typing import Optional

from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.utils.validation import check_is_fitted

from .selector import FuzzyForestSelector


class FuzzyForestRegressor(BaseEstimator, RegressorMixin):
    """Regressor that uses FuzzyForestSelector for feature ranking before fitting."""

    def __init__(
        self,
        *,
        n_estimators: int = 200,
        n_resamples: int = 20,
        sample_fraction: float = 0.8,
        feature_fraction: float = 0.8,
        top_k: Optional[int] = None,
        min_importance: float = 0.0,
        final_n_estimators: int = 300,
        random_state: Optional[int] = None,
        n_jobs: Optional[int] = None,
    ) -> None:
        self.n_estimators = n_estimators
        self.n_resamples = n_resamples
        self.sample_fraction = sample_fraction
        self.feature_fraction = feature_fraction
        self.top_k = top_k
        self.min_importance = min_importance
        self.final_n_estimators = final_n_estimators
        self.random_state = random_state
        self.n_jobs = n_jobs

    def fit(self, X, y):
        self.selector_ = FuzzyForestSelector(
            n_estimators=self.n_estimators,
            n_resamples=self.n_resamples,
            sample_fraction=self.sample_fraction,
            feature_fraction=self.feature_fraction,
            task="regression",
            top_k=self.top_k,
            min_importance=self.min_importance,
            random_state=self.random_state,
            n_jobs=self.n_jobs,
        )
        self.selector_.fit(X, y)

        X_selected = self.selector_.transform(X)
        self.model_ = RandomForestRegressor(
            n_estimators=self.final_n_estimators,
            random_state=self.random_state,
            n_jobs=self.n_jobs,
        )
        self.model_.fit(X_selected, y)

        self.feature_importances_ = self.selector_.feature_importances_
        self.selected_features_ = self.selector_.selected_feature_names_
        return self

    def predict(self, X):
        check_is_fitted(self, "model_")
        X_selected = self.selector_.transform(X)
        return self.model_.predict(X_selected)

    def score(self, X, y):
        return r2_score(y, self.predict(X))
