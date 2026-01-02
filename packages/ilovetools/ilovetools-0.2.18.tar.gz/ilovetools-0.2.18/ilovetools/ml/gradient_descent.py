"""
Gradient Descent Optimization Algorithms
Comprehensive implementation of gradient descent variants and optimizers
"""

import numpy as np
from typing import Tuple, Dict, Optional, Callable, List

__all__ = [
    # Basic Gradient Descent
    'gradient_descent',
    'batch_gradient_descent',
    'stochastic_gradient_descent',
    'mini_batch_gradient_descent',
    
    # Advanced Optimizers
    'momentum_optimizer',
    'nesterov_momentum',
    'adagrad_optimizer',
    'rmsprop_optimizer',
    'adam_optimizer',
    'adamw_optimizer',
    'nadam_optimizer',
    'adadelta_optimizer',
    
    # Learning Rate Schedules
    'step_decay_schedule',
    'exponential_decay_schedule',
    'cosine_annealing_schedule',
    'linear_warmup_schedule',
    'polynomial_decay_schedule',
    
    # Utilities
    'compute_gradient',
    'gradient_clipping',
    'check_convergence',
    'line_search',
    'compute_learning_rate',
]


def gradient_descent(
    params: np.ndarray,
    gradient: np.ndarray,
    learning_rate: float = 0.01
) -> np.ndarray:
    """
    Basic gradient descent update.
    
    Args:
        params: Current parameters
        gradient: Gradient of loss w.r.t. parameters
        learning_rate: Step size
    
    Returns:
        Updated parameters
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import gradient_descent
        
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> gradient = np.array([0.1, 0.2, 0.3])
        >>> new_params = gradient_descent(params, gradient, learning_rate=0.1)
        >>> print(new_params)
        [0.99 1.98 2.97]
    """
    return params - learning_rate * gradient


def batch_gradient_descent(
    params: np.ndarray,
    X: np.ndarray,
    y: np.ndarray,
    gradient_fn: Callable,
    learning_rate: float = 0.01,
    epochs: int = 100
) -> Tuple[np.ndarray, List[float]]:
    """
    Batch gradient descent using entire dataset.
    
    Args:
        params: Initial parameters
        X: Feature matrix
        y: Target values
        gradient_fn: Function to compute gradients
        learning_rate: Step size
        epochs: Number of iterations
    
    Returns:
        Tuple of (final parameters, loss history)
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import batch_gradient_descent
        
        >>> X = np.random.randn(100, 5)
        >>> y = np.random.randn(100)
        >>> params = np.zeros(5)
        >>> 
        >>> def grad_fn(p, X, y):
        ...     pred = X @ p
        ...     return X.T @ (pred - y) / len(y)
        >>> 
        >>> final_params, losses = batch_gradient_descent(
        ...     params, X, y, grad_fn, learning_rate=0.01, epochs=50
        ... )
    """
    loss_history = []
    
    for epoch in range(epochs):
        gradient = gradient_fn(params, X, y)
        params = params - learning_rate * gradient
        
        # Compute loss for tracking
        predictions = X @ params
        loss = np.mean((predictions - y) ** 2)
        loss_history.append(loss)
    
    return params, loss_history


def stochastic_gradient_descent(
    params: np.ndarray,
    X: np.ndarray,
    y: np.ndarray,
    gradient_fn: Callable,
    learning_rate: float = 0.01,
    epochs: int = 100,
    shuffle: bool = True
) -> Tuple[np.ndarray, List[float]]:
    """
    Stochastic gradient descent using one sample at a time.
    
    Args:
        params: Initial parameters
        X: Feature matrix
        y: Target values
        gradient_fn: Function to compute gradients
        learning_rate: Step size
        epochs: Number of iterations
        shuffle: Whether to shuffle data each epoch
    
    Returns:
        Tuple of (final parameters, loss history)
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import stochastic_gradient_descent
        
        >>> X = np.random.randn(100, 5)
        >>> y = np.random.randn(100)
        >>> params = np.zeros(5)
        >>> 
        >>> def grad_fn(p, x, y_val):
        ...     pred = x @ p
        ...     return x * (pred - y_val)
        >>> 
        >>> final_params, losses = stochastic_gradient_descent(
        ...     params, X, y, grad_fn, learning_rate=0.01, epochs=10
        ... )
    """
    n_samples = len(X)
    loss_history = []
    
    for epoch in range(epochs):
        if shuffle:
            indices = np.random.permutation(n_samples)
            X_shuffled = X[indices]
            y_shuffled = y[indices]
        else:
            X_shuffled = X
            y_shuffled = y
        
        epoch_loss = 0
        for i in range(n_samples):
            gradient = gradient_fn(params, X_shuffled[i], y_shuffled[i])
            params = params - learning_rate * gradient
            
            # Track loss
            pred = X_shuffled[i] @ params
            epoch_loss += (pred - y_shuffled[i]) ** 2
        
        loss_history.append(epoch_loss / n_samples)
    
    return params, loss_history


def mini_batch_gradient_descent(
    params: np.ndarray,
    X: np.ndarray,
    y: np.ndarray,
    gradient_fn: Callable,
    learning_rate: float = 0.01,
    batch_size: int = 32,
    epochs: int = 100,
    shuffle: bool = True
) -> Tuple[np.ndarray, List[float]]:
    """
    Mini-batch gradient descent.
    
    Args:
        params: Initial parameters
        X: Feature matrix
        y: Target values
        gradient_fn: Function to compute gradients
        learning_rate: Step size
        batch_size: Number of samples per batch
        epochs: Number of iterations
        shuffle: Whether to shuffle data each epoch
    
    Returns:
        Tuple of (final parameters, loss history)
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import mini_batch_gradient_descent
        
        >>> X = np.random.randn(100, 5)
        >>> y = np.random.randn(100)
        >>> params = np.zeros(5)
        >>> 
        >>> def grad_fn(p, X_batch, y_batch):
        ...     pred = X_batch @ p
        ...     return X_batch.T @ (pred - y_batch) / len(y_batch)
        >>> 
        >>> final_params, losses = mini_batch_gradient_descent(
        ...     params, X, y, grad_fn, batch_size=32, epochs=50
        ... )
    """
    n_samples = len(X)
    loss_history = []
    
    for epoch in range(epochs):
        if shuffle:
            indices = np.random.permutation(n_samples)
            X_shuffled = X[indices]
            y_shuffled = y[indices]
        else:
            X_shuffled = X
            y_shuffled = y
        
        epoch_loss = 0
        n_batches = 0
        
        for i in range(0, n_samples, batch_size):
            X_batch = X_shuffled[i:i+batch_size]
            y_batch = y_shuffled[i:i+batch_size]
            
            gradient = gradient_fn(params, X_batch, y_batch)
            params = params - learning_rate * gradient
            
            # Track loss
            pred = X_batch @ params
            epoch_loss += np.sum((pred - y_batch) ** 2)
            n_batches += 1
        
        loss_history.append(epoch_loss / n_samples)
    
    return params, loss_history


def momentum_optimizer(
    params: np.ndarray,
    gradient: np.ndarray,
    velocity: np.ndarray,
    learning_rate: float = 0.01,
    momentum: float = 0.9
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Momentum optimizer.
    
    Args:
        params: Current parameters
        gradient: Gradient of loss
        velocity: Current velocity
        learning_rate: Step size
        momentum: Momentum coefficient (typically 0.9)
    
    Returns:
        Tuple of (updated parameters, updated velocity)
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import momentum_optimizer
        
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> gradient = np.array([0.1, 0.2, 0.3])
        >>> velocity = np.zeros(3)
        >>> 
        >>> new_params, new_velocity = momentum_optimizer(
        ...     params, gradient, velocity, learning_rate=0.1, momentum=0.9
        ... )
    """
    velocity = momentum * velocity + learning_rate * gradient
    params = params - velocity
    return params, velocity


def nesterov_momentum(
    params: np.ndarray,
    gradient: np.ndarray,
    velocity: np.ndarray,
    learning_rate: float = 0.01,
    momentum: float = 0.9
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Nesterov accelerated gradient (look-ahead momentum).
    
    Args:
        params: Current parameters
        gradient: Gradient at look-ahead position
        velocity: Current velocity
        learning_rate: Step size
        momentum: Momentum coefficient
    
    Returns:
        Tuple of (updated parameters, updated velocity)
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import nesterov_momentum
        
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> gradient = np.array([0.1, 0.2, 0.3])
        >>> velocity = np.zeros(3)
        >>> 
        >>> new_params, new_velocity = nesterov_momentum(
        ...     params, gradient, velocity, learning_rate=0.1
        ... )
    """
    velocity_prev = velocity.copy()
    velocity = momentum * velocity + learning_rate * gradient
    params = params - momentum * velocity_prev - (1 + momentum) * velocity
    return params, velocity


def adagrad_optimizer(
    params: np.ndarray,
    gradient: np.ndarray,
    accumulated_grad: np.ndarray,
    learning_rate: float = 0.01,
    epsilon: float = 1e-8
) -> Tuple[np.ndarray, np.ndarray]:
    """
    AdaGrad optimizer with adaptive learning rates.
    
    Args:
        params: Current parameters
        gradient: Gradient of loss
        accumulated_grad: Accumulated squared gradients
        learning_rate: Initial learning rate
        epsilon: Small constant for numerical stability
    
    Returns:
        Tuple of (updated parameters, updated accumulated gradients)
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import adagrad_optimizer
        
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> gradient = np.array([0.1, 0.2, 0.3])
        >>> acc_grad = np.zeros(3)
        >>> 
        >>> new_params, new_acc = adagrad_optimizer(
        ...     params, gradient, acc_grad, learning_rate=0.1
        ... )
    """
    accumulated_grad += gradient ** 2
    params = params - learning_rate * gradient / (np.sqrt(accumulated_grad) + epsilon)
    return params, accumulated_grad


def rmsprop_optimizer(
    params: np.ndarray,
    gradient: np.ndarray,
    squared_grad: np.ndarray,
    learning_rate: float = 0.001,
    decay_rate: float = 0.9,
    epsilon: float = 1e-8
) -> Tuple[np.ndarray, np.ndarray]:
    """
    RMSProp optimizer.
    
    Args:
        params: Current parameters
        gradient: Gradient of loss
        squared_grad: Exponential moving average of squared gradients
        learning_rate: Step size
        decay_rate: Decay rate for moving average (typically 0.9)
        epsilon: Small constant for numerical stability
    
    Returns:
        Tuple of (updated parameters, updated squared gradients)
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import rmsprop_optimizer
        
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> gradient = np.array([0.1, 0.2, 0.3])
        >>> sq_grad = np.zeros(3)
        >>> 
        >>> new_params, new_sq = rmsprop_optimizer(
        ...     params, gradient, sq_grad, learning_rate=0.001
        ... )
    """
    squared_grad = decay_rate * squared_grad + (1 - decay_rate) * gradient ** 2
    params = params - learning_rate * gradient / (np.sqrt(squared_grad) + epsilon)
    return params, squared_grad


def adam_optimizer(
    params: np.ndarray,
    gradient: np.ndarray,
    m: np.ndarray,
    v: np.ndarray,
    t: int,
    learning_rate: float = 0.001,
    beta1: float = 0.9,
    beta2: float = 0.999,
    epsilon: float = 1e-8
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Adam (Adaptive Moment Estimation) optimizer.
    
    Args:
        params: Current parameters
        gradient: Gradient of loss
        m: First moment estimate (mean)
        v: Second moment estimate (variance)
        t: Time step (iteration number)
        learning_rate: Step size
        beta1: Exponential decay rate for first moment (typically 0.9)
        beta2: Exponential decay rate for second moment (typically 0.999)
        epsilon: Small constant for numerical stability
    
    Returns:
        Tuple of (updated parameters, updated m, updated v)
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import adam_optimizer
        
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> gradient = np.array([0.1, 0.2, 0.3])
        >>> m = np.zeros(3)
        >>> v = np.zeros(3)
        >>> 
        >>> new_params, new_m, new_v = adam_optimizer(
        ...     params, gradient, m, v, t=1, learning_rate=0.001
        ... )
    """
    # Update biased first moment estimate
    m = beta1 * m + (1 - beta1) * gradient
    
    # Update biased second moment estimate
    v = beta2 * v + (1 - beta2) * gradient ** 2
    
    # Bias correction
    m_hat = m / (1 - beta1 ** t)
    v_hat = v / (1 - beta2 ** t)
    
    # Update parameters
    params = params - learning_rate * m_hat / (np.sqrt(v_hat) + epsilon)
    
    return params, m, v


def adamw_optimizer(
    params: np.ndarray,
    gradient: np.ndarray,
    m: np.ndarray,
    v: np.ndarray,
    t: int,
    learning_rate: float = 0.001,
    beta1: float = 0.9,
    beta2: float = 0.999,
    epsilon: float = 1e-8,
    weight_decay: float = 0.01
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    AdamW optimizer (Adam with decoupled weight decay).
    
    Args:
        params: Current parameters
        gradient: Gradient of loss
        m: First moment estimate
        v: Second moment estimate
        t: Time step
        learning_rate: Step size
        beta1: Exponential decay rate for first moment
        beta2: Exponential decay rate for second moment
        epsilon: Small constant for numerical stability
        weight_decay: Weight decay coefficient
    
    Returns:
        Tuple of (updated parameters, updated m, updated v)
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import adamw_optimizer
        
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> gradient = np.array([0.1, 0.2, 0.3])
        >>> m = np.zeros(3)
        >>> v = np.zeros(3)
        >>> 
        >>> new_params, new_m, new_v = adamw_optimizer(
        ...     params, gradient, m, v, t=1, weight_decay=0.01
        ... )
    """
    # Update biased first moment estimate
    m = beta1 * m + (1 - beta1) * gradient
    
    # Update biased second moment estimate
    v = beta2 * v + (1 - beta2) * gradient ** 2
    
    # Bias correction
    m_hat = m / (1 - beta1 ** t)
    v_hat = v / (1 - beta2 ** t)
    
    # Update parameters with decoupled weight decay
    params = params - learning_rate * (m_hat / (np.sqrt(v_hat) + epsilon) + weight_decay * params)
    
    return params, m, v


def nadam_optimizer(
    params: np.ndarray,
    gradient: np.ndarray,
    m: np.ndarray,
    v: np.ndarray,
    t: int,
    learning_rate: float = 0.001,
    beta1: float = 0.9,
    beta2: float = 0.999,
    epsilon: float = 1e-8
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Nadam optimizer (Nesterov-accelerated Adam).
    
    Args:
        params: Current parameters
        gradient: Gradient of loss
        m: First moment estimate
        v: Second moment estimate
        t: Time step
        learning_rate: Step size
        beta1: Exponential decay rate for first moment
        beta2: Exponential decay rate for second moment
        epsilon: Small constant for numerical stability
    
    Returns:
        Tuple of (updated parameters, updated m, updated v)
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import nadam_optimizer
        
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> gradient = np.array([0.1, 0.2, 0.3])
        >>> m = np.zeros(3)
        >>> v = np.zeros(3)
        >>> 
        >>> new_params, new_m, new_v = nadam_optimizer(
        ...     params, gradient, m, v, t=1
        ... )
    """
    # Update biased first moment estimate
    m = beta1 * m + (1 - beta1) * gradient
    
    # Update biased second moment estimate
    v = beta2 * v + (1 - beta2) * gradient ** 2
    
    # Bias correction
    m_hat = m / (1 - beta1 ** t)
    v_hat = v / (1 - beta2 ** t)
    
    # Nesterov momentum
    m_nesterov = beta1 * m_hat + (1 - beta1) * gradient / (1 - beta1 ** t)
    
    # Update parameters
    params = params - learning_rate * m_nesterov / (np.sqrt(v_hat) + epsilon)
    
    return params, m, v


def adadelta_optimizer(
    params: np.ndarray,
    gradient: np.ndarray,
    accumulated_grad: np.ndarray,
    accumulated_update: np.ndarray,
    decay_rate: float = 0.9,
    epsilon: float = 1e-8
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    AdaDelta optimizer (no learning rate required).
    
    Args:
        params: Current parameters
        gradient: Gradient of loss
        accumulated_grad: Accumulated squared gradients
        accumulated_update: Accumulated squared updates
        decay_rate: Decay rate for moving averages
        epsilon: Small constant for numerical stability
    
    Returns:
        Tuple of (updated parameters, updated accumulated_grad, updated accumulated_update)
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import adadelta_optimizer
        
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> gradient = np.array([0.1, 0.2, 0.3])
        >>> acc_grad = np.zeros(3)
        >>> acc_update = np.zeros(3)
        >>> 
        >>> new_params, new_grad, new_update = adadelta_optimizer(
        ...     params, gradient, acc_grad, acc_update
        ... )
    """
    # Accumulate gradient
    accumulated_grad = decay_rate * accumulated_grad + (1 - decay_rate) * gradient ** 2
    
    # Compute update
    update = gradient * np.sqrt(accumulated_update + epsilon) / np.sqrt(accumulated_grad + epsilon)
    
    # Accumulate updates
    accumulated_update = decay_rate * accumulated_update + (1 - decay_rate) * update ** 2
    
    # Update parameters
    params = params - update
    
    return params, accumulated_grad, accumulated_update


def step_decay_schedule(
    initial_lr: float,
    epoch: int,
    drop_rate: float = 0.5,
    epochs_drop: int = 10
) -> float:
    """
    Step decay learning rate schedule.
    
    Args:
        initial_lr: Initial learning rate
        epoch: Current epoch number
        drop_rate: Factor to multiply learning rate by
        epochs_drop: Number of epochs before dropping
    
    Returns:
        Current learning rate
    
    Examples:
        >>> from ilovetools.ml import step_decay_schedule
        
        >>> lr = step_decay_schedule(0.1, epoch=25, drop_rate=0.5, epochs_drop=10)
        >>> print(lr)
        0.025
    """
    return initial_lr * (drop_rate ** (epoch // epochs_drop))


def exponential_decay_schedule(
    initial_lr: float,
    epoch: int,
    decay_rate: float = 0.95
) -> float:
    """
    Exponential decay learning rate schedule.
    
    Args:
        initial_lr: Initial learning rate
        epoch: Current epoch number
        decay_rate: Exponential decay rate
    
    Returns:
        Current learning rate
    
    Examples:
        >>> from ilovetools.ml import exponential_decay_schedule
        
        >>> lr = exponential_decay_schedule(0.1, epoch=10, decay_rate=0.95)
        >>> print(f"{lr:.6f}")
        0.059874
    """
    return initial_lr * (decay_rate ** epoch)


def cosine_annealing_schedule(
    initial_lr: float,
    epoch: int,
    total_epochs: int,
    min_lr: float = 0.0
) -> float:
    """
    Cosine annealing learning rate schedule.
    
    Args:
        initial_lr: Initial learning rate
        epoch: Current epoch number
        total_epochs: Total number of epochs
        min_lr: Minimum learning rate
    
    Returns:
        Current learning rate
    
    Examples:
        >>> from ilovetools.ml import cosine_annealing_schedule
        
        >>> lr = cosine_annealing_schedule(0.1, epoch=50, total_epochs=100)
        >>> print(f"{lr:.6f}")
        0.050000
    """
    return min_lr + (initial_lr - min_lr) * (1 + np.cos(np.pi * epoch / total_epochs)) / 2


def linear_warmup_schedule(
    target_lr: float,
    epoch: int,
    warmup_epochs: int
) -> float:
    """
    Linear warmup learning rate schedule.
    
    Args:
        target_lr: Target learning rate after warmup
        epoch: Current epoch number
        warmup_epochs: Number of warmup epochs
    
    Returns:
        Current learning rate
    
    Examples:
        >>> from ilovetools.ml import linear_warmup_schedule
        
        >>> lr = linear_warmup_schedule(0.1, epoch=5, warmup_epochs=10)
        >>> print(lr)
        0.05
    """
    if epoch >= warmup_epochs:
        return target_lr
    return target_lr * (epoch + 1) / warmup_epochs


def polynomial_decay_schedule(
    initial_lr: float,
    epoch: int,
    total_epochs: int,
    end_lr: float = 0.0001,
    power: float = 1.0
) -> float:
    """
    Polynomial decay learning rate schedule.
    
    Args:
        initial_lr: Initial learning rate
        epoch: Current epoch number
        total_epochs: Total number of epochs
        end_lr: Final learning rate
        power: Polynomial power
    
    Returns:
        Current learning rate
    
    Examples:
        >>> from ilovetools.ml import polynomial_decay_schedule
        
        >>> lr = polynomial_decay_schedule(0.1, epoch=50, total_epochs=100, power=2.0)
        >>> print(f"{lr:.6f}")
        0.025025
    """
    if epoch >= total_epochs:
        return end_lr
    return (initial_lr - end_lr) * ((1 - epoch / total_epochs) ** power) + end_lr


def compute_gradient(
    loss_fn: Callable,
    params: np.ndarray,
    *args,
    epsilon: float = 1e-7
) -> np.ndarray:
    """
    Compute numerical gradient using finite differences.
    
    Args:
        loss_fn: Loss function
        params: Parameters to compute gradient for
        *args: Additional arguments to loss function
        epsilon: Small perturbation for finite differences
    
    Returns:
        Gradient vector
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import compute_gradient
        
        >>> def loss(p):
        ...     return np.sum(p ** 2)
        >>> 
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> grad = compute_gradient(loss, params)
        >>> print(grad)
        [2. 4. 6.]
    """
    gradient = np.zeros_like(params)
    
    for i in range(len(params)):
        params_plus = params.copy()
        params_plus[i] += epsilon
        
        params_minus = params.copy()
        params_minus[i] -= epsilon
        
        gradient[i] = (loss_fn(params_plus, *args) - loss_fn(params_minus, *args)) / (2 * epsilon)
    
    return gradient


def gradient_clipping(
    gradient: np.ndarray,
    max_norm: float = 1.0
) -> np.ndarray:
    """
    Clip gradient by norm to prevent exploding gradients.
    
    Args:
        gradient: Gradient to clip
        max_norm: Maximum allowed norm
    
    Returns:
        Clipped gradient
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import gradient_clipping
        
        >>> gradient = np.array([10.0, 20.0, 30.0])
        >>> clipped = gradient_clipping(gradient, max_norm=1.0)
        >>> print(np.linalg.norm(clipped))
        1.0
    """
    norm = np.linalg.norm(gradient)
    if norm > max_norm:
        return gradient * max_norm / norm
    return gradient


def check_convergence(
    loss_history: List[float],
    tolerance: float = 1e-6,
    patience: int = 10
) -> bool:
    """
    Check if optimization has converged.
    
    Args:
        loss_history: History of loss values
        tolerance: Minimum change in loss to consider convergence
        patience: Number of epochs to wait for improvement
    
    Returns:
        True if converged, False otherwise
    
    Examples:
        >>> from ilovetools.ml import check_convergence
        
        >>> losses = [1.0, 0.5, 0.25, 0.24, 0.24, 0.24]
        >>> converged = check_convergence(losses, tolerance=0.01, patience=3)
        >>> print(converged)
        True
    """
    if len(loss_history) < patience + 1:
        return False
    
    recent_losses = loss_history[-patience-1:]
    changes = [abs(recent_losses[i] - recent_losses[i+1]) for i in range(len(recent_losses)-1)]
    
    return all(change < tolerance for change in changes)


def line_search(
    params: np.ndarray,
    gradient: np.ndarray,
    loss_fn: Callable,
    initial_lr: float = 1.0,
    c: float = 0.5,
    tau: float = 0.5,
    max_iter: int = 20
) -> float:
    """
    Backtracking line search to find optimal learning rate.
    
    Args:
        params: Current parameters
        gradient: Gradient direction
        loss_fn: Loss function
        initial_lr: Initial learning rate to try
        c: Armijo condition constant
        tau: Backtracking factor
        max_iter: Maximum iterations
    
    Returns:
        Optimal learning rate
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import line_search
        
        >>> def loss(p):
        ...     return np.sum(p ** 2)
        >>> 
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> gradient = 2 * params
        >>> lr = line_search(params, gradient, loss)
    """
    lr = initial_lr
    current_loss = loss_fn(params)
    
    for _ in range(max_iter):
        new_params = params - lr * gradient
        new_loss = loss_fn(new_params)
        
        # Armijo condition
        if new_loss <= current_loss - c * lr * np.dot(gradient, gradient):
            return lr
        
        lr *= tau
    
    return lr


def compute_learning_rate(
    initial_lr: float,
    epoch: int,
    schedule: str = 'constant',
    **kwargs
) -> float:
    """
    Compute learning rate based on schedule.
    
    Args:
        initial_lr: Initial learning rate
        epoch: Current epoch
        schedule: Schedule type ('constant', 'step', 'exponential', 'cosine', 'warmup', 'polynomial')
        **kwargs: Additional arguments for specific schedules
    
    Returns:
        Current learning rate
    
    Examples:
        >>> from ilovetools.ml import compute_learning_rate
        
        >>> lr = compute_learning_rate(0.1, epoch=10, schedule='exponential', decay_rate=0.95)
        >>> print(f"{lr:.6f}")
        0.059874
    """
    if schedule == 'constant':
        return initial_lr
    elif schedule == 'step':
        return step_decay_schedule(initial_lr, epoch, **kwargs)
    elif schedule == 'exponential':
        return exponential_decay_schedule(initial_lr, epoch, **kwargs)
    elif schedule == 'cosine':
        return cosine_annealing_schedule(initial_lr, epoch, **kwargs)
    elif schedule == 'warmup':
        return linear_warmup_schedule(initial_lr, epoch, **kwargs)
    elif schedule == 'polynomial':
        return polynomial_decay_schedule(initial_lr, epoch, **kwargs)
    else:
        raise ValueError(f"Unknown schedule: {schedule}")
