from typing import List, Sequence

from prop_profiler.predictors.base import Predictor
from prop_profiler.models.cns_mpo_wrapper import CnsMpoWrapper
from prop_profiler.utils import chem_helpers as chem


class CnsMpoPredictor(Predictor):
    """
        Predictor for CNS-MPO.
    """
    def __init__(
        self,
        pka_predictor: Predictor,
        logd_predictor: Predictor,
    ):
        super().__init__(model_path=None)
        self.pka = pka_predictor
        self.logd = logd_predictor
        self.model = CnsMpoWrapper()

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
        props_needed = ['mw', 'logp', 'tpsa', 'hbd']
        props_list = [chem.get_props(mol, props_needed) for mol in mols]
        pkas = self.pka.predict(mols)
        logds = self.logd.predict(mols)
        for i, props in enumerate(props_list):
            props['most_basic_pka'] = pkas[i]
            props['logd'] = logds[i]
        # cache the molecular properties for possible later use
        self.mol_props = props_list
        return props_list
