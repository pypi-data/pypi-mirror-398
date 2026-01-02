import numpy as np
import pandas as pd
import logging

from prop_profiler.utils import chem_helpers as chem

logger = logging.getLogger(__name__)


def load_dataset(path: str, curate: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """
        Load chemical dataset from a CSV file. It must have 'smiles' and 'y' columns.

        Args:
            path: Path to the CSV file.
            curate: Whether to curate the molecules (recommended).

        Returns:
            X: Array of descriptor vectors.
            y: Array of target values.
    """
    data = pd.read_csv(path, usecols=['smiles', 'y'])

    logger.info(f"Input count: {len(data)} molecules")
    if curate:
        data = chem.curate_df(data)
        logger.info(f"Curated count: {len(data)} molecules")

    X = np.array([chem.compute_features(mol, True) for mol in data['mols']])
    y = data['y'].to_numpy()
    
    return X, y
