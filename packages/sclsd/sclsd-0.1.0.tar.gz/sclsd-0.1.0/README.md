# LSDpy

**Latent State Dynamics for Single-Cell Trajectory Inference**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/sclsd.svg)](https://badge.fury.io/py/sclsd)

LSDpy is a deep learning framework for inferring cell differentiation trajectories from single-cell RNA sequencing data. It combines neural ODEs with variational inference to model the Waddington landscape of cellular differentiation.

## Key Features

- **Neural ODE Dynamics**: Model cell state evolution as gradient flow in a learned potential landscape
- **Variational Inference**: Probabilistic modeling with Pyro for uncertainty quantification
- **Trajectory Inference**: Infer pseudotime and cell fate predictions
- **Reproducible**: Comprehensive RNG management for identical results across runs
- **GPU Accelerated**: Full CUDA support for efficient training

## Installation

### From PyPI (recommended)

```bash
pip install sclsd
```

### From Source

```bash
git clone https://github.com/your-repo/sclsd.git
cd sclsd
pip install -e .
```

### With Conda Environment

```bash
conda env create -f environment.yml
conda activate lsd
pip install -e .
```

## Quick Start

```python
import scanpy as sc
import torch
from sclsd import LSD, LSDConfig, prepare_data_dict

# Load and preprocess data
adata = sc.read("my_data.h5ad")
data_dict = prepare_data_dict(adata, n_top_genes=5000)

# Configure model
cfg = LSDConfig()
cfg.walks.path_len = 50
cfg.walks.num_walks = 10000
cfg.model.z_dim = 10
cfg.model.B_dim = 2

# Create model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
lsd = LSD(data_dict["adata"], cfg, device=device)

# Set prior transition matrix based on pseudotime
lsd.set_prior_transition(prior_time_key="dpt_pseudotime")

# Generate random walks
lsd.prepare_walks()

# Train model
lsd.train(num_epochs=100, random_state=42)

# Get results
result = lsd.get_adata()
print(result.obs["lsd_pseudotime"])
print(result.obsm["cell_rep"])  # Latent cell state
print(result.obsm["diff_rep"])  # Differentiation state
```

## Model Architecture

LSDpy models cellular differentiation using:

1. **Cell State Encoder** (`XEncoder`): Maps gene expression to latent cell state `z`
2. **Differentiation State Encoder** (`ZEncoder`): Maps cell state to differentiation state `B`
3. **Potential Network**: Learns the Waddington landscape potential `V(z)`
4. **Neural ODE**: Evolves cell states as gradient descent on the potential
5. **Decoder** (`ZDecoder`): Reconstructs gene expression from latent state

The model is trained using stochastic variational inference with a Zero-Inflated Negative Binomial likelihood for count data.

## Configuration

```python
from sclsd import LSDConfig

cfg = LSDConfig()

# Model architecture
cfg.model.z_dim = 10          # Latent cell state dimension
cfg.model.B_dim = 2           # Differentiation state dimension
cfg.model.V_coeff = 0.0       # Potential regularization

# Random walks
cfg.walks.path_len = 50       # Steps per walk
cfg.walks.num_walks = 10000   # Number of training walks
cfg.walks.batch_size = 256    # Batch size

# Optimizer
cfg.optimizer.adam.lr = 1e-3
cfg.optimizer.adam.T_0 = 50   # Cosine annealing period

# KL annealing
cfg.optimizer.kl_schedule.min_af = 0.0
cfg.optimizer.kl_schedule.max_af = 1.0
cfg.optimizer.kl_schedule.max_epoch = 50
```

## Prior Pseudotime

LSDpy requires a prior pseudotime or transition matrix to guide training:

```python
# Option 1: Use existing pseudotime (e.g., from diffusion pseudotime)
lsd.set_prior_transition(prior_time_key="dpt_pseudotime")

# Option 2: Infer prior pseudotime automatically
from sclsd import infer_prior_time
adata = infer_prior_time(data_dict, device, origin_cluster="Stem")

# Option 3: Use phylogeny-guided transitions
lsd.set_phylogeny(
    phylogeny={"Stem": ["Prog1", "Prog2"], "Prog1": ["Mature1"]},
    cluster_key="clusters"
)
lsd.set_prior_transition(prior_time_key="pseudotime")
```

## Cell Fate Prediction

```python
# Predict cell fates by propagating through the potential landscape
result = lsd.get_cell_fates(
    adata=result,
    time_range=10.0,
    dt=0.5,
    cluster_key="clusters",
    return_paths=True
)

print(result.obs["fate"])  # Predicted terminal state for each cell
```

## Evaluation Metrics

```python
from sclsd import cross_boundary_correctness, inner_cluster_coh

# Define expected transitions
edges = [("Stem", "Prog"), ("Prog", "Mature")]

# Cross-boundary correctness
scores, mean_score = cross_boundary_correctness(
    adata, "clusters", "velocity", edges
)
print(f"Cross-boundary score: {mean_score:.3f}")

# In-cluster coherence
scores, mean_score = inner_cluster_coh(adata, "clusters", "velocity")
print(f"In-cluster coherence: {mean_score:.3f}")
```

## Visualization

```python
from sclsd import plot_random_walks, plot_z_components, visualize_random_walks_on_umap

# Plot random walks on UMAP
plot_random_walks(result, walks[:10], rep="X_umap")

# Visualize ODE trajectories
plot_z_components(lsd.z_sol[:, :10, :], t_max=10.0)

# Visualize walks from specific clusters
visualize_random_walks_on_umap(
    result, lsd.paths,
    target_clusters=["Stem"],
    cluster_key="clusters"
)
```

## Reproducibility

LSDpy ensures reproducible results through comprehensive RNG management:

```python
from sclsd import set_all_seeds

# Set all random seeds before training
set_all_seeds(42)

# Train model - results will be identical across runs
lsd.train(num_epochs=100, random_state=42)
```

**Important**: The order of `pyro.sample()` calls in the model determines the random number sequence. The implementation preserves the exact sampling order to ensure reproducibility.

## API Reference

### Main Classes

- `LSD`: Main trainer class for model training and inference
- `LSDConfig`: Configuration dataclass with nested configs for model, optimizer, and walks
- `LSDModel`: Neural network model implementing the Pyro generative model and guide

### Preprocessing

- `prepare_data_dict()`: Prepare AnnData for training
- `infer_prior_time()`: Automatically infer prior pseudotime
- `get_prior_transition()`: Compute prior transition matrix

### Analysis

- `cross_boundary_correctness()`: Evaluate velocity direction correctness
- `inner_cluster_coh()`: Evaluate velocity coherence within clusters
- `evaluate()`: Run all evaluation metrics

### Plotting

- `plot_random_walks()`: Visualize random walks on embeddings
- `plot_z_components()`: Plot latent component trajectories
- `plot_streamlines()`: Visualize velocity streamlines
- `visualize_random_walks_on_umap()`: Enhanced walk visualization

## Requirements

- Python >= 3.9
- PyTorch >= 2.0.0
- Pyro-PPL >= 1.8.0
- torchdiffeq >= 0.2.0
- scanpy >= 1.9.0
- anndata >= 0.9.0

## Citation

If you use LSDpy in your research, please cite:

```bibtex
@article{lsd2024,
  title={Latent State Dynamics for Single-Cell Trajectory Inference},
  author={LSD Development Team},
  journal={},
  year={2024}
}
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please see our contributing guidelines for details.

## Support

- **Issues**: https://github.com/csglab/sclsd/issues
