import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split

# Add the project root to the path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from prop_profiler.data.loader import load_dataset
from prop_profiler.utils.logging import configure_logging
from prop_profiler.training.base_trainer import Trainer

logger = logging.getLogger(__name__)

# Model registry - easy to extend with new models
MODEL_REGISTRY = {
    'esol': {
        'default_data_path': 'data/raw/solubility_aqsoldb.csv',
        'default_model_path': 'prop_profiler/model_weights/esol_model.pkl.gz',
        'task': 'regression',
        'ylabel': 'Experimental logS',
        'xlabel': 'Predicted logS',
        'title': 'ESOL Model Performance'
    },
    'logd': {
        'default_data_path': 'data/raw/DB29_logD_data.csv',
        'default_model_path': 'prop_profiler/model_weights/logd_model.pkl.gz',
        'task': 'regression',
        'ylabel': 'Experimental logD',
        'xlabel': 'Predicted logD',
        'title': 'LogD Model Performance'
    }
}


def create_evaluation_plot(
    y_true: np.ndarray, 
    y_pred: np.ndarray, 
    model_name: str,
    metrics: Dict[str, float],
    output_path: str
) -> None:
    """
        Create and save an evaluation scatter plot with metrics.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            model_name: Name of the model
            metrics: Dictionary of evaluation metrics
            output_path: Path to save the plot
    """
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    ax.scatter(y_pred, y_true, alpha=0.6, s=30, edgecolors='black', linewidth=0.5)
    
    min_val = min(min(y_true), min(y_pred))
    max_val = max(max(y_true), max(y_pred))
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.8, linewidth=2, label='Perfect prediction')
    
    model_config = MODEL_REGISTRY[model_name]
    ax.set_xlabel(model_config['xlabel'], fontsize=12)
    ax.set_ylabel(model_config['ylabel'], fontsize=12)
    ax.set_title(f"{model_config['title']} - Test Set Evaluation", fontsize=14, fontweight='bold')
    
    metrics_text = f"""R² = {metrics['r2']:.3f}
RMSE = {metrics['rmse']:.3f}
MAE = {metrics['mae']:.3f}
N = {len(y_true)}"""
    
    ax.text(0.05, 0.95, metrics_text, transform=ax.transAxes, 
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            fontsize=10, fontfamily='monospace')
    
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower right')
    
    ax.set_aspect('equal', adjustable='box')
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"Evaluation plot saved to: {output_path}")
    plt.close()


def train_model(
    model_name: str,
    cv_folds: int = 5,
    test_size: float = 0.15,
    holdout_size: float = 0.1,
    random_state: int = 42,
    data_path: str | None = None,
    model_path: str | None = None,
    logging_level: int | None = None
) -> Dict[str, Any]:
    """
        Train a model with cross-validation and evaluate on hold-out set.
        
        Args:
            model_name: Name of the model to train
            cv_folds: Number of cross-validation folds
            test_size: Size of test set for CV (not the final holdout)
            holdout_size: Size of final holdout set for evaluation
            random_state: Random state for reproducibility
            data_path: Custom data path (optional)
            model_path: Custom model save path (optional)
            logging_level: Logging level to configure package logging (optional)
            
        Returns:
            Dictionary containing training results and metrics
    """
    if logging_level is not None:
        configure_logging(logging_level)

    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model: {model_name}. Available models: {list(MODEL_REGISTRY.keys())}")
    
    model_config = MODEL_REGISTRY[model_name]
    model_task = model_config.get('task', 'regression')
    
    # Use provided paths or defaults
    final_data_path = data_path or model_config['default_data_path']
    final_model_path = model_path or model_config['default_model_path']
    
    logger.info(f"Training {model_name} model...")
    logger.info(f"Data path: {final_data_path}")
    logger.info(f"Model save path: {final_model_path}")
    
    X, y = load_dataset(final_data_path)
    logger.info(f"Loaded dataset with {len(X)} samples and {X.shape[1]} features")

    trainer = Trainer(
        random_state=random_state,
        logging_level=None
    )
    X_train_cv, X_holdout, y_train_cv, y_holdout = train_test_split(
        X, y,
        test_size=holdout_size,
        random_state=random_state
    )
    
    logger.info(f"Training set size: {len(X_train_cv)}")
    logger.info(f"Holdout set size: {len(X_holdout)}")
    
    trainer.build_model(task=model_task)
    if trainer.model is None:
        raise RuntimeError("Trainer model was not initialized.")
    model = trainer.model
    
    if cv_folds and cv_folds > 1:
        logger.info(f"Performing {cv_folds}-fold cross-validation...")
    else:
        logger.info("Performing train/validation split...")
    cv_results = trainer.fit(
        X=X_train_cv,
        y=y_train_cv,
        cv=cv_folds,
        test_size=test_size
    )
    if not cv_folds or cv_folds <= 1:
        model.fit(X_train_cv, y_train_cv)
    
    result_label = "Cross-validation" if cv_folds and cv_folds > 1 else "Validation"
    logger.info(f"{result_label} results:")
    for metric, scores in cv_results.items():
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        logger.info(f"  {metric}: {mean_score:.4f} ± {std_score:.4f}")
    
    logger.info("Evaluating on holdout set...")
    holdout_metrics = trainer._evaluate_model(X_holdout, y_holdout)
    
    logger.info("Holdout set results:")
    for metric, score in holdout_metrics.items():
        logger.info(f"  {metric}: {score:.4f}")
    
    # Create evaluation plot
    figure_path = None
    if model_task == 'regression':
        y_holdout_pred = model.predict(X_holdout)
        figure_path = f"figures/{model_name}_model_test_set.png"
        create_evaluation_plot(y_holdout, y_holdout_pred, model_name, holdout_metrics, figure_path)
    
    # Save the model
    trainer.save_model(path=final_model_path)
    logger.info(f"Model saved to: {final_model_path}")
    
    return {
        'model_name': model_name,
        'cv_results': cv_results,
        'holdout_metrics': holdout_metrics,
        'n_train': len(X_train_cv),
        'n_holdout': len(X_holdout),
        'model_path': final_model_path,
        'figure_path': figure_path
    }


def main():
    """Main function to handle command line arguments and orchestrate training."""
    parser = argparse.ArgumentParser(
        description="Train and evaluate prop_profiler models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python update_model.py esol                    # Train ESOL model with defaults
    python update_model.py logd --cv 10            # Train LogD with 10-fold CV
    python update_model.py esol --holdout 0.2      # Use 20% holdout set
        """
    )
    
    parser.add_argument(
        'model_name',
        choices=list(MODEL_REGISTRY.keys()),
        help='Name of the model to train'
    )
    
    parser.add_argument(
        '--cv', '--cv-folds',
        type=int,
        default=5,
        help='Number of cross-validation folds (default: 5)'
    )
    
    parser.add_argument(
        '--test-size',
        type=float,
        default=0.15,
        help='Test set size for CV splits (default: 0.15)'
    )
    
    parser.add_argument(
        '--holdout',
        type=float,
        default=0.1,
        help='Holdout set size for final evaluation (default: 0.1)'
    )
    
    parser.add_argument(
        '--random-state',
        type=int,
        default=42,
        help='Random state for reproducibility (default: 42)'
    )
    
    parser.add_argument(
        '--data-path',
        type=str,
        help='Custom path to training data'
    )
    
    parser.add_argument(
        '--model-path',
        type=str,
        help='Custom path to save the trained model'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    configure_logging(logging.DEBUG if args.verbose else logging.INFO)
    
    try:
        # Train the model
        results = train_model(
            model_name=args.model_name,
            cv_folds=args.cv,
            test_size=args.test_size,
            holdout_size=args.holdout,
            random_state=args.random_state,
            data_path=args.data_path,
            model_path=args.model_path,
            logging_level=None
        )
        
        logger.info("Training completed successfully!")
        logger.info(f"Results summary for {results['model_name']}:")
        logger.info(f"  Training samples: {results['n_train']}")
        logger.info(f"  Holdout samples: {results['n_holdout']}")
        for metric, score in results['holdout_metrics'].items():
            logger.info(f"  Holdout {metric}: {score:.4f}")
        logger.info(f"  Model saved: {results['model_path']}")
        if results['figure_path']:
            logger.info(f"  Figure saved: {results['figure_path']}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
