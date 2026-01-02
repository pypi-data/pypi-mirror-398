from typing import Dict, Sequence
from .base_wrapper import BaseWrapper

import numpy as np


class StoplightWrapper(BaseWrapper[Sequence[Dict[str, float]], np.ndarray]):
    """
        Wrapper for Stoplight scoring.
    """
    def _esol_score(self, esol: float) -> int:
        if esol >= 50:
            return 0
        elif esol >= 10:
            return 1
        else:
            return 2

    def _logP_score(self, logP: float) -> int:
        if logP < 2:
            return 0
        elif logP <= 3:
            return 1
        else:
            return 2

    def _mw_score(self, mw: float) -> int:
        if mw <= 400:
            return 0
        elif mw <= 500:
            return 1
        else:
            return 2

    def _tPSA_score(self, tPSA: float) -> int:
        if tPSA <= 120:
            return 0
        elif tPSA <= 140:
            return 1
        else:
            return 2

    def _rotBond_score(self, rotBond: float) -> int:
        if rotBond <= 7:
            return 0
        elif rotBond < 11:
            return 1
        else:
            return 2

    def _fsp3_score(self, fsp3: float) -> int:
        if fsp3 > 0.3:
            return 0
        elif fsp3 >= 0.2:
            return 1
        else:
            return 2
        
    def _score_from_props(self, props: Dict[str, float]) -> float:
        """
            Compute Stoplight score from a single props dict.
        """
        components = [
            self._esol_score(props['esol_mg/L']),
            self._logP_score(props['logp']),
            self._mw_score(props['mw']),
            self._tPSA_score(props['tpsa']),
            self._rotBond_score(props['num_rotatable_bonds']),
            self._fsp3_score(props['fsp3'])
        ]
        return sum(components) / len(components)

    def predict(self, props_list: Sequence[Dict[str, float]]) -> np.ndarray:
        """
            Compute Stoplight score for each props dict.
        """
        scores = []
        for props in props_list:
            try:
                score = self._score_from_props(props)
            except KeyError as e:
                raise ValueError(f"Missing property for Stoplight scoring: {e}")
            scores.append(score)
        return np.array(scores)
    
    
