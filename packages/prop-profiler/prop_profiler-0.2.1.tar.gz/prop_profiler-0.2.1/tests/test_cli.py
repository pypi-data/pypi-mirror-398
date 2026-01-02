import pytest
import tempfile
import os
import pandas as pd
from unittest.mock import patch, MagicMock
from io import StringIO

from prop_profiler.cli import main


@pytest.fixture
def sample_smi_content():
    """Sample SMI file content."""
    return "CCO\nCC(=O)O\nc1ccccc1"


@pytest.fixture
def sample_csv_content():
    """Sample CSV file content."""
    return "smiles,name\nCCO,Ethanol\nCC(=O)O,Acetic acid\nc1ccccc1,Benzene"


@pytest.fixture
def sample_sdf_content():
    """Sample SDF file content."""
    return """
  Mrv2014 07172500002D          

  3  2  0  0  0  0            999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    2.0000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  2  3  1  0  0  0  0
M  END
$$$$
"""


def create_temp_file(content, suffix):
    """Helper to create temporary files."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False)
    temp_file.write(content)
    temp_file.close()
    return temp_file.name


def test_cli_smi_input(sample_smi_content):
    """Test CLI with SMI input file."""
    input_file = create_temp_file(sample_smi_content, '.smi')
    output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
    
    try:
        with patch('prop_profiler.cli.profile_molecules') as mock_profile, \
             patch('pandas.read_csv') as mock_read_csv:
            
            # Mock the input file reading
            mock_df_in = pd.DataFrame({0: ['CCO', 'CC(=O)O', 'c1ccccc1']})
            mock_read_csv.return_value = mock_df_in
            
            # Mock the profile_molecules function
            mock_result = pd.DataFrame({
                'smiles': ['CCO', 'CC(=O)O', 'c1ccccc1'],
                'mw': [46.07, 60.05, 78.11],
                'stoplight_color': ['Green', 'Yellow', 'Red']
            })
            mock_profile.return_value = mock_result
            
            with patch('sys.argv', ['prop-profiler', '-i', input_file, '-o', output_file, '--no-header']):
                main()
            
            # Verify profile_molecules was called
            mock_profile.assert_called_once()
            
            # Verify arguments passed to profile_molecules
            call_args = mock_profile.call_args
            assert call_args is not None
            assert call_args[1]['skip_cns_mpo'] is False
            assert call_args[1]['device'] == 'cpu'
            assert call_args[1]['verbose'] is False
            
            # Verify molecules were passed correctly
            molecules = call_args[1]['molecules']
            assert len(molecules) == 3
            assert molecules == ['CCO', 'CC(=O)O', 'c1ccccc1']
            
            # Verify output file was created
            assert os.path.exists(output_file)
            
    finally:
        # Clean up
        os.unlink(input_file)
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_cli_csv_input(sample_csv_content):
    """Test CLI with CSV input file."""
    input_file = create_temp_file(sample_csv_content, '.csv')
    output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
    
    try:
        with patch('prop_profiler.cli.profile_molecules') as mock_profile, \
             patch('pandas.read_csv') as mock_read_csv:
            
            # Mock the input file reading
            mock_df_in = pd.DataFrame({
                'smiles': ['CCO', 'CC(=O)O', 'c1ccccc1'],
                'name': ['ethanol', 'acetic acid', 'benzene']
            })
            mock_read_csv.return_value = mock_df_in
            
            mock_result = pd.DataFrame({
                'smiles': ['CCO', 'CC(=O)O', 'c1ccccc1'],
                'mw': [46.07, 60.05, 78.11],
                'stoplight_color': ['Green', 'Yellow', 'Red']
            })
            mock_profile.return_value = mock_result
            
            with patch('sys.argv', ['prop-profiler', '-i', input_file, '-o', output_file]):
                main()
            
            mock_profile.assert_called_once()
            
            # Verify molecules were extracted from CSV
            call_args = mock_profile.call_args
            molecules = call_args[1]['molecules']
            assert len(molecules) == 3
            assert molecules == ['CCO', 'CC(=O)O', 'c1ccccc1']
            
    finally:
        os.unlink(input_file)
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_cli_sdf_input(sample_sdf_content):
    """Test CLI with SDF input file."""
    input_file = create_temp_file(sample_sdf_content, '.sdf')
    output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
    
    try:
        with patch('prop_profiler.cli.profile_molecules') as mock_profile:
            mock_result = pd.DataFrame({
                'smiles': ['CCO'],
                'mw': [46.07],
                'stoplight_color': ['Green']
            })
            mock_profile.return_value = mock_result
            
            with patch('sys.argv', ['prop-profiler', '-i', input_file, '-o', output_file]):
                main()
            
            mock_profile.assert_called_once()
            
    finally:
        os.unlink(input_file)
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_cli_skip_cns_mpo_flag(sample_smi_content):
    """Test CLI with --skip-cns-mpo flag."""
    input_file = create_temp_file(sample_smi_content, '.smi')
    output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
    
    try:
        with patch('prop_profiler.cli.profile_molecules') as mock_profile, \
             patch('pandas.read_csv') as mock_read_csv:
            
            # Mock the input file reading
            mock_df_in = pd.DataFrame({0: ['CCO']})
            mock_read_csv.return_value = mock_df_in
            
            mock_result = pd.DataFrame({
                'smiles': ['CCO'],
                'mw': [46.07],
                'stoplight_color': ['Green']
            })
            mock_profile.return_value = mock_result
            
            with patch('sys.argv', ['prop-profiler', '-i', input_file, '-o', output_file, '--skip-cns-mpo', '--no-header']):
                main()
            
            mock_profile.assert_called_once()
            
            # Verify skip_cns_mpo was set to True
            call_args = mock_profile.call_args
            assert call_args[1]['skip_cns_mpo'] is True
            
    finally:
        os.unlink(input_file)
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_cli_verbose_flag(sample_smi_content):
    """Test CLI with --verbose flag."""
    input_file = create_temp_file(sample_smi_content, '.smi')
    output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
    
    try:
        with patch('prop_profiler.cli.profile_molecules') as mock_profile, \
             patch('pandas.read_csv') as mock_read_csv:
            
            # Mock the input file reading
            mock_df_in = pd.DataFrame({0: ['CCO']})
            mock_read_csv.return_value = mock_df_in
            
            mock_result = pd.DataFrame({
                'smiles': ['CCO'],
                'mw': [46.07],
                'stoplight_color': ['Green']
            })
            mock_profile.return_value = mock_result
            
            with patch('sys.argv', ['prop-profiler', '-i', input_file, '-o', output_file, '--verbose', '--no-header']):
                main()
            
            mock_profile.assert_called_once()
            
            # Verify verbose was set to True
            call_args = mock_profile.call_args
            assert call_args[1]['verbose'] is True
            
    finally:
        os.unlink(input_file)
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_cli_device_parameter(sample_smi_content):
    """Test CLI with --device parameter."""
    input_file = create_temp_file(sample_smi_content, '.smi')
    output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
    
    try:
        with patch('prop_profiler.cli.profile_molecules') as mock_profile, \
             patch('pandas.read_csv') as mock_read_csv:
            
            # Mock the input file reading
            mock_df_in = pd.DataFrame({0: ['CCO']})
            mock_read_csv.return_value = mock_df_in
            
            mock_result = pd.DataFrame({
                'smiles': ['CCO'],
                'mw': [46.07],
                'stoplight_color': ['Green']
            })
            mock_profile.return_value = mock_result
            
            with patch('sys.argv', ['prop-profiler', '-i', input_file, '-o', output_file, '--device', 'cuda', '--no-header']):
                main()
            
            # Verify device was set to cuda
            call_args = mock_profile.call_args
            assert call_args[1]['device'] == 'cuda'
            
    finally:
        os.unlink(input_file)
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_cli_custom_column_name():
    """Test CLI with custom SMILES column name."""
    csv_content = "molecule,name\nCCO,Ethanol\nCC(=O)O,Acetic acid"
    input_file = create_temp_file(csv_content, '.csv')
    output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
    
    try:
        with patch('prop_profiler.cli.profile_molecules') as mock_profile:
            mock_result = pd.DataFrame({
                'smiles': ['CCO', 'CC(=O)O'],
                'mw': [46.07, 60.05],
                'stoplight_color': ['Green', 'Yellow']
            })
            mock_profile.return_value = mock_result
            
            with patch('sys.argv', ['prop-profiler', '-i', input_file, '-o', output_file, '-c', 'molecule']):
                main()
            
            mock_profile.assert_called_once()
            
    finally:
        os.unlink(input_file)
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_cli_no_header_flag():
    """Test CLI with --no-header flag."""
    csv_content = "CCO,Ethanol\nCC(=O)O,Acetic acid"
    input_file = create_temp_file(csv_content, '.csv')
    output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
    
    try:
        with patch('prop_profiler.cli.profile_molecules') as mock_profile:
            mock_result = pd.DataFrame({
                'smiles': ['CCO', 'CC(=O)O'],
                'mw': [46.07, 60.05],
                'stoplight_color': ['Green', 'Yellow']
            })
            mock_profile.return_value = mock_result
            
            with patch('sys.argv', ['prop-profiler', '-i', input_file, '-o', output_file, '--no-header']):
                main()
            
            mock_profile.assert_called_once()
            
    finally:
        os.unlink(input_file)
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_cli_keep_input_data_flag():
    """Test CLI with --keep-input-data flag."""
    csv_content = "smiles,name\nCCO,Ethanol\nCC(=O)O,Acetic acid"
    input_file = create_temp_file(csv_content, '.csv')
    output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
    
    try:
        with patch('prop_profiler.cli.profile_molecules') as mock_profile:
            mock_result = pd.DataFrame({
                'smiles': ['CCO', 'CC(=O)O'],
                'mw': [46.07, 60.05],
                'stoplight_color': ['Green', 'Yellow']
            })
            mock_profile.return_value = mock_result
            
            with patch('sys.argv', ['prop-profiler', '-i', input_file, '-o', output_file, '--keep-input-data']):
                main()
            
            mock_profile.assert_called_once()
            
            # Verify output file contains both input and result data
            assert os.path.exists(output_file)
            result_df = pd.read_csv(output_file)
            assert 'name' in result_df.columns  # Original column preserved
            assert 'smiles' in result_df.columns
            assert 'mw' in result_df.columns
            
    finally:
        os.unlink(input_file)
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_cli_unsupported_file_format():
    """Test CLI with unsupported file format."""
    input_file = create_temp_file("CCO", '.xyz')  # Use truly unsupported format
    output_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False).name
    
    try:
        with patch('sys.argv', ['prop-profiler', '-i', input_file, '-o', output_file]):
            with pytest.raises(SystemExit):
                main()
            
    finally:
        os.unlink(input_file)
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_cli_missing_required_arguments():
    """Test CLI with missing required arguments."""
    with patch('sys.argv', ['prop-profiler']):
        with pytest.raises(SystemExit):
            main()
    
    with patch('sys.argv', ['prop-profiler', '-i', 'input.smi']):
        with pytest.raises(SystemExit):
            main()
    
    with patch('sys.argv', ['prop-profiler', '-o', 'output.csv']):
        with pytest.raises(SystemExit):
            main()
