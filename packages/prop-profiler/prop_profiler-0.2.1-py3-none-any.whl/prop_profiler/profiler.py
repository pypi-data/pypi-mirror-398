import os
import sys
from pathlib import Path
from typing import Sequence
from typing import cast

import pandas as pd

from prop_profiler.utils import chem_helpers as chem
from prop_profiler.predictors.cns_mpo import CnsMpoPredictor
from prop_profiler.predictors.stoplight import StoplightPredictor
from prop_profiler.predictors.esol import EsolPredictor


def _get_model_path(filename: str, env_var: str | None = None) -> Path:
    """
    Resolve a model filename to an on-disk path.

    Env vars (if set) take precedence:
    - Per-model override: `env_var`
    - Shared model directory: `PROP_PROFILER_MODEL_DIR`
    """
    if env_var:
        override = os.getenv(env_var)
        if override:
            override_path = Path(override).expanduser()
            if not override_path.exists():
                raise FileNotFoundError(f"Model file not found: {override_path}")
            return override_path
    model_dir = os.getenv("PROP_PROFILER_MODEL_DIR")
    if model_dir:
        candidate = Path(model_dir).expanduser() / filename
        if not candidate.exists():
            raise FileNotFoundError(f"Model file not found: {candidate}")
        return candidate
    if sys.version_info >= (3, 9):
        try:
            from importlib import resources
            package_root = resources.files('prop_profiler')
            models_path = Path(cast(Path, package_root)) / 'model_weights'
            model_path = models_path / filename
            if model_path.exists():
                return model_path
        except (ImportError, AttributeError):
            pass
    
    root_dir = Path(__file__).resolve().parent.parent
    model_path = root_dir / 'prop_profiler' / 'model_weights' / filename
    
    if model_path.exists():
        return model_path
    else:
        raise FileNotFoundError(f"Model file not found: {filename}")

ESOL_MODEL = _get_model_path('esol_model.pkl.gz', env_var='PROP_PROFILER_ESOL_MODEL')
LOGD_MODEL = _get_model_path('logd_model.pkl.gz', env_var='PROP_PROFILER_LOGD_MODEL')
ACID_MODEL = _get_model_path('weight_acid.pth', env_var='PROP_PROFILER_ACID_MODEL')
BASE_MODEL = _get_model_path('weight_base.pth', env_var='PROP_PROFILER_BASE_MODEL')


def profile_molecules(
    molecules: Sequence[chem.Mol] | Sequence[str],
    skip_cns_mpo: bool = False,
    skip_curation: bool = False,
    device: str = 'cpu',
    verbose: bool = False
) -> pd.DataFrame:
    """
        Compute descriptor-based properties and optional CNS-MPO scores.

        Args:
            molecules: RDKit Mol objects or SMILES strings.
            skip_cns_mpo: If True, omit CNS-MPO scoring along with logD and pKa.
            skip_curation: If True, skip curation and treat inputs as RDKit Mol objects.
            device: Device to run the pka model on, 'cpu' or 'cuda'.
            verbose: If True, display progress bars.

        Returns:
            DataFrame with properties and scores.
    """
    stoplight = StoplightPredictor(
        esol_predictor=EsolPredictor(ESOL_MODEL)
    )
    if skip_curation:
        mols = list(cast(Sequence[chem.Mol], molecules))
        if len(mols) > 0 and not chem.is_mol_instance(mols[0]):
            raise TypeError("skip_curation expects RDKit Mol inputs.")
    else:
        mols = stoplight.curate(molecules)
    mol_props: list[dict[str, float | str]] = [{'smiles': chem.get_smiles(m)} for m in mols]
    stoplight_scores = stoplight.predict(mols, verbose=verbose)
    stoplight_colors = stoplight.postprocess(stoplight_scores)

    if not skip_cns_mpo:
        try:
            from prop_profiler.predictors.logd import LogDPredictor
            from prop_profiler.predictors.pka import PkaPredictor
            
            cns_mpo = CnsMpoPredictor(
                pka_predictor=PkaPredictor(acid_model_path=ACID_MODEL, base_model_path=BASE_MODEL, device=device),
                logd_predictor=LogDPredictor(LOGD_MODEL),
            )
            cns_mpo_scores = cns_mpo.predict(mols, verbose=verbose)
            for i, props in enumerate(mol_props):
                props.update(chem.get_props(mols[i]))
                props.update(stoplight.mol_props[i])
                props.update(cns_mpo.mol_props[i])
                props.update({'cns_mpo_score': cns_mpo_scores[i]})
        except ImportError:
            if verbose:
                print("Warning: PyTorch not available. Skipping CNS-MPO prediction. Install with: pip install prop-profiler[pka]")
            skip_cns_mpo = True
    
    if skip_cns_mpo:
        for i, props in enumerate(mol_props):
            props.update(chem.get_props(mols[i]))
            props.update(stoplight.mol_props[i])

    # Convert to DataFrame
    df = pd.DataFrame(mol_props)
    df['stoplight_score'] = stoplight_scores
    df['stoplight_color'] = stoplight_colors

    return df
