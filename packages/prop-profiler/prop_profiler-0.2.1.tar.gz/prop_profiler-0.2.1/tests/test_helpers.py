"""Test utilities and fixtures for prop_profiler tests."""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock
from rdkit import Chem


@pytest.fixture
def sample_smiles_list():
    """Sample SMILES strings for testing."""
    return [
        'CCO',  # ethanol
        'CCCO',  # propanol
        'CCCCO',  # butanol
        'c1ccccc1',  # benzene
        'CC(=O)O',  # acetic acid
        'CCN(CC)CC',  # triethylamine
        'C1CCCCC1',  # cyclohexane
        'CC(C)O',  # isopropanol
        'CCCCCCCCCC',  # decane
        'c1ccc2ccccc2c1'  # naphthalene
    ]


@pytest.fixture
def sample_invalid_smiles():
    """Sample invalid SMILES strings for testing."""
    return [
        'INVALID',
        'not_a_smiles',
        '',
        'CB',  # boron - filtered out
        'X[Y]Z',  # invalid syntax
        '123',  # numbers only
        'C(C)(C)(C)(C)',  # overcomplicated
        'C=C=C=C',  # unusual bonding
    ]


@pytest.fixture
def mock_mol():
    """Mock RDKit molecule object."""
    mol = MagicMock()
    mol.GetNumAtoms.return_value = 10
    mol.GetNumBonds.return_value = 9
    return mol


@pytest.fixture
def mock_prediction_results():
    """Mock prediction results for testing."""
    return {
        'esol': [-0.77, -0.25, -1.5],
        'logd': [0.50, 1.25, 2.0],
        'pka': [9.5, 10.2, 8.8],
        'cns_mpo': [4.2, 3.8, 4.5],
        'stoplight': ['green', 'yellow', 'red']
    }


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame with SMILES and properties."""
    return pd.DataFrame({
        'smiles': ['CCO', 'CCCO', 'CCCCO'],
        'logS': [-0.77, -0.25, -1.5],
        'logD': [0.50, 1.25, 2.0],
        'pKa': [9.5, 10.2, 8.8]
    })


@pytest.fixture
def temp_data_files(tmp_path):
    """Create temporary data files for testing."""
    files = {}
    
    # ESOL data file
    esol_content = "Drug\tY\nCCO\t-0.77\nCCCO\t-0.25\nCCCCO\t-1.5"
    esol_file = tmp_path / "esol_test.tsv"
    esol_file.write_text(esol_content)
    files['esol'] = str(esol_file)
    
    # LogD data file
    logd_content = "smiles,logD\nCCO,0.50\nCCCO,1.25\nCCCCO,2.0"
    logd_file = tmp_path / "logd_test.csv"
    logd_file.write_text(logd_content)
    files['logd'] = str(logd_file)
    
    # SMILES file
    smiles_content = "CCO\nCCCO\nCCCCO"
    smiles_file = tmp_path / "smiles_test.smi"
    smiles_file.write_text(smiles_content)
    files['smiles'] = str(smiles_file)
    
    # SDF file (mock content)
    sdf_content = """
  Mrv2014 01012021

  3  2  0  0  0  0            999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    2.0000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  2  3  1  0  0  0  0
M  END
$$$$
"""
    sdf_file = tmp_path / "test.sdf"
    sdf_file.write_text(sdf_content)
    files['sdf'] = str(sdf_file)
    
    return files


def assert_prediction_format(result, expected_length):
    """Assert that prediction result has correct format."""
    assert isinstance(result, dict)
    assert 'predictions' in result
    assert 'metadata' in result
    assert len(result['predictions']) == expected_length
    
    # Check prediction structure
    for pred in result['predictions']:
        assert 'smiles' in pred
        assert 'esol' in pred
        assert 'logd' in pred
        assert 'pka' in pred
        assert 'cns_mpo' in pred
        assert 'stoplight' in pred


def assert_cli_output_format(output):
    """Assert that CLI output has correct format."""
    assert isinstance(output, str)
    assert len(output) > 0
    # Should contain headers
    assert 'SMILES' in output or 'smiles' in output
    assert 'ESOL' in output or 'esol' in output


def create_mock_model(prediction_value):
    """Create a mock model that returns a specific prediction value."""
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([prediction_value])
    return mock_model


def create_mock_predictor(prediction_value):
    """Create a mock predictor that returns a specific prediction value."""
    mock_predictor = MagicMock()
    mock_predictor.predict.return_value = prediction_value
    return mock_predictor


class MockMolecule:
    """Mock molecule class for testing."""
    
    def __init__(self, smiles, properties=None):
        self.smiles = smiles
        self.properties = properties or {}
    
    def GetNumAtoms(self):
        return 10
    
    def GetNumBonds(self):
        return 9
    
    def GetProp(self, prop_name):
        return self.properties.get(prop_name, '')


def parametrize_smiles():
    """Parametrize decorator for SMILES testing."""
    return pytest.mark.parametrize("smiles", [
        'CCO',
        'CCCO',
        'c1ccccc1',
        'CC(=O)O',
        'CCN(CC)CC'
    ])


def parametrize_invalid_smiles():
    """Parametrize decorator for invalid SMILES testing."""
    return pytest.mark.parametrize("invalid_smiles", [
        'INVALID',
        'not_a_smiles',
        '',
        'CB',
        'X[Y]Z'
    ])


def parametrize_file_formats():
    """Parametrize decorator for file format testing."""
    return pytest.mark.parametrize("file_format", [
        'smi',
        'smiles',
        'sdf',
        'mol'
    ])


# Test data constants
SAMPLE_SMILES = [
    'CCO',
    'CCCO',
    'CCCCO',
    'c1ccccc1',
    'CC(=O)O'
]

INVALID_SMILES = [
    'INVALID',
    'not_a_smiles',
    '',
    'CB',
    'X[Y]Z'
]

EXPECTED_PROPERTIES = [
    'esol',
    'logd',
    'pka',
    'cns_mpo',
    'stoplight'
]

CLI_TEST_CASES = [
    {'args': ['--input', 'test.smi'], 'expected_exit': 0},
    {'args': ['--input', 'test.sdf'], 'expected_exit': 0},
    {'args': ['--input', 'nonexistent.smi'], 'expected_exit': 1},
    {'args': ['--smiles', 'CCO'], 'expected_exit': 0},
    {'args': ['--smiles', 'INVALID'], 'expected_exit': 1},
]
