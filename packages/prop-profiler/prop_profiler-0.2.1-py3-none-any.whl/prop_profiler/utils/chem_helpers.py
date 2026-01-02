"""
    Helper functions for the project.
"""
from copy import deepcopy
from typing import Sequence, Any

import numpy as np
import pandas as pd

from rdkit import Chem
from rdkit.Chem import Descriptors, rdFingerprintGenerator, rdMolDescriptors, QED, PandasTools
from rdkit.Chem.MolStandardize import rdMolStandardize

Mol = Chem.Mol
MolUncharger = rdMolStandardize.Uncharger()
MFPGen = rdFingerprintGenerator.GetMorganGenerator(
    radius=3, fpSize=2048, includeChirality=True, useBondTypes=True,
    atomInvariantsGenerator=rdFingerprintGenerator.GetMorganAtomInvGen(False),
    bondInvariantsGenerator=rdFingerprintGenerator.GetMorganBondInvGen()
)
MOLECULAR_PROPERTIES = {
    'mw': getattr(Descriptors, "MolWt"),
    'logp': getattr(Descriptors, "MolLogP"),
    'hba': rdMolDescriptors.CalcNumHBA,
    'hbd': rdMolDescriptors.CalcNumHBD,
    'tpsa': rdMolDescriptors.CalcTPSA,
    'num_rotatable_bonds': rdMolDescriptors.CalcNumRotatableBonds,
    'fsp3': rdMolDescriptors.CalcFractionCSP3,
    'qed': QED.qed,
}


def curate_df(df: pd.DataFrame) -> pd.DataFrame:
    """
        Curate a dataframe of molecules.
            1. Canonicalize and deduplicate the smiles
            2. Remove fragments except the largest one
            3. Neutralize the molecule
            4. Remove molecules with less than 4 heavy atoms

        args:
            df: dataframe with 'smiles' column

        returns:
            curated dataframe with additional 'mols' column
    """
    df['mols'] = df['smiles'].apply(lambda x: get_mol(x))
    df = df[df['mols'].notnull()]
    df = df[[not contains_boron(x) for x in df['mols'].values]]
    df['smiles'] = df['smiles'].apply(lambda x: canonicalize(x))
    df = df.drop_duplicates(subset='smiles')
    df['mols'] = df['mols'].apply(lambda x: keep_largest_fragment(x))
    df['mols'] = df['mols'].apply(lambda x: neutralize_mol(x))
    df = df[[x.GetNumHeavyAtoms() >= 3 for x in df['mols'].values]]
    df = df.reset_index(drop=True)
    return df

def compute_features(
    mol: Chem.Mol,
    count_fp: bool = True,
    additional_props: Sequence[str] | None = None
) -> np.ndarray:
    """
        Compute features for a molecule.

        args:
            mol: rdkit mol object
            count_fp: if True, compute count fingerprint
            additional_props: list of additional properties to add to the features 
                options: 
                    - mw: molecular weight
                    - logp: logP
                    - hba: number of hydrogen bond acceptors
                    - hbd: number of hydrogen bond donors
                    - tpsa: topological polar surface area
                    - num_rotatable_bonds: number of rotatable bonds
                    - fsp3: fraction of sp3 hybridized carbons
                    - qed: QED score

        returns:
            array of features
    """
    if additional_props is None:
        additional_props = []
    if count_fp:
        fp = MFPGen.GetCountFingerprint(mol).ToList()
    else:
        fp = MFPGen.GetFingerprint(mol).ToList()
    
    if additional_props:
        prop_dict = get_props(mol, additional_props)
        prop_values = list(prop_dict.values())
        return np.array(fp + prop_values)
    else:
        return np.array(fp)

def sdf_to_df(sdf_file: str, smiles_col: str = 'smiles') -> pd.DataFrame:
    """
        Read an SDF file and convert it to a DataFrame.

        args:
            sdf_file: path to the SDF file
            smiles_col: name of the column to store smiles strings

        returns:
            DataFrame with smiles strings and mol objects
    """
    return PandasTools.LoadSDF(
        sdf_file, smilesName=smiles_col, molColName=None,
    )

def get_props(molecule: Chem.Mol | str, props: Sequence[str] | None = None) -> dict[str, float]:
    """
        Calculate molecular properties of a molecule.

        args:
            molecule: rdkit mol object or smiles string
            props: list of properties to calculate, if empty all properties
                will be calculated

        returns:
            dictionary of molecular properties
    """
    if isinstance(molecule, str):
        molecule = Chem.MolFromSmiles(molecule)
    if molecule is None:
        raise ValueError("Invalid molecule input.")
    
    if props is None or len(props) == 0:
        props = list(MOLECULAR_PROPERTIES.keys())

    prop_dict = {}
    for prop in props:
        if prop in MOLECULAR_PROPERTIES:
            prop_dict[prop] = MOLECULAR_PROPERTIES[prop](molecule)
        else:
            raise ValueError(
                f'Property {prop} not found. Currently supported'
                f'properties are: {list(MOLECULAR_PROPERTIES.keys())}'
            )
    return prop_dict

def get_mfp(mol: Chem.Mol | str, aslist: bool = True) -> Any:
    """
        Returns the Morgan Fingerprint of a molecule.

        args:
            mol: rdkit mol object or smiles
            aslist: return the fingerprint as a list

        returns:
            morgan fingerprint as list
    """
    if isinstance(mol, Chem.rdchem.Mol):
        pass
    elif isinstance(mol, str):
        mol = Chem.MolFromSmiles(mol)
    else:
        ValueError('mol should rdkit Mol object or smiles string.')

    if aslist:
        return MFPGen.GetFingerprint(mol).ToList()
    else:
        return MFPGen.GetFingerprint(mol)

def get_mfpc(mol: Chem.Mol | str, aslist: bool = True) -> Any:
    """
        Returns the hashed Morgan Fingerprint of a molecule.

        args:
            mol: rdkit mol object or smiles
            aslist: return the fingerprint as a list

        returns:
            hashed morgan fingerprint as list or rdkit SparseIntVector
    """
    if isinstance(mol, str):
        mol = Chem.MolFromSmiles(mol)
    
    if aslist:
        return MFPGen.GetCountFingerprint(mol).ToList()
    else:
        return MFPGen.GetCountFingerprint(mol)

def canonicalize(smiles: str) -> str | None:
    """
        Returns the canonical smiles of a molecule.

        args:
            smiles: smiles string

        returns:
            canonical smiles or None if invalid
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return Chem.MolToSmiles(mol)

def get_mol(smiles: str) -> Chem.Mol | None:
    """
        Returns the rdkit mol object of a molecule.

        args:
            smiles: smiles string

        returns:
            rdkit mol object
    """
    return Chem.MolFromSmiles(smiles)

def get_smiles(mol: Chem.Mol) -> str:
    """
        Returns the smiles string of a molecule.

        args:
            mol: rdkit mol object

        returns:
            smiles string
    """
    return Chem.MolToSmiles(mol, canonical=True)

def neutralize_mol(mol: Chem.Mol) -> Chem.Mol:
    """
        Neutralize a molecule by removing formal charges and adjusting hydrogen counts.

        args:
            mol: rdkit mol object

        returns:
            rdkit mol object with neutralized charges
    """
    mol_copy = deepcopy(mol)
    try:
        pattern = Chem.MolFromSmarts("[+1!h0!$([*]~[-1,-2,-3,-4]),-1!$([*]~[+1,+2,+3,+4])]")
        at_matches = mol.GetSubstructMatches(pattern)
        at_matches_list = [y[0] for y in at_matches]
        if len(at_matches_list) > 0:
            for at_idx in at_matches_list:
                atom = mol.GetAtomWithIdx(at_idx)
                chg = atom.GetFormalCharge()
                hcount = atom.GetTotalNumHs()
                atom.SetFormalCharge(0)
                atom.SetNumExplicitHs(hcount - chg)
                atom.UpdatePropertyCache()
        return mol
    except Exception as e:
        print(
            f"Curation could not neutralize the molecule, {Chem.MolToSmiles(mol)}. Got error: {e}"
            f"Skipping neutralization for this molecule."
        )
        return mol_copy

def uncharge_mol(mol: Chem.Mol) -> Chem.Mol:
    """
        Uncharge a molecule by removing formal charges.

        args:
            mol: rdkit mol object

        returns:
            rdkit mol object with uncharged atoms
    """
    return MolUncharger.uncharge(mol)

def keep_largest_fragment(mol: Chem.Mol) -> Chem.Mol:
    """
        Keep only the largest fragment of a molecule.
        
        args:
            mol: rdkit mol object

        returns:
            rdkit mol object with only the largest fragment
    """
    frags = Chem.GetMolFrags(mol, asMols=True)
    if len(frags) > 1:
        largest_frag = max(frags, key=lambda x: x.GetNumHeavyAtoms())
        return largest_frag
    else:
        return mol
    
def contains_boron(mol: Chem.Mol) -> bool:
    """
        Check if a molecule contains boron.

        args:
            mol: rdkit mol object

        returns:
            True if the molecule contains boron, False otherwise
    """
    for atom in mol.GetAtoms():
        if atom.GetSymbol() == 'B':
            return True
    return False

def add_hydrogens(mol: Chem.Mol) -> Chem.Mol:
    """
        Add hydrogens to a molecule.

        args:
            mol: rdkit mol object

        returns:
            rdkit mol object with added hydrogens
    """
    return Chem.AddHs(mol)

def is_mol_instance(mol: Any) -> bool:
    """
        Check if the input is a valid rdkit mol object.

        args:
            mol: rdkit mol object

        returns:
            True if the input is a valid rdkit mol object, False otherwise
    """
    return isinstance(mol, Chem.Mol)
