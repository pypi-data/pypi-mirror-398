import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from rdkit import Chem

from prop_profiler.predictors.esol import EsolPredictor
from prop_profiler.predictors.logd import LogDPredictor
from prop_profiler.predictors.pka import PkaPredictor
from prop_profiler.predictors.cns_mpo import CnsMpoPredictor
from prop_profiler.predictors.stoplight import StoplightPredictor


@pytest.fixture
def sample_molecules():
    """Sample molecules for testing."""
    return [
        Chem.MolFromSmiles('CCO'),
        Chem.MolFromSmiles('c1ccccc1'),
        Chem.MolFromSmiles('CCN(CC)CC')
    ]


class TestEsolPredictor:
    """Test ESOL predictor."""
    
    def test_esol_predictor_init(self):
        """Test ESOL predictor initialization."""
        with patch('joblib.load') as mock_load:
            mock_model = MagicMock()
            mock_load.return_value = mock_model
            
            predictor = EsolPredictor('dummy_model.pkl')
            
            assert predictor.model == mock_model
            mock_load.assert_called_once_with('dummy_model.pkl')
    
    def test_esol_predictor_predict(self, sample_molecules):
        """Test ESOL prediction."""
        with patch('joblib.load') as mock_load:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.array([-0.77, -0.25, -2.30])
            mock_load.return_value = mock_model
            
            predictor = EsolPredictor('dummy_model.pkl')
            
            with patch('prop_profiler.utils.chem_helpers.compute_features') as mock_features:
                mock_features.return_value = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
                
                result = predictor.predict(sample_molecules)
                
                assert len(result) == 3
                assert all(isinstance(item, (int, float)) for item in result)
                assert result[0] == pytest.approx(-0.77)
                assert result[1] == pytest.approx(-0.25)
                assert result[2] == pytest.approx(-2.30)


class TestLogDPredictor:
    """Test LogD predictor."""
    
    def test_logd_predictor_init(self):
        """Test LogD predictor initialization."""
        with patch('joblib.load') as mock_load:
            mock_model = MagicMock()
            mock_load.return_value = mock_model
            
            predictor = LogDPredictor('dummy_model.pkl')
            
            assert predictor.model == mock_model
            mock_load.assert_called_once_with('dummy_model.pkl')
    
    def test_logd_predictor_predict(self, sample_molecules):
        """Test LogD prediction."""
        with patch('joblib.load') as mock_load:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.array([-0.31, -0.17, 2.13])
            mock_load.return_value = mock_model
            
            predictor = LogDPredictor('dummy_model.pkl')
            
            with patch('prop_profiler.utils.chem_helpers.compute_features') as mock_features:
                mock_features.return_value = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
                
                result = predictor.predict(sample_molecules)
                
                assert len(result) == 3
                assert all(isinstance(item, (int, float)) for item in result)
                assert result[0] == pytest.approx(-0.31)
                assert result[1] == pytest.approx(-0.17)
                assert result[2] == pytest.approx(2.13)


class TestPkaPredictor:
    """Test pKa predictor."""
    
    def test_pka_predictor_init(self):
        """Test pKa predictor initialization."""
        with patch('prop_profiler.predictors.pka.MolGpKaWrapper') as mock_wrapper:
            predictor = PkaPredictor('acid_model.pth', 'base_model.pth')
            
            assert predictor.device == 'cpu'
            mock_wrapper.assert_called_once()
    
    def test_pka_predictor_predict(self, sample_molecules):
        """Test pKa prediction."""
        with patch('prop_profiler.predictors.pka.MolGpKaWrapper') as mock_wrapper:
            mock_wrapper_instance = MagicMock()
            mock_wrapper_instance.predict.return_value = [15.5, -7.0, -5.0]
            mock_wrapper.return_value = mock_wrapper_instance
            
            predictor = PkaPredictor('acid_model.pth', 'base_model.pth')
            result = predictor.predict(sample_molecules)
            
            assert len(result) == 3
            assert all(isinstance(item, (int, float)) for item in result)
            assert result[0] == pytest.approx(15.5)
            assert result[1] == pytest.approx(-7.0)
            assert result[2] == pytest.approx(-5.0)


class TestCnsMpoPredictor:
    """Test CNS-MPO predictor."""
    
    def test_cns_mpo_predictor_init(self):
        """Test CNS-MPO predictor initialization."""
        mock_pka = MagicMock()
        mock_logd = MagicMock()
        
        predictor = CnsMpoPredictor(mock_pka, mock_logd)
        
        assert predictor.pka == mock_pka
        assert predictor.logd == mock_logd
    
    def test_cns_mpo_predictor_predict(self, sample_molecules):
        """Test CNS-MPO prediction."""
        mock_pka = MagicMock()
        mock_pka.predict.return_value = [15.5, -7.0, -5.0]
        
        mock_logd = MagicMock()
        mock_logd.predict.return_value = [-0.31, -0.17, 2.13]
        
        predictor = CnsMpoPredictor(mock_pka, mock_logd)
        
        with patch('prop_profiler.utils.chem_helpers.get_props') as mock_props:
            mock_props.side_effect = [
                {'mw': 46.07, 'logp': -0.31, 'hbd': 1, 'hba': 1, 'tpsa': 20.23},
                {'mw': 60.05, 'logp': -0.17, 'hbd': 1, 'hba': 2, 'tpsa': 37.30},
                {'mw': 78.11, 'logp': 2.13, 'hbd': 0, 'hba': 0, 'tpsa': 0.00}
            ]
            
            result = predictor.predict(sample_molecules)
            
            assert len(result) == 3
            assert all(isinstance(item, (int, float)) for item in result)


class TestStoplightPredictor:
    """Test Stoplight predictor."""
    
    def test_stoplight_predictor_init(self):
        """Test Stoplight predictor initialization."""
        mock_esol = MagicMock()
        
        predictor = StoplightPredictor(mock_esol)
        
        assert predictor.esol == mock_esol
    
    def test_stoplight_predictor_curate(self, sample_molecules):
        """Test Stoplight curation."""
        mock_esol = MagicMock()
        predictor = StoplightPredictor(mock_esol)
        
        with patch('prop_profiler.predictors.base.Predictor.curate') as mock_curate:
            mock_curate.return_value = sample_molecules
            
            result = predictor.curate(sample_molecules)
            
            assert result == sample_molecules
            mock_curate.assert_called_once()
    
    def test_stoplight_predictor_predict(self, sample_molecules):
        """Test Stoplight prediction."""
        mock_esol = MagicMock()
        mock_esol.predict.return_value = [-0.77, -0.25, -2.30]
        mock_esol.postprocess.return_value = [600, 5000, 100]  # esol values converted to solubility
        
        predictor = StoplightPredictor(mock_esol)
        
        with patch('prop_profiler.utils.chem_helpers.get_props') as mock_props:
            mock_props.side_effect = [
                {'mw': 46.07, 'logp': -0.31, 'hbd': 1, 'hba': 1, 'tpsa': 20.23, 'num_rotatable_bonds': 0, 'fsp3': 0.0},
                {'mw': 60.05, 'logp': -0.17, 'hbd': 1, 'hba': 2, 'tpsa': 37.30, 'num_rotatable_bonds': 0, 'fsp3': 0.3},
                {'mw': 78.11, 'logp': 2.13, 'hbd': 0, 'hba': 0, 'tpsa': 0.00, 'num_rotatable_bonds': 0, 'fsp3': 0.0}
            ]
            
            result = predictor.predict(sample_molecules)
            
            assert len(result) == 3
            assert all(isinstance(item, (int, float)) for item in result)
    
    def test_stoplight_predictor_postprocess(self):
        """Test Stoplight postprocessing."""
        mock_esol = MagicMock()
        predictor = StoplightPredictor(mock_esol)
        
        scores = [0.5, 1.5, 2.5]
        result = predictor.postprocess(scores)
        
        assert len(result) == 3
        assert all(isinstance(color, str) for color in result)
        assert result[0] == 'yellow'  # 0 < score < 1
        assert result[1] == 'red'  # score >= 1
        assert result[2] == 'red'  # score >= 1
