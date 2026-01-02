"""
Neural Network Utilities
Helper functions for building, training, and analyzing neural networks
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional, Callable

__all__ = [
    # Activation Functions
    'sigmoid',
    'relu',
    'leaky_relu',
    'tanh',
    'softmax',
    'elu',
    'swish',
    
    # Activation Derivatives
    'sigmoid_derivative',
    'relu_derivative',
    'tanh_derivative',
    
    # Loss Functions
    'mse_loss',
    'binary_crossentropy',
    'categorical_crossentropy',
    'huber_loss',
    
    # Weight Initialization
    'xavier_init',
    'he_init',
    'random_init',
    'zeros_init',
    'ones_init',
    
    # Layer Operations
    'dense_forward',
    'dense_backward',
    'dropout_forward',
    'batch_norm_forward',
    
    # Optimization
    'sgd_update',
    'momentum_update',
    'adam_update',
    'rmsprop_update',
    
    # Utilities
    'one_hot_encode',
    'shuffle_data',
    'mini_batch_generator',
    'calculate_accuracy',
    'confusion_matrix_nn',
]


# ============================================================================
# ACTIVATION FUNCTIONS
# ============================================================================

def sigmoid(x: np.ndarray) -> np.ndarray:
    """
    Sigmoid activation function.
    
    Args:
        x: Input array
    
    Returns:
        np.ndarray: Sigmoid output (0 to 1)
    
    Examples:
        >>> from ilovetools.ml import sigmoid
        >>> import numpy as np
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = sigmoid(x)
        >>> print(output)
        [0.119 0.268 0.5 0.731 0.880]
    """
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))


def relu(x: np.ndarray) -> np.ndarray:
    """
    ReLU (Rectified Linear Unit) activation function.
    
    Args:
        x: Input array
    
    Returns:
        np.ndarray: ReLU output (max(0, x))
    
    Examples:
        >>> from ilovetools.ml import relu
        >>> import numpy as np
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = relu(x)
        >>> print(output)
        [0 0 0 1 2]
    """
    return np.maximum(0, x)


def leaky_relu(x: np.ndarray, alpha: float = 0.01) -> np.ndarray:
    """
    Leaky ReLU activation function.
    
    Args:
        x: Input array
        alpha: Slope for negative values
    
    Returns:
        np.ndarray: Leaky ReLU output
    
    Examples:
        >>> from ilovetools.ml import leaky_relu
        >>> import numpy as np
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = leaky_relu(x, alpha=0.1)
        >>> print(output)
        [-0.2 -0.1 0 1 2]
    """
    return np.where(x > 0, x, alpha * x)


def tanh(x: np.ndarray) -> np.ndarray:
    """
    Hyperbolic tangent activation function.
    
    Args:
        x: Input array
    
    Returns:
        np.ndarray: Tanh output (-1 to 1)
    
    Examples:
        >>> from ilovetools.ml import tanh
        >>> import numpy as np
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = tanh(x)
        >>> print(output)
        [-0.964 -0.761 0 0.761 0.964]
    """
    return np.tanh(x)


def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    """
    Softmax activation function.
    
    Args:
        x: Input array
        axis: Axis along which to compute softmax
    
    Returns:
        np.ndarray: Softmax output (probabilities sum to 1)
    
    Examples:
        >>> from ilovetools.ml import softmax
        >>> import numpy as np
        
        >>> x = np.array([1.0, 2.0, 3.0])
        >>> output = softmax(x)
        >>> print(output)
        [0.090 0.244 0.665]
        >>> print(output.sum())
        1.0
    """
    exp_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


def elu(x: np.ndarray, alpha: float = 1.0) -> np.ndarray:
    """
    ELU (Exponential Linear Unit) activation function.
    
    Args:
        x: Input array
        alpha: Scale for negative values
    
    Returns:
        np.ndarray: ELU output
    
    Examples:
        >>> from ilovetools.ml import elu
        >>> import numpy as np
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = elu(x)
        >>> print(output)
        [-0.865 -0.632 0 1 2]
    """
    return np.where(x > 0, x, alpha * (np.exp(x) - 1))


def swish(x: np.ndarray) -> np.ndarray:
    """
    Swish activation function (x * sigmoid(x)).
    
    Args:
        x: Input array
    
    Returns:
        np.ndarray: Swish output
    
    Examples:
        >>> from ilovetools.ml import swish
        >>> import numpy as np
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> output = swish(x)
        >>> print(output)
        [-0.238 -0.268 0 0.731 1.761]
    """
    return x * sigmoid(x)


# ============================================================================
# ACTIVATION DERIVATIVES
# ============================================================================

def sigmoid_derivative(x: np.ndarray) -> np.ndarray:
    """
    Derivative of sigmoid function.
    
    Args:
        x: Sigmoid output (not input!)
    
    Returns:
        np.ndarray: Derivative
    
    Examples:
        >>> from ilovetools.ml import sigmoid, sigmoid_derivative
        >>> import numpy as np
        
        >>> x = np.array([0, 1, 2])
        >>> sig_out = sigmoid(x)
        >>> derivative = sigmoid_derivative(sig_out)
        >>> print(derivative)
        [0.25 0.196 0.104]
    """
    return x * (1 - x)


def relu_derivative(x: np.ndarray) -> np.ndarray:
    """
    Derivative of ReLU function.
    
    Args:
        x: Input array
    
    Returns:
        np.ndarray: Derivative (0 or 1)
    
    Examples:
        >>> from ilovetools.ml import relu_derivative
        >>> import numpy as np
        
        >>> x = np.array([-2, -1, 0, 1, 2])
        >>> derivative = relu_derivative(x)
        >>> print(derivative)
        [0 0 0 1 1]
    """
    return (x > 0).astype(float)


def tanh_derivative(x: np.ndarray) -> np.ndarray:
    """
    Derivative of tanh function.
    
    Args:
        x: Tanh output (not input!)
    
    Returns:
        np.ndarray: Derivative
    
    Examples:
        >>> from ilovetools.ml import tanh, tanh_derivative
        >>> import numpy as np
        
        >>> x = np.array([0, 1, 2])
        >>> tanh_out = tanh(x)
        >>> derivative = tanh_derivative(tanh_out)
        >>> print(derivative)
        [1.0 0.419 0.070]
    """
    return 1 - x ** 2


# ============================================================================
# LOSS FUNCTIONS
# ============================================================================

def mse_loss(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Mean Squared Error loss.
    
    Args:
        y_true: True values
        y_pred: Predicted values
    
    Returns:
        float: MSE loss
    
    Examples:
        >>> from ilovetools.ml import mse_loss
        >>> import numpy as np
        
        >>> y_true = np.array([1, 2, 3, 4])
        >>> y_pred = np.array([1.1, 2.2, 2.9, 4.1])
        >>> loss = mse_loss(y_true, y_pred)
        >>> print(f"MSE: {loss:.4f}")
        MSE: 0.0175
    """
    return np.mean((y_true - y_pred) ** 2)


def binary_crossentropy(y_true: np.ndarray, y_pred: np.ndarray, epsilon: float = 1e-7) -> float:
    """
    Binary cross-entropy loss.
    
    Args:
        y_true: True labels (0 or 1)
        y_pred: Predicted probabilities
        epsilon: Small value to avoid log(0)
    
    Returns:
        float: Binary cross-entropy loss
    
    Examples:
        >>> from ilovetools.ml import binary_crossentropy
        >>> import numpy as np
        
        >>> y_true = np.array([1, 0, 1, 0])
        >>> y_pred = np.array([0.9, 0.1, 0.8, 0.2])
        >>> loss = binary_crossentropy(y_true, y_pred)
        >>> print(f"BCE: {loss:.4f}")
        BCE: 0.1625
    """
    y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
    return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))


def categorical_crossentropy(y_true: np.ndarray, y_pred: np.ndarray, epsilon: float = 1e-7) -> float:
    """
    Categorical cross-entropy loss.
    
    Args:
        y_true: True labels (one-hot encoded)
        y_pred: Predicted probabilities
        epsilon: Small value to avoid log(0)
    
    Returns:
        float: Categorical cross-entropy loss
    
    Examples:
        >>> from ilovetools.ml import categorical_crossentropy
        >>> import numpy as np
        
        >>> y_true = np.array([[1, 0, 0], [0, 1, 0]])
        >>> y_pred = np.array([[0.8, 0.1, 0.1], [0.2, 0.7, 0.1]])
        >>> loss = categorical_crossentropy(y_true, y_pred)
        >>> print(f"CCE: {loss:.4f}")
        CCE: 0.2682
    """
    y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
    return -np.mean(np.sum(y_true * np.log(y_pred), axis=-1))


def huber_loss(y_true: np.ndarray, y_pred: np.ndarray, delta: float = 1.0) -> float:
    """
    Huber loss (robust to outliers).
    
    Args:
        y_true: True values
        y_pred: Predicted values
        delta: Threshold for switching between MSE and MAE
    
    Returns:
        float: Huber loss
    
    Examples:
        >>> from ilovetools.ml import huber_loss
        >>> import numpy as np
        
        >>> y_true = np.array([1, 2, 3, 10])
        >>> y_pred = np.array([1.1, 2.2, 2.9, 4])
        >>> loss = huber_loss(y_true, y_pred, delta=1.0)
        >>> print(f"Huber: {loss:.4f}")
        Huber: 1.5088
    """
    error = y_true - y_pred
    is_small_error = np.abs(error) <= delta
    squared_loss = 0.5 * error ** 2
    linear_loss = delta * (np.abs(error) - 0.5 * delta)
    return np.mean(np.where(is_small_error, squared_loss, linear_loss))


# ============================================================================
# WEIGHT INITIALIZATION
# ============================================================================

def xavier_init(shape: Tuple[int, ...], seed: Optional[int] = None) -> np.ndarray:
    """
    Xavier/Glorot weight initialization.
    
    Args:
        shape: Shape of weight matrix (input_dim, output_dim)
        seed: Random seed
    
    Returns:
        np.ndarray: Initialized weights
    
    Examples:
        >>> from ilovetools.ml import xavier_init
        
        >>> weights = xavier_init((10, 5), seed=42)
        >>> print(weights.shape)
        (10, 5)
        >>> print(f"Mean: {weights.mean():.4f}, Std: {weights.std():.4f}")
        Mean: 0.0123, Std: 0.3142
    """
    if seed is not None:
        np.random.seed(seed)
    
    fan_in, fan_out = shape[0], shape[1] if len(shape) > 1 else shape[0]
    limit = np.sqrt(6 / (fan_in + fan_out))
    return np.random.uniform(-limit, limit, shape)


def he_init(shape: Tuple[int, ...], seed: Optional[int] = None) -> np.ndarray:
    """
    He weight initialization (good for ReLU).
    
    Args:
        shape: Shape of weight matrix
        seed: Random seed
    
    Returns:
        np.ndarray: Initialized weights
    
    Examples:
        >>> from ilovetools.ml import he_init
        
        >>> weights = he_init((10, 5), seed=42)
        >>> print(weights.shape)
        (10, 5)
        >>> print(f"Mean: {weights.mean():.4f}, Std: {weights.std():.4f}")
        Mean: -0.0234, Std: 0.4321
    """
    if seed is not None:
        np.random.seed(seed)
    
    fan_in = shape[0]
    std = np.sqrt(2 / fan_in)
    return np.random.randn(*shape) * std


def random_init(shape: Tuple[int, ...], scale: float = 0.01, seed: Optional[int] = None) -> np.ndarray:
    """
    Random weight initialization.
    
    Args:
        shape: Shape of weight matrix
        scale: Scale factor
        seed: Random seed
    
    Returns:
        np.ndarray: Initialized weights
    
    Examples:
        >>> from ilovetools.ml import random_init
        
        >>> weights = random_init((10, 5), scale=0.1, seed=42)
        >>> print(weights.shape)
        (10, 5)
    """
    if seed is not None:
        np.random.seed(seed)
    
    return np.random.randn(*shape) * scale


def zeros_init(shape: Tuple[int, ...]) -> np.ndarray:
    """
    Zero weight initialization.
    
    Args:
        shape: Shape of weight matrix
    
    Returns:
        np.ndarray: Zero weights
    
    Examples:
        >>> from ilovetools.ml import zeros_init
        
        >>> weights = zeros_init((10, 5))
        >>> print(weights.sum())
        0.0
    """
    return np.zeros(shape)


def ones_init(shape: Tuple[int, ...]) -> np.ndarray:
    """
    Ones weight initialization.
    
    Args:
        shape: Shape of weight matrix
    
    Returns:
        np.ndarray: Ones weights
    
    Examples:
        >>> from ilovetools.ml import ones_init
        
        >>> weights = ones_init((10, 5))
        >>> print(weights.sum())
        50.0
    """
    return np.ones(shape)


# ============================================================================
# LAYER OPERATIONS
# ============================================================================

def dense_forward(x: np.ndarray, weights: np.ndarray, bias: np.ndarray) -> np.ndarray:
    """
    Forward pass through dense layer.
    
    Args:
        x: Input (batch_size, input_dim)
        weights: Weight matrix (input_dim, output_dim)
        bias: Bias vector (output_dim,)
    
    Returns:
        np.ndarray: Output (batch_size, output_dim)
    
    Examples:
        >>> from ilovetools.ml import dense_forward, xavier_init, zeros_init
        >>> import numpy as np
        
        >>> x = np.random.randn(32, 10)  # 32 samples, 10 features
        >>> weights = xavier_init((10, 5))
        >>> bias = zeros_init((5,))
        >>> output = dense_forward(x, weights, bias)
        >>> print(output.shape)
        (32, 5)
    """
    return np.dot(x, weights) + bias


def dense_backward(
    dout: np.ndarray,
    x: np.ndarray,
    weights: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Backward pass through dense layer.
    
    Args:
        dout: Gradient from next layer (batch_size, output_dim)
        x: Input from forward pass (batch_size, input_dim)
        weights: Weight matrix (input_dim, output_dim)
    
    Returns:
        tuple: (dx, dweights, dbias)
    
    Examples:
        >>> from ilovetools.ml import dense_backward
        >>> import numpy as np
        
        >>> dout = np.random.randn(32, 5)
        >>> x = np.random.randn(32, 10)
        >>> weights = np.random.randn(10, 5)
        >>> dx, dw, db = dense_backward(dout, x, weights)
        >>> print(dx.shape, dw.shape, db.shape)
        (32, 10) (10, 5) (5,)
    """
    dx = np.dot(dout, weights.T)
    dweights = np.dot(x.T, dout)
    dbias = np.sum(dout, axis=0)
    return dx, dweights, dbias


def dropout_forward(x: np.ndarray, dropout_rate: float = 0.5, training: bool = True, seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Forward pass through dropout layer.
    
    Args:
        x: Input array
        dropout_rate: Fraction of neurons to drop
        training: Whether in training mode
        seed: Random seed
    
    Returns:
        tuple: (output, mask)
    
    Examples:
        >>> from ilovetools.ml import dropout_forward
        >>> import numpy as np
        
        >>> x = np.ones((32, 10))
        >>> output, mask = dropout_forward(x, dropout_rate=0.5, seed=42)
        >>> print(f"Dropped: {(mask == 0).sum()} neurons")
        Dropped: 160 neurons
    """
    if not training:
        return x, np.ones_like(x)
    
    if seed is not None:
        np.random.seed(seed)
    
    mask = (np.random.rand(*x.shape) > dropout_rate).astype(float)
    mask /= (1 - dropout_rate)  # Inverted dropout
    return x * mask, mask


def batch_norm_forward(
    x: np.ndarray,
    gamma: np.ndarray,
    beta: np.ndarray,
    epsilon: float = 1e-5
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Forward pass through batch normalization layer.
    
    Args:
        x: Input (batch_size, features)
        gamma: Scale parameter
        beta: Shift parameter
        epsilon: Small constant for numerical stability
    
    Returns:
        tuple: (output, cache)
    
    Examples:
        >>> from ilovetools.ml import batch_norm_forward
        >>> import numpy as np
        
        >>> x = np.random.randn(32, 10)
        >>> gamma = np.ones(10)
        >>> beta = np.zeros(10)
        >>> output, cache = batch_norm_forward(x, gamma, beta)
        >>> print(f"Mean: {output.mean():.4f}, Std: {output.std():.4f}")
        Mean: 0.0000, Std: 1.0000
    """
    mean = np.mean(x, axis=0)
    var = np.var(x, axis=0)
    x_norm = (x - mean) / np.sqrt(var + epsilon)
    out = gamma * x_norm + beta
    
    cache = {
        'x': x,
        'x_norm': x_norm,
        'mean': mean,
        'var': var,
        'gamma': gamma,
        'epsilon': epsilon
    }
    
    return out, cache


# ============================================================================
# OPTIMIZATION
# ============================================================================

def sgd_update(weights: np.ndarray, gradients: np.ndarray, learning_rate: float = 0.01) -> np.ndarray:
    """
    Stochastic Gradient Descent update.
    
    Args:
        weights: Current weights
        gradients: Gradients
        learning_rate: Learning rate
    
    Returns:
        np.ndarray: Updated weights
    
    Examples:
        >>> from ilovetools.ml import sgd_update
        >>> import numpy as np
        
        >>> weights = np.array([1.0, 2.0, 3.0])
        >>> gradients = np.array([0.1, 0.2, 0.3])
        >>> new_weights = sgd_update(weights, gradients, learning_rate=0.1)
        >>> print(new_weights)
        [0.99 1.98 2.97]
    """
    return weights - learning_rate * gradients


def momentum_update(
    weights: np.ndarray,
    gradients: np.ndarray,
    velocity: np.ndarray,
    learning_rate: float = 0.01,
    momentum: float = 0.9
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Momentum-based gradient descent update.
    
    Args:
        weights: Current weights
        gradients: Gradients
        velocity: Velocity from previous step
        learning_rate: Learning rate
        momentum: Momentum coefficient
    
    Returns:
        tuple: (updated_weights, new_velocity)
    
    Examples:
        >>> from ilovetools.ml import momentum_update
        >>> import numpy as np
        
        >>> weights = np.array([1.0, 2.0, 3.0])
        >>> gradients = np.array([0.1, 0.2, 0.3])
        >>> velocity = np.zeros(3)
        >>> new_weights, new_velocity = momentum_update(weights, gradients, velocity)
        >>> print(new_weights)
        [0.999 1.998 2.997]
    """
    velocity = momentum * velocity - learning_rate * gradients
    weights = weights + velocity
    return weights, velocity


def adam_update(
    weights: np.ndarray,
    gradients: np.ndarray,
    m: np.ndarray,
    v: np.ndarray,
    t: int,
    learning_rate: float = 0.001,
    beta1: float = 0.9,
    beta2: float = 0.999,
    epsilon: float = 1e-8
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Adam optimizer update.
    
    Args:
        weights: Current weights
        gradients: Gradients
        m: First moment estimate
        v: Second moment estimate
        t: Time step
        learning_rate: Learning rate
        beta1: Exponential decay rate for first moment
        beta2: Exponential decay rate for second moment
        epsilon: Small constant for numerical stability
    
    Returns:
        tuple: (updated_weights, new_m, new_v)
    
    Examples:
        >>> from ilovetools.ml import adam_update
        >>> import numpy as np
        
        >>> weights = np.array([1.0, 2.0, 3.0])
        >>> gradients = np.array([0.1, 0.2, 0.3])
        >>> m = np.zeros(3)
        >>> v = np.zeros(3)
        >>> new_weights, new_m, new_v = adam_update(weights, gradients, m, v, t=1)
        >>> print(new_weights)
        [0.999 1.999 2.999]
    """
    m = beta1 * m + (1 - beta1) * gradients
    v = beta2 * v + (1 - beta2) * (gradients ** 2)
    
    m_hat = m / (1 - beta1 ** t)
    v_hat = v / (1 - beta2 ** t)
    
    weights = weights - learning_rate * m_hat / (np.sqrt(v_hat) + epsilon)
    
    return weights, m, v


def rmsprop_update(
    weights: np.ndarray,
    gradients: np.ndarray,
    cache: np.ndarray,
    learning_rate: float = 0.001,
    decay_rate: float = 0.9,
    epsilon: float = 1e-8
) -> Tuple[np.ndarray, np.ndarray]:
    """
    RMSprop optimizer update.
    
    Args:
        weights: Current weights
        gradients: Gradients
        cache: Running average of squared gradients
        learning_rate: Learning rate
        decay_rate: Decay rate for cache
        epsilon: Small constant for numerical stability
    
    Returns:
        tuple: (updated_weights, new_cache)
    
    Examples:
        >>> from ilovetools.ml import rmsprop_update
        >>> import numpy as np
        
        >>> weights = np.array([1.0, 2.0, 3.0])
        >>> gradients = np.array([0.1, 0.2, 0.3])
        >>> cache = np.zeros(3)
        >>> new_weights, new_cache = rmsprop_update(weights, gradients, cache)
        >>> print(new_weights)
        [0.997 1.994 2.991]
    """
    cache = decay_rate * cache + (1 - decay_rate) * (gradients ** 2)
    weights = weights - learning_rate * gradients / (np.sqrt(cache) + epsilon)
    return weights, cache


# ============================================================================
# UTILITIES
# ============================================================================

def one_hot_encode(labels: np.ndarray, num_classes: Optional[int] = None) -> np.ndarray:
    """
    One-hot encode labels.
    
    Args:
        labels: Integer labels
        num_classes: Number of classes (auto-detected if None)
    
    Returns:
        np.ndarray: One-hot encoded labels
    
    Examples:
        >>> from ilovetools.ml import one_hot_encode
        >>> import numpy as np
        
        >>> labels = np.array([0, 1, 2, 1, 0])
        >>> one_hot = one_hot_encode(labels)
        >>> print(one_hot)
        [[1 0 0]
         [0 1 0]
         [0 0 1]
         [0 1 0]
         [1 0 0]]
    """
    if num_classes is None:
        num_classes = int(np.max(labels)) + 1
    
    one_hot = np.zeros((labels.size, num_classes))
    one_hot[np.arange(labels.size), labels.astype(int)] = 1
    return one_hot


def shuffle_data(X: np.ndarray, y: np.ndarray, seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Shuffle data and labels together.
    
    Args:
        X: Features
        y: Labels
        seed: Random seed
    
    Returns:
        tuple: (shuffled_X, shuffled_y)
    
    Examples:
        >>> from ilovetools.ml import shuffle_data
        >>> import numpy as np
        
        >>> X = np.array([[1, 2], [3, 4], [5, 6]])
        >>> y = np.array([0, 1, 2])
        >>> X_shuffled, y_shuffled = shuffle_data(X, y, seed=42)
        >>> print(X_shuffled)
        [[5 6]
         [1 2]
         [3 4]]
    """
    if seed is not None:
        np.random.seed(seed)
    
    indices = np.random.permutation(len(X))
    return X[indices], y[indices]


def mini_batch_generator(X: np.ndarray, y: np.ndarray, batch_size: int = 32, shuffle: bool = True, seed: Optional[int] = None):
    """
    Generate mini-batches for training.
    
    Args:
        X: Features
        y: Labels
        batch_size: Batch size
        shuffle: Whether to shuffle data
        seed: Random seed
    
    Yields:
        tuple: (X_batch, y_batch)
    
    Examples:
        >>> from ilovetools.ml import mini_batch_generator
        >>> import numpy as np
        
        >>> X = np.random.randn(100, 10)
        >>> y = np.random.randint(0, 2, 100)
        >>> 
        >>> for X_batch, y_batch in mini_batch_generator(X, y, batch_size=32):
        ...     print(f"Batch shape: {X_batch.shape}")
        ...     break
        Batch shape: (32, 10)
    """
    if shuffle:
        X, y = shuffle_data(X, y, seed=seed)
    
    n_samples = len(X)
    for i in range(0, n_samples, batch_size):
        yield X[i:i + batch_size], y[i:i + batch_size]


def calculate_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate classification accuracy.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
    
    Returns:
        float: Accuracy (0 to 1)
    
    Examples:
        >>> from ilovetools.ml import calculate_accuracy
        >>> import numpy as np
        
        >>> y_true = np.array([0, 1, 2, 1, 0])
        >>> y_pred = np.array([0, 1, 2, 2, 0])
        >>> accuracy = calculate_accuracy(y_true, y_pred)
        >>> print(f"Accuracy: {accuracy:.2%}")
        Accuracy: 80.00%
    """
    return np.mean(y_true == y_pred)


def confusion_matrix_nn(y_true: np.ndarray, y_pred: np.ndarray, num_classes: Optional[int] = None) -> np.ndarray:
    """
    Compute confusion matrix.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        num_classes: Number of classes
    
    Returns:
        np.ndarray: Confusion matrix
    
    Examples:
        >>> from ilovetools.ml import confusion_matrix_nn
        >>> import numpy as np
        
        >>> y_true = np.array([0, 1, 2, 1, 0])
        >>> y_pred = np.array([0, 1, 2, 2, 0])
        >>> cm = confusion_matrix_nn(y_true, y_pred)
        >>> print(cm)
        [[2 0 0]
         [0 1 1]
         [0 0 1]]
    """
    if num_classes is None:
        num_classes = max(int(np.max(y_true)), int(np.max(y_pred))) + 1
    
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for true, pred in zip(y_true.astype(int), y_pred.astype(int)):
        cm[true, pred] += 1
    
    return cm
