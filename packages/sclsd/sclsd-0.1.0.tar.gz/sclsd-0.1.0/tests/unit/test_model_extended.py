"""Extended unit tests for lsdpy.core.model module.

This module extends the existing test_model.py with additional tests
including critical Pyro sample ordering verification.
"""

import pytest
import torch
import torch.nn as nn

pytest.importorskip("pyro")


class TestWassersteinDistance:
    """Tests for wasserstein_distance function."""

    def test_computation(self):
        """Test basic Wasserstein distance computation."""
        from sclsd.core.model import wasserstein_distance
        from sclsd.core.networks import XEncoder

        encoder = XEncoder(hidden_dims=[32], latent_dim=10, num_genes=100)

        batch_size = 8
        path_len = 4
        x = torch.randn(batch_size * path_len, 100)

        W2 = wasserstein_distance(encoder, x, path_len, latent_dim=10)

        assert W2.ndim == 0 or W2.shape == ()  # Scalar
        assert W2.item() >= 0  # Distance is non-negative

    def test_zero_for_identical_trajectories(self):
        """Test that W2 is minimal when all points are similar."""
        from sclsd.core.model import wasserstein_distance
        from sclsd.core.networks import XEncoder

        encoder = XEncoder(hidden_dims=[32], latent_dim=10, num_genes=100)

        batch_size = 8
        path_len = 4
        # Create identical points along trajectory
        x_single = torch.randn(1, 100)
        x = x_single.expand(batch_size * path_len, 100).clone()

        W2 = wasserstein_distance(encoder, x, path_len, latent_dim=10)

        # Should be near zero (or at least small)
        assert W2.item() < 1.0  # Tolerance for numerical differences

    def test_gradient_flow(self):
        """Test that gradients flow through W2 computation."""
        from sclsd.core.model import wasserstein_distance
        from sclsd.core.networks import XEncoder

        encoder = XEncoder(hidden_dims=[32], latent_dim=10, num_genes=100)

        x = torch.randn(32, 100, requires_grad=True)
        W2 = wasserstein_distance(encoder, x, path_len=4, latent_dim=10)
        W2.backward()

        assert x.grad is not None
        assert not torch.isnan(x.grad).any()


class TestEntropyReg:
    """Tests for entropy_reg function."""

    def test_computation(self):
        """Test basic entropy regularization computation."""
        from sclsd.core.model import entropy_reg
        from sclsd.core.networks import ZEncoder

        encoder = ZEncoder(hidden_dims=[32], latent_dim=10, state_dim=2)

        batch_size = 8
        path_len = 4
        s = torch.randn(batch_size * path_len, 10)

        S = entropy_reg(encoder, s, path_len, state_dim=2)

        assert S.ndim == 0 or S.shape == ()  # Scalar

    def test_negative_output(self):
        """Test that entropy_reg returns negative value (penalty)."""
        from sclsd.core.model import entropy_reg
        from sclsd.core.networks import ZEncoder

        encoder = ZEncoder(hidden_dims=[32], latent_dim=10, state_dim=2)

        s = torch.randn(32, 10)
        S = entropy_reg(encoder, s, path_len=4, state_dim=2)

        # Should be non-positive (negative entropy)
        assert S.item() <= 0

    def test_gradient_flow(self):
        """Test that gradients flow through entropy computation."""
        from sclsd.core.model import entropy_reg
        from sclsd.core.networks import ZEncoder

        encoder = ZEncoder(hidden_dims=[32], latent_dim=10, state_dim=2)

        s = torch.randn(32, 10, requires_grad=True)
        S = entropy_reg(encoder, s, path_len=4, state_dim=2)
        S.backward()

        assert s.grad is not None


class TestLSDModelInit:
    """Tests for LSDModel initialization."""

    @pytest.fixture
    def layer_dims(self):
        """Standard layer dims for testing."""
        from sclsd.core.config import LogCoshActivation
        return {
            "B_decoder": [16],
            "z_decoder": [32, 16],
            "x_encoder": [32, 16],
            "potential": [16],
            "potential_af": LogCoshActivation(),
        }

    def test_creates_all_components(self, layer_dims):
        """Test that all network components are created."""
        from sclsd.core.model import LSDModel

        model = LSDModel(
            B_dim=2,
            z_dim=10,
            num_genes=100,
            layer_dims=layer_dims,
            batch_size=32,
            path_len=4,
            device=torch.device("cpu"),
        )

        assert hasattr(model, "B_decoder")
        assert hasattr(model, "z_decoder")
        assert hasattr(model, "x_encoder")
        assert hasattr(model, "z_encoder")
        assert hasattr(model, "xl_encoder")
        assert hasattr(model, "potential")
        assert hasattr(model, "gradnet")
        assert hasattr(model, "rnn")

    def test_dimensions_stored(self, layer_dims):
        """Test that dimensions are stored correctly."""
        from sclsd.core.model import LSDModel

        model = LSDModel(
            B_dim=2,
            z_dim=10,
            num_genes=100,
            layer_dims=layer_dims,
            batch_size=32,
            path_len=4,
            device=torch.device("cpu"),
        )

        assert model.B_dim == 2
        assert model.z_dim == 10
        assert model.x_dim == 100
        assert model.batch_size == 32
        assert model.path_len == 4

    def test_coefficients_stored(self, layer_dims):
        """Test that regularization coefficients are stored."""
        from sclsd.core.model import LSDModel

        model = LSDModel(
            B_dim=2,
            z_dim=10,
            num_genes=100,
            layer_dims=layer_dims,
            batch_size=32,
            path_len=4,
            device=torch.device("cpu"),
            V_coeff=0.01,
            scale_factor=2.0,
        )

        assert model.V_coeff == 0.01
        assert model.scale_factor == 2.0


class TestLSDModelMethods:
    """Tests for LSDModel model() and guide() methods."""

    @pytest.fixture
    def model_and_data(self):
        """Create model and synthetic data for testing."""
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

        batch_size = 8
        path_len = 4
        n_samples = batch_size * path_len

        x_raw = torch.randint(0, 100, (n_samples, 100)).float()
        x = torch.randn(n_samples, 100)
        xl = torch.exp(torch.randn(n_samples, 1) + 7)

        return model, x_raw, x, xl

    def test_model_runs_without_error(self, model_and_data):
        """Test that model() runs without error."""
        import pyro
        from sclsd import clear_pyro_state

        clear_pyro_state()
        model, x_raw, x, xl = model_and_data

        # Should not raise
        model.model(x_raw, x, xl=xl, annealing_factor=1.0)

    def test_guide_runs_without_error(self, model_and_data):
        """Test that guide() runs without error."""
        from sclsd import clear_pyro_state

        clear_pyro_state()
        model, x_raw, x, xl = model_and_data

        # Should not raise
        model.guide(x_raw, x, xl=xl, annealing_factor=1.0)

    def test_model_without_xl(self, model_and_data):
        """Test that model() works when xl is None (sampled from prior)."""
        from sclsd import clear_pyro_state

        clear_pyro_state()
        model, x_raw, x, _ = model_and_data

        # Should not raise - xl should be sampled
        model.model(x_raw, x, xl=None, annealing_factor=1.0)

    def test_guide_without_xl(self, model_and_data):
        """Test that guide() works when xl is None (sampled from guide)."""
        from sclsd import clear_pyro_state

        clear_pyro_state()
        model, x_raw, x, _ = model_and_data

        # Should not raise - xl should be sampled
        model.guide(x_raw, x, xl=None, annealing_factor=1.0)


class TestPyroSampleOrder:
    """CRITICAL tests for Pyro sample ordering.

    These tests verify that the sample order in model() and guide()
    matches the documented order, which is essential for reproducibility.
    """

    @pytest.fixture
    def setup(self):
        """Set up model and data for tracing."""
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
        xl = torch.exp(torch.randn(n_samples, 1) + 7)

        return model, x_raw, x, xl

    def test_model_sample_order(self, setup):
        """CRITICAL: Verify model() sample order matches documentation.

        Order must be: module -> param -> B -> z -> xl -> x
        """
        import pyro
        import pyro.poutine as poutine
        from sclsd import clear_pyro_state

        clear_pyro_state()
        model, x_raw, x, _ = setup

        # Trace the model execution
        trace = poutine.trace(model.model).get_trace(x_raw, x, xl=None)

        # Get sample sites in order
        sample_sites = [
            name for name, node in trace.nodes.items()
            if node["type"] == "sample" and not name.startswith("_")
        ]

        # Extract names (removing plate annotations)
        sample_names = [s.split("[")[0] for s in sample_sites]

        # Verify order - B must come before z, z before xl, xl before x
        assert "B" in sample_names, "B not found in samples"
        assert "z" in sample_names, "z not found in samples"
        assert "xl" in sample_names, "xl not found in samples"
        assert "x" in sample_names, "x not found in samples"

        b_idx = sample_names.index("B")
        z_idx = sample_names.index("z")
        xl_idx = sample_names.index("xl")
        x_idx = sample_names.index("x")

        assert b_idx < z_idx, f"B ({b_idx}) must come before z ({z_idx})"
        assert z_idx < xl_idx, f"z ({z_idx}) must come before xl ({xl_idx})"
        assert xl_idx < x_idx, f"xl ({xl_idx}) must come before x ({x_idx})"

    def test_guide_sample_order(self, setup):
        """CRITICAL: Verify guide() sample order matches documentation.

        Order must be: module -> factor(V_l2) -> z -> B -> xl -> factor(W2)
        """
        import pyro
        import pyro.poutine as poutine
        from sclsd import clear_pyro_state

        clear_pyro_state()
        model, x_raw, x, _ = setup

        # Trace the guide execution
        trace = poutine.trace(model.guide).get_trace(x_raw, x, xl=None)

        # Get sample and factor sites in order
        ordered_sites = []
        for name, node in trace.nodes.items():
            if node["type"] in ["sample", "param"] and not name.startswith("_"):
                ordered_sites.append((name, node["type"]))

        site_names = [s[0].split("[")[0] for s in ordered_sites]

        # Verify z comes before B in guide
        assert "z" in site_names, "z not found in guide samples"
        assert "B" in site_names, "B not found in guide samples"

        z_idx = site_names.index("z")
        b_idx = site_names.index("B")

        assert z_idx < b_idx, f"z ({z_idx}) must come before B ({b_idx}) in guide"

    def test_model_guide_consistency(self, setup):
        """Test that model and guide sample the same variables."""
        import pyro
        import pyro.poutine as poutine
        from sclsd import clear_pyro_state

        clear_pyro_state()
        model, x_raw, x, _ = setup

        # Get model samples
        model_trace = poutine.trace(model.model).get_trace(x_raw, x, xl=None)
        model_samples = {
            name for name, node in model_trace.nodes.items()
            if node["type"] == "sample" and not node.get("is_observed", False)
            and not name.startswith("_")
        }

        clear_pyro_state()

        # Get guide samples
        guide_trace = poutine.trace(model.guide).get_trace(x_raw, x, xl=None)
        guide_samples = {
            name for name, node in guide_trace.nodes.items()
            if node["type"] == "sample" and not name.startswith("_")
        }

        # Model latent samples should be in guide (observed excluded)
        model_latent = {s.split("[")[0] for s in model_samples}
        guide_latent = {s.split("[")[0] for s in guide_samples}

        # z, B, xl should be in both
        for var in ["z", "B", "xl"]:
            assert var in model_latent, f"{var} not in model"
            assert var in guide_latent, f"{var} not in guide"


class TestGradientNet:
    """Tests for GradientNet in the model context."""

    def test_gradnet_output_shape(self):
        """Test GradientNet output shape matches input."""
        from sclsd.core.model import LSDModel
        from sclsd.core.config import LogCoshActivation

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
        )

        z = torch.randn(16, 10)
        t = torch.tensor(0.0)
        grad = model.gradnet(t, z)

        assert grad.shape == z.shape

    def test_gradnet_no_nan(self):
        """Test GradientNet produces no NaN values."""
        from sclsd.core.model import LSDModel
        from sclsd.core.config import LogCoshActivation

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
        )

        for scale in [0.1, 1.0, 10.0]:
            z = torch.randn(16, 10) * scale
            grad = model.gradnet(torch.tensor(0.0), z)
            assert not torch.isnan(grad).any(), f"NaN at scale {scale}"
