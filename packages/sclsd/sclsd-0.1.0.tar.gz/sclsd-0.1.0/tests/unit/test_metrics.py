"""Unit tests for lsdpy.analysis.metrics module."""

import pytest
import numpy as np

pytest.importorskip("scanpy")


class TestSummaryScores:
    """Tests for summary_scores function."""

    def test_group_means(self):
        """Test that group means are computed correctly."""
        from sclsd.analysis.metrics import summary_scores

        all_scores = {
            "A": [0.5, 0.6, 0.7],
            "B": [0.8, 0.9],
        }

        sep_scores, _ = summary_scores(all_scores)

        np.testing.assert_almost_equal(sep_scores["A"], 0.6)
        np.testing.assert_almost_equal(sep_scores["B"], 0.85)

    def test_overall_mean(self):
        """Test that overall mean is computed correctly."""
        from sclsd.analysis.metrics import summary_scores

        all_scores = {
            "A": [0.5, 0.5],  # Mean = 0.5
            "B": [1.0, 1.0],  # Mean = 1.0
        }

        _, overall = summary_scores(all_scores)

        np.testing.assert_almost_equal(overall, 0.75)

    def test_empty_groups(self):
        """Test handling of empty score lists."""
        from sclsd.analysis.metrics import summary_scores

        all_scores = {
            "A": [0.5],
            "B": [],  # Empty
            "C": [0.8],
        }

        sep_scores, overall = summary_scores(all_scores)

        assert "B" not in sep_scores  # Empty groups excluded
        assert "A" in sep_scores
        assert "C" in sep_scores

    def test_single_group(self):
        """Test with single group."""
        from sclsd.analysis.metrics import summary_scores

        all_scores = {"only_group": [0.1, 0.2, 0.3]}

        sep_scores, overall = summary_scores(all_scores)

        assert len(sep_scores) == 1
        np.testing.assert_almost_equal(overall, 0.2)


class TestCrossBoundaryCorrectness:
    """Tests for cross_boundary_correctness function."""

    @pytest.fixture
    def setup_adata(self):
        """Create AnnData with velocity and embeddings for testing."""
        from anndata import AnnData
        import scanpy as sc
        import scipy.sparse as sp

        np.random.seed(42)
        n_cells = 100
        n_genes = 50

        # Create AnnData
        counts = np.random.poisson(5, (n_cells, n_genes)).astype(np.float32)
        adata = AnnData(X=sp.csr_matrix(counts))
        adata.obs_names = [f"cell_{i}" for i in range(n_cells)]
        adata.var_names = [f"gene_{i}" for i in range(n_genes)]

        # Add clusters
        adata.obs["clusters"] = np.array(["A"] * 50 + ["B"] * 50)
        adata.obs["clusters"] = adata.obs["clusters"].astype("category")

        # Add UMAP embedding
        adata.obsm["X_umap"] = np.random.randn(n_cells, 2)

        # Add velocity embedding (pointing from A to B)
        velocity_umap = np.zeros((n_cells, 2))
        velocity_umap[:50, 0] = 0.5  # A cells point right
        velocity_umap[50:, 0] = 0.1  # B cells point slightly right
        adata.obsm["velocity_umap"] = velocity_umap

        # Compute neighbors
        sc.pp.normalize_total(adata)
        sc.pp.log1p(adata)
        sc.pp.pca(adata, n_comps=min(20, n_genes - 1))
        sc.pp.neighbors(adata, n_neighbors=15)

        return adata

    def test_returns_scores_and_mean(self, setup_adata):
        """Test that function returns scores dict and mean."""
        from sclsd.analysis.metrics import cross_boundary_correctness

        adata = setup_adata
        edges = [("A", "B")]

        result = cross_boundary_correctness(
            adata, "clusters", "velocity", edges, x_emb="X_umap"
        )

        assert isinstance(result, tuple)
        assert len(result) == 2

        scores, mean = result
        assert isinstance(scores, dict)
        assert isinstance(mean, (float, np.floating))

    def test_per_edge_scores(self, setup_adata):
        """Test that each edge has a score."""
        from sclsd.analysis.metrics import cross_boundary_correctness

        adata = setup_adata
        edges = [("A", "B")]

        scores, _ = cross_boundary_correctness(
            adata, "clusters", "velocity", edges, x_emb="X_umap"
        )

        assert ("A", "B") in scores

    def test_return_raw(self, setup_adata):
        """Test return_raw option."""
        from sclsd.analysis.metrics import cross_boundary_correctness

        adata = setup_adata
        edges = [("A", "B")]

        result = cross_boundary_correctness(
            adata, "clusters", "velocity", edges,
            return_raw=True, x_emb="X_umap"
        )

        # Should return dict of lists when return_raw=True
        assert isinstance(result, dict)
        assert ("A", "B") in result
        assert isinstance(result[("A", "B")], list)


class TestInnerClusterCoh:
    """Tests for inner_cluster_coh function."""

    @pytest.fixture
    def setup_adata(self):
        """Create AnnData with velocity layers for testing."""
        from anndata import AnnData
        import scanpy as sc
        import scipy.sparse as sp

        np.random.seed(42)
        n_cells = 100
        n_genes = 50

        counts = np.random.poisson(5, (n_cells, n_genes)).astype(np.float32)
        adata = AnnData(X=sp.csr_matrix(counts))
        adata.obs_names = [f"cell_{i}" for i in range(n_cells)]
        adata.var_names = [f"gene_{i}" for i in range(n_genes)]

        # Add clusters
        adata.obs["clusters"] = np.array(["A"] * 50 + ["B"] * 50)
        adata.obs["clusters"] = adata.obs["clusters"].astype("category")

        # Add velocity layer (coherent within clusters)
        velocity = np.zeros((n_cells, n_genes))
        velocity[:50, :25] = 0.5  # A cells have similar velocity
        velocity[50:, 25:] = 0.5  # B cells have similar velocity
        adata.layers["velocity"] = velocity

        # Compute neighbors
        sc.pp.normalize_total(adata)
        sc.pp.log1p(adata)
        sc.pp.pca(adata, n_comps=min(20, n_genes - 1))
        sc.pp.neighbors(adata, n_neighbors=15)

        return adata

    def test_returns_scores_and_mean(self, setup_adata):
        """Test that function returns scores dict and mean."""
        from sclsd.analysis.metrics import inner_cluster_coh

        adata = setup_adata

        result = inner_cluster_coh(adata, "clusters", "velocity")

        assert isinstance(result, tuple)
        assert len(result) == 2

        scores, mean = result
        assert isinstance(scores, dict)
        assert isinstance(mean, (float, np.floating))

    def test_per_cluster_scores(self, setup_adata):
        """Test that each cluster has a score."""
        from sclsd.analysis.metrics import inner_cluster_coh

        adata = setup_adata

        scores, _ = inner_cluster_coh(adata, "clusters", "velocity")

        assert "A" in scores
        assert "B" in scores

    def test_return_raw(self, setup_adata):
        """Test return_raw option."""
        from sclsd.analysis.metrics import inner_cluster_coh

        adata = setup_adata

        result = inner_cluster_coh(
            adata, "clusters", "velocity", return_raw=True
        )

        assert isinstance(result, dict)
        assert "A" in result
        assert isinstance(result["A"], list)


class TestEvaluate:
    """Tests for evaluate function."""

    @pytest.fixture
    def setup_adata(self):
        """Create AnnData with all required data for evaluation."""
        from anndata import AnnData
        import scanpy as sc
        import scipy.sparse as sp

        np.random.seed(42)
        n_cells = 100
        n_genes = 50

        counts = np.random.poisson(5, (n_cells, n_genes)).astype(np.float32)
        adata = AnnData(X=sp.csr_matrix(counts))
        adata.obs_names = [f"cell_{i}" for i in range(n_cells)]
        adata.var_names = [f"gene_{i}" for i in range(n_genes)]

        # Add clusters
        adata.obs["clusters"] = np.array(["A"] * 50 + ["B"] * 50)
        adata.obs["clusters"] = adata.obs["clusters"].astype("category")

        # Add UMAP
        adata.obsm["X_umap"] = np.random.randn(n_cells, 2)

        # Add velocity embedding
        adata.obsm["velocity_umap"] = np.random.randn(n_cells, 2)

        # Add velocity layer
        adata.layers["velocity"] = np.random.randn(n_cells, n_genes)

        # Compute neighbors
        sc.pp.normalize_total(adata)
        sc.pp.log1p(adata)
        sc.pp.pca(adata, n_comps=min(20, n_genes - 1))
        sc.pp.neighbors(adata, n_neighbors=15)

        return adata

    def test_returns_all_metrics(self, setup_adata):
        """Test that evaluate returns all metrics."""
        from sclsd.analysis.metrics import evaluate

        adata = setup_adata
        edges = [("A", "B")]

        results = evaluate(
            adata, edges, "clusters", "velocity",
            x_emb="X_umap", verbose=False
        )

        assert "Cross-Boundary Direction Correctness (A->B)" in results
        assert "In-cluster Coherence" in results

    def test_verbose_mode(self, setup_adata, capsys):
        """Test that verbose mode prints output."""
        from sclsd.analysis.metrics import evaluate

        adata = setup_adata
        edges = [("A", "B")]

        evaluate(
            adata, edges, "clusters", "velocity",
            x_emb="X_umap", verbose=True
        )

        captured = capsys.readouterr()
        assert "Cross-Boundary Direction Correctness" in captured.out
        assert "In-cluster Coherence" in captured.out
