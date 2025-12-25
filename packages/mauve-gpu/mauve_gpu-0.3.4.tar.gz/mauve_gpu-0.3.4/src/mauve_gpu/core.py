# Copyright 2025 Daniel Wood
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from typing import Union

import cupy as cp
import numpy as np
from cuml.decomposition import PCA
from cuml.cluster import KMeans

logger = logging.getLogger(__name__)


class MauveScorer:
    """
    A cuML-accelerated implementation of the MAUVE score.

    This class provides a reusable and robust way to compute the MAUVE score
    between two distributions of features, leveraging RAPIDS.ai cuML for
    GPU acceleration of PCA and K-Means.
    """
    _SMALL_VAL = 1e-10

    def __init__(self,
                 pca_components: int = 50,
                 kmeans_clusters: int = 500,
                 num_kmeans_runs: int = 10,
                 scaling_factor: float = 5.0,
                 divergence_curve_points: int = 100,
                 random_state: int = 42,
                 verbose: bool = False):
        """
        Initialize the MAUVE Scorer using cuML.

        Args:
            pca_components: Number of components for PCA reduction.
            kmeans_clusters: Number of clusters (k) for quantization.
            num_kmeans_runs: Number of times to run K-Means with different seeds.
                             The run with the lowest inertia (sum of squared distances)
                             is selected to improve the stability of the score.
            scaling_factor: The 'c' parameter in the MAUVE paper (default 5.0).
            divergence_curve_points: Number of points to sample for the divergence curve.
            random_state: Seed for reproducibility.
            verbose: If True, print progress logs to INFO.
        """
        # Parameter validation
        if not isinstance(pca_components, int) or pca_components <= 0:
            raise ValueError("pca_components must be a positive integer.")
        if not isinstance(kmeans_clusters, int) or kmeans_clusters <= 0:
            raise ValueError("kmeans_clusters must be a positive integer.")
        if not isinstance(num_kmeans_runs, int) or num_kmeans_runs <= 0:
            raise ValueError("num_kmeans_runs must be a positive integer.")

        self.pca_components = pca_components
        self.kmeans_clusters = kmeans_clusters
        self.num_kmeans_runs = num_kmeans_runs
        self.c = scaling_factor
        self.divergence_curve_points = divergence_curve_points
        self.random_state = random_state
        self.verbose = verbose

    def _log(self, msg: str, level: int = logging.INFO):
        """Helper to log messages based on verbosity."""
        if self.verbose:
            logger.log(level, msg)

    def compute(self, p_features: Union[np.ndarray, cp.ndarray], q_features: Union[np.ndarray, cp.ndarray]) -> float:
        """
        Compute the MAUVE score between two sets of embeddings.
        
        Args:
            p_features: Embeddings for distribution P (Reference/Human), shape (N, D). Can be a NumPy or CuPy array.
            q_features: Embeddings for distribution Q (Generated/Model), shape (M, D). Can be a NumPy or CuPy array.
            
        Returns:
            float: The MAUVE score (0.0 to 1.0).
        """
        # 1. Input Validation and Preparation
        self._validate_inputs(p_features, q_features)
        is_cupy_input = isinstance(p_features, cp.ndarray)
        n_p = p_features.shape[0]

        # Stack data. If input is numpy, this is on CPU. If cupy, on GPU.
        if is_cupy_input:
            all_data = cp.vstack([p_features, q_features])
        else:
            # Convert to CuPy to ensure pipeline stays on GPU and returns CuPy arrays
            all_data = cp.asarray(np.vstack([p_features, q_features]))

        # 2. Dimensionality Reduction (PCA)
        self._log(f"Performing PCA (components={self.pca_components})...")
        pca = PCA(n_components=self.pca_components)
        embedding_gpu = pca.fit_transform(all_data)

        # 3. Robust Quantization (K-Means)
        self._log(f"Performing K-Means (k={self.kmeans_clusters}, runs={self.num_kmeans_runs})...")
        best_inertia = float('inf')
        best_labels_gpu = None

        for i in range(self.num_kmeans_runs):
            current_seed = self.random_state + i
            # n_init=1 because we are manually looping, which is more memory efficient
            # for large datasets than letting cuml do it internally.
            kmeans = KMeans(n_clusters=self.kmeans_clusters, random_state=current_seed, n_init=1)
            labels_gpu = kmeans.fit_predict(embedding_gpu)
            inertia = kmeans.inertia_
            self._log(f"  Run {i + 1}/{self.num_kmeans_runs}: inertia={inertia:.4f}", level=logging.DEBUG)

            if inertia < best_inertia:
                best_inertia = inertia
                best_labels_gpu = labels_gpu

        self._log(f"Selected K-Means run with best inertia: {best_inertia:.4f}")

        # Split labels back
        p_labels = best_labels_gpu[:n_p]
        q_labels = best_labels_gpu[n_p:]

        # 4. Compute Discrete Distributions
        self._log("Computing discrete distributions...", level=logging.DEBUG)
        p_probs = self._get_probs(p_labels)
        q_probs = self._get_probs(q_labels)

        # 5. Compute Divergence Curve and Integrate
        self._log("Calculating divergence curve and integrating...", level=logging.DEBUG)
        mauve_score = self._compute_divergence_integral(p_probs, q_probs)
        
        return mauve_score

    def _validate_inputs(self, p: Union[np.ndarray, cp.ndarray], q: Union[np.ndarray, cp.ndarray]):
        """Performs sanity checks on input arrays."""
        for name, arr in [("p_features", p), ("q_features", q)]:
            if not isinstance(arr, (np.ndarray, cp.ndarray)):
                raise TypeError(f"{name} must be a numpy or cupy array, but got {type(arr)}")
            if arr.ndim != 2:
                raise ValueError(f"{name} must be a 2D array, but has {arr.ndim} dimensions.")

            # Check for NaN/Inf. Use the correct library for the check.
            xp = cp.get_array_module(arr)
            if xp.isnan(arr).any() or xp.isinf(arr).any():
                raise ValueError(f"{name} contains NaN or Inf values.")

        if p.shape[1] != q.shape[1]:
            raise ValueError(f"Feature dimensions of p_features ({p.shape[1]}) and q_features ({q.shape[1]}) do not match.")

        total_samples = p.shape[0] + q.shape[0]
        if self.pca_components > min(total_samples, p.shape[1]):
            raise ValueError(
                f"pca_components ({self.pca_components}) cannot be larger than the number of samples ({total_samples}) or features ({p.shape[1]}).")
        if self.kmeans_clusters > total_samples:
            raise ValueError(
                f"kmeans_clusters ({self.kmeans_clusters}) cannot be larger than the total number of samples ({total_samples}).")

    def _get_probs(self, labels: cp.ndarray) -> cp.ndarray:
        """Compute normalized probability distribution over clusters."""
        counts = cp.bincount(labels, minlength=self.kmeans_clusters)
        total_count = cp.sum(counts)
        # Handle case where there are no labels (empty input)
        if total_count == 0:
            return cp.zeros(self.kmeans_clusters, dtype=cp.float32)
        return counts / total_count

    def _compute_divergence_integral(self, p_probs: cp.ndarray, q_probs: cp.ndarray) -> float:
        """Vectorized calculation of the divergence curve and integration."""
        ld_series = cp.linspace(0.001, 0.999, self.divergence_curve_points)

        # Reshape for broadcasting: (K, 1) and (1, L)
        p_col = p_probs[:, None]
        q_col = q_probs[:, None]
        ld_row = ld_series[None, :]

        # Mixture Distribution R_lambda
        r_matrix = (p_col * ld_row) + (q_col * (1 - ld_row))

        # Calculate KL Divergences
        kl_p_r = self._safe_kl_sum(p_col, r_matrix)
        kl_q_r = self._safe_kl_sum(q_col, r_matrix)

        # Convert to curve coordinates (x, y)
        x_vals = cp.exp(-self.c * kl_q_r)
        y_vals = cp.exp(-self.c * kl_p_r)

        # Add (0,0) and (1,1) for a closed curve from origin to top-right
        x_vals = cp.concatenate([cp.array([0.0]), x_vals])
        y_vals = cp.concatenate([cp.array([1.0]), y_vals])

        # Sort for Trapezoidal rule
        sort_idx = cp.argsort(x_vals)
        x_sorted = x_vals[sort_idx]
        y_sorted = y_vals[sort_idx]

        # Integrate using the trapezoidal rule
        return cp.trapz(y_sorted, x_sorted).item()

    @staticmethod
    def _safe_kl_sum(p_col: cp.ndarray, r_mat: cp.ndarray) -> cp.ndarray:
        """
        Computes sum(P * log(P/R)) handling zeros safely.
        p_col: (K, 1)
        r_mat: (K, L)
        Returns: (L,)
        """
        # Use the class constant for small value comparison
        mask = (p_col[:, 0] > MauveScorer._SMALL_VAL)

        p_safe = p_col[mask]
        r_safe = r_mat[mask, :]

        # Add a small epsilon to the denominator inside the log to prevent log(P/0)
        # which can happen if a cluster has P>0 but R=0.
        r_safe = cp.maximum(r_safe, MauveScorer._SMALL_VAL)

        term = p_safe * cp.log(p_safe / r_safe)
        return cp.sum(term, axis=0)
