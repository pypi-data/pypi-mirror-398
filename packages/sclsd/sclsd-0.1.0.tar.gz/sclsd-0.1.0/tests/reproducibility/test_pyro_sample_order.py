"""CRITICAL tests for Pyro sample ordering.

These tests verify that the sample order in model() and guide() is preserved.
The order determines which random numbers are consumed from the RNG stream.
Any change to the order will produce different results.
"""

import pytest
import torch

pytest.importorskip("pyro")


class TestModelSampleOrder:
    """Tests for model() sample ordering."""

    @pytest.fixture
    def setup(self):
        """Set up model for testing."""
        from sclsd.core.model import LSDModel
        from sclsd.core.config import LogCoshActivation
        from sclsd import set_all_seeds, clear_pyro_state

        clear_pyro_state()
        set_all_seeds(42)

        layer_dims = {
            "B_decoder": [16],
            "z_decoder": [32, 16],
            "x_encoder": [32, 16],
            "potential": [16],
            "potential_af": LogCoshActivation(),
        }

        model = LSDModel(
            B_dim=2,
            z_dim=10,
            num_genes=100,
            layer_dims=layer_dims,
            batch_size=8,
            path_len=4,
            device=torch.device("cpu"),
            xl_loc=7.0,
            xl_scale=0.5,
        )

        n_samples = 32
        x_raw = torch.randint(0, 100, (n_samples, 100)).float()
        x = torch.randn(n_samples, 100)

        return model, x_raw, x

    @pytest.mark.reproducibility
    def test_model_sample_order_preserved(self, setup):
        """CRITICAL: Verify model() sample order.

        Expected order:
        1. pyro.module("LSD", self)
        2. pyro.param("inverse_dispersion", ...)
        3. pyro.sample('B', ...)        # Within annealing scale
        4. pyro.sample('z', ...)
        5. pyro.sample("xl", ...)       # Conditional
        6. pyro.sample("x", ..., obs=...) # Observed
        """
        import pyro
        import pyro.poutine as poutine
        from sclsd import clear_pyro_state

        clear_pyro_state()
        model, x_raw, x = setup

        # Trace the model
        trace = poutine.trace(model.model).get_trace(x_raw, x, xl=None)

        # Collect sample sites in order
        sample_order = []
        for name, node in trace.nodes.items():
            if node["type"] == "sample" and not name.startswith("_"):
                sample_order.append(name.split("[")[0])

        # Critical order: B before z before xl before x
        assert "B" in sample_order, "B sample not found"
        assert "z" in sample_order, "z sample not found"
        assert "xl" in sample_order, "xl sample not found"
        assert "x" in sample_order, "x sample not found"

        b_idx = sample_order.index("B")
        z_idx = sample_order.index("z")
        xl_idx = sample_order.index("xl")
        x_idx = sample_order.index("x")

        assert b_idx < z_idx, f"B must come before z (B={b_idx}, z={z_idx})"
        assert z_idx < xl_idx, f"z must come before xl (z={z_idx}, xl={xl_idx})"
        assert xl_idx < x_idx, f"xl must come before x (xl={xl_idx}, x={x_idx})"

    @pytest.mark.reproducibility
    def test_guide_sample_order_preserved(self, setup):
        """CRITICAL: Verify guide() sample order.

        Expected order:
        1. pyro.module("LSD", self)
        2. pyro.factor("V_l2_reg", ...)
        3. pyro.sample("z", ...)
        4. pyro.sample('B', ...)        # Within annealing scale
        5. pyro.sample("xl", ...)       # Conditional
        6. pyro.factor("W2", ...)
        """
        import pyro
        import pyro.poutine as poutine
        from sclsd import clear_pyro_state

        clear_pyro_state()
        model, x_raw, x = setup

        # Trace the guide
        trace = poutine.trace(model.guide).get_trace(x_raw, x, xl=None)

        # Collect sample sites in order
        sample_order = []
        for name, node in trace.nodes.items():
            if node["type"] == "sample" and not name.startswith("_"):
                sample_order.append(name.split("[")[0])

        # Critical order in guide: z before B
        assert "z" in sample_order, "z sample not found in guide"
        assert "B" in sample_order, "B sample not found in guide"

        z_idx = sample_order.index("z")
        b_idx = sample_order.index("B")

        assert z_idx < b_idx, f"z must come before B in guide (z={z_idx}, B={b_idx})"


class TestDeterminism:
    """Tests for deterministic behavior with same seed."""

    @pytest.mark.reproducibility
    def test_two_runs_identical(self):
        """Test that two runs with same seed produce identical results."""
        from sclsd import LSD, LSDConfig, set_all_seeds, clear_pyro_state
        from tests.fixtures.synthetic_data import create_synthetic_adata
        import numpy as np

        seed = 42
        n_epochs = 2

        # First run
        clear_pyro_state()
        set_all_seeds(seed)
        adata1 = create_synthetic_adata(n_cells=100, n_genes=50, seed=seed)

        cfg = LSDConfig()
        cfg.model.z_dim = 5
        cfg.walks.path_len = 4
        cfg.walks.num_walks = 50
        cfg.walks.batch_size = 25
        cfg.model.layer_dims.B_decoder = [16]
        cfg.model.layer_dims.z_decoder = [32, 16]
        cfg.model.layer_dims.x_encoder = [32, 16]
        cfg.model.layer_dims.potential = [8]

        lsd1 = LSD(adata1, cfg, device=torch.device("cpu"))
        lsd1.set_prior_transition(prior_time_key="pseudotime")
        lsd1.prepare_walks(n_trajectories=50)
        lsd1.train(num_epochs=n_epochs, plot_loss=False, random_state=seed)
        result1 = lsd1.get_adata()

        # Second run
        clear_pyro_state()
        set_all_seeds(seed)
        adata2 = create_synthetic_adata(n_cells=100, n_genes=50, seed=seed)

        lsd2 = LSD(adata2, cfg, device=torch.device("cpu"))
        lsd2.set_prior_transition(prior_time_key="pseudotime")
        lsd2.prepare_walks(n_trajectories=50)
        lsd2.train(num_epochs=n_epochs, plot_loss=False, random_state=seed)
        result2 = lsd2.get_adata()

        # Results must be identical
        np.testing.assert_allclose(
            result1.obs["lsd_pseudotime"].values,
            result2.obs["lsd_pseudotime"].values,
            rtol=1e-5,
            err_msg="Pseudotime differs between runs"
        )
        np.testing.assert_allclose(
            result1.obs["potential"].values,
            result2.obs["potential"].values,
            rtol=1e-5,
            err_msg="Potential differs between runs"
        )
        np.testing.assert_allclose(
            result1.obsm["cell_rep"],
            result2.obsm["cell_rep"],
            rtol=1e-5,
            err_msg="Cell representations differ between runs"
        )

    @pytest.mark.reproducibility
    def test_walks_deterministic(self):
        """Test that random walks are deterministic with same seed."""
        from sclsd import LSD, LSDConfig, set_all_seeds, clear_pyro_state
        from tests.fixtures.synthetic_data import create_synthetic_adata

        seed = 42

        # First run
        clear_pyro_state()
        set_all_seeds(seed)
        adata1 = create_synthetic_adata(n_cells=100, n_genes=50, seed=seed)

        cfg = LSDConfig()
        cfg.model.z_dim = 5
        cfg.walks.path_len = 4
        cfg.model.layer_dims.B_decoder = [16]
        cfg.model.layer_dims.z_decoder = [32, 16]
        cfg.model.layer_dims.x_encoder = [32, 16]
        cfg.model.layer_dims.potential = [8]

        lsd1 = LSD(adata1, cfg, device=torch.device("cpu"))
        lsd1.set_prior_transition(prior_time_key="pseudotime")
        lsd1.prepare_walks(n_trajectories=50)
        walks1 = lsd1.walks.clone()

        # Second run
        clear_pyro_state()
        set_all_seeds(seed)
        adata2 = create_synthetic_adata(n_cells=100, n_genes=50, seed=seed)

        lsd2 = LSD(adata2, cfg, device=torch.device("cpu"))
        lsd2.set_prior_transition(prior_time_key="pseudotime")
        lsd2.prepare_walks(n_trajectories=50)
        walks2 = lsd2.walks.clone()

        assert torch.equal(walks1, walks2), "Walks differ between runs"
