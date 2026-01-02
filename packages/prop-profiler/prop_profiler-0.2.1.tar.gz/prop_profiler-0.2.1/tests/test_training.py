import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.pipeline import Pipeline

from prop_profiler.training.base_trainer import Trainer


class TestTrainer:
    """Test trainer functionality."""

    def test_trainer_init_defaults(self):
        trainer = Trainer()

        assert trainer.random_state == 42
        assert trainer.model is None

    def test_build_model_regression(self):
        trainer = Trainer(random_state=123)
        trainer.build_model(task='regression')

        assert isinstance(trainer.model, Pipeline)
        assert 'scaler' in trainer.model.named_steps
        assert 'regressor' in trainer.model.named_steps
        assert isinstance(trainer.model.named_steps['regressor'], RandomForestRegressor)
        assert trainer.model.named_steps['regressor'].random_state == 123

    def test_build_model_classification(self):
        trainer = Trainer(random_state=7)
        trainer.build_model(task='classification')

        assert isinstance(trainer.model, Pipeline)
        assert 'scaler' in trainer.model.named_steps
        assert 'classifier' in trainer.model.named_steps
        assert isinstance(trainer.model.named_steps['classifier'], RandomForestClassifier)
        assert trainer.model.named_steps['classifier'].random_state == 7

    def test_build_model_invalid_task(self):
        trainer = Trainer()

        with pytest.raises(ValueError, match="Unsupported task type"):
            trainer.build_model(task='clustering')

    def test_cross_validate_returns_metric_dict(self):
        trainer = Trainer()
        trainer.model = DummyRegressor()

        X = np.zeros((4, 2))
        y = np.ones(4)
        mock_results = {
            'test_r2': np.array([0.1, 0.2]),
            'test_neg_mean_squared_error': np.array([-1.0, -2.0]),
            'test_neg_mean_absolute_error': np.array([-0.5, -0.6]),
            'test_neg_root_mean_squared_error': np.array([-1.0, -1.2]),
        }

        with patch('prop_profiler.training.base_trainer.cross_validate', return_value=mock_results) as mock_cv:
            results = trainer._cross_validate(X, y, cv=2)

        scoring = trainer._get_scoring()
        mock_cv.assert_called_once_with(
            trainer.model,
            X,
            y,
            cv=2,
            scoring=scoring,
            return_train_score=False
        )
        assert set(results.keys()) == set(scoring)
        for metric in scoring:
            assert np.array_equal(results[metric], mock_results[f'test_{metric}'])

    def test_fit_with_cv_calls_model_fit(self):
        trainer = Trainer()
        trainer.model = DummyRegressor()
        trainer.model.fit = MagicMock()

        X = np.zeros((3, 2))
        y = np.ones(3)

        with patch.object(trainer, '_cross_validate', return_value={'r2': np.array([0.1])}) as mock_cv:
            results = trainer.fit(X, y, cv=2)

        mock_cv.assert_called_once_with(X, y, 2)
        trainer.model.fit.assert_called_once_with(X, y)
        assert results == {'r2': np.array([0.1])}

    def test_fit_without_cv_uses_train_and_evaluate(self):
        trainer = Trainer()
        trainer.model = DummyRegressor()

        X = np.zeros((5, 2))
        y = np.ones(5)

        with patch.object(trainer, '_train_and_evaluate', return_value={'r2': 0.5}) as mock_eval:
            results = trainer.fit(X, y, cv=1, test_size=0.2)

        mock_eval.assert_called_once_with(X, y, 0.2, trainer.random_state)
        assert results == {'r2': 0.5}

    def test_evaluate_model_regression_metrics(self):
        trainer = Trainer()
        trainer.model = DummyRegressor()
        trainer.model.predict = MagicMock(return_value=np.array([1.0, 2.0]))

        X_val = np.array([[0.0], [1.0]])
        y_val = np.array([1.5, 2.5])
        metrics = trainer._evaluate_model(X_val, y_val)

        assert metrics['mse'] == pytest.approx(0.25)
        assert metrics['rmse'] == pytest.approx(0.5)
        assert metrics['mae'] == pytest.approx(0.5)
        assert metrics['r2'] == pytest.approx(0.0)
