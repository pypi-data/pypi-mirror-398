# Mauve-cuML

A GPU-accelerated implementation of the MAUVE score for comparing distributions, leveraging RAPIDS.ai cuML.

MAUVE is a metric for evaluating the quality of generated text by comparing the distribution of generated text to reference text in an embedding space. This library provides a fast and robust implementation using GPU acceleration for PCA and K-Means clustering.

## Features

*   **GPU Acceleration**: Uses `cupy` and `cuml` for high-performance computation.
*   **Robustness**: Implements multiple K-Means runs to select the best clustering, improving score stability.
*   **Easy Integration**: Compatible with NumPy and CuPy arrays.
*   **Configurable**: Allows tuning of PCA components, K-Means clusters, and other parameters.

## Installation

### Prerequisites

*   Python >= 3.8
*   NVIDIA GPU with CUDA support
*   CUDA Toolkit (compatible with the installed RAPIDS version)

### Installing Dependencies

This library relies on RAPIDS libraries (`cuml`, `cupy`), which are best installed via Conda or from the NVIDIA PyPI index.

**Using Pip:**

You need to point pip to the NVIDIA package index to install `cuml` and `cupy`.

```bash
pip install --extra-index-url https://pypi.nvidia.com cuml-cu12 cupy-cuda12x
pip install mauve-cuml
```

*Note: Adjust `cu12` and `cuda12x` based on your CUDA version (e.g., `cu11` for CUDA 11).*

**Using Conda:**

```bash
conda create -n mauve-env -c rapidsai -c conda-forge -c nvidia \
    cuml=23.10 python=3.10 cupy
conda activate mauve-env
pip install mauve-cuml
```

### Installing from Source

```bash
git clone https://github.com/danielwolber-wood/mauve-cuml.git
cd mauve-cuml
pip install --extra-index-url https://pypi.nvidia.com -e .
```

## Usage

Here is a simple example of how to use `MauveScorer`.

```python
import numpy as np
from mauve_cuml import MauveScorer

# Generate dummy embeddings (replace with your actual embeddings)
# P: Reference distribution (e.g., human text embeddings)
# Q: Generated distribution (e.g., model text embeddings)
p_features = np.random.rand(1000, 768).astype(np.float32)
q_features = np.random.rand(1000, 768).astype(np.float32)

# Initialize the scorer
scorer = MauveScorer(
    pca_components=50,
    kmeans_clusters=100,
    num_kmeans_runs=5,
    verbose=True
)

# Compute the score
score = scorer.compute(p_features, q_features)
print(f"MAUVE Score: {score:.4f}")
```

### Parameters

*   `pca_components` (int): Number of components for PCA reduction (default: 50).
*   `kmeans_clusters` (int): Number of clusters for quantization (default: 500).
*   `num_kmeans_runs` (int): Number of K-Means runs to perform to find the best clustering (default: 10).
*   `scaling_factor` (float): The 'c' parameter in the MAUVE paper (default: 5.0).
*   `divergence_curve_points` (int): Number of points for the divergence curve (default: 100).
*   `random_state` (int): Seed for reproducibility (default: 42).
*   `verbose` (bool): If True, prints progress logs (default: False).

## Examples

See the `examples/` directory for more detailed usage, including an example using `sentence-transformers` to compute MAUVE scores for text datasets.

To run the demo:

1.  Install example dependencies:
    ```bash
    pip install .[examples]
    ```
2.  Run the script:
    ```bash
    python examples/demo.py
    ```

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

*   Based on the original MAUVE paper: "MAUVE: Measuring the Gap Between Neural Text and Human Text using Divergence Frontiers".
*   Built with [RAPIDS.ai](https://rapids.ai/) for GPU acceleration.

## AI Disclosure

The first draft of this README was written with AI assistance. Several of the tests in `tests/test_core.py` were
drafted by AI, but were manually checked for correctness.