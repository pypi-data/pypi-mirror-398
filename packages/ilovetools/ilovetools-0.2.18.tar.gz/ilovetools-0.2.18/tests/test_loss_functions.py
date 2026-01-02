"""
Tests for loss functions module
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml import (
    # Regression Losses
    mean_squared_error_loss,
    mean_absolute_error_loss,
    root_mean_squared_error_loss,
    huber_loss,
    log_cosh_loss,
    quantile_loss,
    mean_squared_logarithmic_error,
    # Classification Losses
    binary_crossentropy_loss,
    categorical_crossentropy_loss,
    sparse_categorical_crossentropy_loss,
    hinge_loss,
    squared_hinge_loss,
    categorical_hinge_loss,
    focal_loss,
    kullback_leibler_divergence,
    # Segmentation Losses
    dice_loss,
    dice_coefficient,
    iou_loss,
    tversky_loss,
    focal_tversky_loss,
    # Utilities
    combined_loss,
    weighted_loss,
)


def test_mean_squared_error_loss():
    """Test MSE loss"""
    print("Testing mean_squared_error_loss...")
    y_true = np.array([1.0, 2.0, 3.0, 4.0])
    y_pred = np.array([1.1, 2.2, 2.8, 4.3])
    loss = mean_squared_error_loss(y_true, y_pred)
    
    expected = np.mean((y_true - y_pred) ** 2)
    assert np.isclose(loss, expected), f"Expected {expected}, got {loss}"
    print("✓ mean_squared_error_loss passed")


def test_mean_absolute_error_loss():
    """Test MAE loss"""
    print("Testing mean_absolute_error_loss...")
    y_true = np.array([1.0, 2.0, 3.0, 4.0])
    y_pred = np.array([1.1, 2.2, 2.8, 4.3])
    loss = mean_absolute_error_loss(y_true, y_pred)
    
    expected = np.mean(np.abs(y_true - y_pred))
    assert np.isclose(loss, expected), f"Expected {expected}, got {loss}"
    print("✓ mean_absolute_error_loss passed")


def test_root_mean_squared_error_loss():
    """Test RMSE loss"""
    print("Testing root_mean_squared_error_loss...")
    y_true = np.array([1.0, 2.0, 3.0, 4.0])
    y_pred = np.array([1.1, 2.2, 2.8, 4.3])
    loss = root_mean_squared_error_loss(y_true, y_pred)
    
    expected = np.sqrt(np.mean((y_true - y_pred) ** 2))
    assert np.isclose(loss, expected), f"Expected {expected}, got {loss}"
    print("✓ root_mean_squared_error_loss passed")


def test_huber_loss():
    """Test Huber loss"""
    print("Testing huber_loss...")
    y_true = np.array([1.0, 2.0, 3.0, 10.0])
    y_pred = np.array([1.1, 2.2, 2.8, 4.0])
    loss = huber_loss(y_true, y_pred, delta=1.0)
    
    assert loss > 0, "Huber loss should be positive"
    print("✓ huber_loss passed")


def test_log_cosh_loss():
    """Test Log-Cosh loss"""
    print("Testing log_cosh_loss...")
    y_true = np.array([1.0, 2.0, 3.0, 4.0])
    y_pred = np.array([1.1, 2.2, 2.8, 4.3])
    loss = log_cosh_loss(y_true, y_pred)
    
    assert loss > 0, "Log-Cosh loss should be positive"
    print("✓ log_cosh_loss passed")


def test_quantile_loss():
    """Test Quantile loss"""
    print("Testing quantile_loss...")
    y_true = np.array([1.0, 2.0, 3.0, 4.0])
    y_pred = np.array([1.1, 2.2, 2.8, 4.3])
    loss = quantile_loss(y_true, y_pred, quantile=0.5)
    
    assert loss >= 0, "Quantile loss should be non-negative"
    print("✓ quantile_loss passed")


def test_mean_squared_logarithmic_error():
    """Test MSLE"""
    print("Testing mean_squared_logarithmic_error...")
    y_true = np.array([1.0, 2.0, 3.0, 4.0])
    y_pred = np.array([1.1, 2.2, 2.8, 4.3])
    loss = mean_squared_logarithmic_error(y_true, y_pred)
    
    assert loss >= 0, "MSLE should be non-negative"
    print("✓ mean_squared_logarithmic_error passed")


def test_binary_crossentropy_loss():
    """Test Binary Cross-Entropy loss"""
    print("Testing binary_crossentropy_loss...")
    y_true = np.array([0, 1, 1, 0])
    y_pred = np.array([0.1, 0.9, 0.8, 0.2])
    loss = binary_crossentropy_loss(y_true, y_pred)
    
    assert loss > 0, "BCE loss should be positive"
    assert loss < 1, "BCE loss should be reasonable"
    print("✓ binary_crossentropy_loss passed")


def test_categorical_crossentropy_loss():
    """Test Categorical Cross-Entropy loss"""
    print("Testing categorical_crossentropy_loss...")
    y_true = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    y_pred = np.array([[0.9, 0.05, 0.05], [0.1, 0.8, 0.1], [0.1, 0.1, 0.8]])
    loss = categorical_crossentropy_loss(y_true, y_pred)
    
    assert loss > 0, "CCE loss should be positive"
    print("✓ categorical_crossentropy_loss passed")


def test_sparse_categorical_crossentropy_loss():
    """Test Sparse Categorical Cross-Entropy loss"""
    print("Testing sparse_categorical_crossentropy_loss...")
    y_true = np.array([0, 1, 2])
    y_pred = np.array([[0.9, 0.05, 0.05], [0.1, 0.8, 0.1], [0.1, 0.1, 0.8]])
    loss = sparse_categorical_crossentropy_loss(y_true, y_pred)
    
    assert loss > 0, "Sparse CCE loss should be positive"
    print("✓ sparse_categorical_crossentropy_loss passed")


def test_hinge_loss():
    """Test Hinge loss"""
    print("Testing hinge_loss...")
    y_true = np.array([1, -1, 1, -1])
    y_pred = np.array([0.9, -0.8, 0.7, -0.6])
    loss = hinge_loss(y_true, y_pred)
    
    assert loss >= 0, "Hinge loss should be non-negative"
    print("✓ hinge_loss passed")


def test_squared_hinge_loss():
    """Test Squared Hinge loss"""
    print("Testing squared_hinge_loss...")
    y_true = np.array([1, -1, 1, -1])
    y_pred = np.array([0.9, -0.8, 0.7, -0.6])
    loss = squared_hinge_loss(y_true, y_pred)
    
    assert loss >= 0, "Squared hinge loss should be non-negative"
    print("✓ squared_hinge_loss passed")


def test_categorical_hinge_loss():
    """Test Categorical Hinge loss"""
    print("Testing categorical_hinge_loss...")
    y_true = np.array([[1, 0, 0], [0, 1, 0]])
    y_pred = np.array([[2.0, 0.5, 0.3], [0.3, 1.8, 0.4]])
    loss = categorical_hinge_loss(y_true, y_pred)
    
    assert loss >= 0, "Categorical hinge loss should be non-negative"
    print("✓ categorical_hinge_loss passed")


def test_focal_loss():
    """Test Focal loss"""
    print("Testing focal_loss...")
    y_true = np.array([0, 1, 1, 0])
    y_pred = np.array([0.1, 0.9, 0.6, 0.2])
    loss = focal_loss(y_true, y_pred, alpha=0.25, gamma=2.0)
    
    assert loss >= 0, "Focal loss should be non-negative"
    print("✓ focal_loss passed")


def test_kullback_leibler_divergence():
    """Test KL Divergence"""
    print("Testing kullback_leibler_divergence...")
    y_true = np.array([0.3, 0.5, 0.2])
    y_pred = np.array([0.25, 0.55, 0.2])
    loss = kullback_leibler_divergence(y_true, y_pred)
    
    assert loss >= 0, "KL divergence should be non-negative"
    print("✓ kullback_leibler_divergence passed")


def test_dice_coefficient():
    """Test Dice coefficient"""
    print("Testing dice_coefficient...")
    y_true = np.array([1, 1, 0, 0, 1])
    y_pred = np.array([1, 1, 0, 1, 1])
    dice = dice_coefficient(y_true, y_pred)
    
    assert 0 <= dice <= 1, "Dice coefficient should be between 0 and 1"
    assert dice > 0.5, "Dice should be high for good overlap"
    print("✓ dice_coefficient passed")


def test_dice_loss():
    """Test Dice loss"""
    print("Testing dice_loss...")
    y_true = np.array([1, 1, 0, 0, 1])
    y_pred = np.array([1, 1, 0, 1, 1])
    loss = dice_loss(y_true, y_pred)
    
    assert 0 <= loss <= 1, "Dice loss should be between 0 and 1"
    print("✓ dice_loss passed")


def test_iou_loss():
    """Test IoU loss"""
    print("Testing iou_loss...")
    y_true = np.array([1, 1, 0, 0, 1])
    y_pred = np.array([1, 1, 0, 1, 1])
    loss = iou_loss(y_true, y_pred)
    
    assert 0 <= loss <= 1, "IoU loss should be between 0 and 1"
    print("✓ iou_loss passed")


def test_tversky_loss():
    """Test Tversky loss"""
    print("Testing tversky_loss...")
    y_true = np.array([1, 1, 0, 0, 1])
    y_pred = np.array([1, 1, 0, 1, 1])
    loss = tversky_loss(y_true, y_pred, alpha=0.5, beta=0.5)
    
    assert 0 <= loss <= 1, "Tversky loss should be between 0 and 1"
    print("✓ tversky_loss passed")


def test_focal_tversky_loss():
    """Test Focal Tversky loss"""
    print("Testing focal_tversky_loss...")
    y_true = np.array([1, 1, 0, 0, 1])
    y_pred = np.array([1, 1, 0, 1, 1])
    loss = focal_tversky_loss(y_true, y_pred, gamma=2.0)
    
    assert loss >= 0, "Focal Tversky loss should be non-negative"
    print("✓ focal_tversky_loss passed")


def test_combined_loss():
    """Test combined loss"""
    print("Testing combined_loss...")
    y_true = np.array([1, 1, 0, 0, 1])
    y_pred = np.array([0.9, 0.8, 0.1, 0.2, 0.85])
    
    loss = combined_loss(
        y_true, y_pred,
        loss_functions=[dice_loss, binary_crossentropy_loss],
        weights=[0.7, 0.3]
    )
    
    assert loss > 0, "Combined loss should be positive"
    print("✓ combined_loss passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("LOSS FUNCTIONS MODULE TESTS")
    print("="*60 + "\n")
    
    # Regression losses
    test_mean_squared_error_loss()
    test_mean_absolute_error_loss()
    test_root_mean_squared_error_loss()
    test_huber_loss()
    test_log_cosh_loss()
    test_quantile_loss()
    test_mean_squared_logarithmic_error()
    
    # Classification losses
    test_binary_crossentropy_loss()
    test_categorical_crossentropy_loss()
    test_sparse_categorical_crossentropy_loss()
    test_hinge_loss()
    test_squared_hinge_loss()
    test_categorical_hinge_loss()
    test_focal_loss()
    test_kullback_leibler_divergence()
    
    # Segmentation losses
    test_dice_coefficient()
    test_dice_loss()
    test_iou_loss()
    test_tversky_loss()
    test_focal_tversky_loss()
    
    # Utilities
    test_combined_loss()
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
