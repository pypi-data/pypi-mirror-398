"""
Tests for activation functions module
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml import (
    # Basic Activations
    sigmoid_activation,
    tanh_activation,
    relu_activation,
    leaky_relu_activation,
    elu_activation,
    selu_activation,
    gelu_activation,
    swish_activation,
    mish_activation,
    softplus_activation,
    softsign_activation,
    hard_sigmoid_activation,
    hard_tanh_activation,
    softmax_activation,
    log_softmax_activation,
    # Derivatives
    sigmoid_deriv,
    tanh_deriv,
    relu_deriv,
    leaky_relu_derivative,
    elu_derivative,
    swish_derivative,
    softplus_derivative,
    # Utilities
    apply_activation,
    get_activation_function,
)


def test_sigmoid_activation():
    """Test Sigmoid activation"""
    print("Testing sigmoid_activation...")
    x = np.array([-2, -1, 0, 1, 2])
    output = sigmoid_activation(x)
    
    assert np.all((output > 0) & (output < 1)), "Sigmoid output should be in (0, 1)"
    assert np.isclose(output[2], 0.5), "Sigmoid(0) should be 0.5"
    print("✓ sigmoid_activation passed")


def test_tanh_activation():
    """Test Tanh activation"""
    print("Testing tanh_activation...")
    x = np.array([-2, -1, 0, 1, 2])
    output = tanh_activation(x)
    
    assert np.all((output > -1) & (output < 1)), "Tanh output should be in (-1, 1)"
    assert np.isclose(output[2], 0.0), "Tanh(0) should be 0"
    print("✓ tanh_activation passed")


def test_relu_activation():
    """Test ReLU activation"""
    print("Testing relu_activation...")
    x = np.array([-2, -1, 0, 1, 2])
    output = relu_activation(x)
    
    expected = np.array([0, 0, 0, 1, 2])
    assert np.array_equal(output, expected), "ReLU should zero out negatives"
    print("✓ relu_activation passed")


def test_leaky_relu_activation():
    """Test Leaky ReLU activation"""
    print("Testing leaky_relu_activation...")
    x = np.array([-2, -1, 0, 1, 2])
    output = leaky_relu_activation(x, alpha=0.01)
    
    assert output[0] == -0.02, "Leaky ReLU should have small negative slope"
    assert output[4] == 2, "Leaky ReLU should pass positive values"
    print("✓ leaky_relu_activation passed")


def test_elu_activation():
    """Test ELU activation"""
    print("Testing elu_activation...")
    x = np.array([-2, -1, 0, 1, 2])
    output = elu_activation(x, alpha=1.0)
    
    assert output[2] == 0, "ELU(0) should be 0"
    assert output[4] == 2, "ELU should pass positive values"
    assert output[0] < 0, "ELU should have negative values for negative input"
    print("✓ elu_activation passed")


def test_selu_activation():
    """Test SELU activation"""
    print("Testing selu_activation...")
    x = np.array([-2, -1, 0, 1, 2])
    output = selu_activation(x)
    
    assert output[2] == 0, "SELU(0) should be 0"
    assert output[4] > 2, "SELU should scale positive values"
    print("✓ selu_activation passed")


def test_gelu_activation():
    """Test GELU activation"""
    print("Testing gelu_activation...")
    x = np.array([-2, -1, 0, 1, 2])
    output = gelu_activation(x)
    
    assert np.isclose(output[2], 0.0, atol=0.01), "GELU(0) should be close to 0"
    assert output[4] > 1.5, "GELU should pass most positive values"
    print("✓ gelu_activation passed")


def test_swish_activation():
    """Test Swish activation"""
    print("Testing swish_activation...")
    x = np.array([-2, -1, 0, 1, 2])
    output = swish_activation(x, beta=1.0)
    
    assert np.isclose(output[2], 0.0), "Swish(0) should be 0"
    assert output[4] > 1.5, "Swish should pass most positive values"
    print("✓ swish_activation passed")


def test_mish_activation():
    """Test Mish activation"""
    print("Testing mish_activation...")
    x = np.array([-2, -1, 0, 1, 2])
    output = mish_activation(x)
    
    assert np.isclose(output[2], 0.0), "Mish(0) should be 0"
    assert output[4] > 1.5, "Mish should pass most positive values"
    print("✓ mish_activation passed")


def test_softplus_activation():
    """Test Softplus activation"""
    print("Testing softplus_activation...")
    x = np.array([-2, -1, 0, 1, 2])
    output = softplus_activation(x)
    
    assert np.all(output > 0), "Softplus should always be positive"
    assert np.isclose(output[2], np.log(2)), "Softplus(0) should be ln(2)"
    print("✓ softplus_activation passed")


def test_softsign_activation():
    """Test Softsign activation"""
    print("Testing softsign_activation...")
    x = np.array([-2, -1, 0, 1, 2])
    output = softsign_activation(x)
    
    assert np.all((output > -1) & (output < 1)), "Softsign output should be in (-1, 1)"
    assert output[2] == 0, "Softsign(0) should be 0"
    print("✓ softsign_activation passed")


def test_hard_sigmoid_activation():
    """Test Hard Sigmoid activation"""
    print("Testing hard_sigmoid_activation...")
    x = np.array([-3, -1, 0, 1, 3])
    output = hard_sigmoid_activation(x)
    
    assert output[0] == 0, "Hard Sigmoid should clip to 0"
    assert output[4] == 1, "Hard Sigmoid should clip to 1"
    assert output[2] == 0.5, "Hard Sigmoid(0) should be 0.5"
    print("✓ hard_sigmoid_activation passed")


def test_hard_tanh_activation():
    """Test Hard Tanh activation"""
    print("Testing hard_tanh_activation...")
    x = np.array([-2, -1, 0, 1, 2])
    output = hard_tanh_activation(x)
    
    assert output[0] == -1, "Hard Tanh should clip to -1"
    assert output[4] == 1, "Hard Tanh should clip to 1"
    assert output[2] == 0, "Hard Tanh(0) should be 0"
    print("✓ hard_tanh_activation passed")


def test_softmax_activation():
    """Test Softmax activation"""
    print("Testing softmax_activation...")
    x = np.array([1.0, 2.0, 3.0])
    output = softmax_activation(x)
    
    assert np.isclose(np.sum(output), 1.0), "Softmax should sum to 1"
    assert np.all(output > 0), "Softmax should be all positive"
    assert output[2] > output[1] > output[0], "Softmax should preserve order"
    print("✓ softmax_activation passed")


def test_log_softmax_activation():
    """Test Log-Softmax activation"""
    print("Testing log_softmax_activation...")
    x = np.array([1.0, 2.0, 3.0])
    output = log_softmax_activation(x)
    
    assert np.all(output < 0), "Log-Softmax should be all negative"
    softmax_output = softmax_activation(x)
    assert np.allclose(np.exp(output), softmax_output), "exp(log_softmax) should equal softmax"
    print("✓ log_softmax_activation passed")


def test_sigmoid_derivative():
    """Test Sigmoid derivative"""
    print("Testing sigmoid_deriv...")
    x = np.array([0.0])
    deriv = sigmoid_deriv(x)
    
    assert np.isclose(deriv[0], 0.25), "Sigmoid'(0) should be 0.25"
    print("✓ sigmoid_deriv passed")


def test_tanh_derivative():
    """Test Tanh derivative"""
    print("Testing tanh_deriv...")
    x = np.array([0.0])
    deriv = tanh_deriv(x)
    
    assert np.isclose(deriv[0], 1.0), "Tanh'(0) should be 1.0"
    print("✓ tanh_deriv passed")


def test_relu_derivative():
    """Test ReLU derivative"""
    print("Testing relu_deriv...")
    x = np.array([-1, 0, 1])
    deriv = relu_deriv(x)
    
    expected = np.array([0, 0, 1])
    assert np.array_equal(deriv, expected), "ReLU' should be 0 for negative, 1 for positive"
    print("✓ relu_deriv passed")


def test_leaky_relu_derivative():
    """Test Leaky ReLU derivative"""
    print("Testing leaky_relu_derivative...")
    x = np.array([-1, 0, 1])
    deriv = leaky_relu_derivative(x, alpha=0.01)
    
    assert deriv[0] == 0.01, "Leaky ReLU' should be alpha for negative"
    assert deriv[2] == 1.0, "Leaky ReLU' should be 1 for positive"
    print("✓ leaky_relu_derivative passed")


def test_elu_derivative():
    """Test ELU derivative"""
    print("Testing elu_derivative...")
    x = np.array([-1, 0, 1])
    deriv = elu_derivative(x, alpha=1.0)
    
    assert deriv[1] == 1.0, "ELU'(0) should be 1"
    assert deriv[2] == 1.0, "ELU' should be 1 for positive"
    print("✓ elu_derivative passed")


def test_swish_derivative():
    """Test Swish derivative"""
    print("Testing swish_derivative...")
    x = np.array([0.0])
    deriv = swish_derivative(x)
    
    assert np.isclose(deriv[0], 0.5), "Swish'(0) should be 0.5"
    print("✓ swish_derivative passed")


def test_softplus_derivative():
    """Test Softplus derivative"""
    print("Testing softplus_derivative...")
    x = np.array([0.0])
    deriv = softplus_derivative(x)
    
    assert np.isclose(deriv[0], 0.5), "Softplus'(0) should be 0.5 (sigmoid(0))"
    print("✓ softplus_derivative passed")


def test_apply_activation():
    """Test apply_activation utility"""
    print("Testing apply_activation...")
    x = np.array([-1, 0, 1])
    
    relu_output = apply_activation(x, 'relu')
    expected = np.array([0, 0, 1])
    assert np.array_equal(relu_output, expected), "apply_activation should work with 'relu'"
    
    sigmoid_output = apply_activation(x, 'sigmoid')
    assert np.all((sigmoid_output > 0) & (sigmoid_output < 1)), "apply_activation should work with 'sigmoid'"
    
    print("✓ apply_activation passed")


def test_get_activation_function():
    """Test get_activation_function utility"""
    print("Testing get_activation_function...")
    
    relu_func = get_activation_function('relu')
    assert relu_func.__name__ == 'relu_activation', "Should return relu_activation function"
    
    sigmoid_func = get_activation_function('sigmoid')
    assert sigmoid_func.__name__ == 'sigmoid_activation', "Should return sigmoid_activation function"
    
    print("✓ get_activation_function passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("ACTIVATION FUNCTIONS MODULE TESTS")
    print("="*60 + "\n")
    
    # Basic activations
    test_sigmoid_activation()
    test_tanh_activation()
    test_relu_activation()
    test_leaky_relu_activation()
    test_elu_activation()
    test_selu_activation()
    test_gelu_activation()
    test_swish_activation()
    test_mish_activation()
    test_softplus_activation()
    test_softsign_activation()
    test_hard_sigmoid_activation()
    test_hard_tanh_activation()
    test_softmax_activation()
    test_log_softmax_activation()
    
    # Derivatives
    test_sigmoid_derivative()
    test_tanh_derivative()
    test_relu_derivative()
    test_leaky_relu_derivative()
    test_elu_derivative()
    test_swish_derivative()
    test_softplus_derivative()
    
    # Utilities
    test_apply_activation()
    test_get_activation_function()
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
