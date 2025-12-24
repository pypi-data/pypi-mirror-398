"""Parity tests comparing lsdpy results against LSD-main-branch baselines.

These tests ensure that lsdpy produces IDENTICAL results to the original
LSD-main-branch implementation when using the same random seeds and
configuration.

To run these tests:
1. First generate baselines using: python scripts/generate_baselines.py --dataset <name> --data-dir <path>
2. Then run: pytest tests/reproducibility/test_parity_all_datasets.py -v -m parity

Requirements:
- Reference baselines must exist in tests/fixtures/reference_data/<dataset>/
- Data files must be available for running lsdpy
"""

import json
import os
from pathlib import Path

import numpy as np
import pytest
import scipy.sparse as sp

# Mark all tests in this module with the parity marker
pytestmark = pytest.mark.parity

# Tolerance for numerical comparison
RTOL = 1e-5  # Relative tolerance
ATOL = 1e-8  # Absolute tolerance
CBDIR_ATOL = 0.01  # CBDir score tolerance

# Dataset configurations
DATASETS = ["pancreas", "bonemarrow", "erythroid", "dentategyrus", "zebrafish"]


def get_reference_data_path():
    """Get path to reference data directory."""
    return Path(__file__).parent.parent / "fixtures" / "reference_data"


def load_reference_baselines(dataset):
    """Load reference baseline data for a dataset.

    Parameters
    ----------
    dataset : str
        Dataset name (pancreas, bonemarrow, etc.)

    Returns
    -------
    dict
        Dictionary containing reference data arrays and config
    """
    ref_path = get_reference_data_path() / dataset

    if not ref_path.exists():
        pytest.skip(f"Reference baselines not found for {dataset}. "
                   f"Run generate_baselines.py first.")

    baselines = {}

    # Load config
    config_file = ref_path / "config.json"
    if config_file.exists():
        with open(config_file) as f:
            baselines["config"] = json.load(f)

    # Load pseudotime
    pt_file = ref_path / "pseudotime.npy"
    if pt_file.exists():
        baselines["pseudotime"] = np.load(pt_file)

    # Load potential
    pot_file = ref_path / "potential.npy"
    if pot_file.exists():
        baselines["potential"] = np.load(pot_file)

    # Load entropy
    ent_file = ref_path / "entropy.npy"
    if ent_file.exists():
        baselines["entropy"] = np.load(ent_file)

    # Load cell representation (z_loc)
    cell_rep_file = ref_path / "cell_rep.npy"
    if cell_rep_file.exists():
        baselines["cell_rep"] = np.load(cell_rep_file)

    # Load differentiation representation (B_loc)
    diff_rep_file = ref_path / "diff_rep.npy"
    if diff_rep_file.exists():
        baselines["diff_rep"] = np.load(diff_rep_file)

    # Load transitions
    trans_file = ref_path / "transitions.npz"
    if trans_file.exists():
        baselines["transitions"] = sp.load_npz(trans_file)

    # Load CBDir scores
    cbdir_file = ref_path / "cbdir_scores.json"
    if cbdir_file.exists():
        with open(cbdir_file) as f:
            baselines["cbdir_scores"] = json.load(f)

    return baselines


@pytest.fixture(scope="module")
def reference_baselines():
    """Fixture to load all reference baselines."""
    return {dataset: load_reference_baselines(dataset) for dataset in DATASETS}


@pytest.fixture
def lsdpy_results(request):
    """Fixture to run lsdpy and get results for comparison.

    This fixture runs lsdpy training with the same configuration as the
    reference baselines and returns the results.
    """
    # This would need to be implemented to actually run lsdpy
    # For now, we'll skip if results aren't available
    pytest.skip("lsdpy results fixture not implemented - run notebooks first")


class TestDatasetParity:
    """Test class for dataset parity checking."""

    @pytest.mark.parametrize("dataset", DATASETS)
    def test_baseline_files_exist(self, dataset):
        """Test that baseline files exist for each dataset."""
        ref_path = get_reference_data_path() / dataset

        if not ref_path.exists():
            pytest.skip(f"Reference directory not found: {ref_path}")

        expected_files = [
            "config.json",
            "pseudotime.npy",
            "potential.npy",
            "entropy.npy",
            "cell_rep.npy",
            "diff_rep.npy",
            "transitions.npz",
        ]

        missing = [f for f in expected_files if not (ref_path / f).exists()]
        if missing:
            pytest.fail(f"Missing baseline files for {dataset}: {missing}")

    @pytest.mark.parametrize("dataset", DATASETS)
    def test_baseline_data_shapes(self, dataset):
        """Test that baseline data has consistent shapes."""
        baselines = load_reference_baselines(dataset)

        if "config" not in baselines:
            pytest.skip(f"No config found for {dataset}")

        n_cells = baselines["config"]["n_cells"]

        # Check array shapes
        if "pseudotime" in baselines:
            assert baselines["pseudotime"].shape == (n_cells,), \
                f"Pseudotime shape mismatch for {dataset}"

        if "potential" in baselines:
            assert baselines["potential"].shape == (n_cells,), \
                f"Potential shape mismatch for {dataset}"

        if "entropy" in baselines:
            assert baselines["entropy"].shape == (n_cells,), \
                f"Entropy shape mismatch for {dataset}"

        if "transitions" in baselines:
            assert baselines["transitions"].shape == (n_cells, n_cells), \
                f"Transitions shape mismatch for {dataset}"


class TestPancreasParity:
    """Specific parity tests for Pancreas dataset."""

    @pytest.fixture
    def pancreas_baselines(self):
        """Load Pancreas baselines."""
        return load_reference_baselines("pancreas")

    def test_pancreas_expected_cbdir(self, pancreas_baselines):
        """Test that Pancreas CBDir matches expected values from paper."""
        if "cbdir_scores" not in pancreas_baselines:
            pytest.skip("CBDir scores not available")

        expected_scores = {
            "('Prlf. Ductal', 'Ductal')": 0.172,
            "('Ductal', 'Ngn3 low')": 0.381,
            "('Ngn3 low', 'Ngn3 high')": 0.305,
            "('Ngn3 high', 'Fev+')": 0.398,
            "('Ngn3 high', 'Epsilon')": 0.715,
            "('Fev+', 'Fev+ Alpha')": 0.603,
            "('Fev+', 'Fev+ Beta')": 0.463,
            "('Fev+ Alpha', 'Alpha')": 0.617,
            "('Fev+ Beta', 'Beta')": 0.583,
            "('Fev+ Delta', 'Delta')": 0.633,
        }

        actual_scores = pancreas_baselines["cbdir_scores"]

        for edge, expected in expected_scores.items():
            if edge in actual_scores:
                actual = actual_scores[edge]
                assert abs(actual - expected) < 0.1, \
                    f"CBDir mismatch for {edge}: expected {expected}, got {actual}"

    def test_pancreas_mean_cbdir(self, pancreas_baselines):
        """Test that mean CBDir is approximately 0.487."""
        if "cbdir_scores" not in pancreas_baselines:
            pytest.skip("CBDir scores not available")

        if "mean" in pancreas_baselines["cbdir_scores"]:
            mean_cbdir = pancreas_baselines["cbdir_scores"]["mean"]
            assert abs(mean_cbdir - 0.487) < 0.05, \
                f"Mean CBDir should be ~0.487, got {mean_cbdir}"

    def test_pancreas_pseudotime_range(self, pancreas_baselines):
        """Test that pseudotime is in [0, 1] range."""
        if "pseudotime" not in pancreas_baselines:
            pytest.skip("Pseudotime not available")

        pt = pancreas_baselines["pseudotime"]
        assert np.all(pt >= 0) and np.all(pt <= 1), \
            "Pseudotime should be in [0, 1] range"

    def test_pancreas_transitions_row_sum(self, pancreas_baselines):
        """Test that transition matrix rows sum to 1."""
        if "transitions" not in pancreas_baselines:
            pytest.skip("Transitions not available")

        T = pancreas_baselines["transitions"]
        if sp.issparse(T):
            row_sums = np.array(T.sum(axis=1)).flatten()
        else:
            row_sums = T.sum(axis=1)

        np.testing.assert_allclose(row_sums, 1.0, rtol=1e-5,
            err_msg="Transition matrix rows should sum to 1")


def compare_arrays(actual, expected, name, rtol=RTOL, atol=ATOL):
    """Compare two arrays with detailed error reporting.

    Parameters
    ----------
    actual : np.ndarray
        Actual array from sclsd
    expected : np.ndarray
        Expected array from reference baselines
    name : str
        Name of the array being compared (for error messages)
    rtol : float
        Relative tolerance
    atol : float
        Absolute tolerance
    """
    assert actual.shape == expected.shape, \
        f"{name} shape mismatch: {actual.shape} vs {expected.shape}"

    try:
        np.testing.assert_allclose(actual, expected, rtol=rtol, atol=atol)
    except AssertionError as e:
        # Compute detailed error statistics
        diff = np.abs(actual - expected)
        max_diff = np.max(diff)
        mean_diff = np.mean(diff)
        max_idx = np.unravel_index(np.argmax(diff), diff.shape)

        raise AssertionError(
            f"{name} mismatch:\n"
            f"  Max difference: {max_diff} at index {max_idx}\n"
            f"  Mean difference: {mean_diff}\n"
            f"  Original error: {e}"
        )


class TestParityComparison:
    """Test class for comparing lsdpy results against baselines.

    These tests require both baseline files and lsdpy results to be available.
    """

    @pytest.mark.parametrize("dataset", DATASETS)
    def test_pseudotime_identical(self, dataset, reference_baselines, lsdpy_results):
        """Test that lsd_pseudotime matches original (rtol=1e-5)."""
        if dataset not in reference_baselines or "pseudotime" not in reference_baselines[dataset]:
            pytest.skip(f"No pseudotime baseline for {dataset}")

        if dataset not in lsdpy_results or "pseudotime" not in lsdpy_results[dataset]:
            pytest.skip(f"No lsdpy pseudotime for {dataset}")

        compare_arrays(
            lsdpy_results[dataset]["pseudotime"],
            reference_baselines[dataset]["pseudotime"],
            f"{dataset} pseudotime"
        )

    @pytest.mark.parametrize("dataset", DATASETS)
    def test_potential_identical(self, dataset, reference_baselines, lsdpy_results):
        """Test that potential values match original."""
        if dataset not in reference_baselines or "potential" not in reference_baselines[dataset]:
            pytest.skip(f"No potential baseline for {dataset}")

        if dataset not in lsdpy_results or "potential" not in lsdpy_results[dataset]:
            pytest.skip(f"No lsdpy potential for {dataset}")

        compare_arrays(
            lsdpy_results[dataset]["potential"],
            reference_baselines[dataset]["potential"],
            f"{dataset} potential"
        )

    @pytest.mark.parametrize("dataset", DATASETS)
    def test_cell_rep_identical(self, dataset, reference_baselines, lsdpy_results):
        """Test that latent representations (z_loc) match original."""
        if dataset not in reference_baselines or "cell_rep" not in reference_baselines[dataset]:
            pytest.skip(f"No cell_rep baseline for {dataset}")

        if dataset not in lsdpy_results or "cell_rep" not in lsdpy_results[dataset]:
            pytest.skip(f"No lsdpy cell_rep for {dataset}")

        compare_arrays(
            lsdpy_results[dataset]["cell_rep"],
            reference_baselines[dataset]["cell_rep"],
            f"{dataset} cell_rep (z_loc)"
        )

    @pytest.mark.parametrize("dataset", DATASETS)
    def test_diff_rep_identical(self, dataset, reference_baselines, lsdpy_results):
        """Test that differentiation representations (B_loc) match original."""
        if dataset not in reference_baselines or "diff_rep" not in reference_baselines[dataset]:
            pytest.skip(f"No diff_rep baseline for {dataset}")

        if dataset not in lsdpy_results or "diff_rep" not in lsdpy_results[dataset]:
            pytest.skip(f"No lsdpy diff_rep for {dataset}")

        compare_arrays(
            lsdpy_results[dataset]["diff_rep"],
            reference_baselines[dataset]["diff_rep"],
            f"{dataset} diff_rep (B_loc)"
        )

    @pytest.mark.parametrize("dataset", DATASETS)
    def test_transitions_identical(self, dataset, reference_baselines, lsdpy_results):
        """Test that transition matrix matches original."""
        if dataset not in reference_baselines or "transitions" not in reference_baselines[dataset]:
            pytest.skip(f"No transitions baseline for {dataset}")

        if dataset not in lsdpy_results or "transitions" not in lsdpy_results[dataset]:
            pytest.skip(f"No lsdpy transitions for {dataset}")

        ref_T = reference_baselines[dataset]["transitions"]
        act_T = lsdpy_results[dataset]["transitions"]

        if sp.issparse(ref_T):
            ref_T = ref_T.toarray()
        if sp.issparse(act_T):
            act_T = act_T.toarray()

        compare_arrays(act_T, ref_T, f"{dataset} transitions")

    @pytest.mark.parametrize("dataset", DATASETS)
    def test_cbdir_scores_identical(self, dataset, reference_baselines, lsdpy_results):
        """Test that CBDir metric scores match original."""
        if dataset not in reference_baselines or "cbdir_scores" not in reference_baselines[dataset]:
            pytest.skip(f"No cbdir_scores baseline for {dataset}")

        if dataset not in lsdpy_results or "cbdir_scores" not in lsdpy_results[dataset]:
            pytest.skip(f"No lsdpy cbdir_scores for {dataset}")

        ref_scores = reference_baselines[dataset]["cbdir_scores"]
        act_scores = lsdpy_results[dataset]["cbdir_scores"]

        for edge, expected in ref_scores.items():
            if edge == "mean":
                continue
            if edge not in act_scores:
                pytest.fail(f"Missing CBDir score for edge {edge}")

            actual = act_scores[edge]
            assert abs(actual - expected) < CBDIR_ATOL, \
                f"CBDir mismatch for {dataset} edge {edge}: " \
                f"expected {expected}, got {actual}"


class TestCrossValidation:
    """Cross-validation tests to ensure reproducibility across runs."""

    def test_deterministic_training(self, small_adata, lsd_config, device, random_seed):
        """Test that training produces identical results with same seed."""
        pytest.importorskip("pyro")
        from sclsd import LSD, set_all_seeds, clear_pyro_state

        results = []

        for _ in range(2):
            clear_pyro_state()
            set_all_seeds(random_seed)

            lsd = LSD(small_adata.copy(), lsd_config, device=device)
            lsd.set_prior_transition(prior_time_key="pseudotime")
            lsd.prepare_walks()

            # Train for a few epochs
            lsd.train(num_epochs=3, save_dir=None, plot_loss=False)

            result = lsd.get_adata()
            results.append({
                "pseudotime": result.obs["lsd_pseudotime"].values.copy(),
                "potential": result.obs["potential"].values.copy(),
            })

        # Compare results
        np.testing.assert_allclose(
            results[0]["pseudotime"],
            results[1]["pseudotime"],
            rtol=RTOL,
            err_msg="Pseudotime should be identical across runs with same seed"
        )
        np.testing.assert_allclose(
            results[0]["potential"],
            results[1]["potential"],
            rtol=RTOL,
            err_msg="Potential should be identical across runs with same seed"
        )
