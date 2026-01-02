import numpy as np
import pytest

from prop_profiler.data.loader import load_dataset


def test_load_dataset(tmp_path):
    # Create a temporary CSV with valid, invalid, and boron SMILES
    content = (
        "smiles,y\n"
        "CCO,-0.77\n"
        "invalid,0.45\n"
        "CB,0.12\n"
    )
    csv_file = tmp_path / "dataset_test.csv"
    csv_file.write_text(content)

    X, y = load_dataset(str(csv_file))
    # Only the valid CCO should remain after curation
    assert isinstance(X, np.ndarray)
    assert isinstance(y, np.ndarray)
    assert X.shape[0] == 1
    assert y.shape == (1,)
    assert y[0] == pytest.approx(-0.77)


def test_loader_preserves_feature_dimension(tmp_path):
    # Ensure that feature length matches compute_features output
    content = "smiles,y\nCCO,-0.00\n"
    csv_file = tmp_path / "dataset_dim.csv"
    csv_file.write_text(content)

    X, _ = load_dataset(str(csv_file))
    assert X.ndim == 2
    assert X.shape[1] > 0
    assert np.issubdtype(X.dtype, np.number)

    content_two = "smiles,y\nCCN,0.10\n"
    csv_file_two = tmp_path / "dataset_dim_two.csv"
    csv_file_two.write_text(content_two)

    X2, _ = load_dataset(str(csv_file_two))
    assert X2.ndim == 2
    assert X2.shape[1] == X.shape[1]
    assert np.issubdtype(X2.dtype, np.number)
