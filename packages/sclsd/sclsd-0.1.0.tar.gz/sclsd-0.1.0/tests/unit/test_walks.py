"""Unit tests for lsdpy.train.walks module."""

import pytest
import numpy as np
import scipy.sparse as sp
import torch


class TestPrepareTransitionMatrixGPU:
    """Tests for prepare_transition_matrix_gpu function."""

    def test_dense_output(self):
        """Test that output is a dense tensor."""
        from sclsd.train.walks import prepare_transition_matrix_gpu

        n = 50
        connectivity = sp.random(n, n, density=0.2, format="csr")
        connectivity = connectivity + connectivity.T  # Symmetrize
        connectivity.setdiag(1)  # Self-loops

        device = torch.device("cpu")
        T = prepare_transition_matrix_gpu(connectivity, device)

        assert isinstance(T, torch.Tensor)
        assert T.shape == (n, n)

    def test_row_normalized(self):
        """Test that output is row-normalized (stochastic)."""
        from sclsd.train.walks import prepare_transition_matrix_gpu

        n = 50
        connectivity = sp.random(n, n, density=0.2, format="csr")
        connectivity = connectivity + connectivity.T
        connectivity.setdiag(1)

        device = torch.device("cpu")
        T = prepare_transition_matrix_gpu(connectivity, device)

        row_sums = T.sum(dim=1).numpy()
        np.testing.assert_allclose(row_sums, np.ones(n), rtol=1e-5)

    def test_non_negative(self):
        """Test that all values are non-negative."""
        from sclsd.train.walks import prepare_transition_matrix_gpu

        n = 50
        connectivity = sp.random(n, n, density=0.2, format="csr")
        connectivity = connectivity + connectivity.T
        connectivity.setdiag(1)

        device = torch.device("cpu")
        T = prepare_transition_matrix_gpu(connectivity, device)

        assert (T >= 0).all()


class TestRandomWalksGPU:
    """Tests for random_walks_gpu function."""

    def test_output_shape(self):
        """Test that output has correct shape."""
        from sclsd.train.walks import random_walks_gpu

        n_cells = 100
        n_steps = 10
        n_trajectories = 50

        # Create random transition matrix
        T = torch.rand(n_cells, n_cells)
        T = T / T.sum(dim=1, keepdim=True)

        device = torch.device("cpu")
        walks = random_walks_gpu(T, n_steps, n_trajectories, device)

        assert walks.shape == (n_trajectories, n_steps)

    def test_valid_indices(self):
        """Test that walk indices are valid cell indices."""
        from sclsd.train.walks import random_walks_gpu

        n_cells = 100
        n_steps = 10
        n_trajectories = 50

        T = torch.rand(n_cells, n_cells)
        T = T / T.sum(dim=1, keepdim=True)

        device = torch.device("cpu")
        walks = random_walks_gpu(T, n_steps, n_trajectories, device)

        assert walks.min() >= 0
        assert walks.max() < n_cells

    def test_deterministic_with_seed(self):
        """Test that walks are deterministic with same seed."""
        from sclsd.train.walks import random_walks_gpu
        from sclsd import set_all_seeds

        n_cells = 100
        n_steps = 10
        n_trajectories = 50

        T = torch.rand(n_cells, n_cells)
        T = T / T.sum(dim=1, keepdim=True)

        device = torch.device("cpu")

        # First run
        set_all_seeds(42)
        walks1 = random_walks_gpu(T, n_steps, n_trajectories, device)

        # Second run
        set_all_seeds(42)
        walks2 = random_walks_gpu(T, n_steps, n_trajectories, device)

        assert torch.equal(walks1, walks2)


class TestPrepareWalks:
    """Tests for prepare_walks function."""

    def test_returns_cpu(self):
        """Test that output is on CPU."""
        from sclsd.train.walks import prepare_walks

        n_cells = 100
        T = torch.rand(n_cells, n_cells)
        T = T / T.sum(dim=1, keepdim=True)

        device = torch.device("cpu")
        walks = prepare_walks(T, n_trajectories=50, path_len=10, device=device)

        assert walks.device == torch.device("cpu")

    def test_correct_shape(self):
        """Test that output has correct shape."""
        from sclsd.train.walks import prepare_walks

        n_cells = 100
        n_trajectories = 50
        path_len = 10

        T = torch.rand(n_cells, n_cells)
        T = T / T.sum(dim=1, keepdim=True)

        device = torch.device("cpu")
        walks = prepare_walks(T, n_trajectories, path_len, device)

        assert walks.shape == (n_trajectories, path_len)


class TestPrepareSimpleWalks:
    """Tests for prepare_simple_walks function (legacy CPU version)."""

    def test_output_shape(self):
        """Test that output has correct shape."""
        from sclsd.train.walks import prepare_simple_walks

        n_cells = 100
        n_steps = 10
        n_trajectories = 50

        connectivity = sp.random(n_cells, n_cells, density=0.2, format="csr")
        connectivity = connectivity + connectivity.T
        connectivity.setdiag(1)

        np.random.seed(42)
        walks = prepare_simple_walks(n_steps, n_trajectories, connectivity)

        assert walks.shape == (n_trajectories, n_steps)

    def test_valid_indices(self):
        """Test that walk indices are valid."""
        from sclsd.train.walks import prepare_simple_walks

        n_cells = 100
        n_steps = 10
        n_trajectories = 20

        connectivity = sp.random(n_cells, n_cells, density=0.2, format="csr")
        connectivity = connectivity + connectivity.T
        connectivity.setdiag(1)

        np.random.seed(42)
        walks = prepare_simple_walks(n_steps, n_trajectories, connectivity)

        assert walks.min() >= 0
        assert walks.max() < n_cells

    def test_returns_tensor(self):
        """Test that output is a torch tensor."""
        from sclsd.train.walks import prepare_simple_walks

        n_cells = 50
        connectivity = sp.random(n_cells, n_cells, density=0.3, format="csr")
        connectivity = connectivity + connectivity.T
        connectivity.setdiag(1)

        np.random.seed(42)
        walks = prepare_simple_walks(5, 10, connectivity)

        assert isinstance(walks, torch.Tensor)


class TestWalkIntegration:
    """Integration tests for walk generation pipeline."""

    def test_gpu_cpu_equivalence(self):
        """Test that GPU and CPU walks follow same probability distribution.

        Note: We can't test exact equality since walks are stochastic,
        but we can test that they produce valid walks with similar properties.
        """
        from sclsd.train.walks import (
            prepare_transition_matrix_gpu,
            random_walks_gpu,
            prepare_simple_walks,
        )
        from sclsd import set_all_seeds

        n_cells = 100
        n_steps = 10
        n_trajectories = 1000  # Many walks to test distribution

        connectivity = sp.random(n_cells, n_cells, density=0.3, format="csr")
        connectivity = connectivity + connectivity.T
        connectivity.setdiag(1)

        device = torch.device("cpu")

        # GPU walks
        set_all_seeds(42)
        T_gpu = prepare_transition_matrix_gpu(connectivity, device)
        walks_gpu = random_walks_gpu(T_gpu, n_steps, n_trajectories, device)

        # CPU walks
        set_all_seeds(42)
        walks_cpu = prepare_simple_walks(n_steps, n_trajectories, connectivity)

        # Both should produce valid walks
        assert walks_gpu.min() >= 0 and walks_gpu.max() < n_cells
        assert walks_cpu.min() >= 0 and walks_cpu.max() < n_cells

        # Both should visit cells across the graph
        unique_gpu = len(torch.unique(walks_gpu))
        unique_cpu = len(torch.unique(walks_cpu))
        assert unique_gpu > n_cells * 0.5  # Should visit many cells
        assert unique_cpu > n_cells * 0.5
