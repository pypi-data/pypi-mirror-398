"""
Advanced Optimizers for Neural Networks

This module provides state-of-the-art optimization algorithms for training neural networks.
Includes Adam variants, RMSprop variants, and modern optimizers used in production systems.

All optimizers support:
- Momentum
- Adaptive learning rates
- Weight decay
- Gradient clipping
- Learning rate scheduling
"""

import numpy as np
from typing import Dict, Optional, Tuple, Callable


# ============================================================================
# ADAM VARIANTS
# ============================================================================

def adam_optimizer(
    params: np.ndarray,
    grads: np.ndarray,
    m: np.ndarray,
    v: np.ndarray,
    t: int,
    learning_rate: float = 0.001,
    beta1: float = 0.9,
    beta2: float = 0.999,
    epsilon: float = 1e-8
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Adam (Adaptive Moment Estimation) optimizer
    
    Combines momentum and RMSprop. Most popular optimizer for deep learning.
    
    Args:
        params: Current parameters
        grads: Gradients
        m: First moment (momentum)
        v: Second moment (RMSprop)
        t: Time step
        learning_rate: Learning rate (default: 0.001)
        beta1: Exponential decay for first moment (default: 0.9)
        beta2: Exponential decay for second moment (default: 0.999)
        epsilon: Small constant for numerical stability
        
    Returns:
        Tuple of (updated_params, updated_m, updated_v)
        
    Example:
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> grads = np.array([0.1, 0.2, 0.3])
        >>> m = np.zeros_like(params)
        >>> v = np.zeros_like(params)
        >>> new_params, m, v = adam_optimizer(params, grads, m, v, t=1)
    """
    # Update biased first moment estimate
    m = beta1 * m + (1 - beta1) * grads
    
    # Update biased second moment estimate
    v = beta2 * v + (1 - beta2) * (grads ** 2)
    
    # Compute bias-corrected first moment
    m_hat = m / (1 - beta1 ** t)
    
    # Compute bias-corrected second moment
    v_hat = v / (1 - beta2 ** t)
    
    # Update parameters
    params = params - learning_rate * m_hat / (np.sqrt(v_hat) + epsilon)
    
    return params, m, v


def adamw_optimizer(
    params: np.ndarray,
    grads: np.ndarray,
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
    AdamW optimizer (Adam with decoupled weight decay)
    
    Fixes weight decay in Adam. Better generalization than Adam.
    Used in BERT, GPT, and modern transformers.
    
    Args:
        params: Current parameters
        grads: Gradients
        m: First moment
        v: Second moment
        t: Time step
        learning_rate: Learning rate
        beta1: First moment decay
        beta2: Second moment decay
        epsilon: Numerical stability
        weight_decay: Weight decay coefficient (default: 0.01)
        
    Returns:
        Tuple of (updated_params, updated_m, updated_v)
        
    Example:
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> grads = np.array([0.1, 0.2, 0.3])
        >>> m = np.zeros_like(params)
        >>> v = np.zeros_like(params)
        >>> new_params, m, v = adamw_optimizer(params, grads, m, v, t=1)
    """
    # Update biased first moment
    m = beta1 * m + (1 - beta1) * grads
    
    # Update biased second moment
    v = beta2 * v + (1 - beta2) * (grads ** 2)
    
    # Bias correction
    m_hat = m / (1 - beta1 ** t)
    v_hat = v / (1 - beta2 ** t)
    
    # Update with decoupled weight decay
    params = params - learning_rate * (m_hat / (np.sqrt(v_hat) + epsilon) + weight_decay * params)
    
    return params, m, v


def adamax_optimizer(
    params: np.ndarray,
    grads: np.ndarray,
    m: np.ndarray,
    u: np.ndarray,
    t: int,
    learning_rate: float = 0.002,
    beta1: float = 0.9,
    beta2: float = 0.999,
    epsilon: float = 1e-8
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    AdaMax optimizer (Adam with infinity norm)
    
    Variant of Adam based on infinity norm. More stable with large gradients.
    
    Args:
        params: Current parameters
        grads: Gradients
        m: First moment
        u: Exponentially weighted infinity norm
        t: Time step
        learning_rate: Learning rate (default: 0.002)
        beta1: First moment decay
        beta2: Infinity norm decay
        epsilon: Numerical stability
        
    Returns:
        Tuple of (updated_params, updated_m, updated_u)
        
    Example:
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> grads = np.array([0.1, 0.2, 0.3])
        >>> m = np.zeros_like(params)
        >>> u = np.zeros_like(params)
        >>> new_params, m, u = adamax_optimizer(params, grads, m, u, t=1)
    """
    # Update biased first moment
    m = beta1 * m + (1 - beta1) * grads
    
    # Update exponentially weighted infinity norm
    u = np.maximum(beta2 * u, np.abs(grads))
    
    # Bias correction for first moment
    m_hat = m / (1 - beta1 ** t)
    
    # Update parameters
    params = params - learning_rate * m_hat / (u + epsilon)
    
    return params, m, u


def nadam_optimizer(
    params: np.ndarray,
    grads: np.ndarray,
    m: np.ndarray,
    v: np.ndarray,
    t: int,
    learning_rate: float = 0.001,
    beta1: float = 0.9,
    beta2: float = 0.999,
    epsilon: float = 1e-8
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Nadam optimizer (Nesterov-accelerated Adam)
    
    Combines Adam with Nesterov momentum. Better convergence than Adam.
    
    Args:
        params: Current parameters
        grads: Gradients
        m: First moment
        v: Second moment
        t: Time step
        learning_rate: Learning rate
        beta1: First moment decay
        beta2: Second moment decay
        epsilon: Numerical stability
        
    Returns:
        Tuple of (updated_params, updated_m, updated_v)
        
    Example:
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> grads = np.array([0.1, 0.2, 0.3])
        >>> m = np.zeros_like(params)
        >>> v = np.zeros_like(params)
        >>> new_params, m, v = nadam_optimizer(params, grads, m, v, t=1)
    """
    # Update biased first moment
    m = beta1 * m + (1 - beta1) * grads
    
    # Update biased second moment
    v = beta2 * v + (1 - beta2) * (grads ** 2)
    
    # Bias correction
    m_hat = m / (1 - beta1 ** t)
    v_hat = v / (1 - beta2 ** t)
    
    # Nesterov momentum
    m_nesterov = beta1 * m_hat + (1 - beta1) * grads / (1 - beta1 ** t)
    
    # Update parameters
    params = params - learning_rate * m_nesterov / (np.sqrt(v_hat) + epsilon)
    
    return params, m, v


def amsgrad_optimizer(
    params: np.ndarray,
    grads: np.ndarray,
    m: np.ndarray,
    v: np.ndarray,
    v_hat_max: np.ndarray,
    t: int,
    learning_rate: float = 0.001,
    beta1: float = 0.9,
    beta2: float = 0.999,
    epsilon: float = 1e-8
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    AMSGrad optimizer (Adam with maximum of past squared gradients)
    
    Fixes convergence issues in Adam. Maintains maximum of v_hat.
    
    Args:
        params: Current parameters
        grads: Gradients
        m: First moment
        v: Second moment
        v_hat_max: Maximum of past v_hat
        t: Time step
        learning_rate: Learning rate
        beta1: First moment decay
        beta2: Second moment decay
        epsilon: Numerical stability
        
    Returns:
        Tuple of (updated_params, updated_m, updated_v, updated_v_hat_max)
        
    Example:
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> grads = np.array([0.1, 0.2, 0.3])
        >>> m = np.zeros_like(params)
        >>> v = np.zeros_like(params)
        >>> v_max = np.zeros_like(params)
        >>> new_params, m, v, v_max = amsgrad_optimizer(params, grads, m, v, v_max, t=1)
    """
    # Update biased moments
    m = beta1 * m + (1 - beta1) * grads
    v = beta2 * v + (1 - beta2) * (grads ** 2)
    
    # Bias correction
    m_hat = m / (1 - beta1 ** t)
    v_hat = v / (1 - beta2 ** t)
    
    # Maintain maximum of v_hat
    v_hat_max = np.maximum(v_hat_max, v_hat)
    
    # Update parameters
    params = params - learning_rate * m_hat / (np.sqrt(v_hat_max) + epsilon)
    
    return params, m, v, v_hat_max


# ============================================================================
# RMSPROP VARIANTS
# ============================================================================

def rmsprop_optimizer(
    params: np.ndarray,
    grads: np.ndarray,
    cache: np.ndarray,
    learning_rate: float = 0.001,
    decay_rate: float = 0.9,
    epsilon: float = 1e-8
) -> Tuple[np.ndarray, np.ndarray]:
    """
    RMSprop optimizer (Root Mean Square Propagation)
    
    Adaptive learning rate method. Good for RNNs and non-stationary problems.
    
    Args:
        params: Current parameters
        grads: Gradients
        cache: Running average of squared gradients
        learning_rate: Learning rate (default: 0.001)
        decay_rate: Decay rate for moving average (default: 0.9)
        epsilon: Numerical stability
        
    Returns:
        Tuple of (updated_params, updated_cache)
        
    Example:
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> grads = np.array([0.1, 0.2, 0.3])
        >>> cache = np.zeros_like(params)
        >>> new_params, cache = rmsprop_optimizer(params, grads, cache)
    """
    # Update cache
    cache = decay_rate * cache + (1 - decay_rate) * (grads ** 2)
    
    # Update parameters
    params = params - learning_rate * grads / (np.sqrt(cache) + epsilon)
    
    return params, cache


def rmsprop_momentum_optimizer(
    params: np.ndarray,
    grads: np.ndarray,
    cache: np.ndarray,
    momentum: np.ndarray,
    learning_rate: float = 0.001,
    decay_rate: float = 0.9,
    momentum_coef: float = 0.9,
    epsilon: float = 1e-8
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    RMSprop with momentum
    
    Combines RMSprop with momentum for better convergence.
    
    Args:
        params: Current parameters
        grads: Gradients
        cache: Running average of squared gradients
        momentum: Momentum term
        learning_rate: Learning rate
        decay_rate: RMSprop decay rate
        momentum_coef: Momentum coefficient
        epsilon: Numerical stability
        
    Returns:
        Tuple of (updated_params, updated_cache, updated_momentum)
        
    Example:
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> grads = np.array([0.1, 0.2, 0.3])
        >>> cache = np.zeros_like(params)
        >>> momentum = np.zeros_like(params)
        >>> new_params, cache, momentum = rmsprop_momentum_optimizer(
        ...     params, grads, cache, momentum
        ... )
    """
    # Update cache
    cache = decay_rate * cache + (1 - decay_rate) * (grads ** 2)
    
    # Update momentum
    momentum = momentum_coef * momentum - learning_rate * grads / (np.sqrt(cache) + epsilon)
    
    # Update parameters
    params = params + momentum
    
    return params, cache, momentum


# ============================================================================
# MODERN OPTIMIZERS
# ============================================================================

def radam_optimizer(
    params: np.ndarray,
    grads: np.ndarray,
    m: np.ndarray,
    v: np.ndarray,
    t: int,
    learning_rate: float = 0.001,
    beta1: float = 0.9,
    beta2: float = 0.999,
    epsilon: float = 1e-8
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    RAdam optimizer (Rectified Adam)
    
    Fixes warmup issues in Adam. Automatically adjusts learning rate in early stages.
    Better than Adam without warmup.
    
    Args:
        params: Current parameters
        grads: Gradients
        m: First moment
        v: Second moment
        t: Time step
        learning_rate: Learning rate
        beta1: First moment decay
        beta2: Second moment decay
        epsilon: Numerical stability
        
    Returns:
        Tuple of (updated_params, updated_m, updated_v)
        
    Example:
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> grads = np.array([0.1, 0.2, 0.3])
        >>> m = np.zeros_like(params)
        >>> v = np.zeros_like(params)
        >>> new_params, m, v = radam_optimizer(params, grads, m, v, t=1)
    """
    # Update biased moments
    m = beta1 * m + (1 - beta1) * grads
    v = beta2 * v + (1 - beta2) * (grads ** 2)
    
    # Bias correction
    m_hat = m / (1 - beta1 ** t)
    
    # Compute length of approximated SMA
    rho_inf = 2 / (1 - beta2) - 1
    rho_t = rho_inf - 2 * t * (beta2 ** t) / (1 - beta2 ** t)
    
    # Check if variance is tractable
    if rho_t > 4:
        # Compute variance rectification term
        r_t = np.sqrt(
            ((rho_t - 4) * (rho_t - 2) * rho_inf) /
            ((rho_inf - 4) * (rho_inf - 2) * rho_t)
        )
        
        # Bias-corrected second moment
        v_hat = v / (1 - beta2 ** t)
        
        # Update with rectification
        params = params - learning_rate * r_t * m_hat / (np.sqrt(v_hat) + epsilon)
    else:
        # Use momentum only (no adaptive learning rate)
        params = params - learning_rate * m_hat
    
    return params, m, v


def lamb_optimizer(
    params: np.ndarray,
    grads: np.ndarray,
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
    LAMB optimizer (Layer-wise Adaptive Moments for Batch training)
    
    Enables large batch training. Used in BERT training with batch size 65k.
    Scales learning rate per layer based on weight and gradient norms.
    
    Args:
        params: Current parameters
        grads: Gradients
        m: First moment
        v: Second moment
        t: Time step
        learning_rate: Learning rate
        beta1: First moment decay
        beta2: Second moment decay
        epsilon: Numerical stability
        weight_decay: Weight decay coefficient
        
    Returns:
        Tuple of (updated_params, updated_m, updated_v)
        
    Example:
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> grads = np.array([0.1, 0.2, 0.3])
        >>> m = np.zeros_like(params)
        >>> v = np.zeros_like(params)
        >>> new_params, m, v = lamb_optimizer(params, grads, m, v, t=1)
    """
    # Update biased moments
    m = beta1 * m + (1 - beta1) * grads
    v = beta2 * v + (1 - beta2) * (grads ** 2)
    
    # Bias correction
    m_hat = m / (1 - beta1 ** t)
    v_hat = v / (1 - beta2 ** t)
    
    # Compute update
    update = m_hat / (np.sqrt(v_hat) + epsilon) + weight_decay * params
    
    # Compute trust ratio (layer-wise adaptation)
    weight_norm = np.linalg.norm(params)
    update_norm = np.linalg.norm(update)
    
    if weight_norm > 0 and update_norm > 0:
        trust_ratio = weight_norm / update_norm
    else:
        trust_ratio = 1.0
    
    # Update parameters with trust ratio
    params = params - learning_rate * trust_ratio * update
    
    return params, m, v


def lookahead_optimizer(
    params: np.ndarray,
    slow_params: np.ndarray,
    k_counter: int,
    k: int = 5,
    alpha: float = 0.5
) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    Lookahead optimizer wrapper
    
    Maintains slow and fast weights. Improves convergence and reduces variance.
    Can wrap any optimizer (Adam, SGD, etc.).
    
    Args:
        params: Current fast parameters
        slow_params: Slow parameters
        k_counter: Step counter
        k: Synchronization period (default: 5)
        alpha: Slow weights step size (default: 0.5)
        
    Returns:
        Tuple of (updated_params, updated_slow_params, updated_counter)
        
    Example:
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> slow_params = np.array([1.0, 2.0, 3.0])
        >>> # After k steps of inner optimizer
        >>> new_params, slow_params, counter = lookahead_optimizer(
        ...     params, slow_params, k_counter=5
        ... )
    """
    k_counter += 1
    
    # Synchronize every k steps
    if k_counter >= k:
        # Update slow weights
        slow_params = slow_params + alpha * (params - slow_params)
        
        # Reset fast weights to slow weights
        params = slow_params.copy()
        
        # Reset counter
        k_counter = 0
    
    return params, slow_params, k_counter


def adabelief_optimizer(
    params: np.ndarray,
    grads: np.ndarray,
    m: np.ndarray,
    s: np.ndarray,
    t: int,
    learning_rate: float = 0.001,
    beta1: float = 0.9,
    beta2: float = 0.999,
    epsilon: float = 1e-16
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    AdaBelief optimizer
    
    Adapts step size based on "belief" in gradient direction.
    Better generalization than Adam. Fast convergence like Adam.
    
    Args:
        params: Current parameters
        grads: Gradients
        m: First moment (mean)
        s: Second moment (variance of gradient prediction error)
        t: Time step
        learning_rate: Learning rate
        beta1: First moment decay
        beta2: Second moment decay
        epsilon: Numerical stability (smaller than Adam)
        
    Returns:
        Tuple of (updated_params, updated_m, updated_s)
        
    Example:
        >>> params = np.array([1.0, 2.0, 3.0])
        >>> grads = np.array([0.1, 0.2, 0.3])
        >>> m = np.zeros_like(params)
        >>> s = np.zeros_like(params)
        >>> new_params, m, s = adabelief_optimizer(params, grads, m, s, t=1)
    """
    # Update biased first moment
    m = beta1 * m + (1 - beta1) * grads
    
    # Update biased second moment (variance of prediction error)
    s = beta2 * s + (1 - beta2) * ((grads - m) ** 2) + epsilon
    
    # Bias correction
    m_hat = m / (1 - beta1 ** t)
    s_hat = s / (1 - beta2 ** t)
    
    # Update parameters
    params = params - learning_rate * m_hat / (np.sqrt(s_hat) + epsilon)
    
    return params, m, s


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_optimizer_state(
    params_shape: tuple,
    optimizer_name: str
) -> Dict[str, np.ndarray]:
    """
    Create initial state for optimizer
    
    Args:
        params_shape: Shape of parameters
        optimizer_name: Name of optimizer
        
    Returns:
        Dictionary with initialized optimizer state
        
    Example:
        >>> state = create_optimizer_state((3,), 'adam')
        >>> print(state.keys())
        dict_keys(['m', 'v', 't'])
    """
    state = {'t': 0}
    
    if optimizer_name in ['adam', 'adamw', 'nadam', 'radam', 'lamb', 'adabelief']:
        state['m'] = np.zeros(params_shape)
        state['v'] = np.zeros(params_shape)
    
    if optimizer_name == 'adamax':
        state['m'] = np.zeros(params_shape)
        state['u'] = np.zeros(params_shape)
    
    if optimizer_name == 'amsgrad':
        state['m'] = np.zeros(params_shape)
        state['v'] = np.zeros(params_shape)
        state['v_hat_max'] = np.zeros(params_shape)
    
    if optimizer_name in ['rmsprop', 'rmsprop_momentum']:
        state['cache'] = np.zeros(params_shape)
        if optimizer_name == 'rmsprop_momentum':
            state['momentum'] = np.zeros(params_shape)
    
    if optimizer_name == 'lookahead':
        state['slow_params'] = np.zeros(params_shape)
        state['k_counter'] = 0
    
    if optimizer_name == 'adabelief':
        state['m'] = np.zeros(params_shape)
        state['s'] = np.zeros(params_shape)
    
    return state


def get_optimizer_function(optimizer_name: str) -> Callable:
    """
    Get optimizer function by name
    
    Args:
        optimizer_name: Name of optimizer
        
    Returns:
        Optimizer function
        
    Example:
        >>> opt_fn = get_optimizer_function('adam')
        >>> print(opt_fn.__name__)
        adam_optimizer
    """
    optimizers = {
        'adam': adam_optimizer,
        'adamw': adamw_optimizer,
        'adamax': adamax_optimizer,
        'nadam': nadam_optimizer,
        'amsgrad': amsgrad_optimizer,
        'rmsprop': rmsprop_optimizer,
        'rmsprop_momentum': rmsprop_momentum_optimizer,
        'radam': radam_optimizer,
        'lamb': lamb_optimizer,
        'lookahead': lookahead_optimizer,
        'adabelief': adabelief_optimizer,
    }
    
    if optimizer_name not in optimizers:
        raise ValueError(f"Unknown optimizer: {optimizer_name}. Available: {list(optimizers.keys())}")
    
    return optimizers[optimizer_name]


# Aliases for convenience
adam = adam_optimizer
adamw = adamw_optimizer
adamax = adamax_optimizer
nadam = nadam_optimizer
amsgrad = amsgrad_optimizer
rmsprop = rmsprop_optimizer
rmsprop_mom = rmsprop_momentum_optimizer
radam = radam_optimizer
lamb = lamb_optimizer
lookahead = lookahead_optimizer
adabelief = adabelief_optimizer
