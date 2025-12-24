"""Synthetic data generators for LSDpy tests."""

import numpy as np
import scipy.sparse as sp

try:
    import scanpy as sc
    from anndata import AnnData
    HAS_SCANPY = True
except ImportError:
    HAS_SCANPY = False
    AnnData = None


def create_synthetic_counts(
    n_cells: int = 200,
    n_genes: int = 100,
    seed: int = 42,
) -> np.ndarray:
    """Generate synthetic count matrix using negative binomial distribution.

    Args:
        n_cells: Number of cells
        n_genes: Number of genes
        seed: Random seed for reproducibility

    Returns:
        Count matrix of shape (n_cells, n_genes)
    """
    np.random.seed(seed)
    counts = np.random.negative_binomial(n=5, p=0.3, size=(n_cells, n_genes))
    return counts.astype(np.float32)


def create_synthetic_trajectories(
    n_cells: int = 200,
    n_clusters: int = 3,
    seed: int = 42,
) -> dict:
    """Generate synthetic trajectory structure with clusters and pseudotime.

    Args:
        n_cells: Number of cells
        n_clusters: Number of cell clusters
        seed: Random seed

    Returns:
        Dictionary with cluster labels and pseudotime values
    """
    np.random.seed(seed)

    # Assign cells to clusters with roughly equal distribution
    cluster_names = [chr(65 + i) for i in range(n_clusters)]  # A, B, C, ...
    clusters = np.random.choice(cluster_names, size=n_cells)

    # Generate pseudotime based on cluster order
    pseudotime = np.zeros(n_cells)
    for i, name in enumerate(cluster_names):
        mask = clusters == name
        base = i / n_clusters
        # Add noise within each cluster
        pseudotime[mask] = base + np.random.uniform(0, 1/n_clusters, mask.sum())

    # Normalize to [0, 1]
    pseudotime = (pseudotime - pseudotime.min()) / (pseudotime.max() - pseudotime.min())

    return {
        "clusters": clusters,
        "pseudotime": pseudotime,
        "cluster_names": cluster_names,
    }


def create_synthetic_adata(
    n_cells: int = 200,
    n_genes: int = 100,
    n_clusters: int = 3,
    seed: int = 42,
    preprocess: bool = True,
) -> "AnnData":
    """Create a complete synthetic AnnData object for testing.

    Args:
        n_cells: Number of cells
        n_genes: Number of genes
        n_clusters: Number of cell clusters
        seed: Random seed
        preprocess: Whether to run preprocessing (normalize, PCA, neighbors)

    Returns:
        AnnData object ready for LSD training
    """
    if not HAS_SCANPY:
        raise ImportError("scanpy is required to create synthetic AnnData")

    # Generate counts
    counts = create_synthetic_counts(n_cells, n_genes, seed)

    # Create sparse AnnData
    adata = AnnData(X=sp.csr_matrix(counts))
    adata.var_names = [f"Gene_{i}" for i in range(n_genes)]
    adata.obs_names = [f"Cell_{i}" for i in range(n_cells)]

    # Add raw layer
    adata.layers["raw"] = adata.X.copy()

    # Add library size
    adata.obs["librarysize"] = np.array(adata.X.sum(axis=1)).flatten()

    # Add trajectory structure
    traj = create_synthetic_trajectories(n_cells, n_clusters, seed)
    adata.obs["clusters"] = traj["clusters"]
    adata.obs["clusters"] = adata.obs["clusters"].astype("category")
    adata.obs["pseudotime"] = traj["pseudotime"]

    if preprocess:
        # Normalize and log transform
        sc.pp.normalize_total(adata, target_sum=1e4)
        sc.pp.log1p(adata)

        # Compute PCA and neighbors
        n_pcs = min(20, n_genes - 1, n_cells - 1)
        sc.pp.pca(adata, n_comps=n_pcs)
        sc.pp.neighbors(adata, n_neighbors=min(15, n_cells - 1))

    return adata


def create_medium_adata(seed: int = 42) -> "AnnData":
    """Create medium-sized AnnData for integration tests.

    Returns:
        AnnData with 1000 cells, 500 genes
    """
    return create_synthetic_adata(
        n_cells=1000,
        n_genes=500,
        n_clusters=5,
        seed=seed,
        preprocess=True,
    )


def create_large_adata(seed: int = 42) -> "AnnData":
    """Create larger AnnData for performance tests.

    Returns:
        AnnData with 5000 cells, 2000 genes
    """
    return create_synthetic_adata(
        n_cells=5000,
        n_genes=2000,
        n_clusters=8,
        seed=seed,
        preprocess=True,
    )
