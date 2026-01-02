"""
Tests for gradient descent optimization module
"""

import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ilovetools.ml import (
    # Basic Gradient Descent
    gradient_descent,
    batch_gradient_descent,
    stochastic_gradient_descent,
    mini_batch_gradient_descent,
    # Advanced Optimizers
    momentum_optimizer,
    nesterov_momentum,
    adagrad_optimizer,
    rmsprop_optimizer,
    adam_optimizer,
    adamw_optimizer,
    nadam_optimizer,
    adadelta_optimizer,
    # Learning Rate Schedules
    step_decay_schedule,
    exponential_decay_schedule,
    cosine_annealing_schedule,
    linear_warmup_schedule,
    polynomial_decay_schedule,
    # Utilities
    compute_gradient,
    gradient_clipping,
    check_convergence,
    line_search,
    compute_learning_rate,
)


def test_gradient_descent():
    """Test basic gradient descent"""
    print("Testing gradient_descent...")
    params = np.array([1.0, 2.0, 3.0])
    gradient = np.array([0.1, 0.2, 0.3])
    new_params = gradient_descent(params, gradient, learning_rate=0.1)
    
    expected = np.array([0.99, 1.98, 2.97])
    assert np.allclose(new_params, expected), f"Expected {expected}, got {new_params}"
    print("✓ gradient_descent passed")


def test_momentum_optimizer():
    """Test momentum optimizer"""
    print("Testing momentum_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    gradient = np.array([0.1, 0.2, 0.3])
    velocity = np.zeros(3)
    
    new_params, new_velocity = momentum_optimizer(
        params, gradient, velocity, learning_rate=0.1, momentum=0.9
    )
    
    assert new_params.shape == params.shape
    assert new_velocity.shape == velocity.shape
    assert not np.allclose(new_params, params)  # Should have changed
    print("✓ momentum_optimizer passed")


def test_adam_optimizer():
    """Test Adam optimizer"""
    print("Testing adam_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    gradient = np.array([0.1, 0.2, 0.3])
    m = np.zeros(3)
    v = np.zeros(3)
    
    new_params, new_m, new_v = adam_optimizer(
        params, gradient, m, v, t=1, learning_rate=0.001
    )
    
    assert new_params.shape == params.shape
    assert new_m.shape == m.shape
    assert new_v.shape == v.shape
    assert not np.allclose(new_params, params)
    print("✓ adam_optimizer passed")


def test_adamw_optimizer():
    """Test AdamW optimizer"""
    print("Testing adamw_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    gradient = np.array([0.1, 0.2, 0.3])
    m = np.zeros(3)
    v = np.zeros(3)
    
    new_params, new_m, new_v = adamw_optimizer(
        params, gradient, m, v, t=1, weight_decay=0.01
    )
    
    assert new_params.shape == params.shape
    assert not np.allclose(new_params, params)
    print("✓ adamw_optimizer passed")


def test_nadam_optimizer():
    """Test Nadam optimizer"""
    print("Testing nadam_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    gradient = np.array([0.1, 0.2, 0.3])
    m = np.zeros(3)
    v = np.zeros(3)
    
    new_params, new_m, new_v = nadam_optimizer(
        params, gradient, m, v, t=1
    )
    
    assert new_params.shape == params.shape
    print("✓ nadam_optimizer passed")


def test_rmsprop_optimizer():
    """Test RMSProp optimizer"""
    print("Testing rmsprop_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    gradient = np.array([0.1, 0.2, 0.3])
    squared_grad = np.zeros(3)
    
    new_params, new_sq = rmsprop_optimizer(
        params, gradient, squared_grad, learning_rate=0.001
    )
    
    assert new_params.shape == params.shape
    assert new_sq.shape == squared_grad.shape
    print("✓ rmsprop_optimizer passed")


def test_adagrad_optimizer():
    """Test AdaGrad optimizer"""
    print("Testing adagrad_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    gradient = np.array([0.1, 0.2, 0.3])
    acc_grad = np.zeros(3)
    
    new_params, new_acc = adagrad_optimizer(
        params, gradient, acc_grad, learning_rate=0.1
    )
    
    assert new_params.shape == params.shape
    assert new_acc.shape == acc_grad.shape
    print("✓ adagrad_optimizer passed")


def test_adadelta_optimizer():
    """Test AdaDelta optimizer"""
    print("Testing adadelta_optimizer...")
    params = np.array([1.0, 2.0, 3.0])
    gradient = np.array([0.1, 0.2, 0.3])
    acc_grad = np.zeros(3)
    acc_update = np.zeros(3)
    
    new_params, new_grad, new_update = adadelta_optimizer(
        params, gradient, acc_grad, acc_update
    )
    
    assert new_params.shape == params.shape
    print("✓ adadelta_optimizer passed")


def test_nesterov_momentum():
    """Test Nesterov momentum"""
    print("Testing nesterov_momentum...")
    params = np.array([1.0, 2.0, 3.0])
    gradient = np.array([0.1, 0.2, 0.3])
    velocity = np.zeros(3)
    
    new_params, new_velocity = nesterov_momentum(
        params, gradient, velocity, learning_rate=0.1
    )
    
    assert new_params.shape == params.shape
    assert new_velocity.shape == velocity.shape
    print("✓ nesterov_momentum passed")


def test_step_decay_schedule():
    """Test step decay schedule"""
    print("Testing step_decay_schedule...")
    lr = step_decay_schedule(0.1, epoch=25, drop_rate=0.5, epochs_drop=10)
    expected = 0.025
    assert np.isclose(lr, expected), f"Expected {expected}, got {lr}"
    print("✓ step_decay_schedule passed")


def test_exponential_decay_schedule():
    """Test exponential decay schedule"""
    print("Testing exponential_decay_schedule...")
    lr = exponential_decay_schedule(0.1, epoch=10, decay_rate=0.95)
    assert 0 < lr < 0.1
    print("✓ exponential_decay_schedule passed")


def test_cosine_annealing_schedule():
    """Test cosine annealing schedule"""
    print("Testing cosine_annealing_schedule...")
    lr = cosine_annealing_schedule(0.1, epoch=50, total_epochs=100)
    expected = 0.05
    assert np.isclose(lr, expected), f"Expected {expected}, got {lr}"
    print("✓ cosine_annealing_schedule passed")


def test_linear_warmup_schedule():
    """Test linear warmup schedule"""
    print("Testing linear_warmup_schedule...")
    lr = linear_warmup_schedule(0.1, epoch=5, warmup_epochs=10)
    expected = 0.05
    assert np.isclose(lr, expected), f"Expected {expected}, got {lr}"
    print("✓ linear_warmup_schedule passed")


def test_polynomial_decay_schedule():
    """Test polynomial decay schedule"""
    print("Testing polynomial_decay_schedule...")
    lr = polynomial_decay_schedule(0.1, epoch=50, total_epochs=100, power=2.0)
    assert 0 < lr < 0.1
    print("✓ polynomial_decay_schedule passed")


def test_gradient_clipping():
    """Test gradient clipping"""
    print("Testing gradient_clipping...")
    gradient = np.array([10.0, 20.0, 30.0])
    clipped = gradient_clipping(gradient, max_norm=1.0)
    
    norm = np.linalg.norm(clipped)
    assert np.isclose(norm, 1.0), f"Expected norm 1.0, got {norm}"
    print("✓ gradient_clipping passed")


def test_check_convergence():
    """Test convergence checking"""
    print("Testing check_convergence...")
    losses = [1.0, 0.5, 0.25, 0.24, 0.24, 0.24]
    converged = check_convergence(losses, tolerance=0.01, patience=3)
    assert converged == True
    print("✓ check_convergence passed")


def test_compute_gradient():
    """Test numerical gradient computation"""
    print("Testing compute_gradient...")
    
    def loss(p):
        return np.sum(p ** 2)
    
    params = np.array([1.0, 2.0, 3.0])
    grad = compute_gradient(loss, params)
    expected = 2 * params
    
    assert np.allclose(grad, expected, atol=1e-5), f"Expected {expected}, got {grad}"
    print("✓ compute_gradient passed")


def test_compute_learning_rate():
    """Test compute learning rate with different schedules"""
    print("Testing compute_learning_rate...")
    
    # Constant
    lr = compute_learning_rate(0.1, epoch=10, schedule='constant')
    assert lr == 0.1
    
    # Exponential
    lr = compute_learning_rate(0.1, epoch=10, schedule='exponential', decay_rate=0.95)
    assert 0 < lr < 0.1
    
    print("✓ compute_learning_rate passed")


def test_batch_gradient_descent():
    """Test batch gradient descent"""
    print("Testing batch_gradient_descent...")
    
    # Simple linear regression problem
    np.random.seed(42)
    X = np.random.randn(100, 5)
    true_params = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = X @ true_params + np.random.randn(100) * 0.1
    
    params = np.zeros(5)
    
    def grad_fn(p, X, y):
        pred = X @ p
        return X.T @ (pred - y) / len(y)
    
    final_params, losses = batch_gradient_descent(
        params, X, y, grad_fn, learning_rate=0.01, epochs=50
    )
    
    assert len(losses) == 50
    assert losses[-1] < losses[0]  # Loss should decrease
    print("✓ batch_gradient_descent passed")


def test_mini_batch_gradient_descent():
    """Test mini-batch gradient descent"""
    print("Testing mini_batch_gradient_descent...")
    
    np.random.seed(42)
    X = np.random.randn(100, 5)
    true_params = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = X @ true_params + np.random.randn(100) * 0.1
    
    params = np.zeros(5)
    
    def grad_fn(p, X_batch, y_batch):
        pred = X_batch @ p
        return X_batch.T @ (pred - y_batch) / len(y_batch)
    
    final_params, losses = mini_batch_gradient_descent(
        params, X, y, grad_fn, batch_size=32, epochs=50
    )
    
    assert len(losses) == 50
    assert losses[-1] < losses[0]
    print("✓ mini_batch_gradient_descent passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("GRADIENT DESCENT MODULE TESTS")
    print("="*60 + "\n")
    
    test_gradient_descent()
    test_momentum_optimizer()
    test_adam_optimizer()
    test_adamw_optimizer()
    test_nadam_optimizer()
    test_rmsprop_optimizer()
    test_adagrad_optimizer()
    test_adadelta_optimizer()
    test_nesterov_momentum()
    test_step_decay_schedule()
    test_exponential_decay_schedule()
    test_cosine_annealing_schedule()
    test_linear_warmup_schedule()
    test_polynomial_decay_schedule()
    test_gradient_clipping()
    test_check_convergence()
    test_compute_gradient()
    test_compute_learning_rate()
    test_batch_gradient_descent()
    test_mini_batch_gradient_descent()
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
