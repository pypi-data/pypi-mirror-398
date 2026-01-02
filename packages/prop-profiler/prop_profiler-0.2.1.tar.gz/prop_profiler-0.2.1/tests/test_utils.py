import pytest
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import DataStructs
from prop_profiler.utils.chem_helpers import (
    curate_df,
    compute_features,
    get_props,
    get_mfp,
    get_mfpc,
    canonicalize,
    get_mol,
    get_smiles,
    neutralize_mol,
    uncharge_mol,
    keep_largest_fragment,
    contains_boron,
    add_hydrogens,
    is_mol_instance
)

@pytest.fixture
def ala_mol():
    """Alanine uncharged (non-canonical SMILES)."""
    return Chem.MolFromSmiles('C[C@@H](C(=O)O)N')

@pytest.fixture
def charged_ala_mol():
    """Alanine with overall +1 charge."""
    return Chem.MolFromSmiles('C[C@@H](C(=O)O)[NH3+]')

@pytest.fixture
def multi_frag_ala_mol():
    """Alanine + water fragments."""
    return Chem.MolFromSmiles('C[C@@H](C(=O)O)N.O')

@pytest.fixture
def sample_df():
    """DataFrame with valid Ala, invalid SMILES, and boron."""
    return pd.DataFrame({'smiles': ['C[C@@H](C(=O)O)N', 'not_a_smiles', 'CB']})


def test_get_mol_and_instance(ala_mol):
    assert is_mol_instance(ala_mol)
    assert get_mol(' ') is None


def test_get_smiles_and_canonicalize(ala_mol):
    smi = get_smiles(ala_mol)
    # canonical SMILES should match RDKit's MolToSmiles
    assert smi == Chem.MolToSmiles(Chem.MolFromSmiles('C[C@@H](C(=O)O)N'))
    # noncanonical input rounds to same canonical form
    noncanon = 'N[C@@H](C)C(=O)O'
    assert canonicalize(noncanon) == smi


def test_contains_boron():
    assert contains_boron(Chem.MolFromSmiles('CB'))
    assert not contains_boron(Chem.MolFromSmiles('C[C@@H](C(=O)O)N'))


def test_uncharge_vs_neutralize(charged_ala_mol):
    # uncharge_mol should neutralize the total formal charge
    unch = uncharge_mol(charged_ala_mol)
    total_charge = sum(atom.GetFormalCharge() for atom in unch.GetAtoms())
    assert total_charge == 0
    # neutralize_mol should set every atom's formal charge to zero
    neut = neutralize_mol(charged_ala_mol)
    assert all(atom.GetFormalCharge() == 0 for atom in neut.GetAtoms())


def test_keep_largest_fragment(multi_frag_ala_mol):
    k = keep_largest_fragment(multi_frag_ala_mol)
    # largest fragment should be alanine, not water
    assert k.GetNumAtoms() > Chem.MolFromSmiles('O').GetNumAtoms()


def test_add_hydrogens(ala_mol):
    h = add_hydrogens(ala_mol)
    assert h.GetNumAtoms() > ala_mol.GetNumAtoms()


def test_compute_features_count_and_props(ala_mol):
    arr = compute_features(ala_mol)
    assert isinstance(arr, np.ndarray)
    arr2 = compute_features(ala_mol, count_fp=False, additional_props=['mw', 'logp'])
    assert arr2.shape[0] == arr.shape[0] + 2


def test_get_props(ala_mol):
    props = get_props(ala_mol, props=['mw', 'logp'])
    assert set(props) == {'mw', 'logp'}
    all_props = get_props(ala_mol)
    assert set(all_props).issuperset({'mw', 'logp', 'hbd', 'hba'})
    with pytest.raises(ValueError):
        get_props(ala_mol, props=['invalid'])


def test_get_mfp_and_mfpc(ala_mol):
    fp = get_mfp(ala_mol, aslist=True)
    assert isinstance(fp, list)
    fp = get_mfp(ala_mol, aslist=False)
    assert isinstance(fp, DataStructs.cDataStructs.ExplicitBitVect)
    fpc = get_mfpc(ala_mol, aslist=True)
    assert isinstance(fpc, list)
    fpc = get_mfpc(ala_mol, aslist=False)
    assert isinstance(fpc, DataStructs.cDataStructs.UIntSparseIntVect)


def test_curate_df(sample_df):
    curated = curate_df(sample_df)
    assert 'not_a_smiles' not in curated['smiles'].values
    assert 'CB' not in curated['smiles'].values
    assert curated['mols'].notnull().all()

