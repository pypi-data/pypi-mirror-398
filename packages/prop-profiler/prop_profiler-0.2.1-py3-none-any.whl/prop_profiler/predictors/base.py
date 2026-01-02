import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Sequence, cast

import pandas as pd
import numpy as np
from tqdm import tqdm

from prop_profiler.utils import chem_helpers as chem

logger = logging.getLogger(__name__)


class Predictor(ABC):
    """
        Base class for molecular property predictors.
        Supports a primary model via `model_path` and optional named models via kwargs.
    """
    def __init__(
        self,
        model_path: str | Path | None = None,
        **model_paths: str | Path
    ):
        # Primary model under 'default'; additional models under their kwargs names
        self.model_paths: Dict[str, str | Path | None] = {'default': model_path}
        self.model_paths.update(model_paths)
        self.model: Any | None = None

    @abstractmethod
    def _load_model(self):
        """
            Load model(s) into `self.model`. Multi-model predictors 
            should be wrapped to have a single predict logic.
        """
        pass

    @abstractmethod
    def preprocess(self, mols: Sequence[chem.Mol]) -> Any:
        """Compute feature vector for a list of molecules."""
        pass

    def postprocess(self, predictions: Any) -> Any:
        """Post-process the predictions if needed."""
        return predictions

    def predict(
        self,
        mols: Sequence[chem.Mol],
        batch_size: int = 256,
        verbose: bool = False
    ) -> np.ndarray:
        """
            Predict property values for a list of molecules.

            NOTE: Run Predictor.curate() before this method to ensure valid input.
                Otherwise, it will fail on invalid SMILES or RDKit Mol objects.

            Args:
                mols: List of RDKit Mol objects.

            Returns:
                Array of predictions.
        """
        if self.model is None:
            self._load_model()
        if self.model is None:
            raise ValueError("Model is not initialized; call _load_model first.")
        model = self.model
        feats = self.preprocess(mols)
        preds = np.zeros(len(feats))
        for i in tqdm(range(0, len(feats), batch_size), desc='Predicting', total=len(feats)//batch_size, disable=not verbose):
            batch = feats[i:i+batch_size]
            pred = model.predict(batch)
            preds[i:i+batch_size] = pred
        return preds
    
    def curate(self, mols: Sequence[chem.Mol] | Sequence[str]) -> list[chem.Mol]:
        """
            Curate the input molecules.

            Args:
                mols: List of SMILES or RDKit Mol objects.

            Returns:
                List of RDKit Mol objects.
        """
        mols_list = list(mols)
        if len(mols_list) == 0:
            return []
        
        if chem.is_mol_instance(mols_list[0]):
            mols_smiles = [chem.get_smiles(cast(chem.Mol, mol)) for mol in mols_list]
        else:
            mols_smiles = cast(list[str], mols_list)
        initial_count = len(mols_smiles)
        curated = chem.curate_df(pd.DataFrame({'smiles': mols_smiles}))['mols'].tolist()
        logger.info(
            f"Curated molecule count: {len(curated)}, dropped {initial_count - len(curated)} molecules."
        )
        return curated
    
