import logging

import joblib
import numpy as np
from typing import Mapping, TypeAlias

from sklearn import metrics as m
from sklearn.model_selection import train_test_split, cross_validate
from sklearn.base import RegressorMixin, ClassifierMixin, is_classifier, is_regressor
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from numpy.typing import NDArray

from prop_profiler.utils.logging import configure_logging

logger = logging.getLogger(__name__)

MetricValue: TypeAlias = float | NDArray[np.floating]


class Trainer:
    """
        Training workflow with optional cross-validation and metric detection.
    """
    def __init__(
        self,
        random_state: int = 42,
        logging_level: int | None = None,
        **kwargs
    ):
        """
            Initialize the trainer with a random seed and logging level.

            Args:
                random_state: Random seed for reproducibility.
                logging_level: Logging verbosity for the trainer logger. If None,
                    logging configuration is left unchanged.
        """
        self.random_state = random_state
        if logging_level is not None:
            configure_logging(logging_level)
        logger.info("Initializing Trainer")

        self.model: RegressorMixin | ClassifierMixin | None = None

    def build_model(
        self, 
        estimator: str = 'random_forest',
        task: str = 'regression',
        **kwargs
    ) -> None:
        """
            Build the model pipeline based on estimator and task type.

            Args:
                estimator: Type of model to build ('random_forest', etc.)
                task: 'regression' or 'classification'
                kwargs: Additional parameters for model configuration
        """
        logger.info(f"Building model: estimator={estimator}, task={task}, params={kwargs}")
        if task == 'regression':
            if estimator == 'random_forest':
                self.model = Pipeline([
                    ('scaler', MinMaxScaler()),
                    ('regressor', RandomForestRegressor(
                        n_estimators=kwargs.get('n_estimators', 100),
                        max_depth=kwargs.get('max_depth', None),
                        random_state=self.random_state,
                        n_jobs=kwargs.get('n_jobs', -1)
                    ))
                ])
            else:
                raise ValueError("Unsupported estimator type for regression.")
        elif task == 'classification':
            if estimator == 'random_forest':
                self.model = Pipeline([
                    ('scaler', MinMaxScaler()),
                    ('classifier', RandomForestClassifier(
                        n_estimators=kwargs.get('n_estimators', 100),
                        max_depth=kwargs.get('max_depth', None),
                        random_state=self.random_state,
                        n_jobs=kwargs.get('n_jobs', -1)
                    ))
                ])
            else:
                raise ValueError("Unsupported estimator type for classification.")
        else:
            raise ValueError("Unsupported task type. Use 'regression' or 'classification'.")

    def fit(
        self,
        X: NDArray[np.number],
        y: NDArray[np.number],
        cv: int | None = None,
        test_size: float | None = None,
    ) -> Mapping[str, MetricValue]:
        """
            Train the model. Allows overriding data, CV, split size, and random state.
            Returns a dict of scores.
        """
        if self.model is None:
            raise ValueError("Model is not initialized; call build_model first.")
        model = self.model
        if cv and cv > 1:
            logger.info(f"Performing {cv}-fold cross-validation")
            cv_results = self._cross_validate(X, y, cv)
            model.fit(X, y)
            return cv_results
        else:
            logger.info("Performing train/validation split evaluation")
            return self._train_and_evaluate(X, y, test_size, self.random_state)
        
    def _cross_validate(
        self,
        X: NDArray[np.number],
        y: NDArray[np.number],
        cv: int
    ) -> Mapping[str, MetricValue]:
        """
            Perform cross-validation and return scoring dictionary.
        """
        if self.model is None:
            raise ValueError("Model is not initialized; call build_model first.")
        scoring = self._get_scoring()
        results = cross_validate(
            self.model, X, y,
            cv=cv,
            scoring=scoring,
            return_train_score=False
        )
        return {metric: results[f'test_{metric}'] for metric in scoring}

    def _train_and_evaluate(
        self,
        X: NDArray[np.number],
        y: NDArray[np.number],
        test_size: float | None,
        random_state: int
    ) -> dict[str, float]:
        """
            Train on a single split and evaluate metrics.
        """
        if self.model is None:
            raise ValueError("Model is not initialized; call build_model first.")
        X_train, X_val, y_train, y_val = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state
        )
        self.model.fit(X_train, y_train)
        return self._evaluate_model(X_val, y_val)

    def _get_scoring(self) -> list[str]:
        """
            Determine appropriate scoring metrics based on model type.
        """
        if self.model is None:
            raise ValueError("Model is not initialized; call build_model first.")
        if is_classifier(self.model):
            return ['accuracy', 'precision', 'recall', 'f1']
        elif is_regressor(self.model):
            return ['r2', 'neg_mean_squared_error', 'neg_mean_absolute_error', 
                    'neg_root_mean_squared_error']
        else:
            raise ValueError("Unsupported model type for scoring")

    def _evaluate_model(
        self,
        X_val: NDArray[np.number],
        y_val: NDArray[np.number]
    ) -> dict[str, float]:
        """
            Evaluate on a validation split and return metrics.
        """
        if self.model is None:
            raise ValueError("Model is not initialized; call build_model first.")
        preds = self.model.predict(X_val)
        if is_classifier(self.model):
            return {
                'accuracy': m.accuracy_score(y_val, preds),
                'precision': m.precision_score(y_val, preds, average='weighted'),
                'recall': m.recall_score(y_val, preds, average='weighted'),
                'f1': m.f1_score(y_val, preds, average='weighted')
            }
        elif is_regressor(self.model):
            return {
                'mse': m.mean_squared_error(y_val, preds),
                'rmse': m.root_mean_squared_error(y_val, preds),
                'mae': m.mean_absolute_error(y_val, preds),
                'r2': m.r2_score(y_val, preds)
            }
        else:
            raise ValueError("Unsupported model type for evaluation")

    def save_model(self, path: str | None = None) -> None:
        """Serialize the trained model to disk using joblib with compression."""
        logger.info(f"Saving model to {path}")
        joblib.dump(self.model, path, compress=('gzip', 6))
