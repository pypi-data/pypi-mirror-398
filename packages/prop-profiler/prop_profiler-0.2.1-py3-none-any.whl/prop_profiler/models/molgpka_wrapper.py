from pathlib import Path

import numpy as np
from tqdm import tqdm

try:
    from prop_profiler.external.MolGpKa.predict_pka import model_pred, load_model as molgpka_load_model
    from prop_profiler.external.MolGpKa.utils.ionization_group import get_ionization_aid
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from prop_profiler.utils import chem_helpers as chem
from prop_profiler.models.base_wrapper import BaseWrapper


class MolGpKaWrapper(BaseWrapper[list[chem.Mol], np.ndarray]):
    """
        Wrapper for MolGpKa models to provide `predict` interface similar to scikit-learn.
        Accepts two model paths for acidic and basic predictions.
    """
    def __init__(
        self,
        acid_model_path: str | Path,
        base_model_path: str | Path,
        device: str = 'cpu',
        verbose: bool = False
    ):
        """
            Initialize the MolGpKa model wrapper.

            Args:
                acid_model_path: Path to the acid model.
                base_model_path: Path to the base model.
                device: Device to run the model on ('cpu' or 'cuda').
                verbose: Whether to print verbose output.
        """
        if not TORCH_AVAILABLE:
            raise ImportError(
                "PyTorch and torch-geometric are required for pKa prediction. "
                "Install with: pip install prop-profiler[pka]"
            )
        
        self.acid_model_path = acid_model_path
        self.base_model_path = base_model_path
        self.device = device
        self.verbose = verbose
        self.acid_model = molgpka_load_model(acid_model_path, device=device)
        self.base_model = molgpka_load_model(base_model_path, device=device)

    def predict(self, mols: list[chem.Mol]) -> np.ndarray:
        """
            Predict the most basic pKa value for a list of molecules.
            Returns an array of pKa predictions.
        """
        preds = []
        for m in tqdm(mols, total=len(mols), desc='Predicting pKa', disable=not self.verbose):
            # Uncharge and add Hs
            mol = self.standardize(m)

            # Basic pKa
            base_idxs = get_ionization_aid(mol, acid_or_base='base')
            base_vals = [model_pred(mol, aid, self.base_model, device=self.device)
                         for aid in base_idxs]
            if base_vals:
                preds.append(max(base_vals))
                continue

            # Acidic pKa
            acid_idxs = get_ionization_aid(mol, acid_or_base='acid')
            acid_vals = [model_pred(mol, aid, self.acid_model, device=self.device)
                         for aid in acid_idxs]
            if acid_vals:
                preds.append(max(acid_vals))
            else:
                preds.append(np.nan)
        return np.array(preds)
    
    def standardize(self, mol: chem.Mol) -> chem.Mol:
        """
            MolGpKa standardization protocol.  
                1. Uncharge
                2. Sanitize
                3. Add Hs
        """
        uncharged = chem.uncharge_mol(mol)
        sanitized = chem.get_mol(chem.get_smiles(uncharged))
        if sanitized is None:
            raise ValueError("Failed to sanitize molecule for pKa prediction.")
        hmol = chem.add_hydrogens(sanitized)
        return hmol
        
