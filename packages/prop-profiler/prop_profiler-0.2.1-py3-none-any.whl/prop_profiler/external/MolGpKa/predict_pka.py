#!/usr/bin/env python
# coding: utf-8

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import RDLogger
RDLogger.DisableLog('rdApp.*')
from rdkit.Chem.MolStandardize import rdMolStandardize

from pathlib import Path

import torch
from .utils.ionization_group import get_ionization_aid
from .utils.descriptor import mol2vec
from .utils.net import GCNNet

def get_model_path(model_name):
    """Get the absolute path to a model file in a robust way."""
    current_file = Path(__file__).resolve()
    models_dir = current_file.parent.parent.parent / "models"
    model_path = models_dir / model_name
    if model_path.exists():
        return str(model_path)
    
    try:
        import prop_profiler
        package_root = Path(prop_profiler.__file__).parent
        model_path = package_root / "models" / model_name
        if model_path.exists():
            return str(model_path)
    except ImportError:
        pass
    
    try:
        from importlib import resources
        if hasattr(resources, 'files'):
            model_path = resources.files('prop_profiler') / 'models' / model_name
            if model_path.is_file():
                return str(model_path)
    except (ImportError, AttributeError):
        pass
    
    raise FileNotFoundError(f"Could not find model file: {model_name}")

def load_model(model_file, device="cpu"):
    model= GCNNet().to(device)
    model.load_state_dict(torch.load(model_file, map_location=device, weights_only=True))
    model.eval()
    return model

def model_pred(m2, aid, model, device="cpu"):
    data = mol2vec(m2, aid)
    with torch.no_grad():
        data = data.to(device)
        pKa = model(data)
        pKa = pKa.cpu().numpy()
        pka = pKa[0][0]
    return pka

def predict_acid(mol):
    model_file = get_model_path("weight_acid.pth")
    model_acid = load_model(model_file)

    acid_idxs= get_ionization_aid(mol, acid_or_base="acid")
    acid_res = {}
    for aid in acid_idxs:
        apka = model_pred(mol, aid, model_acid)
        acid_res.update({aid:apka})
    return acid_res

def predict_base(mol):
    model_file = get_model_path("weight_base.pth")
    model_base = load_model(model_file)

    base_idxs= get_ionization_aid(mol, acid_or_base="base")
    base_res = {}
    for aid in base_idxs:
        bpka = model_pred(mol, aid, model_base) 
        base_res.update({aid:bpka})
    return base_res

def predict(mol, uncharged=True):
    if uncharged:
        un = rdMolStandardize.Uncharger()
        mol = un.uncharge(mol)
        mol = Chem.MolFromSmiles(Chem.MolToSmiles(mol))
    mol = AllChem.AddHs(mol)
    base_dict = predict_base(mol)
    acid_dict = predict_acid(mol)
    return base_dict, acid_dict

def predict_for_protonate(mol, uncharged=True):
    if uncharged:
        un = rdMolStandardize.Uncharger()
        mol = un.uncharge(mol)
        mol = Chem.MolFromSmiles(Chem.MolToSmiles(mol))
    mol = AllChem.AddHs(mol)
    base_dict = predict_base(mol)
    acid_dict = predict_acid(mol)
    return base_dict, acid_dict, mol


if __name__=="__main__":
    mol = Chem.MolFromSmiles("CN(C)CCCN1C2=CC=CC=C2SC2=C1C=C(C=C2)C(C)=O")
    base_dict, acid_dict = predict(mol)
    print("base:",base_dict)
    print("acid:",acid_dict)

