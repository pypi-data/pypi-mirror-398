"""Pytest configuration and fixtures for LSDpy tests."""

import pytest
import numpy as np
import torch
import scipy.sparse as sp
from pathlib import Path

# Try to import optional dependencies
try:
    import scanpy as sc
    from anndata import AnnData
    HAS_SCANPY = True
except ImportError:
    HAS_SCANPY = False
    AnnData = None


@pytest.fixture
def device():
    """Get test device (CPU for CI, GPU if available for local)."""
    return torch.device("cpu")


@pytest.fixture(scope="session")
def reference_data_path():
    """Get path to reference data directory."""
    return Path(__file__).parent / "fixtures" / "reference_data"


@pytest.fixture
def random_seed():
    """Standard random seed for reproducibility tests."""
    return 42


@pytest.fixture
def small_adata():
    """Create a small synthetic AnnData for testing."""
    if not HAS_SCANPY:
        pytest.skip("scanpy not installed")

    np.random.seed(42)

    n_cells = 200
    n_genes = 100

    # Generate synthetic count data
    counts = np.random.negative_binomial(n=5, p=0.3, size=(n_cells, n_genes))
    counts = counts.astype(np.float32)

    # Create AnnData
    adata = AnnData(X=sp.csr_matrix(counts))
    adata.var_names = [f"Gene_{i}" for i in range(n_genes)]
    adata.obs_names = [f"Cell_{i}" for i in range(n_cells)]

    # Add layers
    adata.layers["raw"] = adata.X.copy()

    # Add library size
    adata.obs["librarysize"] = np.array(adata.X.sum(axis=1)).flatten()

    # Add clusters
    adata.obs["clusters"] = np.random.choice(["A", "B", "C"], size=n_cells)
    adata.obs["clusters"] = adata.obs["clusters"].astype("category")

    # Preprocess
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    sc.pp.pca(adata, n_comps=20)
    sc.pp.neighbors(adata, n_neighbors=15)

    # Add pseudotime
    adata.obs["pseudotime"] = np.linspace(0, 1, n_cells)

    return adata


@pytest.fixture
def lsd_config():
    """Create a minimal LSD config for testing."""
    from sclsd import LSDConfig

    cfg = LSDConfig()
    cfg.model.z_dim = 5
    cfg.model.B_dim = 2
    cfg.walks.path_len = 4
    cfg.walks.num_walks = 100
    cfg.walks.batch_size = 25

    # Small networks for fast testing
    cfg.model.layer_dims.B_decoder = [16]
    cfg.model.layer_dims.z_decoder = [32, 16]
    cfg.model.layer_dims.x_encoder = [32, 16]
    cfg.model.layer_dims.potential = [8]

    return cfg


@pytest.fixture
def data_dict(small_adata):
    """Create data dictionary for testing."""
    if not HAS_SCANPY:
        pytest.skip("scanpy not installed")

    adata = small_adata

    # Get raw counts
    if hasattr(adata.layers["raw"], "toarray"):
        raw_counts = adata.layers["raw"].toarray()
    else:
        raw_counts = np.array(adata.layers["raw"])

    # Get normalized counts
    if hasattr(adata.X, "toarray"):
        normal_counts = adata.X.toarray()
    else:
        normal_counts = np.array(adata.X)

    return {
        "raw_counts": raw_counts,
        "normal_counts": normal_counts,
        "librarysize": adata.obs["librarysize"].values,
        "adata": adata.copy(),
    }
