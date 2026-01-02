import logging
from pathlib import Path
from typing import Sequence

from prop_profiler.predictors.base import Predictor
from prop_profiler.models.molgpka_wrapper import MolGpKaWrapper
from prop_profiler.utils import chem_helpers as chem

logger = logging.getLogger(__name__)


class PkaPredictor(Predictor):
    """
        Predicts the most basic pKa using MolGpKaWrapper.
    """
    def __init__(
        self,
        acid_model_path: str | Path,
        base_model_path: str | Path,
        device: str = 'cpu',
        verbose: bool = False
    ):
        """
            Initialize the pKa predictor.

            Args:
                acid_model_path: Path to the acid model.
                base_model_path: Path to the base model.
                device: Device to run the model on ('cpu' or 'cuda').
                verbose: Whether to print verbose output.
        """
        super().__init__(acid=acid_model_path, base=base_model_path)
        self.device = device
        self.verbose = verbose
        self._load_model()

    def _load_model(self) -> None:
        acid_model_path = self.model_paths.get('acid')
        base_model_path = self.model_paths.get('base')
        if acid_model_path is None or base_model_path is None:
            raise ValueError("Both acid and base model paths are required for pKa prediction.")
        molgpka = MolGpKaWrapper(
            acid_model_path=acid_model_path,
            base_model_path=base_model_path,
            device=self.device,
            verbose=self.verbose
        )
        self.model = molgpka

    def preprocess(self, mols: Sequence[chem.Mol]) -> list[chem.Mol]:
        """
            Preprocess the input molecules.

            Args:
                mols: List of RDKit Mol objects.

            Returns:
                List of RDKit Mol objects (identity transform).
        """
        return list(mols)
    
