"""Reference data and baselines from original LSD implementation.

This module contains expected values extracted from executed notebooks
in LSD-main-branch/Notebooks/ for parity testing.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np


# =============================================================================
# Pancreas Dataset Reference Values (from postprocessing.ipynb)
# =============================================================================

PANCREAS_CLUSTER_EDGES = [
    ("Prlf. Ductal", "Ductal"),
    ("Ductal", "Ngn3 low"),
    ("Ngn3 low", "Ngn3 high"),
    ("Ngn3 high", "Fev+"),
    ("Ngn3 high", "Epsilon"),
    ("Fev+", "Fev+ Alpha"),
    ("Fev+", "Fev+ Beta"),
    ("Fev+ Alpha", "Alpha"),
    ("Fev+ Beta", "Beta"),
    ("Fev+ Delta", "Delta"),
]

PANCREAS_CBDIR_EXPECTED = {
    ("Prlf. Ductal", "Ductal"): 0.172,
    ("Ductal", "Ngn3 low"): 0.381,
    ("Ngn3 low", "Ngn3 high"): 0.305,
    ("Ngn3 high", "Fev+"): 0.398,
    ("Ngn3 high", "Epsilon"): 0.715,
    ("Fev+", "Fev+ Alpha"): 0.603,
    ("Fev+", "Fev+ Beta"): 0.463,
    ("Fev+ Alpha", "Alpha"): 0.617,
    ("Fev+ Beta", "Beta"): 0.583,
    ("Fev+ Delta", "Delta"): 0.633,
}

PANCREAS_CBDIR_MEAN = 0.487

PANCREAS_CONFIG = {
    "n_cells": 16822,
    "n_genes": 5000,
    "z_dim": 10,
    "B_dim": 2,
    "V_coeff": 5e-3,
    "path_len": 50,
    "batch_size": 256,
    "num_epochs": 100,
    "lr": 2e-3,
    "kl_af": 3,
    "seed": 42,
}

PANCREAS_PHYLOGENY = {
    "Prlf. Ductal": ["Ductal"],
    "Ductal": ["Ngn3 low"],
    "Ngn3 low": ["Ngn3 high"],
    "Ngn3 high": ["Fev+", "Fev+ Delta", "Epsilon"],
    "Fev+": ["Fev+ Alpha", "Fev+ Beta"],
    "Fev+ Delta": ["Delta"],
    "Fev+ Alpha": ["Alpha"],
    "Fev+ Beta": ["Beta"],
    "Epsilon": [],
    "Alpha": [],
    "Beta": [],
    "Delta": [],
}


# =============================================================================
# BoneMarrow Dataset Reference Values (from postprocessing.ipynb)
# =============================================================================

BONEMARROW_CBDIR_MEAN = 0.594  # From notebook execution

BONEMARROW_CONFIG = {
    "n_cells": 5292,
    "num_epochs": 200,
}


# =============================================================================
# Reference Data Loading Functions
# =============================================================================

def load_reference_baselines(dataset: str = "pancreas") -> Dict[str, Any]:
    """Load reference baselines for a dataset.

    Args:
        dataset: Dataset name ("pancreas", "bonemarrow", etc.)

    Returns:
        Dictionary containing reference values
    """
    if dataset.lower() == "pancreas":
        return {
            "config": PANCREAS_CONFIG,
            "cbdir_scores": PANCREAS_CBDIR_EXPECTED,
            "cbdir_mean": PANCREAS_CBDIR_MEAN,
            "cluster_edges": PANCREAS_CLUSTER_EDGES,
            "phylogeny": PANCREAS_PHYLOGENY,
        }
    elif dataset.lower() == "bonemarrow":
        return {
            "config": BONEMARROW_CONFIG,
            "cbdir_mean": BONEMARROW_CBDIR_MEAN,
        }
    else:
        raise ValueError(f"Unknown dataset: {dataset}")


def get_reference_data_path() -> Path:
    """Get path to reference data directory.

    Returns:
        Path to tests/fixtures/reference_data/
    """
    return Path(__file__).parent / "reference_data"


def load_numpy_baseline(dataset: str, name: str) -> Optional[np.ndarray]:
    """Load a numpy baseline file if it exists.

    Args:
        dataset: Dataset name
        name: Baseline name (e.g., "pseudotime", "potential")

    Returns:
        Numpy array or None if file doesn't exist
    """
    path = get_reference_data_path() / f"{dataset}_{name}.npy"
    if path.exists():
        return np.load(path)
    return None


def save_numpy_baseline(data: np.ndarray, dataset: str, name: str) -> Path:
    """Save a numpy baseline file.

    Args:
        data: Numpy array to save
        dataset: Dataset name
        name: Baseline name

    Returns:
        Path to saved file
    """
    ref_dir = get_reference_data_path()
    ref_dir.mkdir(parents=True, exist_ok=True)
    path = ref_dir / f"{dataset}_{name}.npy"
    np.save(path, data)
    return path
