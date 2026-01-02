"""
Tests for normalization techniques module
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml.normalization import (
    # Main functions
    batch_normalization,
    layer_normalization,
    group_normalization,
    instance_normalization,
    weight_normalization,
    # Forward passes with cache
    batch_norm_forward,
    layer_norm_forward,
    # Utilities
    create_normalization_params,
    apply_normalization,
    # Aliases
    batchnorm,
    layernorm,
    groupnorm,
    instancenorm,
    weightnorm,
)


def test_batch_normalization():
    """Test Batch Normalization"""
    print("Testing batch_normalization...")
    
    # Test 2D input (fully connected)
    x = np.random.randn(32, 64)
    gamma = np.ones(64)
    beta = np.zeros(64)
    
    out, running_mean, running_var = batch_normalization(
        x, gamma, beta, training=True
    )
    
    assert out.shape == x.shape, "Output shape should match input"
    assert running_mean.shape == (64,), "Running mean shape incorrect"
    assert running_var.shape == (64,), "Running var shape incorrect"
    
    # Check normalization (mean ≈ 0, var ≈ 1)
    assert np.abs(np.mean(out)) < 0.1, "Mean should be close to 0"
    assert np.abs(np.var(out) - 1.0) < 0.2, "Variance should be close to 1"
    
    print("✓ batch_normalization passed")


def test_batch_normalization_4d():
    """Test Batch Normalization with 4D input (CNN)"""
    print("Testing batch_normalization with 4D input...")
    
    # Test 4D input (convolutional)
    x = np.random.randn(8, 32, 16, 16)  # (N, C, H, W)
    gamma = np.ones(32)
    beta = np.zeros(32)
    
    out, running_mean, running_var = batch_normalization(
        x, gamma, beta, training=True
    )
    
    assert out.shape == x.shape, "Output shape should match input"
    assert running_mean.shape == (32,), "Running mean shape incorrect"
    
    print("✓ batch_normalization 4D passed")


def test_batch_normalization_inference():
    """Test Batch Normalization in inference mode"""
    print("Testing batch_normalization inference mode...")
    
    x = np.random.randn(32, 64)
    gamma = np.ones(64)
    beta = np.zeros(64)
    running_mean = np.random.randn(64)
    running_var = np.abs(np.random.randn(64))
    
    out, _, _ = batch_normalization(
        x, gamma, beta, running_mean, running_var, training=False
    )
    
    assert out.shape == x.shape, "Output shape should match input"
    print("✓ batch_normalization inference passed")


def test_layer_normalization():
    """Test Layer Normalization"""
    print("Testing layer_normalization...")
    
    # Test 2D input
    x = np.random.randn(32, 512)
    gamma = np.ones(512)
    beta = np.zeros(512)
    
    out = layer_normalization(x, gamma, beta)
    
    assert out.shape == x.shape, "Output shape should match input"
    
    # Check normalization per sample
    for i in range(32):
        sample_mean = np.mean(out[i])
        sample_var = np.var(out[i])
        assert np.abs(sample_mean) < 0.1, f"Sample {i} mean should be close to 0"
        assert np.abs(sample_var - 1.0) < 0.2, f"Sample {i} variance should be close to 1"
    
    print("✓ layer_normalization passed")


def test_layer_normalization_3d():
    """Test Layer Normalization with 3D input (sequences)"""
    print("Testing layer_normalization with 3D input...")
    
    # Test 3D input (sequences for Transformers)
    x = np.random.randn(32, 10, 512)  # (N, L, D)
    gamma = np.ones(512)
    beta = np.zeros(512)
    
    out = layer_normalization(x, gamma, beta)
    
    assert out.shape == x.shape, "Output shape should match input"
    
    # Check normalization per sample per timestep
    for i in range(32):
        for t in range(10):
            token_mean = np.mean(out[i, t])
            token_var = np.var(out[i, t])
            assert np.abs(token_mean) < 0.1, "Token mean should be close to 0"
            assert np.abs(token_var - 1.0) < 0.2, "Token variance should be close to 1"
    
    print("✓ layer_normalization 3D passed")


def test_group_normalization():
    """Test Group Normalization"""
    print("Testing group_normalization...")
    
    x = np.random.randn(8, 64, 32, 32)  # (N, C, H, W)
    gamma = np.ones(64)
    beta = np.zeros(64)
    
    out = group_normalization(x, gamma, beta, num_groups=32)
    
    assert out.shape == x.shape, "Output shape should match input"
    print("✓ group_normalization passed")


def test_group_normalization_invalid_groups():
    """Test Group Normalization with invalid number of groups"""
    print("Testing group_normalization with invalid groups...")
    
    x = np.random.randn(8, 64, 32, 32)
    gamma = np.ones(64)
    beta = np.zeros(64)
    
    try:
        out = group_normalization(x, gamma, beta, num_groups=30)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "divisible" in str(e).lower()
    
    print("✓ group_normalization invalid groups passed")


def test_instance_normalization():
    """Test Instance Normalization"""
    print("Testing instance_normalization...")
    
    x = np.random.randn(8, 64, 32, 32)  # (N, C, H, W)
    gamma = np.ones(64)
    beta = np.zeros(64)
    
    out = instance_normalization(x, gamma, beta)
    
    assert out.shape == x.shape, "Output shape should match input"
    
    # Check normalization per instance per channel
    for n in range(8):
        for c in range(64):
            channel_mean = np.mean(out[n, c])
            channel_var = np.var(out[n, c])
            assert np.abs(channel_mean) < 0.1, "Channel mean should be close to 0"
            assert np.abs(channel_var - 1.0) < 0.2, "Channel variance should be close to 1"
    
    print("✓ instance_normalization passed")


def test_weight_normalization():
    """Test Weight Normalization"""
    print("Testing weight_normalization...")
    
    w = np.random.randn(512, 256)
    
    w_norm, g = weight_normalization(w, axis=0)
    
    assert w_norm.shape == w.shape, "Output shape should match input"
    assert g.shape == (512,), "Magnitude shape incorrect"
    
    # Check that each row has unit norm
    for i in range(512):
        row_norm = np.linalg.norm(w_norm[i])
        expected_norm = g[i]
        assert np.abs(row_norm - expected_norm) < 1e-5, "Row norm should match magnitude"
    
    print("✓ weight_normalization passed")


def test_weight_normalization_axis1():
    """Test Weight Normalization with axis=1"""
    print("Testing weight_normalization with axis=1...")
    
    w = np.random.randn(512, 256)
    
    w_norm, g = weight_normalization(w, axis=1)
    
    assert w_norm.shape == w.shape, "Output shape should match input"
    assert g.shape == (256,), "Magnitude shape incorrect"
    
    print("✓ weight_normalization axis=1 passed")


def test_batch_norm_forward():
    """Test Batch Normalization forward with cache"""
    print("Testing batch_norm_forward...")
    
    x = np.random.randn(32, 64)
    gamma = np.ones(64)
    beta = np.zeros(64)
    
    bn_params = {
        'mode': 'train',
        'eps': 1e-5,
        'momentum': 0.9,
        'running_mean': np.zeros(64),
        'running_var': np.ones(64)
    }
    
    out, cache = batch_norm_forward(x, gamma, beta, bn_params)
    
    assert out.shape == x.shape, "Output shape should match input"
    assert 'x' in cache, "Cache should contain input"
    assert 'gamma' in cache, "Cache should contain gamma"
    assert 'x_normalized' in cache, "Cache should contain normalized input"
    
    print("✓ batch_norm_forward passed")


def test_layer_norm_forward():
    """Test Layer Normalization forward with cache"""
    print("Testing layer_norm_forward...")
    
    x = np.random.randn(32, 512)
    gamma = np.ones(512)
    beta = np.zeros(512)
    
    out, cache = layer_norm_forward(x, gamma, beta)
    
    assert out.shape == x.shape, "Output shape should match input"
    assert 'x' in cache, "Cache should contain input"
    assert 'gamma' in cache, "Cache should contain gamma"
    assert 'x_normalized' in cache, "Cache should contain normalized input"
    
    print("✓ layer_norm_forward passed")


def test_create_normalization_params():
    """Test create_normalization_params utility"""
    print("Testing create_normalization_params...")
    
    # Test batch norm params
    params = create_normalization_params(64, 'batch')
    assert 'gamma' in params, "Should have gamma"
    assert 'beta' in params, "Should have beta"
    assert 'running_mean' in params, "Batch norm should have running_mean"
    assert 'running_var' in params, "Batch norm should have running_var"
    assert params['gamma'].shape == (64,), "Gamma shape incorrect"
    
    # Test layer norm params
    params = create_normalization_params(512, 'layer')
    assert 'gamma' in params, "Should have gamma"
    assert 'beta' in params, "Should have beta"
    assert 'running_mean' not in params, "Layer norm should not have running_mean"
    
    print("✓ create_normalization_params passed")


def test_apply_normalization():
    """Test apply_normalization utility"""
    print("Testing apply_normalization...")
    
    x = np.random.randn(32, 64)
    gamma = np.ones(64)
    beta = np.zeros(64)
    
    # Test batch norm
    out = apply_normalization(x, 'batch', gamma, beta, training=True)
    assert out.shape == x.shape, "Batch norm output shape incorrect"
    
    # Test layer norm
    out = apply_normalization(x, 'layer', gamma, beta)
    assert out.shape == x.shape, "Layer norm output shape incorrect"
    
    print("✓ apply_normalization passed")


def test_apply_normalization_invalid():
    """Test apply_normalization with invalid type"""
    print("Testing apply_normalization with invalid type...")
    
    x = np.random.randn(32, 64)
    gamma = np.ones(64)
    beta = np.zeros(64)
    
    try:
        out = apply_normalization(x, 'invalid', gamma, beta)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "unknown" in str(e).lower()
    
    print("✓ apply_normalization invalid type passed")


def test_aliases():
    """Test function aliases"""
    print("Testing aliases...")
    
    x = np.random.randn(32, 64)
    gamma = np.ones(64)
    beta = np.zeros(64)
    
    # Test batchnorm alias
    out1, _, _ = batchnorm(x, gamma, beta, training=True)
    out2, _, _ = batch_normalization(x, gamma, beta, training=True)
    assert np.allclose(out1, out2), "Batchnorm alias should work"
    
    # Test layernorm alias
    out1 = layernorm(x, gamma, beta)
    out2 = layer_normalization(x, gamma, beta)
    assert np.allclose(out1, out2), "Layernorm alias should work"
    
    print("✓ aliases passed")


def test_batch_vs_layer_norm():
    """Test difference between batch and layer normalization"""
    print("Testing batch vs layer normalization...")
    
    x = np.random.randn(32, 64)
    gamma = np.ones(64)
    beta = np.zeros(64)
    
    # Batch norm normalizes across batch
    out_batch, _, _ = batch_normalization(x, gamma, beta, training=True)
    
    # Layer norm normalizes across features
    out_layer = layer_normalization(x, gamma, beta)
    
    # They should produce different results
    assert not np.allclose(out_batch, out_layer), "Batch and layer norm should differ"
    
    print("✓ batch vs layer norm comparison passed")


def test_normalization_stability():
    """Test numerical stability with extreme values"""
    print("Testing normalization stability...")
    
    # Test with very large values
    x = np.random.randn(32, 64) * 1000
    gamma = np.ones(64)
    beta = np.zeros(64)
    
    out, _, _ = batch_normalization(x, gamma, beta, training=True)
    assert not np.any(np.isnan(out)), "Should not produce NaN"
    assert not np.any(np.isinf(out)), "Should not produce Inf"
    
    # Test with very small values
    x = np.random.randn(32, 64) * 1e-10
    out, _, _ = batch_normalization(x, gamma, beta, training=True)
    assert not np.any(np.isnan(out)), "Should not produce NaN with small values"
    
    print("✓ normalization stability passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("NORMALIZATION TECHNIQUES MODULE TESTS")
    print("="*60 + "\n")
    
    # Batch Normalization
    test_batch_normalization()
    test_batch_normalization_4d()
    test_batch_normalization_inference()
    test_batch_norm_forward()
    
    # Layer Normalization
    test_layer_normalization()
    test_layer_normalization_3d()
    test_layer_norm_forward()
    
    # Group Normalization
    test_group_normalization()
    test_group_normalization_invalid_groups()
    
    # Instance Normalization
    test_instance_normalization()
    
    # Weight Normalization
    test_weight_normalization()
    test_weight_normalization_axis1()
    
    # Utilities
    test_create_normalization_params()
    test_apply_normalization()
    test_apply_normalization_invalid()
    
    # Aliases
    test_aliases()
    
    # Comparisons
    test_batch_vs_layer_norm()
    test_normalization_stability()
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
