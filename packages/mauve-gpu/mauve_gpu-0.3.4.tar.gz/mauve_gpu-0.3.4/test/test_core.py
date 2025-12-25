import pytest
import numpy as np
import cupy as cp
import logging
from mauve_gpu import MauveScorer


def test_compute_identical_distributions():
    """Identical distributions should yield a MAUVE score very close to 1.0."""
    scorer = MauveScorer(random_state=42, verbose=True)
    # Use a realistic embedding dimension
    features = np.random.rand(2000, 384).astype(np.float32)
    score = scorer.compute(features, features.copy())
    # The score may not be exactly 1.0 due to floating point arithmetic
    assert score == pytest.approx(1.0, abs=1e-2)


def test_compute_different_distributions():
    """Different distributions should yield a MAUVE score less than 1.0."""
    scorer = MauveScorer(random_state=42)
    # Generate two distinct distributions
    p_features = np.random.normal(0, 1, (1000, 64)).astype(np.float32)
    q_features = np.random.normal(5, 1, (1000, 64)).astype(np.float32)
    score = scorer.compute(p_features, q_features)
    assert 0.0 <= score < 0.9  # Should be significantly less than 1.0


def test_cupy_input():
    """Test that CuPy arrays are handled correctly."""
    scorer = MauveScorer(random_state=42)
    p_features = cp.random.rand(1000, 64).astype(cp.float32)
    q_features = cp.random.rand(1000, 64).astype(cp.float32)
    score = scorer.compute(p_features, q_features)
    assert 0.0 <= score <= 1.0


def test_different_sample_sizes():
    """Test that P and Q can have different number of samples."""
    scorer = MauveScorer(random_state=42)
    p_features = np.random.rand(1000, 64).astype(np.float32)
    q_features = np.random.rand(500, 64).astype(np.float32)
    score = scorer.compute(p_features, q_features)
    assert 0.0 <= score <= 1.0


def test_scaling_factor_impact():
    """Test that changing the scaling factor affects the score."""
    p_features = np.random.rand(600, 64).astype(np.float32)
    q_features = np.random.rand(600, 64).astype(np.float32)
    
    scorer1 = MauveScorer(scaling_factor=1.0, random_state=42)
    score1 = scorer1.compute(p_features, q_features)
    
    scorer2 = MauveScorer(scaling_factor=10.0, random_state=42)
    score2 = scorer2.compute(p_features, q_features)
    
    # Scores should likely be different for different scaling factors
    assert score1 != score2


def test_float64_input():
    """Test that float64 inputs are accepted and processed."""
    scorer = MauveScorer(random_state=42)
    p_features = np.random.rand(1000, 64).astype(np.float64)
    q_features = np.random.rand(1000, 64).astype(np.float64)
    score = scorer.compute(p_features, q_features)
    assert 0.0 <= score <= 1.0


def test_logging_output(caplog):
    """Test that verbose mode logs information."""
    # Adjust parameters to fit small data
    scorer = MauveScorer(verbose=True, pca_components=10, kmeans_clusters=10)
    p_features = np.random.rand(100, 32).astype(np.float32)
    q_features = np.random.rand(100, 32).astype(np.float32)
    
    with caplog.at_level(logging.INFO):
        scorer.compute(p_features, q_features)
    
    assert "Performing PCA" in caplog.text
    assert "Performing K-Means" in caplog.text


def test_pca_components_equal_features():
    """Test when PCA components equal feature dimension."""
    scorer = MauveScorer(pca_components=32, kmeans_clusters=10, verbose=False)
    p_features = np.random.rand(100, 32).astype(np.float32)
    q_features = np.random.rand(100, 32).astype(np.float32)
    score = scorer.compute(p_features, q_features)
    assert 0.0 <= score <= 1.0


def test_small_kmeans_clusters():
    """Test with a small number of clusters."""
    scorer = MauveScorer(pca_components=10, kmeans_clusters=2, verbose=False)
    p_features = np.random.rand(100, 32).astype(np.float32)
    q_features = np.random.rand(100, 32).astype(np.float32)
    score = scorer.compute(p_features, q_features)
    assert 0.0 <= score <= 1.0


def test_kmeans_clusters_one():
    """Test with k=1 (single cluster)."""
    scorer = MauveScorer(pca_components=10, kmeans_clusters=1, verbose=False)
    p_features = np.random.rand(100, 32).astype(np.float32)
    q_features = np.random.rand(100, 32).astype(np.float32)
    score = scorer.compute(p_features, q_features)
    assert 0.0 <= score <= 1.0


def test_disjoint_distributions():
    """Test with completely disjoint distributions."""
    scorer = MauveScorer(random_state=42)
    # P centered at -10, Q centered at +10
    p_features = np.random.normal(-10, 1, (1000, 64)).astype(np.float32)
    q_features = np.random.normal(10, 1, (1000, 64)).astype(np.float32)
    score = scorer.compute(p_features, q_features)
    # Score should be very low
    assert score < 0.1


def test_kmeans_clusters_near_sample_size():
    """Test when kmeans_clusters is close to the number of samples."""
    # total samples = 200. kmeans_clusters = 100.
    scorer = MauveScorer(pca_components=10, kmeans_clusters=100, verbose=False)
    p_features = np.random.rand(100, 32).astype(np.float32)
    q_features = np.random.rand(100, 32).astype(np.float32)
    score = scorer.compute(p_features, q_features)
    assert 0.0 <= score <= 1.0


def test_divergence_curve_points():
    """Test that changing divergence_curve_points works."""
    scorer = MauveScorer(divergence_curve_points=10, verbose=False)
    p_features = np.random.rand(500, 100).astype(np.float32)
    q_features = np.random.rand(500, 100).astype(np.float32)
    score = scorer.compute(p_features, q_features)
    assert 0.0 <= score <= 1.0


def test_single_kmeans_run():
    """Test that num_kmeans_runs=1 works."""
    scorer = MauveScorer(num_kmeans_runs=1, verbose=False)
    p_features = np.random.rand(500, 100).astype(np.float32)
    q_features = np.random.rand(500, 100).astype(np.float32)
    score = scorer.compute(p_features, q_features)
    assert 0.0 <= score <= 1.0


def test_input_validation_errors():
    """Test that invalid inputs raise appropriate errors."""
    scorer = MauveScorer()
    p = np.random.rand(100, 10)

    # Mismatched feature dimensions
    q_wrong_dim = np.random.rand(100, 11)
    with pytest.raises(ValueError):
        scorer.compute(p, q_wrong_dim)

    # Invalid input type
    q_wrong_type = list(range(100))
    with pytest.raises((TypeError, AttributeError)):
        scorer.compute(p, q_wrong_type)

    # Input contains NaN
    q_nan = p.copy()
    q_nan[0, 0] = np.nan
    with pytest.raises(ValueError):
        scorer.compute(p, q_nan)

    # Too few samples for PCA/K-Means
    p_small = np.random.rand(5, 50)
    q_small = np.random.rand(5, 50)
    with pytest.raises(ValueError):
        scorer.compute(p_small, q_small)


def test_init_validation():
    """Test initialization parameter validation."""
    with pytest.raises(ValueError):
        MauveScorer(pca_components=0)
    with pytest.raises(ValueError):
        MauveScorer(kmeans_clusters=-1)
    with pytest.raises(ValueError):
        MauveScorer(num_kmeans_runs=0)


def test_reproducibility():
    """Test that results are reproducible with the same random_state."""
    p_features = np.random.rand(1000, 64).astype(np.float32)
    q_features = np.random.rand(1000, 64).astype(np.float32)
    
    scorer1 = MauveScorer(random_state=42)
    score1 = scorer1.compute(p_features, q_features)
    
    scorer2 = MauveScorer(random_state=42)
    score2 = scorer2.compute(p_features, q_features)
    
    assert score1 == score2
