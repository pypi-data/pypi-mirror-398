from typing import List, Sequence

import numpy as np

from prop_profiler.predictors.base import Predictor
from prop_profiler.models.stoplight_wrapper import StoplightWrapper
from prop_profiler.utils import chem_helpers as chem


class StoplightPredictor(Predictor):
    """
    Predicts Stoplight color coding using ESOL and RDKit descriptors.
    """
    def __init__(self, esol_predictor: Predictor):
        super().__init__(model_path=None)
        self.esol = esol_predictor
        self.model = StoplightWrapper()

        self.stoplight_colors = {
            0: 'green',
            1: 'yellow',
            2: 'red',
        }

    def _load_model(self) -> None:
        pass

    def preprocess(self, mols: Sequence[chem.Mol]) -> List[dict[str, float]]:
        """
            Prepare model input.

            Args:
                mols: List of RDKit Mol objects.
                
            Returns:
                List of dictionaries with computed properties.
        """
        props_needed = [
            'logp', 'mw', 'tpsa', 'num_rotatable_bonds', 'fsp3'
        ]
        props_list = [chem.get_props(mol, props_needed) for mol in mols]
        esols = self.esol.predict(mols)
        esols = self.esol.postprocess(esols)
        for i, props in enumerate(props_list):
            props['esol_mg/L'] = esols[i]
        # cache the molecular properties for possible later use
        self.mol_props = props_list
        return props_list
    
    def postprocess(self, predictions: np.ndarray) -> List[str]:
        """
            Convert model predictions to Stoplight colors.

            Args:
                predictions: Model predictions between 0 and 2.

            Returns:
                List of Stoplight colors.
        """
        return [self.stoplight_colors[2] if p >= 1 else 
                self.stoplight_colors[1] if p > 0 else 
                self.stoplight_colors[0] for p in predictions]
        
