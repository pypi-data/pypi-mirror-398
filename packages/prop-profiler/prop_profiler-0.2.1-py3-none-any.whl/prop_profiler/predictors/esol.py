import joblib
import logging

from pathlib import Path
from typing import Sequence

import numpy as np
from numpy.typing import NDArray

from prop_profiler.predictors.base import Predictor
from prop_profiler.utils import chem_helpers as chem

logger = logging.getLogger(__name__)


class EsolPredictor(Predictor):
    """
        Predicts ESOL water solubility (log S).
    """
    def __init__(self, model_path: str | Path):
        super().__init__(model_path)
        self._load_model()

    def _load_model(self) -> None:
        model_path = self.model_paths['default']
        if model_path is None:
            raise ValueError("Missing model path for ESOL predictor.")
        self.model = joblib.load(model_path)

    def preprocess(self, mols: Sequence[chem.Mol]) -> NDArray[np.floating]:
        """
            Compute feature vector for a list of molecules.

            Args:
                mols: List of RDKit Mol objects.

            Returns:
                Array of descriptor vectors.
        """
        # Feature computation must be done in the same way as training
        X = np.array([chem.compute_features(mol, True, ['logp']) for mol in mols])
        # cache the molecular weights for later use
        self.mol_weights = np.array([chem.get_props(x, ['mw'])['mw'] for x in mols])
        return X

    def postprocess(self, predictions: NDArray[np.floating]) -> NDArray[np.floating]:
        """
            Convert log of molarity predictions to solubility in mg/L.
        """
        return 10**predictions * self.mol_weights * 1000
            
