from typing import Dict, Sequence

import numpy as np

from prop_profiler.models.base_wrapper import BaseWrapper


class CnsMpoWrapper(BaseWrapper[Sequence[Dict[str, float]], np.ndarray]):
    """
        Wrapper that computes a CNS-MPO score from provided molecular property dictionaries.
        Each input dict must contain keys: 'mw', 'hbd', 'tpsa', 'logp', 'pka', 'logd'.
    
        Resource: https://doi.org/10.1021/cn100008c
    """
    def __init__(self) -> None:
        pass

    def _t0_mw(self, mw: float) -> float:
        if mw < 360:
            return 1.0
        elif mw < 500:
            return -1/140 * mw + 500/140
        else:
            return 0.0

    def _t0_hbd(self, hbd: float) -> float:
        if hbd < 0.5:
            return 1.0
        elif hbd < 3.5:
            return -1/3 * hbd + 3.5/3
        else:
            return 0.0

    def _t0_tPSA(self, tPSA: float) -> float:
        if tPSA < 20:
            return 0.0
        elif tPSA < 40:
            return 1/20 * tPSA - 1
        elif tPSA < 90:
            return 1.0
        elif tPSA < 120:
            return -1/30 * tPSA + 120/30
        else:
            return 0.0

    def _t0_logP(self, logP: float) -> float:
        if logP < 3.0:
            return 1.0
        elif logP < 5.0:
            return -1/2 * logP + 5/2
        else:
            return 0.0

    def _t0_pKa(self, pKa: float) -> float:
        if pKa < 8.0:
            return 1.0
        elif pKa < 10.0:
            return -1/2 * pKa + 5.0
        else:
            return 0.0

    def _t0_logD(self, logD: float) -> float:
        if logD < 2.0:
            return 1.0
        elif logD < 4.0:
            return -1/2 * logD + 2.0
        else:
            return 0.0

    def _score_from_props(self, props: Dict[str, float]) -> float:
        """
            Compute CNS-MPO score from a single props dict.
        """
        components = [
            self._t0_mw(props['mw']),
            self._t0_hbd(props['hbd']),
            self._t0_tPSA(props['tpsa']),
            self._t0_logP(props['logp']),
            self._t0_pKa(props['most_basic_pka']),
            self._t0_logD(props['logd'])
        ]
        return sum(components)

    def predict(self, props_list: Sequence[Dict[str, float]]) -> np.ndarray:
        """
            Compute CNS-MPO scores for a list of property dicts.
        """
        scores = []
        for props in props_list:
            try:
                score = self._score_from_props(props)
            except KeyError as e:
                raise ValueError(f"Missing property for CNS-MPO scoring: {e}")
            scores.append(score)
        return np.array(scores)
    
