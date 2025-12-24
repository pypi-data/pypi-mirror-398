"""Unit tests for lsdpy.core.config module."""

import pytest
import torch
import torch.nn as nn


class TestLogCoshActivation:
    """Tests for LogCoshActivation module."""

    def test_forward_shape(self):
        """Test that output shape matches input shape."""
        from sclsd.core.config import LogCoshActivation

        act = LogCoshActivation()
        x = torch.randn(32, 10)
        y = act(x)
        assert y.shape == x.shape

    def test_forward_values(self):
        """Test that log-cosh is computed correctly."""
        from sclsd.core.config import LogCoshActivation

        act = LogCoshActivation()
        x = torch.tensor([0.0, 1.0, -1.0, 2.0])
        y = act(x)

        # log(cosh(0)) = 0
        assert torch.isclose(y[0], torch.tensor(0.0), atol=1e-6)

        # log(cosh(x)) = log(cosh(-x)) for symmetry
        assert torch.isclose(y[1], y[2], atol=1e-6)

        # All outputs should be non-negative (log(cosh(x)) >= 0)
        assert (y >= 0).all()

    def test_gradient_flow(self):
        """Test that gradients flow through activation."""
        from sclsd.core.config import LogCoshActivation

        act = LogCoshActivation()
        x = torch.randn(32, 10, requires_grad=True)
        y = act(x)
        loss = y.sum()
        loss.backward()

        assert x.grad is not None
        assert not torch.isnan(x.grad).any()
        assert not torch.isinf(x.grad).any()

    def test_batch_independence(self):
        """Test that activation is applied independently per element."""
        from sclsd.core.config import LogCoshActivation

        act = LogCoshActivation()
        x1 = torch.randn(16, 10)
        x2 = torch.randn(16, 10)

        # Process separately
        y1 = act(x1)
        y2 = act(x2)

        # Process concatenated
        combined = torch.cat([x1, x2], dim=0)
        y_combined = act(combined)

        assert torch.allclose(y1, y_combined[:16])
        assert torch.allclose(y2, y_combined[16:])


class TestResolveActivation:
    """Tests for resolve_activation function."""

    def test_module_passthrough(self):
        """Test that nn.Module instance is returned as-is."""
        from sclsd.core.config import resolve_activation

        relu = nn.ReLU()
        result = resolve_activation(relu)
        assert result is relu

    def test_none_returns_identity(self):
        """Test that None returns nn.Identity."""
        from sclsd.core.config import resolve_activation

        result = resolve_activation(None)
        assert isinstance(result, nn.Identity)

    def test_class_instantiation(self):
        """Test that class type is instantiated."""
        from sclsd.core.config import resolve_activation

        result = resolve_activation(nn.Tanh)
        assert isinstance(result, nn.Tanh)

    def test_string_logcosh(self):
        """Test 'logcosh' string."""
        from sclsd.core.config import resolve_activation, LogCoshActivation

        result = resolve_activation("logcosh")
        assert isinstance(result, LogCoshActivation)

    def test_string_relu(self):
        """Test 'relu' string."""
        from sclsd.core.config import resolve_activation

        result = resolve_activation("relu")
        assert isinstance(result, nn.ReLU)

    def test_string_softplus(self):
        """Test 'softplus' and 'sp' strings."""
        from sclsd.core.config import resolve_activation

        result1 = resolve_activation("softplus")
        result2 = resolve_activation("sp")
        assert isinstance(result1, nn.Softplus)
        assert isinstance(result2, nn.Softplus)

    def test_string_identity(self):
        """Test 'identity' and 'id' strings."""
        from sclsd.core.config import resolve_activation

        result1 = resolve_activation("identity")
        result2 = resolve_activation("id")
        assert isinstance(result1, nn.Identity)
        assert isinstance(result2, nn.Identity)

    def test_string_case_insensitive(self):
        """Test that string matching is case-insensitive."""
        from sclsd.core.config import resolve_activation

        result1 = resolve_activation("RELU")
        result2 = resolve_activation("ReLU")
        result3 = resolve_activation("relu")
        assert all(isinstance(r, nn.ReLU) for r in [result1, result2, result3])

    def test_unknown_string_raises(self):
        """Test that unknown string raises ValueError."""
        from sclsd.core.config import resolve_activation

        with pytest.raises(ValueError, match="Unknown activation keyword"):
            resolve_activation("unknown_activation")

    def test_unsupported_type_raises(self):
        """Test that unsupported types raise TypeError."""
        from sclsd.core.config import resolve_activation

        with pytest.raises(TypeError, match="Unsupported activation spec"):
            resolve_activation(42)

        with pytest.raises(TypeError, match="Unsupported activation spec"):
            resolve_activation([nn.ReLU])


class TestLayerDims:
    """Tests for LayerDims dataclass."""

    def test_default_values(self):
        """Test default layer dimensions."""
        from sclsd.core.config import LayerDims

        dims = LayerDims()
        assert dims.B_decoder == [32, 64]
        assert dims.z_decoder == [128, 256]
        assert dims.x_encoder == [512, 256]
        assert dims.z_encoder == [64, 32]
        assert dims.xl_encoder == [64, 32]
        assert dims.potential == [32, 32]
        assert dims.potential_af == "logcosh"

    def test_custom_values(self):
        """Test custom layer dimensions."""
        from sclsd.core.config import LayerDims

        dims = LayerDims(
            B_decoder=[16, 32],
            z_decoder=[64, 128],
            potential=[16],
            potential_af="relu",
        )
        assert dims.B_decoder == [16, 32]
        assert dims.z_decoder == [64, 128]
        assert dims.potential == [16]
        assert dims.potential_af == "relu"

    def test_as_dict_keys(self):
        """Test that as_dict returns all expected keys."""
        from sclsd.core.config import LayerDims

        dims = LayerDims()
        d = dims.as_dict()

        expected_keys = {
            "B_decoder", "z_decoder", "x_encoder",
            "z_encoder", "xl_encoder", "potential", "potential_af"
        }
        assert set(d.keys()) == expected_keys

    def test_as_dict_returns_lists(self):
        """Test that dimension values are lists."""
        from sclsd.core.config import LayerDims

        dims = LayerDims()
        d = dims.as_dict()

        for key in ["B_decoder", "z_decoder", "x_encoder", "z_encoder", "xl_encoder", "potential"]:
            assert isinstance(d[key], list)

    def test_as_dict_resolves_activation(self):
        """Test that potential_af is resolved to nn.Module."""
        from sclsd.core.config import LayerDims, LogCoshActivation

        dims = LayerDims()
        d = dims.as_dict()

        assert isinstance(d["potential_af"], nn.Module)
        assert isinstance(d["potential_af"], LogCoshActivation)

    def test_as_dict_with_different_activations(self):
        """Test as_dict with different activation specs."""
        from sclsd.core.config import LayerDims

        dims_relu = LayerDims(potential_af="relu")
        d_relu = dims_relu.as_dict()
        assert isinstance(d_relu["potential_af"], nn.ReLU)

        dims_module = LayerDims(potential_af=nn.Tanh())
        d_module = dims_module.as_dict()
        assert isinstance(d_module["potential_af"], nn.Tanh)


class TestAdamConfig:
    """Tests for AdamConfig dataclass."""

    def test_default_values(self):
        """Test default optimizer values."""
        from sclsd.core.config import AdamConfig

        cfg = AdamConfig()
        assert cfg.lr == 1e-3
        assert cfg.eta_min == 1e-5
        assert cfg.T_0 == 40
        assert cfg.T_mult == 1

    def test_custom_values(self):
        """Test custom optimizer values."""
        from sclsd.core.config import AdamConfig

        cfg = AdamConfig(lr=2e-3, T_0=50)
        assert cfg.lr == 2e-3
        assert cfg.T_0 == 50

    def test_as_dict(self):
        """Test conversion to dictionary."""
        from sclsd.core.config import AdamConfig

        cfg = AdamConfig(lr=5e-4, eta_min=1e-6, T_0=100, T_mult=2)
        d = cfg.as_dict()

        assert d["lr"] == 5e-4
        assert d["eta_min"] == 1e-6
        assert d["T_0"] == 100
        assert d["T_mult"] == 2


class TestKLScheduleConfig:
    """Tests for KLScheduleConfig dataclass."""

    def test_default_values(self):
        """Test default KL schedule values."""
        from sclsd.core.config import KLScheduleConfig

        cfg = KLScheduleConfig()
        assert cfg.af == 1.0

    def test_custom_af(self):
        """Test custom annealing factor."""
        from sclsd.core.config import KLScheduleConfig

        cfg = KLScheduleConfig(af=3.0)
        assert cfg.af == 3.0

    def test_as_dict(self):
        """Test conversion to dictionary with schedule parameters."""
        from sclsd.core.config import KLScheduleConfig

        cfg = KLScheduleConfig(af=2.0)
        d = cfg.as_dict()

        assert d["min_af"] == 2.0
        assert d["max_af"] == 2.0
        assert d["max_epoch"] == 100


class TestWassersteinScheduleConfig:
    """Tests for WassersteinScheduleConfig dataclass."""

    def test_default_values(self):
        """Test default Wasserstein schedule values."""
        from sclsd.core.config import WassersteinScheduleConfig

        cfg = WassersteinScheduleConfig()
        assert cfg.min_W == 1e-4
        assert cfg.max_W == 1e-3
        assert cfg.max_epoch == 50

    def test_custom_values(self):
        """Test custom Wasserstein schedule values."""
        from sclsd.core.config import WassersteinScheduleConfig

        cfg = WassersteinScheduleConfig(min_W=1e-5, max_W=1e-2, max_epoch=100)
        assert cfg.min_W == 1e-5
        assert cfg.max_W == 1e-2
        assert cfg.max_epoch == 100

    def test_as_dict(self):
        """Test conversion to dictionary."""
        from sclsd.core.config import WassersteinScheduleConfig

        cfg = WassersteinScheduleConfig(min_W=0.001, max_W=0.01, max_epoch=75)
        d = cfg.as_dict()

        assert d["min_W"] == 0.001
        assert d["max_W"] == 0.01
        assert d["max_epoch"] == 75


class TestOptimizerConfig:
    """Tests for OptimizerConfig dataclass."""

    def test_default_nested_configs(self):
        """Test that nested configs have defaults."""
        from sclsd.core.config import OptimizerConfig, AdamConfig, KLScheduleConfig

        cfg = OptimizerConfig()
        assert isinstance(cfg.adam, AdamConfig)
        assert isinstance(cfg.kl_schedule, KLScheduleConfig)
        assert cfg.adam.lr == 1e-3
        assert cfg.kl_schedule.af == 1.0

    def test_nested_modification(self):
        """Test modifying nested config values."""
        from sclsd.core.config import OptimizerConfig

        cfg = OptimizerConfig()
        cfg.adam.lr = 5e-4
        cfg.kl_schedule.af = 3.0

        assert cfg.adam.lr == 5e-4
        assert cfg.kl_schedule.af == 3.0


class TestWalkConfig:
    """Tests for WalkConfig dataclass."""

    def test_default_values(self):
        """Test default walk configuration."""
        from sclsd.core.config import WalkConfig

        cfg = WalkConfig()
        assert cfg.batch_size == 256
        assert cfg.path_len == 10
        assert cfg.num_walks == 4096
        assert cfg.random_state == 42

    def test_custom_values(self):
        """Test custom walk configuration."""
        from sclsd.core.config import WalkConfig

        cfg = WalkConfig(batch_size=128, path_len=50, num_walks=10000, random_state=123)
        assert cfg.batch_size == 128
        assert cfg.path_len == 50
        assert cfg.num_walks == 10000
        assert cfg.random_state == 123


class TestModelConfig:
    """Tests for ModelConfig dataclass."""

    def test_default_values(self):
        """Test default model configuration."""
        from sclsd.core.config import ModelConfig

        cfg = ModelConfig()
        assert cfg.z_dim == 10
        assert cfg.B_dim == 2
        assert cfg.V_coeff == 0.01

    def test_nested_layer_dims(self):
        """Test that layer_dims is accessible."""
        from sclsd.core.config import ModelConfig, LayerDims

        cfg = ModelConfig()
        assert isinstance(cfg.layer_dims, LayerDims)
        assert cfg.layer_dims.B_decoder == [32, 64]

    def test_modification(self):
        """Test modifying model config values."""
        from sclsd.core.config import ModelConfig

        cfg = ModelConfig()
        cfg.z_dim = 20
        cfg.B_dim = 3
        cfg.V_coeff = 5e-3
        cfg.layer_dims.potential = [64, 64]

        assert cfg.z_dim == 20
        assert cfg.B_dim == 3
        assert cfg.V_coeff == 5e-3
        assert cfg.layer_dims.potential == [64, 64]


class TestLSDConfig:
    """Tests for the main LSDConfig dataclass."""

    def test_default_values(self):
        """Test that default config can be created."""
        from sclsd.core.config import LSDConfig

        cfg = LSDConfig()
        assert cfg.model.z_dim == 10
        assert cfg.model.B_dim == 2
        assert cfg.walks.path_len == 10
        assert cfg.walks.num_walks == 4096
        assert cfg.optimizer.adam.lr == 1e-3

    def test_nested_modification(self):
        """Test that nested values can be modified."""
        from sclsd.core.config import LSDConfig

        cfg = LSDConfig()
        cfg.model.z_dim = 20
        cfg.walks.path_len = 100
        cfg.optimizer.adam.lr = 2e-3

        assert cfg.model.z_dim == 20
        assert cfg.walks.path_len == 100
        assert cfg.optimizer.adam.lr == 2e-3

    def test_deep_nested_modification(self):
        """Test deeply nested modifications."""
        from sclsd.core.config import LSDConfig

        cfg = LSDConfig()
        cfg.model.layer_dims.x_encoder = [256, 128]
        cfg.model.layer_dims.potential_af = "relu"
        cfg.optimizer.kl_schedule.af = 5.0

        assert cfg.model.layer_dims.x_encoder == [256, 128]
        assert cfg.model.layer_dims.potential_af == "relu"
        assert cfg.optimizer.kl_schedule.af == 5.0


class TestDefaultConfig:
    """Tests for default_config function."""

    def test_returns_lsd_config(self):
        """Test that default_config returns LSDConfig."""
        from sclsd.core.config import default_config, LSDConfig

        cfg = default_config()
        assert isinstance(cfg, LSDConfig)

    def test_same_as_constructor(self):
        """Test that default_config matches LSDConfig()."""
        from sclsd.core.config import default_config, LSDConfig

        cfg1 = default_config()
        cfg2 = LSDConfig()

        assert cfg1.model.z_dim == cfg2.model.z_dim
        assert cfg1.walks.path_len == cfg2.walks.path_len
        assert cfg1.optimizer.adam.lr == cfg2.optimizer.adam.lr
