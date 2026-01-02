"""
Test suite for neural network utilities
Run: python -m pytest tests/test_neural_network.py -v
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml import (
    # Activation Functions
    sigmoid, relu, leaky_relu, tanh, softmax, elu, swish,
    # Activation Derivatives
    sigmoid_derivative, relu_derivative, tanh_derivative,
    # Loss Functions
    mse_loss, binary_crossentropy, categorical_crossentropy, huber_loss,
    # Weight Initialization
    xavier_init, he_init, random_init, zeros_init, ones_init,
    # Layer Operations
    dense_forward, dense_backward, dropout_forward, batch_norm_forward,
    # Optimization
    sgd_update, momentum_update, adam_update, rmsprop_update,
    # Utilities
    one_hot_encode, shuffle_data, mini_batch_generator, calculate_accuracy, confusion_matrix_nn
)


def test_activation_functions():
    """Test all activation functions"""
    print("\n=== Testing Activation Functions ===")
    
    x = np.array([-2, -1, 0, 1, 2])
    
    # Sigmoid
    sig_out = sigmoid(x)
    print(f"✓ Sigmoid: {sig_out}")
    assert sig_out.shape == x.shape
    assert np.all((sig_out >= 0) & (sig_out <= 1))
    
    # ReLU
    relu_out = relu(x)
    print(f"✓ ReLU: {relu_out}")
    assert np.all(relu_out >= 0)
    
    # Leaky ReLU
    leaky_out = leaky_relu(x, alpha=0.1)
    print(f"✓ Leaky ReLU: {leaky_out}")
    
    # Tanh
    tanh_out = tanh(x)
    print(f"✓ Tanh: {tanh_out}")
    assert np.all((tanh_out >= -1) & (tanh_out <= 1))
    
    # Softmax
    soft_out = softmax(x)
    print(f"✓ Softmax: {soft_out}, Sum: {soft_out.sum()}")
    assert np.isclose(soft_out.sum(), 1.0)
    
    # ELU
    elu_out = elu(x)
    print(f"✓ ELU: {elu_out}")
    
    # Swish
    swish_out = swish(x)
    print(f"✓ Swish: {swish_out}")
    
    print("✅ All activation functions passed!")


def test_activation_derivatives():
    """Test activation derivatives"""
    print("\n=== Testing Activation Derivatives ===")
    
    x = np.array([0, 1, 2])
    
    # Sigmoid derivative
    sig_out = sigmoid(x)
    sig_deriv = sigmoid_derivative(sig_out)
    print(f"✓ Sigmoid derivative: {sig_deriv}")
    
    # ReLU derivative
    relu_deriv = relu_derivative(x)
    print(f"✓ ReLU derivative: {relu_deriv}")
    
    # Tanh derivative
    tanh_out = tanh(x)
    tanh_deriv = tanh_derivative(tanh_out)
    print(f"✓ Tanh derivative: {tanh_deriv}")
    
    print("✅ All activation derivatives passed!")


def test_loss_functions():
    """Test loss functions"""
    print("\n=== Testing Loss Functions ===")
    
    # MSE Loss
    y_true = np.array([1, 2, 3, 4])
    y_pred = np.array([1.1, 2.2, 2.9, 4.1])
    mse = mse_loss(y_true, y_pred)
    print(f"✓ MSE Loss: {mse:.4f}")
    assert mse >= 0
    
    # Binary Cross-Entropy
    y_true_bin = np.array([1, 0, 1, 0])
    y_pred_bin = np.array([0.9, 0.1, 0.8, 0.2])
    bce = binary_crossentropy(y_true_bin, y_pred_bin)
    print(f"✓ Binary Cross-Entropy: {bce:.4f}")
    assert bce >= 0
    
    # Categorical Cross-Entropy
    y_true_cat = np.array([[1, 0, 0], [0, 1, 0]])
    y_pred_cat = np.array([[0.8, 0.1, 0.1], [0.2, 0.7, 0.1]])
    cce = categorical_crossentropy(y_true_cat, y_pred_cat)
    print(f"✓ Categorical Cross-Entropy: {cce:.4f}")
    assert cce >= 0
    
    # Huber Loss
    y_true_hub = np.array([1, 2, 3, 10])
    y_pred_hub = np.array([1.1, 2.2, 2.9, 4])
    huber = huber_loss(y_true_hub, y_pred_hub, delta=1.0)
    print(f"✓ Huber Loss: {huber:.4f}")
    assert huber >= 0
    
    print("✅ All loss functions passed!")


def test_weight_initialization():
    """Test weight initialization methods"""
    print("\n=== Testing Weight Initialization ===")
    
    shape = (10, 5)
    
    # Xavier
    xavier_weights = xavier_init(shape, seed=42)
    print(f"✓ Xavier: shape={xavier_weights.shape}, mean={xavier_weights.mean():.4f}, std={xavier_weights.std():.4f}")
    assert xavier_weights.shape == shape
    
    # He
    he_weights = he_init(shape, seed=42)
    print(f"✓ He: shape={he_weights.shape}, mean={he_weights.mean():.4f}, std={he_weights.std():.4f}")
    assert he_weights.shape == shape
    
    # Random
    random_weights = random_init(shape, scale=0.1, seed=42)
    print(f"✓ Random: shape={random_weights.shape}")
    assert random_weights.shape == shape
    
    # Zeros
    zero_weights = zeros_init(shape)
    print(f"✓ Zeros: sum={zero_weights.sum()}")
    assert zero_weights.sum() == 0
    
    # Ones
    one_weights = ones_init(shape)
    print(f"✓ Ones: sum={one_weights.sum()}")
    assert one_weights.sum() == 50
    
    print("✅ All weight initialization methods passed!")


def test_layer_operations():
    """Test layer operations"""
    print("\n=== Testing Layer Operations ===")
    
    # Dense forward
    x = np.random.randn(32, 10)
    weights = xavier_init((10, 5))
    bias = zeros_init((5,))
    output = dense_forward(x, weights, bias)
    print(f"✓ Dense forward: input={x.shape}, output={output.shape}")
    assert output.shape == (32, 5)
    
    # Dense backward
    dout = np.random.randn(32, 5)
    dx, dw, db = dense_backward(dout, x, weights)
    print(f"✓ Dense backward: dx={dx.shape}, dw={dw.shape}, db={db.shape}")
    assert dx.shape == x.shape
    assert dw.shape == weights.shape
    assert db.shape == bias.shape
    
    # Dropout
    x_drop = np.ones((32, 10))
    output_drop, mask = dropout_forward(x_drop, dropout_rate=0.5, seed=42)
    dropped = (mask == 0).sum()
    print(f"✓ Dropout: dropped {dropped} neurons")
    
    # Batch Norm
    x_bn = np.random.randn(32, 10)
    gamma = np.ones(10)
    beta = np.zeros(10)
    output_bn, cache = batch_norm_forward(x_bn, gamma, beta)
    print(f"✓ Batch Norm: mean={output_bn.mean():.4f}, std={output_bn.std():.4f}")
    assert np.isclose(output_bn.mean(), 0, atol=1e-6)
    
    print("✅ All layer operations passed!")


def test_optimization():
    """Test optimization algorithms"""
    print("\n=== Testing Optimization Algorithms ===")
    
    weights = np.array([1.0, 2.0, 3.0])
    gradients = np.array([0.1, 0.2, 0.3])
    
    # SGD
    new_weights_sgd = sgd_update(weights, gradients, learning_rate=0.1)
    print(f"✓ SGD: {weights} -> {new_weights_sgd}")
    
    # Momentum
    velocity = np.zeros(3)
    new_weights_mom, new_velocity = momentum_update(weights, gradients, velocity)
    print(f"✓ Momentum: {weights} -> {new_weights_mom}")
    
    # Adam
    m = np.zeros(3)
    v = np.zeros(3)
    new_weights_adam, new_m, new_v = adam_update(weights, gradients, m, v, t=1)
    print(f"✓ Adam: {weights} -> {new_weights_adam}")
    
    # RMSprop
    cache = np.zeros(3)
    new_weights_rms, new_cache = rmsprop_update(weights, gradients, cache)
    print(f"✓ RMSprop: {weights} -> {new_weights_rms}")
    
    print("✅ All optimization algorithms passed!")


def test_utilities():
    """Test utility functions"""
    print("\n=== Testing Utility Functions ===")
    
    # One-hot encoding
    labels = np.array([0, 1, 2, 1, 0])
    one_hot = one_hot_encode(labels)
    print(f"✓ One-hot encode: {labels.shape} -> {one_hot.shape}")
    assert one_hot.shape == (5, 3)
    
    # Shuffle data
    X = np.array([[1, 2], [3, 4], [5, 6]])
    y = np.array([0, 1, 2])
    X_shuffled, y_shuffled = shuffle_data(X, y, seed=42)
    print(f"✓ Shuffle data: original y={y}, shuffled y={y_shuffled}")
    
    # Mini-batch generator
    X_large = np.random.randn(100, 10)
    y_large = np.random.randint(0, 2, 100)
    batch_count = 0
    for X_batch, y_batch in mini_batch_generator(X_large, y_large, batch_size=32):
        batch_count += 1
        if batch_count == 1:
            print(f"✓ Mini-batch generator: batch shape={X_batch.shape}")
    
    # Calculate accuracy
    y_true = np.array([0, 1, 2, 1, 0])
    y_pred = np.array([0, 1, 2, 2, 0])
    accuracy = calculate_accuracy(y_true, y_pred)
    print(f"✓ Calculate accuracy: {accuracy:.2%}")
    assert 0 <= accuracy <= 1
    
    # Confusion matrix
    cm = confusion_matrix_nn(y_true, y_pred)
    print(f"✓ Confusion matrix:\n{cm}")
    assert cm.shape == (3, 3)
    
    print("✅ All utility functions passed!")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("NEURAL NETWORK UTILITIES TEST SUITE")
    print("="*60)
    
    try:
        test_activation_functions()
        test_activation_derivatives()
        test_loss_functions()
        test_weight_initialization()
        test_layer_operations()
        test_optimization()
        test_utilities()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED SUCCESSFULLY!")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
