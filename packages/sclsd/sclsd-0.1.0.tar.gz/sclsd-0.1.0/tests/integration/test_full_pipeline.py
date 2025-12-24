"""Integration tests for LSDpy end-to-end workflows."""

import pytest
import numpy as np
import torch

pytest.importorskip("scanpy")
pytest.importorskip("pyro")


class TestSyntheticPipeline:
    """Integration tests with synthetic data."""

    @pytest.mark.integration
    def test_synthetic_pipeline_cpu(self, random_seed):
        """Complete workflow: data -> train -> inference on CPU."""
        from sclsd import LSD, LSDConfig, set_all_seeds, clear_pyro_state
        from tests.fixtures.synthetic_data import create_synthetic_adata

        # Setup
        clear_pyro_state()
        set_all_seeds(random_seed)

        # 1. Create synthetic data
        adata = create_synthetic_adata(n_cells=200, n_genes=100, seed=random_seed)

        # 2. Configure model
        cfg = LSDConfig()
        cfg.model.z_dim = 5
        cfg.model.B_dim = 2
        cfg.walks.path_len = 4
        cfg.walks.num_walks = 100
        cfg.walks.batch_size = 25
        cfg.model.layer_dims.B_decoder = [16]
        cfg.model.layer_dims.z_decoder = [32, 16]
        cfg.model.layer_dims.x_encoder = [32, 16]
        cfg.model.layer_dims.potential = [8]

        # 3. Initialize model
        device = torch.device("cpu")
        lsd = LSD(adata, cfg, device=device)

        # 4. Set prior transition
        lsd.set_prior_transition(prior_time_key="pseudotime")
        assert lsd.P is not None

        # 5. Generate walks
        lsd.prepare_walks(n_trajectories=100)
        assert lsd.walks is not None
        assert lsd.walks.shape == (100, 4)

        # 6. Train for a few epochs
        lsd.train(num_epochs=2, plot_loss=False, random_state=random_seed)
        assert lsd.epoch == 2

        # 7. Get results
        result = lsd.get_adata()

        # 8. Verify outputs
        assert "lsd_pseudotime" in result.obs.columns
        assert "potential" in result.obs.columns
        assert "entropy" in result.obs.columns
        assert "cell_rep" in result.obsm
        assert "diff_rep" in result.obsm
        assert "transitions" in result.obsp

    @pytest.mark.integration
    def test_pipeline_with_phylogeny(self, random_seed):
        """Workflow with phylogenetic constraints."""
        from sclsd import LSD, LSDConfig, set_all_seeds, clear_pyro_state
        from tests.fixtures.synthetic_data import create_synthetic_adata

        clear_pyro_state()
        set_all_seeds(random_seed)

        # Create data with specific clusters
        adata = create_synthetic_adata(n_cells=200, n_genes=100, n_clusters=3, seed=random_seed)

        cfg = LSDConfig()
        cfg.model.z_dim = 5
        cfg.walks.path_len = 4
        cfg.walks.num_walks = 50
        cfg.walks.batch_size = 25
        cfg.model.layer_dims.B_decoder = [16]
        cfg.model.layer_dims.z_decoder = [32, 16]
        cfg.model.layer_dims.x_encoder = [32, 16]
        cfg.model.layer_dims.potential = [8]

        device = torch.device("cpu")
        lsd = LSD(adata, cfg, device=device)

        # Set phylogeny
        phylogeny = {"A": ["B"], "B": ["C"], "C": []}
        lsd.set_phylogeny(phylogeny, cluster_key="clusters")

        assert lsd.phylogeny == phylogeny
        assert lsd.cluster_key == "clusters"

        # Set prior transition from pseudotime
        lsd.set_prior_transition(prior_time_key="pseudotime")
        assert lsd.P is not None

    @pytest.mark.integration
    def test_output_ranges(self, random_seed):
        """Verify outputs are in expected ranges."""
        from sclsd import LSD, LSDConfig, set_all_seeds, clear_pyro_state
        from tests.fixtures.synthetic_data import create_synthetic_adata

        clear_pyro_state()
        set_all_seeds(random_seed)

        adata = create_synthetic_adata(n_cells=200, n_genes=100, seed=random_seed)

        cfg = LSDConfig()
        cfg.model.z_dim = 5
        cfg.walks.path_len = 4
        cfg.walks.num_walks = 50
        cfg.walks.batch_size = 25
        cfg.model.layer_dims.B_decoder = [16]
        cfg.model.layer_dims.z_decoder = [32, 16]
        cfg.model.layer_dims.x_encoder = [32, 16]
        cfg.model.layer_dims.potential = [8]

        device = torch.device("cpu")
        lsd = LSD(adata, cfg, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")
        lsd.prepare_walks(n_trajectories=50)
        lsd.train(num_epochs=2, plot_loss=False, random_state=random_seed)

        result = lsd.get_adata()

        # Pseudotime should be in [0, 1]
        pseudotime = result.obs["lsd_pseudotime"].values
        assert pseudotime.min() >= 0
        assert pseudotime.max() <= 1

        # Transitions should sum to 1
        transitions = result.obsp["transitions"]
        row_sums = transitions.sum(axis=1)
        np.testing.assert_allclose(row_sums, np.ones_like(row_sums), rtol=1e-5)


class TestSaveLoadPipeline:
    """Integration tests for save/load functionality."""

    @pytest.mark.integration
    def test_save_load_continues_correctly(self, random_seed, tmp_path):
        """Test that saved model produces same results after loading."""
        from sclsd import LSD, LSDConfig, set_all_seeds, clear_pyro_state
        from tests.fixtures.synthetic_data import create_synthetic_adata

        clear_pyro_state()
        set_all_seeds(random_seed)

        adata = create_synthetic_adata(n_cells=200, n_genes=100, seed=random_seed)

        cfg = LSDConfig()
        cfg.model.z_dim = 5
        cfg.walks.path_len = 4
        cfg.walks.num_walks = 50
        cfg.walks.batch_size = 25
        cfg.model.layer_dims.B_decoder = [16]
        cfg.model.layer_dims.z_decoder = [32, 16]
        cfg.model.layer_dims.x_encoder = [32, 16]
        cfg.model.layer_dims.potential = [8]

        device = torch.device("cpu")
        lsd = LSD(adata, cfg, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")
        lsd.prepare_walks(n_trajectories=50)
        lsd.train(num_epochs=2, plot_loss=False, random_state=random_seed)

        # Get results before saving
        result_before = lsd.get_adata()

        # Save
        save_path = str(tmp_path / "test_model")
        lsd.save(dir_path=save_path, file_name="model.pth")

        # Create new model and load
        clear_pyro_state()
        lsd_loaded = LSD(adata, cfg, device=device)
        lsd_loaded.load(dir_path=save_path, file_name="model.pth")

        # Get results after loading
        result_after = lsd_loaded.get_adata()

        # Compare
        np.testing.assert_allclose(
            result_before.obs["lsd_pseudotime"].values,
            result_after.obs["lsd_pseudotime"].values,
            rtol=1e-5,
        )
        np.testing.assert_allclose(
            result_before.obsm["cell_rep"],
            result_after.obsm["cell_rep"],
            rtol=1e-5,
        )


class TestModelDimensions:
    """Tests for different model dimension configurations."""

    @pytest.mark.integration
    @pytest.mark.parametrize("z_dim", [5, 10, 20])
    def test_different_z_dims(self, z_dim, random_seed):
        """Test model works with different latent dimensions."""
        from sclsd import LSD, LSDConfig, set_all_seeds, clear_pyro_state
        from tests.fixtures.synthetic_data import create_synthetic_adata

        clear_pyro_state()
        set_all_seeds(random_seed)

        adata = create_synthetic_adata(n_cells=100, n_genes=50, seed=random_seed)

        cfg = LSDConfig()
        cfg.model.z_dim = z_dim
        cfg.walks.path_len = 4
        cfg.walks.num_walks = 25
        cfg.walks.batch_size = 25
        cfg.model.layer_dims.B_decoder = [16]
        cfg.model.layer_dims.z_decoder = [32, 16]
        cfg.model.layer_dims.x_encoder = [32, 16]
        cfg.model.layer_dims.potential = [8]

        device = torch.device("cpu")
        lsd = LSD(adata, cfg, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")
        lsd.prepare_walks(n_trajectories=25)

        # Should not raise
        lsd.train(num_epochs=1, plot_loss=False, random_state=random_seed)

        result = lsd.get_adata()
        assert result.obsm["cell_rep"].shape[1] == z_dim

    @pytest.mark.integration
    @pytest.mark.parametrize("B_dim", [2, 3, 5])
    def test_different_B_dims(self, B_dim, random_seed):
        """Test model works with different B dimensions."""
        from sclsd import LSD, LSDConfig, set_all_seeds, clear_pyro_state
        from tests.fixtures.synthetic_data import create_synthetic_adata

        clear_pyro_state()
        set_all_seeds(random_seed)

        adata = create_synthetic_adata(n_cells=100, n_genes=50, seed=random_seed)

        cfg = LSDConfig()
        cfg.model.B_dim = B_dim
        cfg.model.z_dim = 5
        cfg.walks.path_len = 4
        cfg.walks.num_walks = 25
        cfg.walks.batch_size = 25
        cfg.model.layer_dims.B_decoder = [16]
        cfg.model.layer_dims.z_decoder = [32, 16]
        cfg.model.layer_dims.x_encoder = [32, 16]
        cfg.model.layer_dims.potential = [8]

        device = torch.device("cpu")
        lsd = LSD(adata, cfg, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")
        lsd.prepare_walks(n_trajectories=25)

        lsd.train(num_epochs=1, plot_loss=False, random_state=random_seed)

        result = lsd.get_adata()
        assert result.obsm["diff_rep"].shape[1] == B_dim
