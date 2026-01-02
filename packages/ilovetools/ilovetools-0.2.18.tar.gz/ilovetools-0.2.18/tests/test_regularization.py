"""
Tests for regularization module
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml import (
    # L1/L2 Regularization
    l1_regularization,
    l2_regularization,
    elastic_net_regularization,
    l1_penalty,
    l2_penalty,
    elastic_net_penalty,
    # Dropout
    dropout,
    dropout_mask,
    inverted_dropout,
    # Early Stopping
    reg_early_stopping_monitor,
    should_stop_early,
    # Weight Constraints
    max_norm_constraint,
    unit_norm_constraint,
    non_negative_constraint,
    # Regularization Utilities
    compute_regularization_loss,
    apply_weight_decay,
)


def test_l1_regularization():
    """Test L1 regularization"""
    print("Testing l1_regularization...")
    weights = np.array([1.0, -2.0, 3.0, 0.5])
    penalty = l1_regularization(weights, lambda_param=0.01)
    
    expected = 0.01 * (1.0 + 2.0 + 3.0 + 0.5)
    assert np.isclose(penalty, expected), f"Expected {expected}, got {penalty}"
    print("✓ l1_regularization passed")


def test_l2_regularization():
    """Test L2 regularization"""
    print("Testing l2_regularization...")
    weights = np.array([1.0, -2.0, 3.0, 0.5])
    penalty = l2_regularization(weights, lambda_param=0.01)
    
    expected = 0.01 * (1.0**2 + 2.0**2 + 3.0**2 + 0.5**2)
    assert np.isclose(penalty, expected), f"Expected {expected}, got {penalty}"
    print("✓ l2_regularization passed")


def test_elastic_net_regularization():
    """Test Elastic Net regularization"""
    print("Testing elastic_net_regularization...")
    weights = np.array([1.0, -2.0, 3.0, 0.5])
    penalty = elastic_net_regularization(weights, l1_ratio=0.5, lambda_param=0.01)
    
    l1_term = 0.5 * (1.0 + 2.0 + 3.0 + 0.5)
    l2_term = 0.5 * (1.0**2 + 2.0**2 + 3.0**2 + 0.5**2)
    expected = 0.01 * (l1_term + l2_term)
    
    assert np.isclose(penalty, expected), f"Expected {expected}, got {penalty}"
    print("✓ elastic_net_regularization passed")


def test_l1_penalty():
    """Test L1 gradient penalty"""
    print("Testing l1_penalty...")
    weights = np.array([1.0, -2.0, 0.0, 0.5])
    gradient_penalty = l1_penalty(weights, lambda_param=0.01)
    
    expected = np.array([0.01, -0.01, 0.0, 0.01])
    assert np.allclose(gradient_penalty, expected), f"Expected {expected}, got {gradient_penalty}"
    print("✓ l1_penalty passed")


def test_l2_penalty():
    """Test L2 gradient penalty"""
    print("Testing l2_penalty...")
    weights = np.array([1.0, -2.0, 3.0, 0.5])
    gradient_penalty = l2_penalty(weights, lambda_param=0.01)
    
    expected = 2 * 0.01 * weights
    assert np.allclose(gradient_penalty, expected), f"Expected {expected}, got {gradient_penalty}"
    print("✓ l2_penalty passed")


def test_elastic_net_penalty():
    """Test Elastic Net gradient penalty"""
    print("Testing elastic_net_penalty...")
    weights = np.array([1.0, -2.0, 3.0, 0.5])
    gradient_penalty = elastic_net_penalty(weights, l1_ratio=0.5, lambda_param=0.01)
    
    assert gradient_penalty.shape == weights.shape
    print("✓ elastic_net_penalty passed")


def test_dropout():
    """Test dropout"""
    print("Testing dropout...")
    np.random.seed(42)
    X = np.random.randn(100, 50)
    
    # Training mode
    X_dropout, mask = dropout(X, dropout_rate=0.5, training=True, seed=42)
    assert X_dropout.shape == X.shape
    assert mask.shape == X.shape
    assert np.sum(mask == 0) > 0  # Some neurons should be dropped
    
    # Inference mode
    X_inference, mask_inf = dropout(X, dropout_rate=0.5, training=False)
    assert np.allclose(X_inference, X)  # No dropout in inference
    
    print("✓ dropout passed")


def test_dropout_mask():
    """Test dropout mask generation"""
    print("Testing dropout_mask...")
    mask = dropout_mask((100, 50), dropout_rate=0.3, seed=42)
    
    assert mask.shape == (100, 50)
    assert np.all((mask == 0) | (mask == 1))  # Binary mask
    
    # Approximately 70% should be active (1 - dropout_rate)
    active_ratio = np.mean(mask)
    assert 0.6 < active_ratio < 0.8, f"Active ratio {active_ratio} not close to 0.7"
    
    print("✓ dropout_mask passed")


def test_inverted_dropout():
    """Test inverted dropout"""
    print("Testing inverted_dropout...")
    np.random.seed(42)
    X = np.random.randn(100, 50)
    
    # Training mode
    X_train = inverted_dropout(X, dropout_rate=0.5, training=True, seed=42)
    assert X_train.shape == X.shape
    assert not np.allclose(X_train, X)  # Should be different
    
    # Inference mode
    X_test = inverted_dropout(X, dropout_rate=0.5, training=False)
    assert np.allclose(X_test, X)  # Should be unchanged
    
    print("✓ inverted_dropout passed")


def test_early_stopping_monitor():
    """Test early stopping monitor"""
    print("Testing reg_early_stopping_monitor...")
    
    # Improving losses
    val_losses = [1.0, 0.8, 0.7, 0.6, 0.5]
    should_stop, epochs_no_improve, best = reg_early_stopping_monitor(
        val_losses, patience=3
    )
    assert should_stop == False
    assert best == 0.5
    
    # Plateauing losses
    val_losses = [1.0, 0.8, 0.7, 0.71, 0.72, 0.73, 0.74]
    should_stop, epochs_no_improve, best = reg_early_stopping_monitor(
        val_losses, patience=3
    )
    assert should_stop == True
    assert best == 0.7
    
    print("✓ reg_early_stopping_monitor passed")


def test_should_stop_early():
    """Test should stop early (stateless)"""
    print("Testing should_stop_early...")
    
    # Improvement
    stop, counter, best = should_stop_early(
        current_loss=0.65,
        best_loss=0.70,
        patience_counter=2,
        patience=5
    )
    assert stop == False
    assert counter == 0  # Reset
    assert best == 0.65
    
    # No improvement
    stop, counter, best = should_stop_early(
        current_loss=0.75,
        best_loss=0.70,
        patience_counter=4,
        patience=5
    )
    assert stop == True
    assert counter == 5
    assert best == 0.70
    
    print("✓ should_stop_early passed")


def test_max_norm_constraint():
    """Test max norm constraint"""
    print("Testing max_norm_constraint...")
    
    # Create weights with large norms
    weights = np.random.randn(100, 50) * 10
    constrained = max_norm_constraint(weights, max_norm=3.0, axis=0)
    
    # Check norms are constrained
    norms = np.linalg.norm(constrained, axis=0)
    assert np.all(norms <= 3.0 + 1e-6), f"Max norm {norms.max()} exceeds 3.0"
    
    print("✓ max_norm_constraint passed")


def test_unit_norm_constraint():
    """Test unit norm constraint"""
    print("Testing unit_norm_constraint...")
    
    weights = np.random.randn(100, 50)
    normalized = unit_norm_constraint(weights, axis=0)
    
    # Check all norms are 1
    norms = np.linalg.norm(normalized, axis=0)
    assert np.allclose(norms, 1.0), f"Norms not all 1.0: {norms}"
    
    print("✓ unit_norm_constraint passed")


def test_non_negative_constraint():
    """Test non-negative constraint"""
    print("Testing non_negative_constraint...")
    
    weights = np.array([1.0, -2.0, 3.0, -0.5, 0.0])
    constrained = non_negative_constraint(weights)
    
    expected = np.array([1.0, 0.0, 3.0, 0.0, 0.0])
    assert np.allclose(constrained, expected), f"Expected {expected}, got {constrained}"
    assert np.all(constrained >= 0), "Some weights are negative"
    
    print("✓ non_negative_constraint passed")


def test_compute_regularization_loss():
    """Test compute regularization loss"""
    print("Testing compute_regularization_loss...")
    
    weights = np.random.randn(100)
    
    # L1
    l1_loss = compute_regularization_loss(weights, 'l1', 0.01)
    assert l1_loss > 0
    
    # L2
    l2_loss = compute_regularization_loss(weights, 'l2', 0.01)
    assert l2_loss > 0
    
    # Elastic Net
    elastic_loss = compute_regularization_loss(
        weights, 'elastic_net', 0.01, l1_ratio=0.5
    )
    assert elastic_loss > 0
    
    # None
    none_loss = compute_regularization_loss(weights, 'none', 0.01)
    assert none_loss == 0.0
    
    print("✓ compute_regularization_loss passed")


def test_apply_weight_decay():
    """Test weight decay"""
    print("Testing apply_weight_decay...")
    
    weights = np.array([1.0, 2.0, 3.0])
    decayed = apply_weight_decay(weights, learning_rate=0.01, weight_decay=0.01)
    
    expected = weights * (1 - 0.01 * 0.01)
    assert np.allclose(decayed, expected), f"Expected {expected}, got {decayed}"
    assert np.all(decayed < weights), "Weights should decrease"
    
    print("✓ apply_weight_decay passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("REGULARIZATION MODULE TESTS")
    print("="*60 + "\n")
    
    test_l1_regularization()
    test_l2_regularization()
    test_elastic_net_regularization()
    test_l1_penalty()
    test_l2_penalty()
    test_elastic_net_penalty()
    test_dropout()
    test_dropout_mask()
    test_inverted_dropout()
    test_early_stopping_monitor()
    test_should_stop_early()
    test_max_norm_constraint()
    test_unit_norm_constraint()
    test_non_negative_constraint()
    test_compute_regularization_loss()
    test_apply_weight_decay()
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
