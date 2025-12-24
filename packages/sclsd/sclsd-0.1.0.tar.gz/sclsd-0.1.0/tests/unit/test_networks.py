"""Unit tests for lsdpy.core.networks module."""

import pytest
import torch
import torch.nn as nn


class TestMakeFC:
    """Tests for make_fc helper function."""

    def test_output_shape(self):
        """Test that output shape is correct."""
        from sclsd.core.networks import make_fc

        net = make_fc([100, 64, 32, 10])
        x = torch.randn(16, 100)
        y = net(x)
        assert y.shape == (16, 10)

    def test_contains_batchnorm(self):
        """Test that BatchNorm layers are included."""
        from sclsd.core.networks import make_fc

        net = make_fc([100, 64, 32])
        batchnorm_count = sum(1 for m in net.modules() if isinstance(m, nn.BatchNorm1d))
        assert batchnorm_count == 2  # One per hidden layer transition

    def test_contains_softplus(self):
        """Test that Softplus activations are included."""
        from sclsd.core.networks import make_fc

        net = make_fc([100, 64, 32])
        softplus_count = sum(1 for m in net.modules() if isinstance(m, nn.Softplus))
        # Should have softplus after each hidden layer except last
        assert softplus_count >= 1

    def test_single_layer(self):
        """Test with single layer (input -> output)."""
        from sclsd.core.networks import make_fc

        net = make_fc([100, 10])
        x = torch.randn(16, 100)
        y = net(x)
        assert y.shape == (16, 10)


class TestMakeFCWoBatchNorm:
    """Tests for make_fc_wo_batch_norm helper function."""

    def test_output_shape(self):
        """Test that output shape is correct."""
        from sclsd.core.networks import make_fc_wo_batch_norm

        net = make_fc_wo_batch_norm([100, 64, 32, 10])
        x = torch.randn(16, 100)
        y = net(x)
        assert y.shape == (16, 10)

    def test_no_batchnorm(self):
        """Test that no BatchNorm layers are included."""
        from sclsd.core.networks import make_fc_wo_batch_norm

        net = make_fc_wo_batch_norm([100, 64, 32])
        batchnorm_count = sum(1 for m in net.modules() if isinstance(m, nn.BatchNorm1d))
        assert batchnorm_count == 0


class TestMakeF:
    """Tests for make_f helper function with custom activation."""

    def test_output_shape(self):
        """Test that output shape is correct."""
        from sclsd.core.networks import make_f

        net = make_f([100, 64, 32], nn.Tanh())
        x = torch.randn(16, 100)
        y = net(x)
        assert y.shape == (16, 32)

    def test_uses_custom_activation(self):
        """Test that custom activation is used."""
        from sclsd.core.networks import make_f

        net = make_f([100, 64, 32], nn.ReLU())
        relu_count = sum(1 for m in net.modules() if isinstance(m, nn.ReLU))
        assert relu_count >= 1


class TestSplitInHalf:
    """Tests for split_in_half helper function."""

    def test_split_dimensions(self):
        """Test that tensors are split correctly."""
        from sclsd.core.networks import split_in_half

        t = torch.randn(16, 20)
        a, b = split_in_half(t)
        assert a.shape == (16, 10)
        assert b.shape == (16, 10)

    def test_split_values(self):
        """Test that values are preserved correctly."""
        from sclsd.core.networks import split_in_half

        t = torch.arange(20).float().unsqueeze(0)  # Shape (1, 20)
        a, b = split_in_half(t)
        # First half should be 0-9, second half 10-19
        assert torch.allclose(a, torch.arange(10).float().unsqueeze(0))
        assert torch.allclose(b, torch.arange(10, 20).float().unsqueeze(0))

    def test_batched_split(self):
        """Test split with batch dimensions."""
        from sclsd.core.networks import split_in_half

        t = torch.randn(8, 16, 20)
        a, b = split_in_half(t)
        assert a.shape == (8, 16, 10)
        assert b.shape == (8, 16, 10)


class TestStateDecoder:
    """Tests for StateDecoder network (p(z|B))."""

    def test_output_shape(self):
        """Test that output shapes are correct."""
        from sclsd.core.networks import StateDecoder

        decoder = StateDecoder(hidden_dims=[32, 64], latent_dim=10, state_dim=2)
        B = torch.randn(16, 2)
        loc, scale = decoder(B)

        assert loc.shape == (16, 10)
        assert scale.shape == (16, 10)

    def test_scale_positive(self):
        """Test that scale values are always positive."""
        from sclsd.core.networks import StateDecoder

        decoder = StateDecoder(hidden_dims=[32], latent_dim=10, state_dim=2)
        B = torch.randn(100, 2)
        _, scale = decoder(B)

        assert (scale > 0).all(), "Scale must be positive"

    def test_gradient_flow(self):
        """Test that gradients flow correctly."""
        from sclsd.core.networks import StateDecoder

        decoder = StateDecoder(hidden_dims=[32], latent_dim=10, state_dim=2)
        B = torch.randn(16, 2, requires_grad=True)
        loc, scale = decoder(B)
        loss = loc.sum() + scale.sum()
        loss.backward()

        assert B.grad is not None
        assert not torch.isnan(B.grad).any()

    def test_batched_input(self):
        """Test with extra batch dimensions."""
        from sclsd.core.networks import StateDecoder

        decoder = StateDecoder(hidden_dims=[32], latent_dim=10, state_dim=2)
        # Flatten batch for forward, reshape after
        B = torch.randn(8 * 16, 2)
        loc, scale = decoder(B)
        assert loc.shape == (128, 10)


class TestZDecoder:
    """Tests for ZDecoder network (p(x|z))."""

    def test_output_shape(self):
        """Test that output shapes are correct."""
        from sclsd.core.networks import ZDecoder

        decoder = ZDecoder(hidden_dims=[32, 64], num_genes=100, latent_dim=10)
        z = torch.randn(16, 10)
        gate, mu = decoder(z)

        assert gate.shape == (16, 100)
        assert mu.shape == (16, 100)

    def test_mu_normalized(self):
        """Test that mu values sum to 1 (softmax normalization)."""
        from sclsd.core.networks import ZDecoder

        decoder = ZDecoder(hidden_dims=[32], num_genes=100, latent_dim=10)
        z = torch.randn(16, 10)
        _, mu = decoder(z)

        sums = mu.sum(dim=-1)
        assert torch.allclose(sums, torch.ones_like(sums), atol=1e-5)

    def test_mu_positive(self):
        """Test that mu values are positive."""
        from sclsd.core.networks import ZDecoder

        decoder = ZDecoder(hidden_dims=[32], num_genes=100, latent_dim=10)
        z = torch.randn(100, 10)
        _, mu = decoder(z)

        assert (mu >= 0).all(), "Mu must be non-negative"

    def test_gradient_flow(self):
        """Test that gradients flow correctly."""
        from sclsd.core.networks import ZDecoder

        decoder = ZDecoder(hidden_dims=[32], num_genes=100, latent_dim=10)
        z = torch.randn(16, 10, requires_grad=True)
        gate, mu = decoder(z)
        loss = gate.sum() + mu.sum()
        loss.backward()

        assert z.grad is not None


class TestXEncoder:
    """Tests for XEncoder network (q(z|x))."""

    def test_output_shape(self):
        """Test that output shapes are correct."""
        from sclsd.core.networks import XEncoder

        encoder = XEncoder(hidden_dims=[64, 32], latent_dim=10, num_genes=100)
        x = torch.randn(16, 100)
        loc, scale = encoder(x)

        assert loc.shape == (16, 10)
        assert scale.shape == (16, 10)

    def test_scale_positive(self):
        """Test that scale values are always positive."""
        from sclsd.core.networks import XEncoder

        encoder = XEncoder(hidden_dims=[32], latent_dim=10, num_genes=100)
        x = torch.randn(100, 100)
        _, scale = encoder(x)

        assert (scale > 0).all(), "Scale must be positive"

    def test_handles_sparse_input(self):
        """Test that encoder handles sparse-like input (many zeros)."""
        from sclsd.core.networks import XEncoder

        encoder = XEncoder(hidden_dims=[32], latent_dim=10, num_genes=100)
        # Simulate sparse count data
        x = torch.zeros(16, 100)
        x[:, :10] = torch.randn(16, 10).abs()  # Only first 10 genes expressed
        loc, scale = encoder(x)

        assert not torch.isnan(loc).any()
        assert not torch.isnan(scale).any()

    def test_gradient_flow(self):
        """Test that gradients flow correctly."""
        from sclsd.core.networks import XEncoder

        encoder = XEncoder(hidden_dims=[32], latent_dim=10, num_genes=100)
        x = torch.randn(16, 100, requires_grad=True)
        loc, scale = encoder(x)
        loss = loc.sum() + scale.sum()
        loss.backward()

        assert x.grad is not None


class TestZEncoder:
    """Tests for ZEncoder network (q(B|z))."""

    def test_output_shape(self):
        """Test that output shapes are correct."""
        from sclsd.core.networks import ZEncoder

        encoder = ZEncoder(hidden_dims=[32, 16], latent_dim=10, state_dim=2)
        z = torch.randn(16, 10)
        loc, scale = encoder(z)

        assert loc.shape == (16, 2)
        assert scale.shape == (16, 2)

    def test_scale_positive(self):
        """Test that scale values are always positive."""
        from sclsd.core.networks import ZEncoder

        encoder = ZEncoder(hidden_dims=[32], latent_dim=10, state_dim=2)
        z = torch.randn(100, 10)
        _, scale = encoder(z)

        assert (scale > 0).all(), "Scale must be positive"

    def test_gradient_flow(self):
        """Test that gradients flow correctly."""
        from sclsd.core.networks import ZEncoder

        encoder = ZEncoder(hidden_dims=[32], latent_dim=10, state_dim=2)
        z = torch.randn(16, 10, requires_grad=True)
        loc, scale = encoder(z)
        loss = loc.sum() + scale.sum()
        loss.backward()

        assert z.grad is not None


class TestLEncoder:
    """Tests for LEncoder network (library size encoder)."""

    def test_output_shape(self):
        """Test that output shapes are correct."""
        from sclsd.core.networks import LEncoder

        encoder = LEncoder(hidden_dims=[32, 16], num_genes=100)
        x = torch.randn(16, 100)
        loc, scale = encoder(x)

        assert loc.shape == (16, 1)
        assert scale.shape == (16, 1)

    def test_scale_positive(self):
        """Test that scale values are always positive."""
        from sclsd.core.networks import LEncoder

        encoder = LEncoder(hidden_dims=[32], num_genes=100)
        x = torch.randn(100, 100)
        _, scale = encoder(x)

        assert (scale > 0).all(), "Scale must be positive"


class TestPotentialNet:
    """Tests for PotentialNet network."""

    def test_output_shape(self):
        """Test that output shape is correct."""
        from sclsd.core.networks import PotentialNet
        from sclsd.core.config import LogCoshActivation

        potential = PotentialNet(hidden_dims=[32, 16], latent_dim=10, af=LogCoshActivation())
        z = torch.randn(16, 10)
        V = potential(z)

        assert V.shape == (16, 1)

    def test_gate_parameter_exists(self):
        """Test that gate parameter is created."""
        from sclsd.core.networks import PotentialNet
        from sclsd.core.config import LogCoshActivation

        potential = PotentialNet(hidden_dims=[32], latent_dim=10, af=LogCoshActivation())

        assert hasattr(potential, 'gate')
        assert isinstance(potential.gate, nn.Parameter)

    def test_gate_controls_output(self):
        """Test that gate parameter controls output magnitude."""
        from sclsd.core.networks import PotentialNet
        from sclsd.core.config import LogCoshActivation

        potential = PotentialNet(hidden_dims=[32], latent_dim=10, af=LogCoshActivation())
        z = torch.randn(16, 10)

        # With gate = 0 (sigmoid(0) = 0.5), output is halved
        potential.gate.data = torch.tensor(0.0)
        V1 = potential(z)

        # With large positive gate, output is near full
        potential.gate.data = torch.tensor(10.0)
        V2 = potential(z)

        # Gate at -10 should produce near-zero output
        potential.gate.data = torch.tensor(-10.0)
        V3 = potential(z)

        assert V3.abs().mean() < V1.abs().mean() < V2.abs().mean()

    def test_smooth_gradients(self):
        """Test that potential has smooth gradients (no NaN/Inf)."""
        from sclsd.core.networks import PotentialNet
        from sclsd.core.config import LogCoshActivation

        potential = PotentialNet(hidden_dims=[32], latent_dim=10, af=LogCoshActivation())
        z = torch.randn(16, 10, requires_grad=True)
        V = potential(z)
        V.sum().backward()

        assert not torch.isnan(z.grad).any()
        assert not torch.isinf(z.grad).any()


class TestGradientNet:
    """Tests for GradientNet network (ODE dynamics)."""

    def test_output_shape(self):
        """Test that output shape matches input."""
        from sclsd.core.networks import PotentialNet, GradientNet
        from sclsd.core.config import LogCoshActivation

        potential = PotentialNet(hidden_dims=[32], latent_dim=10, af=LogCoshActivation())
        gradnet = GradientNet(potential)

        z = torch.randn(16, 10)
        t = torch.tensor(0.0)
        grad = gradnet(t, z)

        assert grad.shape == z.shape

    def test_negative_gradient(self):
        """Test that output is negative gradient of potential."""
        from sclsd.core.networks import PotentialNet, GradientNet
        from sclsd.core.config import LogCoshActivation

        potential = PotentialNet(hidden_dims=[32], latent_dim=10, af=LogCoshActivation())
        gradnet = GradientNet(potential)

        # Compute gradient manually
        z = torch.randn(16, 10, requires_grad=True)
        V = potential(z)
        manual_grad = torch.autograd.grad(V.sum(), z, create_graph=True)[0]

        # Compute via GradientNet
        z2 = z.detach().clone()
        gradnet_output = gradnet(torch.tensor(0.0), z2)

        # GradientNet should return -grad
        assert torch.allclose(-manual_grad, gradnet_output, atol=1e-5)

    def test_ode_interface(self):
        """Test that GradientNet works with ODE solver interface."""
        from sclsd.core.networks import PotentialNet, GradientNet
        from sclsd.core.config import LogCoshActivation

        try:
            from torchdiffeq import odeint
        except ImportError:
            pytest.skip("torchdiffeq not installed")

        potential = PotentialNet(hidden_dims=[16], latent_dim=5, af=LogCoshActivation())
        gradnet = GradientNet(potential)

        z0 = torch.randn(8, 5)
        t = torch.linspace(0, 1, 10)

        # Should work with odeint
        z_traj = odeint(gradnet, z0, t)
        assert z_traj.shape == (10, 8, 5)

    def test_handles_non_requires_grad(self):
        """Test that GradientNet handles inputs without requires_grad."""
        from sclsd.core.networks import PotentialNet, GradientNet
        from sclsd.core.config import LogCoshActivation

        potential = PotentialNet(hidden_dims=[32], latent_dim=10, af=LogCoshActivation())
        gradnet = GradientNet(potential)

        z = torch.randn(16, 10)  # No requires_grad
        t = torch.tensor(0.0)
        grad = gradnet(t, z)

        assert grad.shape == z.shape
        assert not torch.isnan(grad).any()

    def test_no_nan_in_gradients(self):
        """Test that gradients don't contain NaN."""
        from sclsd.core.networks import PotentialNet, GradientNet
        from sclsd.core.config import LogCoshActivation

        potential = PotentialNet(hidden_dims=[32, 32], latent_dim=10, af=LogCoshActivation())
        gradnet = GradientNet(potential)

        # Test with various input ranges
        for scale in [0.1, 1.0, 10.0]:
            z = torch.randn(16, 10) * scale
            grad = gradnet(torch.tensor(0.0), z)
            assert not torch.isnan(grad).any(), f"NaN at scale {scale}"
            assert not torch.isinf(grad).any(), f"Inf at scale {scale}"


class TestNetworkIntegration:
    """Integration tests for network components working together."""

    def test_encoder_decoder_roundtrip(self):
        """Test that encoder-decoder produces valid outputs."""
        from sclsd.core.networks import XEncoder, ZDecoder

        n_genes = 100
        latent_dim = 10

        encoder = XEncoder(hidden_dims=[64, 32], latent_dim=latent_dim, num_genes=n_genes)
        decoder = ZDecoder(hidden_dims=[32, 64], num_genes=n_genes, latent_dim=latent_dim)

        x = torch.randn(16, n_genes)
        z_loc, z_scale = encoder(x)

        # Sample from latent
        z = z_loc + z_scale * torch.randn_like(z_scale)

        gate, mu = decoder(z)

        assert gate.shape == (16, n_genes)
        assert mu.shape == (16, n_genes)
        assert (mu.sum(dim=-1) - 1.0).abs().max() < 1e-5

    def test_full_chain(self):
        """Test full x -> z -> B -> z -> x chain."""
        from sclsd.core.networks import XEncoder, ZEncoder, StateDecoder, ZDecoder

        n_genes = 100
        latent_dim = 10
        state_dim = 2

        x_encoder = XEncoder(hidden_dims=[64], latent_dim=latent_dim, num_genes=n_genes)
        z_encoder = ZEncoder(hidden_dims=[32], latent_dim=latent_dim, state_dim=state_dim)
        state_decoder = StateDecoder(hidden_dims=[32], latent_dim=latent_dim, state_dim=state_dim)
        z_decoder = ZDecoder(hidden_dims=[64], num_genes=n_genes, latent_dim=latent_dim)

        x = torch.randn(16, n_genes)

        # Encode x -> z
        z_loc, z_scale = x_encoder(x)
        z = z_loc + z_scale * torch.randn_like(z_scale)

        # Encode z -> B
        B_loc, B_scale = z_encoder(z)
        B = B_loc + B_scale * torch.randn_like(B_scale)

        # Decode B -> z'
        z_prime_loc, z_prime_scale = state_decoder(B)

        # Decode z' -> x'
        gate, mu = z_decoder(z_prime_loc)

        assert B.shape == (16, state_dim)
        assert gate.shape == (16, n_genes)
        assert mu.shape == (16, n_genes)
