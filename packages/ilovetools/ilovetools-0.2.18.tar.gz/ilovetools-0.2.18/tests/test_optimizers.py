"""
Tests for advanced optimizers module
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml.optimizers import (
    # Adam Variants
    adam_optimizer,
    adamw_optimizer,
    adamax_optimizer,
    nadam_optimizer,
    amsgrad_optimizer,
    # RMSprop Variants
    rmsprop_optimizer,
    rmsprop_momentum_optimizer,
    # Modern Optimizers
    radam_optimizer,
    lamb_optimizer,
    lookahead_optimizer,
    adabelief_optimizer,
    # Utilities
    create_optimizer_state,
    get_optimizer_function,
)


def test_adam_optimizer():
    """Test Adam optimizer"""
    print("Testing adam_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    grads = np.array([0.1, 0.2, 0.3])
    m = np.zeros_like(params)
    v = np.zeros_like(params)
    
    new_params, m, v = adam_optimizer(params, grads, m, v, t=1)
    
    assert new_params.shape == params.shape, "Output shape should match input"
    assert not np.array_equal(new_params, params), "Parameters should be updated"
    assert np.all(m != 0), "First moment should be updated"
    assert np.all(v != 0), "Second moment should be updated"
    print("✓ adam_optimizer passed")


def test_adamw_optimizer():
    """Test AdamW optimizer"""
    print("Testing adamw_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    grads = np.array([0.1, 0.2, 0.3])
    m = np.zeros_like(params)
    v = np.zeros_like(params)
    
    new_params, m, v = adamw_optimizer(params, grads, m, v, t=1, weight_decay=0.01)
    
    assert new_params.shape == params.shape, "Output shape should match input"
    assert not np.array_equal(new_params, params), "Parameters should be updated"
    print("✓ adamw_optimizer passed")


def test_adamax_optimizer():
    """Test AdaMax optimizer"""
    print("Testing adamax_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    grads = np.array([0.1, 0.2, 0.3])
    m = np.zeros_like(params)
    u = np.zeros_like(params)
    
    new_params, m, u = adamax_optimizer(params, grads, m, u, t=1)
    
    assert new_params.shape == params.shape, "Output shape should match input"
    assert not np.array_equal(new_params, params), "Parameters should be updated"
    print("✓ adamax_optimizer passed")


def test_nadam_optimizer():
    """Test Nadam optimizer"""
    print("Testing nadam_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    grads = np.array([0.1, 0.2, 0.3])
    m = np.zeros_like(params)
    v = np.zeros_like(params)
    
    new_params, m, v = nadam_optimizer(params, grads, m, v, t=1)
    
    assert new_params.shape == params.shape, "Output shape should match input"
    assert not np.array_equal(new_params, params), "Parameters should be updated"
    print("✓ nadam_optimizer passed")


def test_amsgrad_optimizer():
    """Test AMSGrad optimizer"""
    print("Testing amsgrad_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    grads = np.array([0.1, 0.2, 0.3])
    m = np.zeros_like(params)
    v = np.zeros_like(params)
    v_max = np.zeros_like(params)
    
    new_params, m, v, v_max = amsgrad_optimizer(params, grads, m, v, v_max, t=1)
    
    assert new_params.shape == params.shape, "Output shape should match input"
    assert not np.array_equal(new_params, params), "Parameters should be updated"
    assert np.all(v_max >= 0), "v_max should be non-negative"
    print("✓ amsgrad_optimizer passed")


def test_rmsprop_optimizer():
    """Test RMSprop optimizer"""
    print("Testing rmsprop_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    grads = np.array([0.1, 0.2, 0.3])
    cache = np.zeros_like(params)
    
    new_params, cache = rmsprop_optimizer(params, grads, cache)
    
    assert new_params.shape == params.shape, "Output shape should match input"
    assert not np.array_equal(new_params, params), "Parameters should be updated"
    assert np.all(cache >= 0), "Cache should be non-negative"
    print("✓ rmsprop_optimizer passed")


def test_rmsprop_momentum_optimizer():
    """Test RMSprop with momentum"""
    print("Testing rmsprop_momentum_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    grads = np.array([0.1, 0.2, 0.3])
    cache = np.zeros_like(params)
    momentum = np.zeros_like(params)
    
    new_params, cache, momentum = rmsprop_momentum_optimizer(
        params, grads, cache, momentum
    )
    
    assert new_params.shape == params.shape, "Output shape should match input"
    assert not np.array_equal(new_params, params), "Parameters should be updated"
    print("✓ rmsprop_momentum_optimizer passed")


def test_radam_optimizer():
    """Test RAdam optimizer"""
    print("Testing radam_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    grads = np.array([0.1, 0.2, 0.3])
    m = np.zeros_like(params)
    v = np.zeros_like(params)
    
    new_params, m, v = radam_optimizer(params, grads, m, v, t=1)
    
    assert new_params.shape == params.shape, "Output shape should match input"
    assert not np.array_equal(new_params, params), "Parameters should be updated"
    print("✓ radam_optimizer passed")


def test_lamb_optimizer():
    """Test LAMB optimizer"""
    print("Testing lamb_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    grads = np.array([0.1, 0.2, 0.3])
    m = np.zeros_like(params)
    v = np.zeros_like(params)
    
    new_params, m, v = lamb_optimizer(params, grads, m, v, t=1)
    
    assert new_params.shape == params.shape, "Output shape should match input"
    assert not np.array_equal(new_params, params), "Parameters should be updated"
    print("✓ lamb_optimizer passed")


def test_lookahead_optimizer():
    """Test Lookahead optimizer"""
    print("Testing lookahead_optimizer...")
    params = np.array([1.5, 2.5, 3.5])
    slow_params = np.array([1.0, 2.0, 3.0])
    
    new_params, slow_params, counter = lookahead_optimizer(
        params, slow_params, k_counter=5, k=5
    )
    
    assert new_params.shape == params.shape, "Output shape should match input"
    assert counter == 0, "Counter should reset after k steps"
    print("✓ lookahead_optimizer passed")


def test_adabelief_optimizer():
    """Test AdaBelief optimizer"""
    print("Testing adabelief_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    grads = np.array([0.1, 0.2, 0.3])
    m = np.zeros_like(params)
    s = np.zeros_like(params)
    
    new_params, m, s = adabelief_optimizer(params, grads, m, s, t=1)
    
    assert new_params.shape == params.shape, "Output shape should match input"
    assert not np.array_equal(new_params, params), "Parameters should be updated"
    print("✓ adabelief_optimizer passed")


def test_create_optimizer_state():
    """Test create_optimizer_state utility"""
    print("Testing create_optimizer_state...")
    
    # Test Adam state
    state = create_optimizer_state((3,), 'adam')
    assert 'm' in state, "Adam should have first moment"
    assert 'v' in state, "Adam should have second moment"
    assert 't' in state, "Should have time step"
    
    # Test RMSprop state
    state = create_optimizer_state((3,), 'rmsprop')
    assert 'cache' in state, "RMSprop should have cache"
    
    print("✓ create_optimizer_state passed")


def test_get_optimizer_function():
    """Test get_optimizer_function utility"""
    print("Testing get_optimizer_function...")
    
    opt_fn = get_optimizer_function('adam')
    assert opt_fn.__name__ == 'adam_optimizer', "Should return adam_optimizer function"
    
    opt_fn = get_optimizer_function('adamw')
    assert opt_fn.__name__ == 'adamw_optimizer', "Should return adamw_optimizer function"
    
    print("✓ get_optimizer_function passed")


def test_optimizer_convergence():
    """Test optimizer convergence on simple problem"""
    print("Testing optimizer convergence...")
    
    # Simple quadratic: f(x) = x^2, gradient = 2x
    # Minimum at x = 0
    params = np.array([5.0])
    
    m = np.zeros_like(params)
    v = np.zeros_like(params)
    
    # Run Adam for 100 steps
    for t in range(1, 101):
        grads = 2 * params  # Gradient of x^2
        params, m, v = adam_optimizer(params, grads, m, v, t, learning_rate=0.1)
    
    assert np.abs(params[0]) < 0.1, "Should converge close to minimum"
    print(f"  Final value: {params[0]:.6f} (should be close to 0)")
    print("✓ optimizer_convergence passed")


def test_adamw_weight_decay():
    """Test AdamW weight decay effect"""
    print("Testing AdamW weight decay...")
    
    params = np.array([1.0, 2.0, 3.0])
    grads = np.zeros_like(params)  # Zero gradients
    m = np.zeros_like(params)
    v = np.zeros_like(params)
    
    # With weight decay, parameters should shrink even with zero gradients
    new_params, m, v = adamw_optimizer(
        params, grads, m, v, t=1, weight_decay=0.1, learning_rate=0.1
    )
    
    assert np.all(np.abs(new_params) < np.abs(params)), "Weight decay should shrink parameters"
    print("✓ adamw_weight_decay passed")


def test_lamb_trust_ratio():
    """Test LAMB trust ratio computation"""
    print("Testing LAMB trust ratio...")
    
    # Large parameters, small gradients
    params = np.array([10.0, 20.0, 30.0])
    grads = np.array([0.01, 0.02, 0.03])
    m = np.zeros_like(params)
    v = np.zeros_like(params)
    
    new_params, m, v = lamb_optimizer(params, grads, m, v, t=1)
    
    # LAMB should adapt step size based on layer norm
    assert new_params.shape == params.shape, "Output shape should match"
    print("✓ lamb_trust_ratio passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("ADVANCED OPTIMIZERS MODULE TESTS")
    print("="*60 + "\n")
    
    # Adam variants
    test_adam_optimizer()
    test_adamw_optimizer()
    test_adamax_optimizer()
    test_nadam_optimizer()
    test_amsgrad_optimizer()
    
    # RMSprop variants
    test_rmsprop_optimizer()
    test_rmsprop_momentum_optimizer()
    
    # Modern optimizers
    test_radam_optimizer()
    test_lamb_optimizer()
    test_lookahead_optimizer()
    test_adabelief_optimizer()
    
    # Utilities
    test_create_optimizer_state()
    test_get_optimizer_function()
    
    # Integration tests
    test_optimizer_convergence()
    test_adamw_weight_decay()
    test_lamb_trust_ratio()
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
