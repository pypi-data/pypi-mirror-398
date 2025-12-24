"""Tests for reproducibility of LSD training.

CRITICAL: These tests verify that the package produces IDENTICAL results
with the same random seed. Any changes to Pyro sample ordering will cause
these tests to fail.
"""

import pytest
import numpy as np
import torch

# Skip tests if dependencies not available
pytest.importorskip("scanpy")
pytest.importorskip("pyro")


class TestReproducibility:
    """Tests for reproducible training results."""

    def test_set_all_seeds_deterministic(self, random_seed):
        """Test that set_all_seeds produces deterministic random numbers."""
        from sclsd import set_all_seeds

        # First run
        set_all_seeds(random_seed)
        rand1 = np.random.rand(10)
        torch1 = torch.rand(10)

        # Second run with same seed
        set_all_seeds(random_seed)
        rand2 = np.random.rand(10)
        torch2 = torch.rand(10)

        np.testing.assert_array_equal(rand1, rand2)
        assert torch.allclose(torch1, torch2)

    def test_model_initialization_deterministic(self, small_adata, lsd_config, device, random_seed):
        """Test that model initialization is deterministic."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        # First initialization
        clear_pyro_state()
        set_all_seeds(random_seed)
        lsd1 = LSD(small_adata, lsd_config, device=device)
        weights1 = {k: v.clone() for k, v in lsd1.lsd.state_dict().items()}

        # Second initialization with same seed
        clear_pyro_state()
        set_all_seeds(random_seed)
        lsd2 = LSD(small_adata, lsd_config, device=device)
        weights2 = lsd2.lsd.state_dict()

        for key in weights1:
            assert torch.allclose(weights1[key], weights2[key]), f"Mismatch in {key}"

    def test_random_walks_deterministic(self, small_adata, lsd_config, device, random_seed):
        """Test that random walk generation is deterministic."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        # First run
        clear_pyro_state()
        set_all_seeds(random_seed)
        lsd1 = LSD(small_adata, lsd_config, device=device)
        lsd1.set_prior_transition(prior_time_key="pseudotime")
        lsd1.prepare_walks(n_trajectories=50)
        walks1 = lsd1.walks.clone()

        # Second run with same seed
        clear_pyro_state()
        set_all_seeds(random_seed)
        lsd2 = LSD(small_adata, lsd_config, device=device)
        lsd2.set_prior_transition(prior_time_key="pseudotime")
        lsd2.prepare_walks(n_trajectories=50)
        walks2 = lsd2.walks.clone()

        assert torch.equal(walks1, walks2), "Random walks are not deterministic"

    def test_training_deterministic(self, small_adata, lsd_config, device, random_seed):
        """Test that training produces identical results with same seed."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        n_epochs = 2  # Small number for testing

        # First training run
        clear_pyro_state()
        set_all_seeds(random_seed)
        lsd1 = LSD(small_adata, lsd_config, device=device)
        lsd1.set_prior_transition(prior_time_key="pseudotime")
        lsd1.prepare_walks(n_trajectories=50)
        lsd1.train(num_epochs=n_epochs, plot_loss=False, random_state=random_seed)
        result1 = lsd1.get_adata()

        # Second training run with same seed
        clear_pyro_state()
        set_all_seeds(random_seed)
        lsd2 = LSD(small_adata, lsd_config, device=device)
        lsd2.set_prior_transition(prior_time_key="pseudotime")
        lsd2.prepare_walks(n_trajectories=50)
        lsd2.train(num_epochs=n_epochs, plot_loss=False, random_state=random_seed)
        result2 = lsd2.get_adata()

        # Check that results are identical
        np.testing.assert_allclose(
            result1.obs["lsd_pseudotime"].values,
            result2.obs["lsd_pseudotime"].values,
            rtol=1e-5,
            err_msg="Pseudotime values differ between runs"
        )
        np.testing.assert_allclose(
            result1.obs["potential"].values,
            result2.obs["potential"].values,
            rtol=1e-5,
            err_msg="Potential values differ between runs"
        )
        np.testing.assert_allclose(
            result1.obsm["cell_rep"],
            result2.obsm["cell_rep"],
            rtol=1e-5,
            err_msg="Cell representations differ between runs"
        )

    def test_get_variables_deterministic(self, small_adata, lsd_config, device, random_seed):
        """Test that get_variables produces deterministic outputs."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)
        lsd = LSD(small_adata, lsd_config, device=device)

        x = small_adata.X
        if hasattr(x, "toarray"):
            x = x.toarray()
        x = torch.from_numpy(x).float()

        # First call
        B1, z1, entropy1, potential1, pseudotime1 = lsd.get_variables(x)

        # Second call (should be identical since model is in eval mode)
        B2, z2, entropy2, potential2, pseudotime2 = lsd.get_variables(x)

        assert torch.allclose(B1, B2)
        assert torch.allclose(z1, z2)
        assert torch.allclose(potential1, potential2)


class TestModelSaveLoad:
    """Tests for model save/load reproducibility."""

    def test_save_load_produces_same_results(self, small_adata, lsd_config, device, random_seed, tmp_path):
        """Test that saved and loaded models produce identical results."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        # Train a model
        clear_pyro_state()
        set_all_seeds(random_seed)
        lsd = LSD(small_adata, lsd_config, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")
        lsd.prepare_walks(n_trajectories=50)
        lsd.train(num_epochs=2, plot_loss=False, random_state=random_seed)

        # Get results before saving
        result_before = lsd.get_adata()

        # Save model
        save_path = str(tmp_path / "test_model")
        lsd.save(dir_path=save_path, file_name="model.pth")

        # Create new model and load
        clear_pyro_state()
        lsd_loaded = LSD(small_adata, lsd_config, device=device)
        lsd_loaded.load(dir_path=save_path, file_name="model.pth")

        # Get results after loading
        result_after = lsd_loaded.get_adata()

        # Compare results
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


class TestTransitionMatrix:
    """Tests for transition matrix computation."""

    def test_transition_probs_sum_to_one(self, small_adata, lsd_config, device, random_seed):
        """Test that transition probabilities sum to 1."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)
        lsd = LSD(small_adata, lsd_config, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")

        P = lsd.P.numpy()
        row_sums = P.sum(axis=1)

        np.testing.assert_allclose(row_sums, np.ones_like(row_sums), rtol=1e-5)

    def test_transition_probs_non_negative(self, small_adata, lsd_config, device, random_seed):
        """Test that transition probabilities are non-negative."""
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(random_seed)
        lsd = LSD(small_adata, lsd_config, device=device)
        lsd.set_prior_transition(prior_time_key="pseudotime")

        P = lsd.P.numpy()

        assert np.all(P >= 0), "Transition probabilities contain negative values"
