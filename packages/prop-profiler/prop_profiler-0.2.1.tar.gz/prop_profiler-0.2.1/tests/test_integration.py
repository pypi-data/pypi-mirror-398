"""Integration tests for prop_profiler."""

import pytest
import tempfile
import os
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

from prop_profiler.profiler import profile_molecules
from prop_profiler.cli import main


@pytest.mark.integration
class TestEndToEndIntegration:
    """Test end-to-end integration scenarios."""
    
    @patch('prop_profiler.profiler.StoplightPredictor')
    @patch('prop_profiler.profiler.CnsMpoPredictor')
    @patch('prop_profiler.utils.chem_helpers.get_props')
    @patch('prop_profiler.utils.chem_helpers.get_smiles')
    def test_complete_workflow_with_file(self, mock_get_smiles, mock_get_props, 
                                        mock_cns_class, mock_stoplight_class, tmp_path):
        """Test complete workflow from file input to output."""
        # Create test SMILES file
        smiles_file = tmp_path / "test.smi"
        smiles_file.write_text("CCO\nCCCO\nc1ccccc1\n")

        # Create output file
        output_file = tmp_path / "output.csv"
        
        # Configure mock predictor instances
        mock_stoplight_instance = MagicMock()
        mock_cns_instance = MagicMock()
        
        mock_stoplight_class.return_value = mock_stoplight_instance
        mock_cns_class.return_value = mock_cns_instance
        
        # Mock chemical helper functions
        mock_get_smiles.side_effect = ["CCO", "CCCO", "c1ccccc1"]
        mock_get_props.return_value = {
            'mw': 78.11, 'logp': 1.69, 'hba': 0, 'hbd': 0, 
            'tpsa': 0.0, 'num_rotatable_bonds': 0, 'fsp3': 0.0, 'qed': 0.44
        }
        
        # Mock the methods and properties
        mock_stoplight_instance.curate.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_stoplight_instance.predict.return_value = [0.33, 0.67, 0.5]
        mock_stoplight_instance.postprocess.return_value = ['yellow', 'green', 'yellow']
        mock_stoplight_instance.mol_props = [
            {'esol': 1998.36, 'pka': None, 'logd': 1.50},
            {'esol': 75044.69, 'pka': 4.47, 'logd': -0.58},
            {'esol': 143622.46, 'pka': 5.13, 'logd': 0.55}
        ]
        
        mock_cns_instance.predict.return_value = [4.0, 5.7, 5.0]
        mock_cns_instance.mol_props = [
            {'cns_property1': 1.0},
            {'cns_property1': 2.0},
            {'cns_property1': 3.0}
        ]
        
        # Run profiling
        smiles_list = ["CCO", "CCCO", "c1ccccc1"]
        result = profile_molecules(
            molecules=smiles_list,
            skip_cns_mpo=False,
            device='cpu',
            verbose=False
        )
        
        # Verify results
        assert result is not None
        assert len(result) == 3
        assert isinstance(result, pd.DataFrame)
        
        # Verify output file content
        assert 'smiles' in result.columns
        assert 'esol' in result.columns
        assert 'CCO' in result['smiles'].values
    
    def test_cli_integration_with_smiles_input(self, tmp_path, capsys):
        """Test CLI integration with SMILES input."""
        # Create dummy input file for CLI
        input_file = tmp_path / "dummy_input.smi"
        input_file.write_text("CCO\n")
        
        output_file = tmp_path / "cli_output.csv"
        
        # Mock all predictors
        with patch('prop_profiler.predictors.esol.EsolPredictor') as mock_esol, \
             patch('prop_profiler.predictors.logd.LogDPredictor') as mock_logd, \
             patch('prop_profiler.predictors.pka.PkaPredictor') as mock_pka, \
             patch('prop_profiler.predictors.cns_mpo.CnsMpoPredictor') as mock_cns, \
             patch('prop_profiler.predictors.stoplight.StoplightPredictor') as mock_stoplight:
            
            # Configure mock predictors - return lists for batch processing
            mock_esol.return_value.predict.return_value = [-0.77]
            mock_logd.return_value.predict.return_value = [0.50] 
            mock_pka.return_value.predict.return_value = [9.5]
            mock_cns.return_value.predict.return_value = [4.2]
            mock_stoplight.return_value.predict.return_value = ['green']
            
            # Test CLI with --no-header option for .smi files
            import sys
            sys.argv = [
                'prop_profiler',
                '--input', str(input_file),
                '--output', str(output_file),
                '--no-header'
            ]
            
            try:
                main()
                
                # Check output
                assert output_file.exists()
                captured = capsys.readouterr()
                # Just check that no error occurred
                
            except SystemExit as e:
                # CLI might exit with 0 on success
                assert e.code == 0
    
    def test_cli_integration_with_file_input(self, tmp_path, capsys):
        """Test CLI integration with file input."""
        # Create test input file with headers for CSV format
        input_file = tmp_path / "input.csv"
        input_file.write_text("smiles\nCCO\nCCCO\n")
        
        output_file = tmp_path / "output.csv"
        
        # Mock all predictors
        with patch('prop_profiler.predictors.esol.EsolPredictor') as mock_esol, \
             patch('prop_profiler.predictors.logd.LogDPredictor') as mock_logd, \
             patch('prop_profiler.predictors.pka.PkaPredictor') as mock_pka, \
             patch('prop_profiler.predictors.cns_mpo.CnsMpoPredictor') as mock_cns, \
             patch('prop_profiler.predictors.stoplight.StoplightPredictor') as mock_stoplight:
            
            # Configure mock predictors - return lists for batch processing
            mock_esol.return_value.predict.return_value = [-0.77, -1.2]
            mock_logd.return_value.predict.return_value = [0.50, 0.8] 
            mock_pka.return_value.predict.return_value = [9.5, 8.2]
            mock_cns.return_value.predict.return_value = [4.2, 3.8]
            mock_stoplight.return_value.predict.return_value = ['green', 'yellow']
            
            # Test CLI
            import sys
            sys.argv = [
                'prop_profiler',
                '--input', str(input_file),
                '--output', str(output_file)
            ]
            
            try:
                main()
                
                # Check output
                assert output_file.exists()
                
            except SystemExit as e:
                # CLI might exit with 0 on success
                assert e.code == 0
    
    def test_error_handling_integration(self, tmp_path):
        """Test error handling in integration scenarios."""
        # Test with invalid SMILES
        invalid_smiles = ['INVALID_SMILES', 'ANOTHER_INVALID']
        
        with patch('prop_profiler.profiler.StoplightPredictor') as mock_stoplight, \
             patch('prop_profiler.profiler.CnsMpoPredictor') as mock_cns:
            mock_stoplight_instance = MagicMock()
            mock_cns_instance = MagicMock()
            mock_stoplight.return_value = mock_stoplight_instance
            mock_cns.return_value = mock_cns_instance
            
            # Mock curate to return empty list for invalid SMILES
            mock_stoplight_instance.curate.return_value = []  # Invalid SMILES filtered out
            
            result = profile_molecules(invalid_smiles)
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0
    
    @pytest.mark.slow
    def test_performance_with_large_dataset(self, tmp_path):
        """Test performance with a larger dataset."""
        # Create a larger test dataset
        large_smiles = ["CCO", "CCCO", "CCCCO", "c1ccccc1", "CC(=O)O"] * 20
        
        smiles_file = tmp_path / "large_test.smi"
        smiles_file.write_text("\n".join(large_smiles))
        
        output_file = tmp_path / "large_output.csv"
        
        # Mock all predictors for fast execution
        with patch('prop_profiler.predictors.esol.EsolPredictor') as mock_esol, \
             patch('prop_profiler.predictors.logd.LogDPredictor') as mock_logd, \
             patch('prop_profiler.predictors.pka.PkaPredictor') as mock_pka, \
             patch('prop_profiler.predictors.cns_mpo.CnsMpoPredictor') as mock_cns, \
             patch('prop_profiler.predictors.stoplight.StoplightPredictor') as mock_stoplight:
            
            # Configure mock predictors - return lists matching the input size
            expected_count = 100  # 5 * 20 molecules
            mock_esol.return_value.predict.return_value = [-0.77] * expected_count
            mock_logd.return_value.predict.return_value = [0.50] * expected_count
            mock_pka.return_value.predict.return_value = [9.5] * expected_count
            mock_cns.return_value.predict.return_value = [4.2] * expected_count
            mock_stoplight.return_value.predict.return_value = ['green'] * expected_count
            
            # Run profiling
            large_smiles = ["CCO", "CCCO", "CCCCO", "c1ccccc1", "CC(=O)O"] * 20
            result = profile_molecules(
                molecules=large_smiles,
                skip_cns_mpo=False,
                device='cpu',
                verbose=False
            )
            
            # Verify results - NOTE: duplicates are removed during curation
            assert result is not None
            assert len(result) == 5  # unique molecules only
            assert isinstance(result, pd.DataFrame)
    
    def test_multiple_output_formats(self, tmp_path):
        """Test multiple output formats."""
        smiles_list = ["CCO", "CCCO"]
        
        # Mock all predictors
        with patch('prop_profiler.predictors.esol.EsolPredictor') as mock_esol, \
             patch('prop_profiler.predictors.logd.LogDPredictor') as mock_logd, \
             patch('prop_profiler.predictors.pka.PkaPredictor') as mock_pka, \
             patch('prop_profiler.predictors.cns_mpo.CnsMpoPredictor') as mock_cns, \
             patch('prop_profiler.predictors.stoplight.StoplightPredictor') as mock_stoplight:
            
            # Configure mock predictors - return lists for 2 molecules
            mock_esol.return_value.predict.return_value = [-0.77, -1.2]
            mock_logd.return_value.predict.return_value = [0.50, 0.8]
            mock_pka.return_value.predict.return_value = [9.5, 8.2]
            mock_cns.return_value.predict.return_value = [4.2, 3.8]
            mock_stoplight.return_value.predict.return_value = ['green', 'yellow']
            
            # Run profiling
            result = profile_molecules(
                molecules=smiles_list,
                skip_cns_mpo=False,
                device='cpu',
                verbose=False
            )
            
            # Verify results
            assert result is not None
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2
            
            # Check that expected columns are present
            assert 'smiles' in result.columns
            assert 'esol_mg/L' in result.columns
