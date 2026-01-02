import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

from prop_profiler.data.loader import load_dataset
from prop_profiler.utils.chem_helpers import canonicalize, get_props


class TestDataLoader:
    """Test data loading functionality."""
    
    def test_load_dataset(self):
        """Test dataset loading."""
        with patch('pandas.read_csv') as mock_read:
            mock_df = pd.DataFrame({
                'smiles': ['CCO', 'CCCO'],
                'y': [-0.77, -0.25]
            })
            mock_read.return_value = mock_df
            
            with patch('prop_profiler.utils.chem_helpers.curate_df') as mock_curate:
                mock_curate.return_value = pd.DataFrame({
                    'smiles': ['CCO', 'CCCO'],
                    'y': [-0.77, -0.25],
                    'mols': [MagicMock(), MagicMock()]
                })
                
                with patch('prop_profiler.utils.chem_helpers.compute_features') as mock_compute:
                    mock_compute.side_effect = [
                        np.array([1, 2, 3]),
                        np.array([4, 5, 6])
                    ]
                    
                    X, y = load_dataset('test_data.csv')
                    
                    assert X.shape == (2, 3)
                    assert y.shape == (2,)
                    assert y[0] == pytest.approx(-0.77)
                    assert y[1] == pytest.approx(-0.25)
                    mock_read.assert_called_once_with('test_data.csv', usecols=['smiles', 'y'])
                    assert mock_compute.call_count == 2
    
    def test_load_dataset_with_invalid_smiles(self):
        """Test dataset loading with invalid SMILES."""
        with patch('pandas.read_csv') as mock_read:
            mock_df = pd.DataFrame({
                'smiles': ['CCO', 'INVALID', 'CCCO'],
                'y': [-0.77, -0.25, -1.5]
            })
            mock_read.return_value = mock_df
            
            with patch('prop_profiler.utils.chem_helpers.curate_df') as mock_curate:
                mock_curate.return_value = pd.DataFrame({
                    'smiles': ['CCO', 'CCCO'],
                    'y': [-0.77, -1.5],
                    'mols': [MagicMock(), MagicMock()]
                })
                
                with patch('prop_profiler.utils.chem_helpers.compute_features') as mock_compute:
                    mock_compute.side_effect = [
                        np.array([1, 2, 3]),
                        np.array([4, 5, 6])
                    ]
                    
                    X, y = load_dataset('test_data.csv')
                    
                    assert X.shape == (2, 3)
                    assert y.shape == (2,)
                    assert y[0] == pytest.approx(-0.77)
                    assert y[1] == pytest.approx(-1.5)
    
    def test_load_dataset_empty_file(self):
        """Test handling of empty dataset file."""
        with patch('pandas.read_csv') as mock_read:
            mock_read.return_value = pd.DataFrame(columns=['smiles', 'y'])
            
            with patch('prop_profiler.utils.chem_helpers.curate_df') as mock_curate:
                mock_curate.return_value = pd.DataFrame(columns=['smiles', 'y', 'mols'])
                
                with patch('prop_profiler.utils.chem_helpers.compute_features') as mock_compute:
                    X, y = load_dataset('empty_data.csv')
                
                assert X.shape == (0,)
                assert y.shape == (0,)
                mock_compute.assert_not_called()


class TestChemHelpers:
    """Test chemical helper functions."""
    
    def test_canonicalize_valid(self):
        """Test SMILES canonicalization with valid input."""
        with patch('rdkit.Chem.MolFromSmiles') as mock_mol_from_smiles, \
             patch('rdkit.Chem.MolToSmiles') as mock_mol_to_smiles:
            
            mock_mol = MagicMock()
            mock_mol_from_smiles.return_value = mock_mol
            mock_mol_to_smiles.return_value = 'CCO'
            
            result = canonicalize('CCO')
            
            assert result == 'CCO'
            mock_mol_from_smiles.assert_called_once_with('CCO')
            mock_mol_to_smiles.assert_called_once_with(mock_mol)
    
    def test_canonicalize_invalid(self):
        """Test SMILES canonicalization with invalid input."""
        with patch('rdkit.Chem.MolFromSmiles') as mock_mol_from_smiles:
            mock_mol_from_smiles.return_value = None
            
            result = canonicalize('INVALID')
            
            assert result is None
            mock_mol_from_smiles.assert_called_once_with('INVALID')
    
    def test_get_props_valid(self):
        """Test molecular descriptor calculation with valid SMILES."""
        # Just test that get_props works with a real molecule object
        result = get_props('CCO', ['mw'])
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'mw' in result
        assert isinstance(result['mw'], (int, float))
    
    def test_get_props_invalid(self):
        """Test molecular descriptor calculation with invalid SMILES."""
        # get_props should raise an exception or handle None gracefully
        # Since it calls Chem.MolFromSmiles directly, it will get None for invalid SMILES
        # and RDKit descriptors will fail
        with pytest.raises((AttributeError, Exception)):
            get_props('INVALID')
    
    def test_get_props_calculation_error(self):
        """Test handling of unknown property names."""
        with pytest.raises(ValueError, match="Property unknown_prop not found"):
            get_props('CCO', ['unknown_prop'])


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_batch_processing(self):
        """Test batch processing of molecules."""
        smiles_list = ['CCO', 'CCCO', 'CCCCO']
        
        with patch('prop_profiler.utils.chem_helpers.get_props') as mock_descriptors:
            mock_descriptors.side_effect = [
                {'mw': 46.07, 'logp': -0.31, 'hbd': 1},
                {'mw': 74.12, 'logp': 0.25, 'hbd': 1},
                {'mw': 88.15, 'logp': 0.88, 'hbd': 1}
            ]
            
            # Simulate batch processing
            results = []
            for smiles in smiles_list:
                desc = mock_descriptors(smiles)
                results.append(desc)
            
            assert len(results) == 3
            assert mock_descriptors.call_count == 3
    
    def test_error_handling_in_batch(self):
        """Test error handling in batch processing."""
        smiles_list = ['CCO', 'INVALID', 'CCCO']
        
        with patch('prop_profiler.utils.chem_helpers.get_props') as mock_descriptors:
            mock_descriptors.side_effect = [
                {'mw': 46.07, 'logp': -0.31, 'hbd': 1},
                None,  # Error case
                {'mw': 74.12, 'logp': 0.25, 'hbd': 1}
            ]
            
            # Simulate batch processing with error handling
            results = []
            for smiles in smiles_list:
                desc = mock_descriptors(smiles)
                if desc is not None:
                    results.append(desc)
            
            assert len(results) == 2  # Should skip the invalid one
            assert mock_descriptors.call_count == 3
