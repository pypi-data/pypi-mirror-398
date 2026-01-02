"""
Normalization Techniques for Neural Networks

This module provides various normalization techniques used in deep learning:
- Batch Normalization
- Layer Normalization
- Group Normalization
- Instance Normalization
- Weight Normalization

All normalization functions support both training and inference modes.
"""

import numpy as np
from typing import Tuple, Optional


# ============================================================================
# BATCH NORMALIZATION
# ============================================================================

def batch_normalization(
    x: np.ndarray,
    gamma: np.ndarray,
    beta: np.ndarray,
    running_mean: Optional[np.ndarray] = None,
    running_var: Optional[np.ndarray] = None,
    training: bool = True,
    momentum: float = 0.9,
    epsilon: float = 1e-5
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Batch Normalization
    
    Normalizes activations across the batch dimension. Reduces internal covariate shift
    and allows higher learning rates.
    
    Formula: y = gamma * (x - mean) / sqrt(var + epsilon) + beta
    
    Args:
        x: Input tensor of shape (N, D) or (N, C, H, W)
        gamma: Scale parameter of shape (D,) or (C,)
        beta: Shift parameter of shape (D,) or (C,)
        running_mean: Running mean for inference (updated during training)
        running_var: Running variance for inference (updated during training)
        training: Whether in training mode
        momentum: Momentum for running statistics (default: 0.9)
        epsilon: Small constant for numerical stability (default: 1e-5)
        
    Returns:
        Tuple of (normalized_output, updated_running_mean, updated_running_var)
        
    Example:
        >>> x = np.random.randn(32, 64)  # Batch of 32, 64 features
        >>> gamma = np.ones(64)
        >>> beta = np.zeros(64)
        >>> out, mean, var = batch_normalization(x, gamma, beta, training=True)
        >>> print(out.shape)  # (32, 64)
    """
    if running_mean is None:
        running_mean = np.zeros(gamma.shape)
    if running_var is None:
        running_var = np.ones(gamma.shape)
    
    if training:
        # Compute batch statistics
        if x.ndim == 2:
            # Fully connected layer: (N, D)
            batch_mean = np.mean(x, axis=0)
            batch_var = np.var(x, axis=0)
        elif x.ndim == 4:
            # Convolutional layer: (N, C, H, W)
            batch_mean = np.mean(x, axis=(0, 2, 3), keepdims=True)
            batch_var = np.var(x, axis=(0, 2, 3), keepdims=True)
        else:
            raise ValueError(f"Unsupported input shape: {x.shape}")
        
        # Normalize
        x_normalized = (x - batch_mean) / np.sqrt(batch_var + epsilon)
        
        # Update running statistics
        running_mean = momentum * running_mean + (1 - momentum) * batch_mean.squeeze()
        running_var = momentum * running_var + (1 - momentum) * batch_var.squeeze()
    else:
        # Use running statistics for inference
        if x.ndim == 2:
            x_normalized = (x - running_mean) / np.sqrt(running_var + epsilon)
        elif x.ndim == 4:
            mean_reshaped = running_mean.reshape(1, -1, 1, 1)
            var_reshaped = running_var.reshape(1, -1, 1, 1)
            x_normalized = (x - mean_reshaped) / np.sqrt(var_reshaped + epsilon)
    
    # Scale and shift
    if x.ndim == 2:
        out = gamma * x_normalized + beta
    elif x.ndim == 4:
        gamma_reshaped = gamma.reshape(1, -1, 1, 1)
        beta_reshaped = beta.reshape(1, -1, 1, 1)
        out = gamma_reshaped * x_normalized + beta_reshaped
    
    return out, running_mean, running_var


def batch_norm_forward(
    x: np.ndarray,
    gamma: np.ndarray,
    beta: np.ndarray,
    bn_params: dict
) -> Tuple[np.ndarray, dict]:
    """
    Forward pass for batch normalization with cache
    
    Args:
        x: Input data
        gamma: Scale parameter
        beta: Shift parameter
        bn_params: Dictionary with keys:
            - mode: 'train' or 'test'
            - eps: Epsilon for numerical stability
            - momentum: Momentum for running statistics
            - running_mean: Running mean
            - running_var: Running variance
            
    Returns:
        Tuple of (output, cache)
        
    Example:
        >>> x = np.random.randn(32, 64)
        >>> gamma = np.ones(64)
        >>> beta = np.zeros(64)
        >>> bn_params = {
        ...     'mode': 'train',
        ...     'eps': 1e-5,
        ...     'momentum': 0.9,
        ...     'running_mean': np.zeros(64),
        ...     'running_var': np.ones(64)
        ... }
        >>> out, cache = batch_norm_forward(x, gamma, beta, bn_params)
    """
    mode = bn_params.get('mode', 'train')
    eps = bn_params.get('eps', 1e-5)
    momentum = bn_params.get('momentum', 0.9)
    
    running_mean = bn_params.get('running_mean', np.zeros(gamma.shape))
    running_var = bn_params.get('running_var', np.ones(gamma.shape))
    
    training = (mode == 'train')
    
    out, running_mean, running_var = batch_normalization(
        x, gamma, beta, running_mean, running_var,
        training=training, momentum=momentum, epsilon=eps
    )
    
    # Update running statistics in params
    bn_params['running_mean'] = running_mean
    bn_params['running_var'] = running_var
    
    # Cache for backward pass
    cache = {
        'x': x,
        'gamma': gamma,
        'beta': beta,
        'eps': eps,
        'x_normalized': (x - running_mean) / np.sqrt(running_var + eps),
        'mean': running_mean,
        'var': running_var
    }
    
    return out, cache


# ============================================================================
# LAYER NORMALIZATION
# ============================================================================

def layer_normalization(
    x: np.ndarray,
    gamma: np.ndarray,
    beta: np.ndarray,
    epsilon: float = 1e-5
) -> np.ndarray:
    """
    Layer Normalization
    
    Normalizes activations across the feature dimension. Independent of batch size,
    making it suitable for RNNs and Transformers.
    
    Formula: y = gamma * (x - mean) / sqrt(var + epsilon) + beta
    
    Args:
        x: Input tensor of shape (N, D) or (N, L, D)
        gamma: Scale parameter of shape (D,)
        beta: Shift parameter of shape (D,)
        epsilon: Small constant for numerical stability (default: 1e-5)
        
    Returns:
        Normalized output of same shape as input
        
    Example:
        >>> x = np.random.randn(32, 512)  # Batch of 32, 512 features
        >>> gamma = np.ones(512)
        >>> beta = np.zeros(512)
        >>> out = layer_normalization(x, gamma, beta)
        >>> print(out.shape)  # (32, 512)
        
        >>> # For sequences (Transformers)
        >>> x = np.random.randn(32, 10, 512)  # Batch 32, seq len 10, dim 512
        >>> out = layer_normalization(x, gamma, beta)
        >>> print(out.shape)  # (32, 10, 512)
    """
    # Compute mean and variance across feature dimension
    if x.ndim == 2:
        # (N, D) - Fully connected
        mean = np.mean(x, axis=1, keepdims=True)
        var = np.var(x, axis=1, keepdims=True)
    elif x.ndim == 3:
        # (N, L, D) - Sequence data (Transformers)
        mean = np.mean(x, axis=2, keepdims=True)
        var = np.var(x, axis=2, keepdims=True)
    else:
        raise ValueError(f"Unsupported input shape: {x.shape}")
    
    # Normalize
    x_normalized = (x - mean) / np.sqrt(var + epsilon)
    
    # Scale and shift
    out = gamma * x_normalized + beta
    
    return out


def layer_norm_forward(
    x: np.ndarray,
    gamma: np.ndarray,
    beta: np.ndarray,
    epsilon: float = 1e-5
) -> Tuple[np.ndarray, dict]:
    """
    Forward pass for layer normalization with cache
    
    Args:
        x: Input data
        gamma: Scale parameter
        beta: Shift parameter
        epsilon: Epsilon for numerical stability
        
    Returns:
        Tuple of (output, cache)
        
    Example:
        >>> x = np.random.randn(32, 512)
        >>> gamma = np.ones(512)
        >>> beta = np.zeros(512)
        >>> out, cache = layer_norm_forward(x, gamma, beta)
    """
    # Compute statistics
    if x.ndim == 2:
        mean = np.mean(x, axis=1, keepdims=True)
        var = np.var(x, axis=1, keepdims=True)
    elif x.ndim == 3:
        mean = np.mean(x, axis=2, keepdims=True)
        var = np.var(x, axis=2, keepdims=True)
    else:
        raise ValueError(f"Unsupported input shape: {x.shape}")
    
    # Normalize
    x_normalized = (x - mean) / np.sqrt(var + epsilon)
    
    # Scale and shift
    out = gamma * x_normalized + beta
    
    # Cache for backward pass
    cache = {
        'x': x,
        'gamma': gamma,
        'beta': beta,
        'eps': epsilon,
        'x_normalized': x_normalized,
        'mean': mean,
        'var': var
    }
    
    return out, cache


# ============================================================================
# GROUP NORMALIZATION
# ============================================================================

def group_normalization(
    x: np.ndarray,
    gamma: np.ndarray,
    beta: np.ndarray,
    num_groups: int = 32,
    epsilon: float = 1e-5
) -> np.ndarray:
    """
    Group Normalization
    
    Divides channels into groups and normalizes within each group.
    Works well with small batch sizes.
    
    Args:
        x: Input tensor of shape (N, C, H, W)
        gamma: Scale parameter of shape (C,)
        beta: Shift parameter of shape (C,)
        num_groups: Number of groups (default: 32)
        epsilon: Small constant for numerical stability
        
    Returns:
        Normalized output of same shape as input
        
    Example:
        >>> x = np.random.randn(8, 64, 32, 32)  # Small batch
        >>> gamma = np.ones(64)
        >>> beta = np.zeros(64)
        >>> out = group_normalization(x, gamma, beta, num_groups=32)
        >>> print(out.shape)  # (8, 64, 32, 32)
    """
    N, C, H, W = x.shape
    
    if C % num_groups != 0:
        raise ValueError(f"Number of channels ({C}) must be divisible by num_groups ({num_groups})")
    
    # Reshape to (N, num_groups, C // num_groups, H, W)
    x_grouped = x.reshape(N, num_groups, C // num_groups, H, W)
    
    # Compute mean and variance per group
    mean = np.mean(x_grouped, axis=(2, 3, 4), keepdims=True)
    var = np.var(x_grouped, axis=(2, 3, 4), keepdims=True)
    
    # Normalize
    x_normalized = (x_grouped - mean) / np.sqrt(var + epsilon)
    
    # Reshape back
    x_normalized = x_normalized.reshape(N, C, H, W)
    
    # Scale and shift
    gamma_reshaped = gamma.reshape(1, -1, 1, 1)
    beta_reshaped = beta.reshape(1, -1, 1, 1)
    out = gamma_reshaped * x_normalized + beta_reshaped
    
    return out


# ============================================================================
# INSTANCE NORMALIZATION
# ============================================================================

def instance_normalization(
    x: np.ndarray,
    gamma: np.ndarray,
    beta: np.ndarray,
    epsilon: float = 1e-5
) -> np.ndarray:
    """
    Instance Normalization
    
    Normalizes each sample independently. Used in style transfer and GANs.
    
    Args:
        x: Input tensor of shape (N, C, H, W)
        gamma: Scale parameter of shape (C,)
        beta: Shift parameter of shape (C,)
        epsilon: Small constant for numerical stability
        
    Returns:
        Normalized output of same shape as input
        
    Example:
        >>> x = np.random.randn(8, 64, 32, 32)
        >>> gamma = np.ones(64)
        >>> beta = np.zeros(64)
        >>> out = instance_normalization(x, gamma, beta)
        >>> print(out.shape)  # (8, 64, 32, 32)
    """
    N, C, H, W = x.shape
    
    # Compute mean and variance per instance per channel
    mean = np.mean(x, axis=(2, 3), keepdims=True)
    var = np.var(x, axis=(2, 3), keepdims=True)
    
    # Normalize
    x_normalized = (x - mean) / np.sqrt(var + epsilon)
    
    # Scale and shift
    gamma_reshaped = gamma.reshape(1, -1, 1, 1)
    beta_reshaped = beta.reshape(1, -1, 1, 1)
    out = gamma_reshaped * x_normalized + beta_reshaped
    
    return out


# ============================================================================
# WEIGHT NORMALIZATION
# ============================================================================

def weight_normalization(
    w: np.ndarray,
    g: Optional[np.ndarray] = None,
    axis: int = 0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Weight Normalization
    
    Decouples the magnitude and direction of weight vectors.
    Faster than batch normalization.
    
    Formula: w = g * (v / ||v||)
    
    Args:
        w: Weight matrix
        g: Magnitude parameter (if None, computed from w)
        axis: Axis along which to normalize (default: 0)
        
    Returns:
        Tuple of (normalized_weights, magnitude)
        
    Example:
        >>> w = np.random.randn(512, 256)  # Weight matrix
        >>> w_norm, g = weight_normalization(w)
        >>> print(w_norm.shape)  # (512, 256)
        >>> print(g.shape)  # (512,) or (256,) depending on axis
    """
    # Compute norm along specified axis
    norm = np.linalg.norm(w, axis=axis, keepdims=True)
    
    # Normalize direction
    v = w / (norm + 1e-8)
    
    # Compute or use provided magnitude
    if g is None:
        g = norm.squeeze()
    
    # Reconstruct weights
    if axis == 0:
        w_normalized = g.reshape(-1, 1) * v
    else:
        w_normalized = g.reshape(1, -1) * v
    
    return w_normalized, g


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_normalization_params(
    num_features: int,
    norm_type: str = 'batch'
) -> dict:
    """
    Create parameters for normalization layers
    
    Args:
        num_features: Number of features/channels
        norm_type: Type of normalization ('batch', 'layer', 'group', 'instance')
        
    Returns:
        Dictionary with initialized parameters
        
    Example:
        >>> params = create_normalization_params(64, 'batch')
        >>> print(params.keys())
        dict_keys(['gamma', 'beta', 'running_mean', 'running_var'])
    """
    params = {
        'gamma': np.ones(num_features),
        'beta': np.zeros(num_features)
    }
    
    if norm_type == 'batch':
        params['running_mean'] = np.zeros(num_features)
        params['running_var'] = np.ones(num_features)
    
    return params


def apply_normalization(
    x: np.ndarray,
    norm_type: str,
    gamma: np.ndarray,
    beta: np.ndarray,
    **kwargs
) -> np.ndarray:
    """
    Apply normalization by type name
    
    Args:
        x: Input tensor
        norm_type: Type of normalization
        gamma: Scale parameter
        beta: Shift parameter
        **kwargs: Additional arguments for specific normalization
        
    Returns:
        Normalized output
        
    Example:
        >>> x = np.random.randn(32, 64)
        >>> gamma = np.ones(64)
        >>> beta = np.zeros(64)
        >>> out = apply_normalization(x, 'layer', gamma, beta)
    """
    if norm_type == 'batch':
        out, _, _ = batch_normalization(x, gamma, beta, **kwargs)
        return out
    elif norm_type == 'layer':
        return layer_normalization(x, gamma, beta, **kwargs)
    elif norm_type == 'group':
        return group_normalization(x, gamma, beta, **kwargs)
    elif norm_type == 'instance':
        return instance_normalization(x, gamma, beta, **kwargs)
    else:
        raise ValueError(f"Unknown normalization type: {norm_type}")


# Aliases for convenience
batchnorm = batch_normalization
layernorm = layer_normalization
groupnorm = group_normalization
instancenorm = instance_normalization
weightnorm = weight_normalization
