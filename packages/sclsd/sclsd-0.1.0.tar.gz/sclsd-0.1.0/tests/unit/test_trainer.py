"""Unit tests for lsdpy.train.trainer module."""

import pytest
import numpy as np
import torch

pytest.importorskip("scanpy")
pytest.importorskip("pyro")


class TestLSDInit:
    """Tests for LSD class initialization."""

    def test_from_adata(self, small_adata, lsd_config, device, random_seed):
        """Test that LSD can be initialized from AnnData."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)

        assert lsd.adata is not None
        assert lsd.lsd is not None
        assert lsd.z_dim == lsd_config.model.z_dim
        assert lsd.B_dim == lsd_config.model.B_dim

    def test_default_config(self, small_adata, device, random_seed):
        """Test that LSD uses default config when none provided."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, device=device)

        assert lsd.config is not None
        assert lsd.z_dim == 10  # Default z_dim

    def test_device_assignment(self, small_adata, lsd_config, random_seed):
        """Test that device is assigned correctly."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        device = torch.device("cpu")
        lsd = LSD(small_adata, lsd_config, device=device)

        assert lsd.device == device

    def test_library_size_extracted(self, small_adata, lsd_config, device, random_seed):
        """Test that library size statistics are extracted."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)

        expected_mean = small_adata.obs["librarysize"].mean()
        expected_std = small_adata.obs["librarysize"].std()

        assert np.isclose(lsd.xl_loc, expected_mean)
        assert np.isclose(lsd.xl_scale, expected_std)


class TestPrepareDatadict:
    """Tests for prepare_datadict method."""

    def test_dict_structure(self, small_adata, lsd_config, device, random_seed):
        """Test that data dict contains required keys."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)
        data_dict = lsd.prepare_datadict()

        assert "raw_counts" in data_dict
        assert "normal_counts" in data_dict
        assert "librarysize" in data_dict
        assert "adata" in data_dict

    def test_sparse_handling(self, small_adata, lsd_config, device, random_seed):
        """Test that sparse matrices are converted to dense."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)
        data_dict = lsd.prepare_datadict()

        # Should be numpy arrays, not sparse
        assert isinstance(data_dict["raw_counts"], np.ndarray)
        assert isinstance(data_dict["normal_counts"], np.ndarray)


class TestSetPriorTransition:
    """Tests for set_prior_transition method."""

    def test_from_matrix(self, small_adata, lsd_config, device, random_seed):
        """Test setting prior transition from a matrix."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)

        n_cells = len(lsd.adata)
        # Create random transition matrix
        P = np.random.rand(n_cells, n_cells)
        P = P / P.sum(axis=1, keepdims=True)

        lsd.set_prior_transition(prior_transition=P)

        assert lsd.P is not None
        assert lsd.P.shape == (n_cells, n_cells)

    def test_from_time(self, small_adata, lsd_config, device, random_seed):
        """Test setting prior transition from pseudotime."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")

        assert lsd.P is not None
        assert lsd.P.shape[0] == len(lsd.adata)

    def test_transition_rows_sum_to_one(self, small_adata, lsd_config, device, random_seed):
        """Test that transition matrix rows sum to 1."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")

        row_sums = lsd.P.sum(dim=1).numpy()
        np.testing.assert_allclose(row_sums, np.ones_like(row_sums), rtol=1e-5)


class TestPrepareWalks:
    """Tests for prepare_walks method."""

    def test_walk_shape(self, small_adata, lsd_config, device, random_seed):
        """Test that walks have correct shape."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")
        lsd.prepare_walks(n_trajectories=50)

        assert lsd.walks is not None
        assert lsd.walks.shape == (50, lsd_config.walks.path_len)

    def test_valid_indices(self, small_adata, lsd_config, device, random_seed):
        """Test that walk indices are valid cell indices."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")
        lsd.prepare_walks(n_trajectories=50)

        n_cells = len(lsd.adata)
        assert lsd.walks.min() >= 0
        assert lsd.walks.max() < n_cells

    def test_on_cpu(self, small_adata, lsd_config, device, random_seed):
        """Test that walks are moved to CPU after generation."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")
        lsd.prepare_walks(n_trajectories=50)

        assert lsd.walks.device == torch.device("cpu")


class TestGetVariables:
    """Tests for get_variables method."""

    def test_output_shapes(self, small_adata, lsd_config, device, random_seed):
        """Test that get_variables produces correct shapes."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)

        x = small_adata.X
        if hasattr(x, "toarray"):
            x = x.toarray()
        x = torch.from_numpy(x).float()

        B, z, entropy, potential, pseudotime = lsd.get_variables(x)

        n_cells = len(small_adata)
        assert B.shape == (n_cells, lsd_config.model.B_dim)
        assert z.shape == (n_cells, lsd_config.model.z_dim)
        assert entropy.shape == (n_cells,)
        assert potential.shape == (n_cells, 1)
        assert pseudotime.shape == (n_cells, 1)

    def test_deterministic(self, small_adata, lsd_config, device, random_seed):
        """Test that get_variables is deterministic (eval mode)."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)

        x = small_adata.X
        if hasattr(x, "toarray"):
            x = x.toarray()
        x = torch.from_numpy(x).float()

        # Call twice
        B1, z1, _, _, _ = lsd.get_variables(x)
        B2, z2, _, _, _ = lsd.get_variables(x)

        assert torch.allclose(B1, B2)
        assert torch.allclose(z1, z2)

    def test_pseudotime_normalized(self, small_adata, lsd_config, device, random_seed):
        """Test that pseudotime is normalized to [0, 1]."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)

        x = small_adata.X
        if hasattr(x, "toarray"):
            x = x.toarray()
        x = torch.from_numpy(x).float()

        _, _, _, _, pseudotime = lsd.get_variables(x)

        assert pseudotime.min() >= 0
        assert pseudotime.max() <= 1


class TestGetAdata:
    """Tests for get_adata method."""

    def test_adds_obs(self, small_adata, lsd_config, device, random_seed):
        """Test that get_adata adds required obs columns."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")
        result = lsd.get_adata()

        assert "lsd_pseudotime" in result.obs.columns
        assert "potential" in result.obs.columns
        assert "entropy" in result.obs.columns

    def test_adds_obsm(self, small_adata, lsd_config, device, random_seed):
        """Test that get_adata adds required obsm entries."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")
        result = lsd.get_adata()

        assert "cell_rep" in result.obsm
        assert "diff_rep" in result.obsm
        assert result.obsm["cell_rep"].shape == (len(result), lsd_config.model.z_dim)
        assert result.obsm["diff_rep"].shape == (len(result), lsd_config.model.B_dim)

    def test_adds_obsp(self, small_adata, lsd_config, device, random_seed):
        """Test that get_adata adds transition matrix to obsp."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")
        result = lsd.get_adata()

        assert "transitions" in result.obsp
        n_cells = len(result)
        assert result.obsp["transitions"].shape == (n_cells, n_cells)


class TestSaveLoad:
    """Tests for save and load methods."""

    def test_creates_file(self, small_adata, lsd_config, device, random_seed, tmp_path):
        """Test that save creates checkpoint file."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)
        save_path = str(tmp_path / "test_checkpoint")

        lsd.save(dir_path=save_path, file_name="model.pth")

        assert (tmp_path / "test_checkpoint" / "model.pth").exists()

    def test_restores_state(self, small_adata, lsd_config, device, random_seed, tmp_path):
        """Test that load restores model state correctly."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        # Train briefly and save
        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")
        lsd.prepare_walks(n_trajectories=50)

        # Get state before save
        x = small_adata.X
        if hasattr(x, "toarray"):
            x = x.toarray()
        x = torch.from_numpy(x).float()
        _, z_before, _, _, _ = lsd.get_variables(x)

        # Save
        save_path = str(tmp_path / "checkpoint")
        lsd.save(dir_path=save_path, file_name="model.pth")

        # Create new model and load
        clear_pyro_state()
        lsd_loaded = LSD(small_adata, lsd_config, device=device)
        lsd_loaded.load(dir_path=save_path, file_name="model.pth")

        # Get state after load
        _, z_after, _, _, _ = lsd_loaded.get_variables(x)

        assert torch.allclose(z_before, z_after)


class TestTrain:
    """Tests for train method."""

    @pytest.mark.slow
    def test_epochs_complete(self, small_adata, lsd_config, device, random_seed):
        """Test that training completes all epochs."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")
        lsd.prepare_walks(n_trajectories=50)

        n_epochs = 2
        lsd.train(num_epochs=n_epochs, plot_loss=False, random_state=random_seed)

        assert lsd.epoch == n_epochs

    @pytest.mark.slow
    def test_checkpointing(self, small_adata, lsd_config, device, random_seed, tmp_path):
        """Test that checkpoints are saved at intervals."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")
        lsd.prepare_walks(n_trajectories=50)

        save_dir = str(tmp_path / "checkpoints")
        lsd.train(
            num_epochs=2,
            save_dir=save_dir,
            save_interval=1,
            plot_loss=False,
            random_state=random_seed
        )

        # Should have checkpoint at epoch 1 and 2
        assert (tmp_path / "checkpoints" / "lsd_model_epoch0001.pth").exists()
        assert (tmp_path / "checkpoints" / "lsd_model_epoch0002.pth").exists()


class TestCalculateTransitionProbs:
    """Tests for calculate_transition_probs method."""

    def test_row_normalized(self, small_adata, lsd_config, device, random_seed):
        """Test that transition matrix is row-normalized."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)

        n = 10
        potential = np.linspace(0, 1, n)
        connectivity = np.ones((n, n))

        P = lsd.calculate_transition_probs(potential, connectivity)

        row_sums = P.sum(axis=1)
        np.testing.assert_allclose(row_sums, np.ones_like(row_sums), rtol=1e-5)

    def test_respects_connectivity(self, small_adata, lsd_config, device, random_seed):
        """Test that disconnected cells have zero transition prob."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)

        n = 10
        potential = np.linspace(0, 1, n)
        # Block diagonal connectivity (two disconnected groups)
        connectivity = np.zeros((n, n))
        connectivity[:5, :5] = 1
        connectivity[5:, 5:] = 1

        P = lsd.calculate_transition_probs(potential, connectivity)

        # No transitions between groups
        assert P[:5, 5:].sum() == 0
        assert P[5:, :5].sum() == 0


class TestPhylogeny:
    """Tests for phylogeny-related methods."""

    def test_set_phylogeny(self, small_adata, lsd_config, device, random_seed):
        """Test setting phylogeny."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)

        lsd = LSD(small_adata, lsd_config, device=device)

        phylogeny = {
            "A": ["B"],
            "B": ["C"],
            "C": [],
        }
        lsd.set_phylogeny(phylogeny, cluster_key="clusters")

        assert lsd.phylogeny == phylogeny
        assert lsd.cluster_key == "clusters"
