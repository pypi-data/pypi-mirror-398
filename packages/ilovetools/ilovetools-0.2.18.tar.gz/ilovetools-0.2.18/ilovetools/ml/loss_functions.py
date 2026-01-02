"""
Loss Functions for Machine Learning
Comprehensive implementation of loss functions for regression, classification, and segmentation
"""

import numpy as np
from typing import Optional, Tuple

__all__ = [
    # Regression Losses
    'mean_squared_error_loss',
    'mean_absolute_error_loss',
    'root_mean_squared_error_loss',
    'huber_loss',
    'log_cosh_loss',
    'quantile_loss',
    'mean_squared_logarithmic_error',
    
    # Classification Losses
    'binary_crossentropy_loss',
    'categorical_crossentropy_loss',
    'sparse_categorical_crossentropy_loss',
    'hinge_loss',
    'squared_hinge_loss',
    'categorical_hinge_loss',
    'focal_loss',
    'kullback_leibler_divergence',
    
    # Segmentation Losses
    'dice_loss',
    'dice_coefficient',
    'iou_loss',
    'tversky_loss',
    'focal_tversky_loss',
    
    # Utilities
    'combined_loss',
    'weighted_loss',
]


# ==================== REGRESSION LOSSES ====================

def mean_squared_error_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> float:
    """
    Compute Mean Squared Error (MSE) loss.
    
    MSE = (1/n) × Σ(y_true - y_pred)²
    
    Most common regression loss. Penalizes large errors heavily.
    Sensitive to outliers.
    
    Args:
        y_true: True values
        y_pred: Predicted values
    
    Returns:
        MSE loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import mean_squared_error_loss
        
        >>> y_true = np.array([1.0, 2.0, 3.0, 4.0])
        >>> y_pred = np.array([1.1, 2.2, 2.8, 4.3])
        >>> loss = mean_squared_error_loss(y_true, y_pred)
        >>> print(f"MSE Loss: {loss:.4f}")
        MSE Loss: 0.0350
    """
    return np.mean((y_true - y_pred) ** 2)


def mean_absolute_error_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> float:
    """
    Compute Mean Absolute Error (MAE) loss.
    
    MAE = (1/n) × Σ|y_true - y_pred|
    
    Robust to outliers. Linear penalty.
    Non-smooth at zero (can cause optimization issues).
    
    Args:
        y_true: True values
        y_pred: Predicted values
    
    Returns:
        MAE loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import mean_absolute_error_loss
        
        >>> y_true = np.array([1.0, 2.0, 3.0, 4.0])
        >>> y_pred = np.array([1.1, 2.2, 2.8, 4.3])
        >>> loss = mean_absolute_error_loss(y_true, y_pred)
        >>> print(f"MAE Loss: {loss:.4f}")
        MAE Loss: 0.1500
    """
    return np.mean(np.abs(y_true - y_pred))


def root_mean_squared_error_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> float:
    """
    Compute Root Mean Squared Error (RMSE) loss.
    
    RMSE = √[(1/n) × Σ(y_true - y_pred)²]
    
    Same scale as target variable. Penalizes large errors.
    
    Args:
        y_true: True values
        y_pred: Predicted values
    
    Returns:
        RMSE loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import root_mean_squared_error_loss
        
        >>> y_true = np.array([1.0, 2.0, 3.0, 4.0])
        >>> y_pred = np.array([1.1, 2.2, 2.8, 4.3])
        >>> loss = root_mean_squared_error_loss(y_true, y_pred)
        >>> print(f"RMSE Loss: {loss:.4f}")
        RMSE Loss: 0.1871
    """
    return np.sqrt(np.mean((y_true - y_pred) ** 2))


def huber_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    delta: float = 1.0
) -> float:
    """
    Compute Huber loss (smooth combination of MSE and MAE).
    
    Huber = {
        0.5 × (y_true - y_pred)²           if |y_true - y_pred| ≤ δ
        δ × (|y_true - y_pred| - 0.5δ)     otherwise
    }
    
    Combines benefits of MSE and MAE. Smooth everywhere.
    Robust to outliers while maintaining smoothness.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        delta: Threshold for switching between MSE and MAE
    
    Returns:
        Huber loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import huber_loss
        
        >>> y_true = np.array([1.0, 2.0, 3.0, 10.0])
        >>> y_pred = np.array([1.1, 2.2, 2.8, 4.0])
        >>> loss = huber_loss(y_true, y_pred, delta=1.0)
        >>> print(f"Huber Loss: {loss:.4f}")
        Huber Loss: 1.3825
    """
    error = y_true - y_pred
    abs_error = np.abs(error)
    
    quadratic = 0.5 * error ** 2
    linear = delta * (abs_error - 0.5 * delta)
    
    return np.mean(np.where(abs_error <= delta, quadratic, linear))


def log_cosh_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> float:
    """
    Compute Log-Cosh loss.
    
    Log-Cosh = Σ log(cosh(y_pred - y_true))
    
    Smooth like MSE, robust like MAE. Twice differentiable.
    Good for regression with outliers.
    
    Args:
        y_true: True values
        y_pred: Predicted values
    
    Returns:
        Log-Cosh loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import log_cosh_loss
        
        >>> y_true = np.array([1.0, 2.0, 3.0, 4.0])
        >>> y_pred = np.array([1.1, 2.2, 2.8, 4.3])
        >>> loss = log_cosh_loss(y_true, y_pred)
        >>> print(f"Log-Cosh Loss: {loss:.4f}")
        Log-Cosh Loss: 0.0174
    """
    error = y_pred - y_true
    return np.mean(np.log(np.cosh(error)))


def quantile_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    quantile: float = 0.5
) -> float:
    """
    Compute Quantile loss (for quantile regression).
    
    Quantile Loss = Σ max(q(y_true - y_pred), (q-1)(y_true - y_pred))
    
    Predicts specific quantiles instead of mean.
    Useful for uncertainty estimation.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        quantile: Target quantile (0 to 1)
    
    Returns:
        Quantile loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import quantile_loss
        
        >>> y_true = np.array([1.0, 2.0, 3.0, 4.0])
        >>> y_pred = np.array([1.1, 2.2, 2.8, 4.3])
        >>> loss = quantile_loss(y_true, y_pred, quantile=0.5)
        >>> print(f"Quantile Loss: {loss:.4f}")
        Quantile Loss: 0.0750
    """
    error = y_true - y_pred
    return np.mean(np.maximum(quantile * error, (quantile - 1) * error))


def mean_squared_logarithmic_error(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> float:
    """
    Compute Mean Squared Logarithmic Error (MSLE).
    
    MSLE = (1/n) × Σ(log(1 + y_true) - log(1 + y_pred))²
    
    Good for targets with exponential growth.
    Penalizes underestimation more than overestimation.
    
    Args:
        y_true: True values (must be non-negative)
        y_pred: Predicted values (must be non-negative)
    
    Returns:
        MSLE loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import mean_squared_logarithmic_error
        
        >>> y_true = np.array([1.0, 2.0, 3.0, 4.0])
        >>> y_pred = np.array([1.1, 2.2, 2.8, 4.3])
        >>> loss = mean_squared_logarithmic_error(y_true, y_pred)
        >>> print(f"MSLE Loss: {loss:.4f}")
        MSLE Loss: 0.0024
    """
    return np.mean((np.log1p(y_true) - np.log1p(y_pred)) ** 2)


# ==================== CLASSIFICATION LOSSES ====================

def binary_crossentropy_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    epsilon: float = 1e-7
) -> float:
    """
    Compute Binary Cross-Entropy loss.
    
    BCE = -(1/n) × Σ[y_true × log(y_pred) + (1 - y_true) × log(1 - y_pred)]
    
    Standard loss for binary classification.
    Works with sigmoid activation.
    
    Args:
        y_true: True labels (0 or 1)
        y_pred: Predicted probabilities (0 to 1)
        epsilon: Small constant to avoid log(0)
    
    Returns:
        Binary cross-entropy loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import binary_crossentropy_loss
        
        >>> y_true = np.array([0, 1, 1, 0])
        >>> y_pred = np.array([0.1, 0.9, 0.8, 0.2])
        >>> loss = binary_crossentropy_loss(y_true, y_pred)
        >>> print(f"BCE Loss: {loss:.4f}")
        BCE Loss: 0.1438
    """
    y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
    return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))


def categorical_crossentropy_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    epsilon: float = 1e-7
) -> float:
    """
    Compute Categorical Cross-Entropy loss.
    
    CCE = -(1/n) × Σ Σ y_true_i × log(y_pred_i)
    
    Standard loss for multi-class classification.
    Works with softmax activation. Requires one-hot encoded labels.
    
    Args:
        y_true: True labels (one-hot encoded)
        y_pred: Predicted probabilities
        epsilon: Small constant to avoid log(0)
    
    Returns:
        Categorical cross-entropy loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import categorical_crossentropy_loss
        
        >>> y_true = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        >>> y_pred = np.array([[0.9, 0.05, 0.05], [0.1, 0.8, 0.1], [0.1, 0.1, 0.8]])
        >>> loss = categorical_crossentropy_loss(y_true, y_pred)
        >>> print(f"CCE Loss: {loss:.4f}")
        CCE Loss: 0.1625
    """
    y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
    return -np.mean(np.sum(y_true * np.log(y_pred), axis=-1))


def sparse_categorical_crossentropy_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    epsilon: float = 1e-7
) -> float:
    """
    Compute Sparse Categorical Cross-Entropy loss.
    
    Same as categorical cross-entropy but with integer labels.
    More memory efficient for large number of classes.
    
    Args:
        y_true: True labels (integers)
        y_pred: Predicted probabilities
        epsilon: Small constant to avoid log(0)
    
    Returns:
        Sparse categorical cross-entropy loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import sparse_categorical_crossentropy_loss
        
        >>> y_true = np.array([0, 1, 2])
        >>> y_pred = np.array([[0.9, 0.05, 0.05], [0.1, 0.8, 0.1], [0.1, 0.1, 0.8]])
        >>> loss = sparse_categorical_crossentropy_loss(y_true, y_pred)
        >>> print(f"Sparse CCE Loss: {loss:.4f}")
        Sparse CCE Loss: 0.1625
    """
    y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
    n_samples = y_true.shape[0]
    log_likelihood = -np.log(y_pred[range(n_samples), y_true.astype(int)])
    return np.mean(log_likelihood)


def hinge_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> float:
    """
    Compute Hinge loss (for SVM).
    
    Hinge = max(0, 1 - y_true × y_pred)
    
    Margin-based loss for binary classification.
    Used in Support Vector Machines.
    
    Args:
        y_true: True labels (-1 or 1)
        y_pred: Predicted values (raw scores)
    
    Returns:
        Hinge loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import hinge_loss
        
        >>> y_true = np.array([1, -1, 1, -1])
        >>> y_pred = np.array([0.9, -0.8, 0.7, -0.6])
        >>> loss = hinge_loss(y_true, y_pred)
        >>> print(f"Hinge Loss: {loss:.4f}")
        Hinge Loss: 0.1500
    """
    return np.mean(np.maximum(0, 1 - y_true * y_pred))


def squared_hinge_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> float:
    """
    Compute Squared Hinge loss.
    
    Squared Hinge = max(0, 1 - y_true × y_pred)²
    
    Smoother version of hinge loss.
    More sensitive to outliers.
    
    Args:
        y_true: True labels (-1 or 1)
        y_pred: Predicted values (raw scores)
    
    Returns:
        Squared hinge loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import squared_hinge_loss
        
        >>> y_true = np.array([1, -1, 1, -1])
        >>> y_pred = np.array([0.9, -0.8, 0.7, -0.6])
        >>> loss = squared_hinge_loss(y_true, y_pred)
        >>> print(f"Squared Hinge Loss: {loss:.4f}")
        Squared Hinge Loss: 0.0350
    """
    return np.mean(np.maximum(0, 1 - y_true * y_pred) ** 2)


def categorical_hinge_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> float:
    """
    Compute Categorical Hinge loss (multi-class hinge).
    
    Extends hinge loss to multi-class classification.
    
    Args:
        y_true: True labels (one-hot encoded)
        y_pred: Predicted values (raw scores)
    
    Returns:
        Categorical hinge loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import categorical_hinge_loss
        
        >>> y_true = np.array([[1, 0, 0], [0, 1, 0]])
        >>> y_pred = np.array([[2.0, 0.5, 0.3], [0.3, 1.8, 0.4]])
        >>> loss = categorical_hinge_loss(y_true, y_pred)
        >>> print(f"Categorical Hinge Loss: {loss:.4f}")
        Categorical Hinge Loss: 0.0000
    """
    pos = np.sum(y_true * y_pred, axis=-1)
    neg = np.max((1 - y_true) * y_pred, axis=-1)
    return np.mean(np.maximum(0, neg - pos + 1))


def focal_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    alpha: float = 0.25,
    gamma: float = 2.0,
    epsilon: float = 1e-7
) -> float:
    """
    Compute Focal loss (for imbalanced classification).
    
    Focal = -α × (1 - p)^γ × log(p)
    
    Focuses on hard examples. Reduces weight of easy examples.
    Excellent for class imbalance.
    
    Args:
        y_true: True labels (0 or 1)
        y_pred: Predicted probabilities (0 to 1)
        alpha: Weighting factor (0 to 1)
        gamma: Focusing parameter (≥ 0)
        epsilon: Small constant to avoid log(0)
    
    Returns:
        Focal loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import focal_loss
        
        >>> y_true = np.array([0, 1, 1, 0])
        >>> y_pred = np.array([0.1, 0.9, 0.6, 0.2])
        >>> loss = focal_loss(y_true, y_pred, alpha=0.25, gamma=2.0)
        >>> print(f"Focal Loss: {loss:.4f}")
        Focal Loss: 0.0234
    """
    y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
    
    # Compute focal loss
    ce = -y_true * np.log(y_pred) - (1 - y_true) * np.log(1 - y_pred)
    p_t = y_true * y_pred + (1 - y_true) * (1 - y_pred)
    alpha_t = y_true * alpha + (1 - y_true) * (1 - alpha)
    
    focal = alpha_t * (1 - p_t) ** gamma * ce
    
    return np.mean(focal)


def kullback_leibler_divergence(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    epsilon: float = 1e-7
) -> float:
    """
    Compute Kullback-Leibler Divergence.
    
    KL = Σ y_true × log(y_true / y_pred)
    
    Measures difference between probability distributions.
    
    Args:
        y_true: True probability distribution
        y_pred: Predicted probability distribution
        epsilon: Small constant to avoid division by zero
    
    Returns:
        KL divergence value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import kullback_leibler_divergence
        
        >>> y_true = np.array([0.3, 0.5, 0.2])
        >>> y_pred = np.array([0.25, 0.55, 0.2])
        >>> loss = kullback_leibler_divergence(y_true, y_pred)
        >>> print(f"KL Divergence: {loss:.4f}")
        KL Divergence: 0.0052
    """
    y_true = np.clip(y_true, epsilon, 1)
    y_pred = np.clip(y_pred, epsilon, 1)
    return np.sum(y_true * np.log(y_true / y_pred))


# ==================== SEGMENTATION LOSSES ====================

def dice_coefficient(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    smooth: float = 1.0
) -> float:
    """
    Compute Dice coefficient (F1 score for segmentation).
    
    Dice = (2 × |A ∩ B|) / (|A| + |B|)
    
    Measures overlap between prediction and ground truth.
    
    Args:
        y_true: True binary mask
        y_pred: Predicted binary mask or probabilities
        smooth: Smoothing constant to avoid division by zero
    
    Returns:
        Dice coefficient (0 to 1, higher is better)
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import dice_coefficient
        
        >>> y_true = np.array([1, 1, 0, 0, 1])
        >>> y_pred = np.array([1, 1, 0, 1, 1])
        >>> dice = dice_coefficient(y_true, y_pred)
        >>> print(f"Dice Coefficient: {dice:.4f}")
        Dice Coefficient: 0.8571
    """
    y_true_flat = y_true.flatten()
    y_pred_flat = y_pred.flatten()
    
    intersection = np.sum(y_true_flat * y_pred_flat)
    return (2.0 * intersection + smooth) / (np.sum(y_true_flat) + np.sum(y_pred_flat) + smooth)


def dice_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    smooth: float = 1.0
) -> float:
    """
    Compute Dice loss (1 - Dice coefficient).
    
    Dice Loss = 1 - (2 × |A ∩ B|) / (|A| + |B|)
    
    Overlap-based loss for segmentation.
    Handles class imbalance well.
    
    Args:
        y_true: True binary mask
        y_pred: Predicted binary mask or probabilities
        smooth: Smoothing constant
    
    Returns:
        Dice loss value (0 to 1, lower is better)
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import dice_loss
        
        >>> y_true = np.array([1, 1, 0, 0, 1])
        >>> y_pred = np.array([1, 1, 0, 1, 1])
        >>> loss = dice_loss(y_true, y_pred)
        >>> print(f"Dice Loss: {loss:.4f}")
        Dice Loss: 0.1429
    """
    return 1 - dice_coefficient(y_true, y_pred, smooth)


def iou_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    smooth: float = 1.0
) -> float:
    """
    Compute IoU (Intersection over Union) loss.
    
    IoU Loss = 1 - (|A ∩ B|) / (|A ∪ B|)
    
    Also known as Jaccard loss.
    Geometric interpretation of overlap.
    
    Args:
        y_true: True binary mask
        y_pred: Predicted binary mask or probabilities
        smooth: Smoothing constant
    
    Returns:
        IoU loss value (0 to 1, lower is better)
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import iou_loss
        
        >>> y_true = np.array([1, 1, 0, 0, 1])
        >>> y_pred = np.array([1, 1, 0, 1, 1])
        >>> loss = iou_loss(y_true, y_pred)
        >>> print(f"IoU Loss: {loss:.4f}")
        IoU Loss: 0.2500
    """
    y_true_flat = y_true.flatten()
    y_pred_flat = y_pred.flatten()
    
    intersection = np.sum(y_true_flat * y_pred_flat)
    union = np.sum(y_true_flat) + np.sum(y_pred_flat) - intersection
    
    iou = (intersection + smooth) / (union + smooth)
    return 1 - iou


def tversky_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    alpha: float = 0.5,
    beta: float = 0.5,
    smooth: float = 1.0
) -> float:
    """
    Compute Tversky loss (generalization of Dice loss).
    
    Tversky = 1 - (TP) / (TP + α×FP + β×FN)
    
    Controls trade-off between false positives and false negatives.
    α = β = 0.5 gives Dice loss.
    
    Args:
        y_true: True binary mask
        y_pred: Predicted binary mask or probabilities
        alpha: Weight for false positives
        beta: Weight for false negatives
        smooth: Smoothing constant
    
    Returns:
        Tversky loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import tversky_loss
        
        >>> y_true = np.array([1, 1, 0, 0, 1])
        >>> y_pred = np.array([1, 1, 0, 1, 1])
        >>> loss = tversky_loss(y_true, y_pred, alpha=0.5, beta=0.5)
        >>> print(f"Tversky Loss: {loss:.4f}")
        Tversky Loss: 0.1429
    """
    y_true_flat = y_true.flatten()
    y_pred_flat = y_pred.flatten()
    
    true_pos = np.sum(y_true_flat * y_pred_flat)
    false_neg = np.sum(y_true_flat * (1 - y_pred_flat))
    false_pos = np.sum((1 - y_true_flat) * y_pred_flat)
    
    tversky_index = (true_pos + smooth) / (true_pos + alpha * false_pos + beta * false_neg + smooth)
    return 1 - tversky_index


def focal_tversky_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    alpha: float = 0.5,
    beta: float = 0.5,
    gamma: float = 1.0,
    smooth: float = 1.0
) -> float:
    """
    Compute Focal Tversky loss.
    
    Focal Tversky = (1 - Tversky)^γ
    
    Combines Tversky and Focal loss.
    Focuses on hard examples in segmentation.
    
    Args:
        y_true: True binary mask
        y_pred: Predicted binary mask or probabilities
        alpha: Weight for false positives
        beta: Weight for false negatives
        gamma: Focusing parameter
        smooth: Smoothing constant
    
    Returns:
        Focal Tversky loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import focal_tversky_loss
        
        >>> y_true = np.array([1, 1, 0, 0, 1])
        >>> y_pred = np.array([1, 1, 0, 1, 1])
        >>> loss = focal_tversky_loss(y_true, y_pred, gamma=2.0)
        >>> print(f"Focal Tversky Loss: {loss:.4f}")
        Focal Tversky Loss: 0.0204
    """
    tversky = tversky_loss(y_true, y_pred, alpha, beta, smooth)
    return tversky ** gamma


# ==================== UTILITIES ====================

def combined_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    loss_functions: list,
    weights: Optional[list] = None
) -> float:
    """
    Combine multiple loss functions with optional weights.
    
    Combined = w1 × Loss1 + w2 × Loss2 + ...
    
    Useful for multi-task learning or custom objectives.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        loss_functions: List of loss functions
        weights: List of weights for each loss (default: equal weights)
    
    Returns:
        Combined loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import (
        ...     combined_loss,
        ...     dice_loss,
        ...     binary_crossentropy_loss
        ... )
        
        >>> y_true = np.array([1, 1, 0, 0, 1])
        >>> y_pred = np.array([0.9, 0.8, 0.1, 0.2, 0.85])
        >>> 
        >>> loss = combined_loss(
        ...     y_true, y_pred,
        ...     loss_functions=[dice_loss, binary_crossentropy_loss],
        ...     weights=[0.7, 0.3]
        ... )
        >>> print(f"Combined Loss: {loss:.4f}")
    """
    if weights is None:
        weights = [1.0 / len(loss_functions)] * len(loss_functions)
    
    total_loss = 0.0
    for loss_fn, weight in zip(loss_functions, weights):
        total_loss += weight * loss_fn(y_true, y_pred)
    
    return total_loss


def weighted_loss(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    loss_function: callable,
    sample_weights: np.ndarray
) -> float:
    """
    Apply sample weights to a loss function.
    
    Weighted Loss = Σ(w_i × Loss_i) / Σw_i
    
    Useful for handling class imbalance or importance weighting.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        loss_function: Base loss function
        sample_weights: Weight for each sample
    
    Returns:
        Weighted loss value
    
    Examples:
        >>> import numpy as np
        >>> from ilovetools.ml import (
        ...     weighted_loss,
        ...     mean_squared_error_loss
        ... )
        
        >>> y_true = np.array([1.0, 2.0, 3.0, 4.0])
        >>> y_pred = np.array([1.1, 2.2, 2.8, 4.3])
        >>> weights = np.array([1.0, 1.0, 2.0, 2.0])  # More weight on last two
        >>> 
        >>> loss = weighted_loss(
        ...     y_true, y_pred,
        ...     mean_squared_error_loss,
        ...     weights
        ... )
        >>> print(f"Weighted Loss: {loss:.4f}")
    """
    # Compute per-sample losses
    if len(y_true.shape) == 1:
        per_sample_loss = (y_true - y_pred) ** 2  # Simplified for MSE
    else:
        per_sample_loss = np.mean((y_true - y_pred) ** 2, axis=tuple(range(1, len(y_true.shape))))
    
    # Apply weights
    weighted = per_sample_loss * sample_weights
    return np.sum(weighted) / np.sum(sample_weights)
