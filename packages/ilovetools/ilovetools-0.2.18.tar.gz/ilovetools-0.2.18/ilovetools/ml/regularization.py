"""
Regularization Techniques for Machine Learning
Comprehensive implementation of regularization methods to prevent overfitting
"""

import numpy as np
from typing import Tuple, Optional, Callable, List

__all__ = [
    # L1/L2 Regularization
    'l1_regularization',
    'l2_regularization',
    'elastic_net_regularization',
    'l1_penalty',
    'l2_penalty',
    'elastic_net_penalty',
    
    # Dropout
    'dropout',
    'dropout_mask',
    'inverted_dropout',
    
    # Early Stopping
    'early_stopping_monitor',
    'should_stop_early',
    
    # Weight Constraints
    'max_norm_constraint',
    'unit_norm_constraint',
    'non_negative_constraint',
    
    # Regularization Utilities
    'compute_regularization_loss',
    'apply_weight_decay',
]


def l1_regularization(
    weights: np.ndarray,
    lambda_param: float = 0.01
) -> float:
    """
    Compute L1 (Lasso) regularization penalty.
    
    L1 = λ × Σ|w_i|
    
    Creates sparse models by driving some weights to exactly zero.
    Good for feature selection.
    
    Args:
        weights: Model weights
        lambda_param: Regularization strength (λ)
    
    Returns:
        L1 penalty value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import l1_regularization
        
        >>> weights = np.array([1.0, -2.0, 3.0, 0.5])
        >>> penalty = l1_regularization(weights, lambda_param=0.01)
        >>> print(f"L1 penalty: {penalty:.4f}")
        L1 penalty: 0.0650
    """
    return lambda_param * np.sum(np.abs(weights))


def l2_regularization(
    weights: np.ndarray,
    lambda_param: float = 0.01
) -> float:
    """
    Compute L2 (Ridge) regularization penalty.
    
    L2 = λ × Σw_i²
    
    Shrinks all weights smoothly. Better for correlated features.
    Most commonly used regularization.
    
    Args:
        weights: Model weights
        lambda_param: Regularization strength (λ)
    
    Returns:
        L2 penalty value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import l2_regularization
        
        >>> weights = np.array([1.0, -2.0, 3.0, 0.5])
        >>> penalty = l2_regularization(weights, lambda_param=0.01)
        >>> print(f"L2 penalty: {penalty:.4f}")
        L2 penalty: 0.1425
    """
    return lambda_param * np.sum(weights ** 2)


def elastic_net_regularization(
    weights: np.ndarray,
    l1_ratio: float = 0.5,
    lambda_param: float = 0.01
) -> float:
    """
    Compute Elastic Net regularization (L1 + L2 combination).
    
    Elastic Net = λ × (α × Σ|w_i| + (1-α) × Σw_i²)
    
    Combines benefits of L1 and L2. Good for grouped features.
    
    Args:
        weights: Model weights
        l1_ratio: Ratio of L1 to L2 (α), between 0 and 1
        lambda_param: Overall regularization strength (λ)
    
    Returns:
        Elastic Net penalty value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import elastic_net_regularization
        
        >>> weights = np.array([1.0, -2.0, 3.0, 0.5])
        >>> penalty = elastic_net_regularization(
        ...     weights, l1_ratio=0.5, lambda_param=0.01
        ... )
        >>> print(f"Elastic Net penalty: {penalty:.4f}")
        Elastic Net penalty: 0.1038
    """
    l1_term = l1_ratio * np.sum(np.abs(weights))
    l2_term = (1 - l1_ratio) * np.sum(weights ** 2)
    return lambda_param * (l1_term + l2_term)


def l1_penalty(
    weights: np.ndarray,
    lambda_param: float = 0.01
) -> np.ndarray:
    """
    Compute L1 gradient penalty for weight updates.
    
    Gradient = λ × sign(w)
    
    Args:
        weights: Model weights
        lambda_param: Regularization strength
    
    Returns:
        L1 gradient penalty
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import l1_penalty
        
        >>> weights = np.array([1.0, -2.0, 0.0, 0.5])
        >>> gradient_penalty = l1_penalty(weights, lambda_param=0.01)
        >>> print(gradient_penalty)
        [ 0.01 -0.01  0.    0.01]
    """
    return lambda_param * np.sign(weights)


def l2_penalty(
    weights: np.ndarray,
    lambda_param: float = 0.01
) -> np.ndarray:
    """
    Compute L2 gradient penalty for weight updates.
    
    Gradient = 2λ × w
    
    Args:
        weights: Model weights
        lambda_param: Regularization strength
    
    Returns:
        L2 gradient penalty
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import l2_penalty
        
        >>> weights = np.array([1.0, -2.0, 3.0, 0.5])
        >>> gradient_penalty = l2_penalty(weights, lambda_param=0.01)
        >>> print(gradient_penalty)
        [ 0.02 -0.04  0.06  0.01]
    """
    return 2 * lambda_param * weights


def elastic_net_penalty(
    weights: np.ndarray,
    l1_ratio: float = 0.5,
    lambda_param: float = 0.01
) -> np.ndarray:
    """
    Compute Elastic Net gradient penalty for weight updates.
    
    Gradient = λ × (α × sign(w) + 2(1-α) × w)
    
    Args:
        weights: Model weights
        l1_ratio: Ratio of L1 to L2
        lambda_param: Overall regularization strength
    
    Returns:
        Elastic Net gradient penalty
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import elastic_net_penalty
        
        >>> weights = np.array([1.0, -2.0, 3.0, 0.5])
        >>> gradient_penalty = elastic_net_penalty(
        ...     weights, l1_ratio=0.5, lambda_param=0.01
        ... )
    """
    l1_grad = l1_ratio * np.sign(weights)
    l2_grad = 2 * (1 - l1_ratio) * weights
    return lambda_param * (l1_grad + l2_grad)


def dropout(
    X: np.ndarray,
    dropout_rate: float = 0.5,
    training: bool = True,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply dropout regularization.
    
    During training: Randomly set neurons to 0 with probability dropout_rate
    During inference: Use all neurons (no dropout)
    
    Args:
        X: Input data (samples × features)
        dropout_rate: Probability of dropping a neuron (0 to 1)
        training: Whether in training mode
        seed: Random seed for reproducibility
    
    Returns:
        Tuple of (output after dropout, dropout mask)
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import dropout
        
        >>> X = np.random.randn(100, 50)
        >>> X_dropout, mask = dropout(X, dropout_rate=0.5, training=True)
        >>> print(f"Dropped neurons: {np.sum(mask == 0)}")
    """
    if not training or dropout_rate == 0:
        return X, np.ones_like(X)
    
    if seed is not None:
        np.random.seed(seed)
    
    # Create dropout mask
    mask = np.random.binomial(1, 1 - dropout_rate, size=X.shape)
    
    # Apply mask and scale (inverted dropout)
    output = X * mask / (1 - dropout_rate)
    
    return output, mask


def dropout_mask(
    shape: Tuple[int, ...],
    dropout_rate: float = 0.5,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate a dropout mask.
    
    Args:
        shape: Shape of the mask
        dropout_rate: Probability of dropping
        seed: Random seed
    
    Returns:
        Binary dropout mask
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import dropout_mask
        
        >>> mask = dropout_mask((100, 50), dropout_rate=0.3)
        >>> print(f"Active neurons: {np.sum(mask)}")
    """
    if seed is not None:
        np.random.seed(seed)
    
    return np.random.binomial(1, 1 - dropout_rate, size=shape)


def inverted_dropout(
    X: np.ndarray,
    dropout_rate: float = 0.5,
    training: bool = True,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Apply inverted dropout (scales during training, not inference).
    
    This is the preferred dropout implementation as it doesn't require
    scaling during inference.
    
    Args:
        X: Input data
        dropout_rate: Dropout probability
        training: Training mode flag
        seed: Random seed
    
    Returns:
        Output after dropout
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import inverted_dropout
        
        >>> X = np.random.randn(100, 50)
        >>> X_train = inverted_dropout(X, dropout_rate=0.5, training=True)
        >>> X_test = inverted_dropout(X, dropout_rate=0.5, training=False)
        >>> # X_test is unchanged, X_train has dropout applied
    """
    if not training or dropout_rate == 0:
        return X
    
    if seed is not None:
        np.random.seed(seed)
    
    mask = np.random.binomial(1, 1 - dropout_rate, size=X.shape)
    return X * mask / (1 - dropout_rate)


def early_stopping_monitor(
    validation_losses: List[float],
    patience: int = 10,
    min_delta: float = 0.0,
    mode: str = 'min'
) -> Tuple[bool, int, float]:
    """
    Monitor validation loss for early stopping.
    
    Args:
        validation_losses: List of validation losses
        patience: Number of epochs to wait for improvement
        min_delta: Minimum change to qualify as improvement
        mode: 'min' for loss, 'max' for accuracy
    
    Returns:
        Tuple of (should_stop, epochs_without_improvement, best_loss)
    
    Examples:
        >>> from ilovetools.ml import early_stopping_monitor
        
        >>> val_losses = [1.0, 0.8, 0.7, 0.71, 0.72, 0.73]
        >>> should_stop, epochs_no_improve, best = early_stopping_monitor(
        ...     val_losses, patience=3
        ... )
        >>> print(f"Stop: {should_stop}, Best: {best:.2f}")
        Stop: True, Best: 0.70
    """
    if len(validation_losses) < 2:
        return False, 0, validation_losses[0] if validation_losses else float('inf')
    
    if mode == 'min':
        best_loss = min(validation_losses)
        best_epoch = validation_losses.index(best_loss)
    else:  # mode == 'max'
        best_loss = max(validation_losses)
        best_epoch = validation_losses.index(best_loss)
    
    epochs_without_improvement = len(validation_losses) - 1 - best_epoch
    
    # Check if there's improvement
    if mode == 'min':
        improved = validation_losses[-1] < (best_loss - min_delta)
    else:
        improved = validation_losses[-1] > (best_loss + min_delta)
    
    should_stop = epochs_without_improvement >= patience and not improved
    
    return should_stop, epochs_without_improvement, best_loss


def should_stop_early(
    current_loss: float,
    best_loss: float,
    patience_counter: int,
    patience: int = 10,
    min_delta: float = 0.0,
    mode: str = 'min'
) -> Tuple[bool, int, float]:
    """
    Check if training should stop early (stateless version).
    
    Args:
        current_loss: Current validation loss
        best_loss: Best validation loss so far
        patience_counter: Current patience counter
        patience: Maximum patience
        min_delta: Minimum improvement threshold
        mode: 'min' or 'max'
    
    Returns:
        Tuple of (should_stop, new_patience_counter, new_best_loss)
    
    Examples:
        >>> from ilovetools.ml import should_stop_early
        
        >>> stop, counter, best = should_stop_early(
        ...     current_loss=0.75,
        ...     best_loss=0.70,
        ...     patience_counter=2,
        ...     patience=5
        ... )
        >>> print(f"Stop: {stop}, Counter: {counter}")
        Stop: False, Counter: 3
    """
    if mode == 'min':
        improved = current_loss < (best_loss - min_delta)
    else:
        improved = current_loss > (best_loss + min_delta)
    
    if improved:
        new_best_loss = current_loss
        new_patience_counter = 0
    else:
        new_best_loss = best_loss
        new_patience_counter = patience_counter + 1
    
    should_stop = new_patience_counter >= patience
    
    return should_stop, new_patience_counter, new_best_loss


def max_norm_constraint(
    weights: np.ndarray,
    max_norm: float = 3.0,
    axis: int = 0
) -> np.ndarray:
    """
    Apply max-norm constraint to weights.
    
    Constrains the norm of weight vectors to be at most max_norm.
    Common in deep learning to prevent weights from growing too large.
    
    Args:
        weights: Weight matrix
        max_norm: Maximum allowed norm
        axis: Axis along which to compute norm (0 for columns, 1 for rows)
    
    Returns:
        Constrained weights
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import max_norm_constraint
        
        >>> weights = np.random.randn(100, 50) * 10
        >>> constrained = max_norm_constraint(weights, max_norm=3.0)
        >>> norms = np.linalg.norm(constrained, axis=0)
        >>> print(f"Max norm: {norms.max():.2f}")
        Max norm: 3.00
    """
    norms = np.linalg.norm(weights, axis=axis, keepdims=True)
    scale = np.minimum(1.0, max_norm / (norms + 1e-8))
    return weights * scale


def unit_norm_constraint(
    weights: np.ndarray,
    axis: int = 0
) -> np.ndarray:
    """
    Normalize weights to unit norm.
    
    Forces weight vectors to have norm = 1.
    
    Args:
        weights: Weight matrix
        axis: Axis along which to normalize
    
    Returns:
        Unit-normalized weights
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import unit_norm_constraint
        
        >>> weights = np.random.randn(100, 50)
        >>> normalized = unit_norm_constraint(weights, axis=0)
        >>> norms = np.linalg.norm(normalized, axis=0)
        >>> print(f"All norms = 1: {np.allclose(norms, 1.0)}")
        All norms = 1: True
    """
    norms = np.linalg.norm(weights, axis=axis, keepdims=True)
    return weights / (norms + 1e-8)


def non_negative_constraint(
    weights: np.ndarray
) -> np.ndarray:
    """
    Apply non-negative constraint (ReLU on weights).
    
    Forces all weights to be >= 0.
    
    Args:
        weights: Weight matrix
    
    Returns:
        Non-negative weights
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import non_negative_constraint
        
        >>> weights = np.array([1.0, -2.0, 3.0, -0.5])
        >>> constrained = non_negative_constraint(weights)
        >>> print(constrained)
        [1. 0. 3. 0.]
    """
    return np.maximum(0, weights)


def compute_regularization_loss(
    weights: np.ndarray,
    reg_type: str = 'l2',
    lambda_param: float = 0.01,
    l1_ratio: float = 0.5
) -> float:
    """
    Compute regularization loss based on type.
    
    Args:
        weights: Model weights
        reg_type: Type of regularization ('l1', 'l2', 'elastic_net', 'none')
        lambda_param: Regularization strength
        l1_ratio: L1 ratio for elastic net
    
    Returns:
        Regularization loss
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import compute_regularization_loss
        
        >>> weights = np.random.randn(100)
        >>> 
        >>> l1_loss = compute_regularization_loss(weights, 'l1', 0.01)
        >>> l2_loss = compute_regularization_loss(weights, 'l2', 0.01)
        >>> elastic_loss = compute_regularization_loss(
        ...     weights, 'elastic_net', 0.01, l1_ratio=0.5
        ... )
    """
    if reg_type == 'none' or lambda_param == 0:
        return 0.0
    elif reg_type == 'l1':
        return l1_regularization(weights, lambda_param)
    elif reg_type == 'l2':
        return l2_regularization(weights, lambda_param)
    elif reg_type == 'elastic_net':
        return elastic_net_regularization(weights, l1_ratio, lambda_param)
    else:
        raise ValueError(f"Unknown regularization type: {reg_type}")


def apply_weight_decay(
    weights: np.ndarray,
    learning_rate: float,
    weight_decay: float = 0.01
) -> np.ndarray:
    """
    Apply weight decay (L2 regularization in optimizer).
    
    Weight decay is equivalent to L2 regularization but applied
    directly in the optimizer update step.
    
    w = w × (1 - lr × decay)
    
    Args:
        weights: Current weights
        learning_rate: Learning rate
        weight_decay: Weight decay coefficient
    
    Returns:
        Weights after decay
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import apply_weight_decay
        
        >>> weights = np.array([1.0, 2.0, 3.0])
        >>> decayed = apply_weight_decay(
        ...     weights, learning_rate=0.01, weight_decay=0.01
        ... )
        >>> print(decayed)
        [0.9999 1.9998 2.9997]
    """
    return weights * (1 - learning_rate * weight_decay)
