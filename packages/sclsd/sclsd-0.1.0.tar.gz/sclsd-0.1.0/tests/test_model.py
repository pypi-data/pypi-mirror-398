"""Tests for LSD model components."""

import pytest
import numpy as np
import torch

pytest.importorskip("pyro")


class TestLSDModel:
    """Tests for the LSDModel neural network."""

    def test_model_forward_shapes(self, small_adata, lsd_config, device, random_seed):
        """Test that model forward pass produces correct shapes."""
        from sclsd import LSDModel, set_all_seeds

        set_all_seeds(random_seed)

        n_genes = small_adata.n_vars
        batch_size = 32
        path_len = lsd_config.walks.path_len

        model = LSDModel(
            B_dim=lsd_config.model.B_dim,
            z_dim=lsd_config.model.z_dim,
            num_genes=n_genes,
            layer_dims=lsd_config.model.layer_dims.as_dict(),
            batch_size=batch_size,
            path_len=path_len,
            device=device,
        ).to(device)

        # Test encoder shapes
        x = torch.randn(batch_size * path_len, n_genes).to(device)
        z_loc, z_scale = model.x_encoder(x)

        assert z_loc.shape == (batch_size * path_len, lsd_config.model.z_dim)
        assert z_scale.shape == (batch_size * path_len, lsd_config.model.z_dim)

        # Test z_encoder shapes
        B_loc, B_scale = model.z_encoder(z_loc)
        assert B_loc.shape == (batch_size * path_len, lsd_config.model.B_dim)
        assert B_scale.shape == (batch_size * path_len, lsd_config.model.B_dim)

        # Test potential shape
        V = model.potential(z_loc)
        assert V.shape == (batch_size * path_len, 1)

    def test_potential_gradient(self, small_adata, lsd_config, device, random_seed):
        """Test that potential gradient can be computed."""
        from sclsd import LSDModel, set_all_seeds

        set_all_seeds(random_seed)

        n_genes = small_adata.n_vars

        model = LSDModel(
            B_dim=lsd_config.model.B_dim,
            z_dim=lsd_config.model.z_dim,
            num_genes=n_genes,
            layer_dims=lsd_config.model.layer_dims.as_dict(),
            batch_size=32,
            path_len=4,
            device=device,
        ).to(device)

        # Test gradient computation
        z = torch.randn(10, lsd_config.model.z_dim, requires_grad=True).to(device)
        grad = model.gradnet(0, z)

        assert grad.shape == z.shape
        assert not torch.isnan(grad).any()


class TestNetworks:
    """Tests for individual network components."""

    def test_x_encoder(self, random_seed):
        """Test XEncoder network."""
        from sclsd.core.networks import XEncoder
        from sclsd import set_all_seeds

        set_all_seeds(random_seed)

        encoder = XEncoder(
            hidden_dims=[64, 32],
            latent_dim=10,
            num_genes=100,
        )

        x = torch.randn(32, 100)
        z_loc, z_scale = encoder(x)

        assert z_loc.shape == (32, 10)
        assert z_scale.shape == (32, 10)
        assert (z_scale > 0).all(), "Scale must be positive"

    def test_z_decoder(self, random_seed):
        """Test ZDecoder network."""
        from sclsd.core.networks import ZDecoder
        from sclsd import set_all_seeds

        set_all_seeds(random_seed)

        decoder = ZDecoder(
            hidden_dims=[32, 64],
            num_genes=100,
            latent_dim=10,
        )

        z = torch.randn(32, 10)
        gate_logits, mu = decoder(z)

        assert gate_logits.shape == (32, 100)
        assert mu.shape == (32, 100)
        assert (mu > 0).all(), "Rate must be positive"

    def test_potential_net(self, random_seed):
        """Test PotentialNet network."""
        from sclsd.core.networks import PotentialNet
        from sclsd.core.config import LogCoshActivation
        from sclsd import set_all_seeds

        set_all_seeds(random_seed)

        potential = PotentialNet(
            hidden_dims=[16, 8],
            latent_dim=10,
            af=LogCoshActivation(),
        )

        z = torch.randn(32, 10)
        V = potential(z)

        assert V.shape == (32, 1)
        assert not torch.isnan(V).any()


class TestConfig:
    """Tests for configuration classes."""

    def test_default_config(self):
        """Test that default config can be created."""
        from sclsd import LSDConfig

        cfg = LSDConfig()

        assert cfg.model.z_dim == 10
        assert cfg.model.B_dim == 2
        assert cfg.walks.path_len == 10
        assert cfg.walks.num_walks == 4096

    def test_config_modification(self):
        """Test that config can be modified."""
        from sclsd import LSDConfig

        cfg = LSDConfig()
        cfg.model.z_dim = 20
        cfg.walks.path_len = 100

        assert cfg.model.z_dim == 20
        assert cfg.walks.path_len == 100

    def test_layer_dims_as_dict(self):
        """Test LayerDims.as_dict() method."""
        from sclsd import LayerDims
        import torch.nn as nn

        dims = LayerDims()
        d = dims.as_dict()

        assert "B_decoder" in d
        assert "z_decoder" in d
        assert "x_encoder" in d
        assert "potential" in d
        assert "potential_af" in d
        assert isinstance(d["potential_af"], nn.Module)
