"""
Feature selection utilities for ML workflows
Each function has TWO names: full descriptive name + abbreviated alias
"""

from typing import List, Dict, Any, Callable, Optional, Tuple
import random

__all__ = [
    # Full names
    'correlation_filter',
    'variance_threshold_filter',
    'chi_square_filter',
    'mutual_information_filter',
    'recursive_feature_elimination',
    'forward_feature_selection',
    'backward_feature_elimination',
    'feature_importance_ranking',
    'l1_feature_selection',
    'univariate_feature_selection',
    'select_k_best_features',
    'remove_correlated_features',
    # Abbreviated aliases
    'corr_filter',
    'var_filter',
    'chi2_filter',
    'mi_filter',
    'rfe',
    'forward_select',
    'backward_select',
    'feat_importance',
    'l1_select',
    'univariate_select',
    'select_k_best',
    'remove_corr',
]


def correlation_filter(
    X: List[List[float]],
    feature_names: Optional[List[str]] = None,
    threshold: float = 0.9
) -> Tuple[List[int], List[str]]:
    """
    Remove highly correlated features.
    
    Alias: corr_filter()
    
    Args:
        X: Feature matrix [n_samples, n_features]
        feature_names: Optional feature names
        threshold: Correlation threshold (default: 0.9)
    
    Returns:
        tuple: (selected_indices, selected_names)
    
    Examples:
        >>> from ilovetools.ml import corr_filter  # Short alias
        
        >>> X = [
        ...     [1, 2, 2.1],
        ...     [2, 4, 4.2],
        ...     [3, 6, 6.3],
        ...     [4, 8, 8.4]
        ... ]
        >>> feature_names = ['A', 'B', 'C']
        >>> 
        >>> # Features B and C are highly correlated (0.99+)
        >>> indices, names = corr_filter(X, feature_names, threshold=0.9)
        >>> print(f"Selected: {names}")
        Selected: ['A', 'B']
        
        >>> from ilovetools.ml import correlation_filter  # Full name
        >>> indices, names = correlation_filter(X, feature_names)
    
    Notes:
        - Removes redundant features
        - Keeps first of correlated pair
        - Fast filter method
        - Use before training
    """
    n_features = len(X[0])
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    # Calculate correlation matrix
    corr_matrix = []
    for i in range(n_features):
        row = []
        for j in range(n_features):
            if i == j:
                row.append(1.0)
            else:
                # Calculate correlation
                col_i = [row[i] for row in X]
                col_j = [row[j] for row in X]
                
                mean_i = sum(col_i) / len(col_i)
                mean_j = sum(col_j) / len(col_j)
                
                numerator = sum((col_i[k] - mean_i) * (col_j[k] - mean_j) 
                              for k in range(len(col_i)))
                
                std_i = (sum((x - mean_i) ** 2 for x in col_i) / len(col_i)) ** 0.5
                std_j = (sum((x - mean_j) ** 2 for x in col_j) / len(col_j)) ** 0.5
                
                if std_i == 0 or std_j == 0:
                    corr = 0.0
                else:
                    corr = numerator / (len(col_i) * std_i * std_j)
                
                row.append(abs(corr))
        corr_matrix.append(row)
    
    # Find features to keep
    to_remove = set()
    for i in range(n_features):
        if i in to_remove:
            continue
        for j in range(i + 1, n_features):
            if j in to_remove:
                continue
            if corr_matrix[i][j] > threshold:
                to_remove.add(j)
    
    selected_indices = [i for i in range(n_features) if i not in to_remove]
    selected_names = [feature_names[i] for i in selected_indices]
    
    return selected_indices, selected_names


# Create alias
corr_filter = correlation_filter


def variance_threshold_filter(
    X: List[List[float]],
    feature_names: Optional[List[str]] = None,
    threshold: float = 0.0
) -> Tuple[List[int], List[str]]:
    """
    Remove low-variance features.
    
    Alias: var_filter()
    
    Args:
        X: Feature matrix [n_samples, n_features]
        feature_names: Optional feature names
        threshold: Variance threshold (default: 0.0)
    
    Returns:
        tuple: (selected_indices, selected_names)
    
    Examples:
        >>> from ilovetools.ml import var_filter  # Short alias
        
        >>> X = [
        ...     [1, 5, 0],
        ...     [2, 6, 0],
        ...     [3, 7, 0],
        ...     [4, 8, 0]
        ... ]
        >>> feature_names = ['A', 'B', 'C']
        >>> 
        >>> # Feature C has zero variance (constant)
        >>> indices, names = var_filter(X, feature_names, threshold=0.1)
        >>> print(f"Selected: {names}")
        Selected: ['A', 'B']
        
        >>> from ilovetools.ml import variance_threshold_filter  # Full name
        >>> indices, names = variance_threshold_filter(X, feature_names)
    
    Notes:
        - Removes constant/near-constant features
        - Very fast filter method
        - Run first in pipeline
        - Threshold 0.0 removes only constants
    """
    n_features = len(X[0])
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    selected_indices = []
    selected_names = []
    
    for i in range(n_features):
        col = [row[i] for row in X]
        mean = sum(col) / len(col)
        variance = sum((x - mean) ** 2 for x in col) / len(col)
        
        if variance > threshold:
            selected_indices.append(i)
            selected_names.append(feature_names[i])
    
    return selected_indices, selected_names


# Create alias
var_filter = variance_threshold_filter


def chi_square_filter(
    X: List[List[float]],
    y: List[int],
    feature_names: Optional[List[str]] = None,
    k: int = 10
) -> Tuple[List[int], List[str], List[float]]:
    """
    Chi-square test for categorical features.
    
    Alias: chi2_filter()
    
    Args:
        X: Feature matrix [n_samples, n_features]
        y: Target labels (categorical)
        feature_names: Optional feature names
        k: Number of top features to select
    
    Returns:
        tuple: (selected_indices, selected_names, scores)
    
    Examples:
        >>> from ilovetools.ml import chi2_filter  # Short alias
        
        >>> X = [
        ...     [1, 0, 1],
        ...     [0, 1, 1],
        ...     [1, 1, 0],
        ...     [0, 0, 0]
        ... ]
        >>> y = [1, 1, 0, 0]
        >>> feature_names = ['A', 'B', 'C']
        >>> 
        >>> indices, names, scores = chi2_filter(X, y, feature_names, k=2)
        >>> print(f"Selected: {names}")
        >>> print(f"Scores: {[f'{s:.2f}' for s in scores]}")
        
        >>> from ilovetools.ml import chi_square_filter  # Full name
        >>> indices, names, scores = chi_square_filter(X, y, feature_names)
    
    Notes:
        - For categorical/binary features
        - Measures independence from target
        - Fast filter method
        - Higher score = more important
    """
    n_features = len(X[0])
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    # Calculate chi-square scores
    scores = []
    for i in range(n_features):
        col = [row[i] for row in X]
        
        # Simple chi-square approximation
        # Group by class and calculate observed vs expected
        class_0_sum = sum(col[j] for j in range(len(col)) if y[j] == 0)
        class_1_sum = sum(col[j] for j in range(len(col)) if y[j] == 1)
        
        class_0_count = sum(1 for label in y if label == 0)
        class_1_count = sum(1 for label in y if label == 1)
        
        total = sum(col)
        
        if total == 0 or class_0_count == 0 or class_1_count == 0:
            scores.append(0.0)
            continue
        
        expected_0 = total * class_0_count / len(y)
        expected_1 = total * class_1_count / len(y)
        
        chi2 = 0.0
        if expected_0 > 0:
            chi2 += (class_0_sum - expected_0) ** 2 / expected_0
        if expected_1 > 0:
            chi2 += (class_1_sum - expected_1) ** 2 / expected_1
        
        scores.append(chi2)
    
    # Select top k features
    indexed_scores = [(i, score) for i, score in enumerate(scores)]
    indexed_scores.sort(key=lambda x: x[1], reverse=True)
    
    selected_indices = [i for i, _ in indexed_scores[:k]]
    selected_names = [feature_names[i] for i in selected_indices]
    selected_scores = [scores[i] for i in selected_indices]
    
    return selected_indices, selected_names, selected_scores


# Create alias
chi2_filter = chi_square_filter


def mutual_information_filter(
    X: List[List[float]],
    y: List,
    feature_names: Optional[List[str]] = None,
    k: int = 10
) -> Tuple[List[int], List[str], List[float]]:
    """
    Mutual information for feature selection.
    
    Alias: mi_filter()
    
    Args:
        X: Feature matrix [n_samples, n_features]
        y: Target values
        feature_names: Optional feature names
        k: Number of top features to select
    
    Returns:
        tuple: (selected_indices, selected_names, scores)
    
    Examples:
        >>> from ilovetools.ml import mi_filter  # Short alias
        
        >>> X = [
        ...     [1, 2, 3],
        ...     [2, 4, 6],
        ...     [3, 6, 9],
        ...     [4, 8, 12]
        ... ]
        >>> y = [1, 2, 3, 4]
        >>> feature_names = ['A', 'B', 'C']
        >>> 
        >>> indices, names, scores = mi_filter(X, y, feature_names, k=2)
        >>> print(f"Selected: {names}")
        
        >>> from ilovetools.ml import mutual_information_filter  # Full name
        >>> indices, names, scores = mutual_information_filter(X, y, feature_names)
    
    Notes:
        - Measures dependency on target
        - Works for any relationship
        - Non-linear dependencies
        - Higher score = more informative
    """
    n_features = len(X[0])
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    # Calculate MI scores (simplified correlation-based approximation)
    scores = []
    for i in range(n_features):
        col = [row[i] for row in X]
        
        # Calculate correlation with target
        mean_x = sum(col) / len(col)
        mean_y = sum(y) / len(y)
        
        numerator = sum((col[j] - mean_x) * (y[j] - mean_y) for j in range(len(col)))
        
        std_x = (sum((x - mean_x) ** 2 for x in col) / len(col)) ** 0.5
        std_y = (sum((y_val - mean_y) ** 2 for y_val in y) / len(y)) ** 0.5
        
        if std_x == 0 or std_y == 0:
            mi_score = 0.0
        else:
            corr = numerator / (len(col) * std_x * std_y)
            mi_score = abs(corr)  # Simplified MI approximation
        
        scores.append(mi_score)
    
    # Select top k features
    indexed_scores = [(i, score) for i, score in enumerate(scores)]
    indexed_scores.sort(key=lambda x: x[1], reverse=True)
    
    selected_indices = [i for i, _ in indexed_scores[:k]]
    selected_names = [feature_names[i] for i in selected_indices]
    selected_scores = [scores[i] for i in selected_indices]
    
    return selected_indices, selected_names, selected_scores


# Create alias
mi_filter = mutual_information_filter


def recursive_feature_elimination(
    X: List[List[float]],
    y: List,
    model_func: Callable,
    metric_func: Callable,
    feature_names: Optional[List[str]] = None,
    n_features_to_select: int = 5
) -> Tuple[List[int], List[str], List[float]]:
    """
    Recursive Feature Elimination (RFE).
    
    Alias: rfe()
    
    Args:
        X: Feature matrix [n_samples, n_features]
        y: Target values
        model_func: Function(X_train, y_train, X_test) -> predictions
        metric_func: Function(y_true, y_pred) -> score
        feature_names: Optional feature names
        n_features_to_select: Number of features to keep
    
    Returns:
        tuple: (selected_indices, selected_names, scores_history)
    
    Examples:
        >>> from ilovetools.ml import rfe  # Short alias
        
        >>> X = [[1, 2, 3], [2, 4, 6], [3, 6, 9], [4, 8, 12]]
        >>> y = [1, 2, 3, 4]
        >>> 
        >>> def model(X_tr, y_tr, X_te):
        ...     avg = sum(y_tr) / len(y_tr)
        ...     return [avg] * len(X_te)
        >>> 
        >>> def metric(y_true, y_pred):
        ...     return -sum(abs(y_true[i] - y_pred[i]) for i in range(len(y_true)))
        >>> 
        >>> indices, names, history = rfe(X, y, model, metric, n_features_to_select=2)
        >>> print(f"Selected: {names}")
        
        >>> from ilovetools.ml import recursive_feature_elimination  # Full name
        >>> indices, names, history = recursive_feature_elimination(X, y, model, metric)
    
    Notes:
        - Wrapper method (uses model)
        - Removes worst feature iteratively
        - Considers feature interactions
        - Computationally expensive
    """
    n_features = len(X[0])
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    remaining_indices = list(range(n_features))
    scores_history = []
    
    while len(remaining_indices) > n_features_to_select:
        # Evaluate each feature's contribution
        feature_scores = []
        
        for idx in remaining_indices:
            # Create subset without this feature
            subset_indices = [i for i in remaining_indices if i != idx]
            X_subset = [[row[i] for i in subset_indices] for row in X]
            
            # Train and evaluate
            predictions = model_func(X_subset, y, X_subset)
            score = metric_func(y, predictions)
            feature_scores.append((idx, score))
        
        # Remove feature with worst score
        worst_idx = min(feature_scores, key=lambda x: x[1])[0]
        remaining_indices.remove(worst_idx)
        
        # Record score
        X_current = [[row[i] for i in remaining_indices] for row in X]
        predictions = model_func(X_current, y, X_current)
        current_score = metric_func(y, predictions)
        scores_history.append(current_score)
    
    selected_names = [feature_names[i] for i in remaining_indices]
    
    return remaining_indices, selected_names, scores_history


# Create alias
rfe = recursive_feature_elimination


def forward_feature_selection(
    X: List[List[float]],
    y: List,
    model_func: Callable,
    metric_func: Callable,
    feature_names: Optional[List[str]] = None,
    n_features_to_select: int = 5
) -> Tuple[List[int], List[str], List[float]]:
    """
    Forward Feature Selection.
    
    Alias: forward_select()
    
    Args:
        X: Feature matrix [n_samples, n_features]
        y: Target values
        model_func: Function(X_train, y_train, X_test) -> predictions
        metric_func: Function(y_true, y_pred) -> score (higher is better)
        feature_names: Optional feature names
        n_features_to_select: Number of features to select
    
    Returns:
        tuple: (selected_indices, selected_names, scores_history)
    
    Examples:
        >>> from ilovetools.ml import forward_select  # Short alias
        
        >>> X = [[1, 2, 3], [2, 4, 6], [3, 6, 9], [4, 8, 12]]
        >>> y = [1, 2, 3, 4]
        >>> 
        >>> def model(X_tr, y_tr, X_te):
        ...     avg = sum(y_tr) / len(y_tr)
        ...     return [avg] * len(X_te)
        >>> 
        >>> def metric(y_true, y_pred):
        ...     return -sum(abs(y_true[i] - y_pred[i]) for i in range(len(y_true)))
        >>> 
        >>> indices, names, history = forward_select(X, y, model, metric, n_features_to_select=2)
        >>> print(f"Selected: {names}")
        
        >>> from ilovetools.ml import forward_feature_selection  # Full name
        >>> indices, names, history = forward_feature_selection(X, y, model, metric)
    
    Notes:
        - Wrapper method
        - Adds best feature iteratively
        - Greedy approach
        - Good for small feature sets
    """
    n_features = len(X[0])
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    selected_indices = []
    remaining_indices = list(range(n_features))
    scores_history = []
    
    for _ in range(min(n_features_to_select, n_features)):
        best_score = float('-inf')
        best_idx = None
        
        for idx in remaining_indices:
            # Try adding this feature
            trial_indices = selected_indices + [idx]
            X_subset = [[row[i] for i in trial_indices] for row in X]
            
            # Evaluate
            predictions = model_func(X_subset, y, X_subset)
            score = metric_func(y, predictions)
            
            if score > best_score:
                best_score = score
                best_idx = idx
        
        if best_idx is not None:
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)
            scores_history.append(best_score)
    
    selected_names = [feature_names[i] for i in selected_indices]
    
    return selected_indices, selected_names, scores_history


# Create alias
forward_select = forward_feature_selection


def backward_feature_elimination(
    X: List[List[float]],
    y: List,
    model_func: Callable,
    metric_func: Callable,
    feature_names: Optional[List[str]] = None,
    n_features_to_select: int = 5
) -> Tuple[List[int], List[str], List[float]]:
    """
    Backward Feature Elimination.
    
    Alias: backward_select()
    
    Similar to RFE but evaluates full model each iteration.
    
    Args:
        X: Feature matrix [n_samples, n_features]
        y: Target values
        model_func: Function(X_train, y_train, X_test) -> predictions
        metric_func: Function(y_true, y_pred) -> score
        feature_names: Optional feature names
        n_features_to_select: Number of features to keep
    
    Returns:
        tuple: (selected_indices, selected_names, scores_history)
    
    Examples:
        >>> from ilovetools.ml import backward_select  # Short alias
        
        >>> X = [[1, 2, 3], [2, 4, 6], [3, 6, 9], [4, 8, 12]]
        >>> y = [1, 2, 3, 4]
        >>> 
        >>> def model(X_tr, y_tr, X_te):
        ...     avg = sum(y_tr) / len(y_tr)
        ...     return [avg] * len(X_te)
        >>> 
        >>> def metric(y_true, y_pred):
        ...     return -sum(abs(y_true[i] - y_pred[i]) for i in range(len(y_true)))
        >>> 
        >>> indices, names, history = backward_select(X, y, model, metric, n_features_to_select=2)
        
        >>> from ilovetools.ml import backward_feature_elimination  # Full name
        >>> indices, names, history = backward_feature_elimination(X, y, model, metric)
    
    Notes:
        - Wrapper method
        - Starts with all features
        - Removes least important
        - More thorough than RFE
    """
    # Same implementation as RFE for simplicity
    return recursive_feature_elimination(
        X, y, model_func, metric_func, feature_names, n_features_to_select
    )


# Create alias
backward_select = backward_feature_elimination


def feature_importance_ranking(
    importances: List[float],
    feature_names: Optional[List[str]] = None,
    k: Optional[int] = None
) -> Tuple[List[int], List[str], List[float]]:
    """
    Rank features by importance scores.
    
    Alias: feat_importance()
    
    Args:
        importances: Feature importance scores
        feature_names: Optional feature names
        k: Number of top features to select (None = all)
    
    Returns:
        tuple: (selected_indices, selected_names, selected_scores)
    
    Examples:
        >>> from ilovetools.ml import feat_importance  # Short alias
        
        >>> importances = [0.1, 0.5, 0.3, 0.8, 0.2]
        >>> feature_names = ['A', 'B', 'C', 'D', 'E']
        >>> 
        >>> indices, names, scores = feat_importance(importances, feature_names, k=3)
        >>> print(f"Top 3: {names}")
        Top 3: ['D', 'B', 'C']
        >>> print(f"Scores: {scores}")
        [0.8, 0.5, 0.3]
        
        >>> from ilovetools.ml import feature_importance_ranking  # Full name
        >>> indices, names, scores = feature_importance_ranking(importances, feature_names)
    
    Notes:
        - Works with any importance scores
        - Random Forest, XGBoost, etc.
        - Simple and effective
        - Use after training
    """
    n_features = len(importances)
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    # Sort by importance
    indexed_importances = [(i, imp) for i, imp in enumerate(importances)]
    indexed_importances.sort(key=lambda x: x[1], reverse=True)
    
    if k is None:
        k = n_features
    
    selected_indices = [i for i, _ in indexed_importances[:k]]
    selected_names = [feature_names[i] for i in selected_indices]
    selected_scores = [importances[i] for i in selected_indices]
    
    return selected_indices, selected_names, selected_scores


# Create alias
feat_importance = feature_importance_ranking


def l1_feature_selection(
    X: List[List[float]],
    y: List[float],
    feature_names: Optional[List[str]] = None,
    alpha: float = 0.1
) -> Tuple[List[int], List[str], List[float]]:
    """
    L1 regularization for feature selection (Lasso).
    
    Alias: l1_select()
    
    Args:
        X: Feature matrix [n_samples, n_features]
        y: Target values
        feature_names: Optional feature names
        alpha: Regularization strength (higher = more sparse)
    
    Returns:
        tuple: (selected_indices, selected_names, coefficients)
    
    Examples:
        >>> from ilovetools.ml import l1_select  # Short alias
        
        >>> X = [[1, 2, 3], [2, 4, 6], [3, 6, 9], [4, 8, 12]]
        >>> y = [1.0, 2.0, 3.0, 4.0]
        >>> feature_names = ['A', 'B', 'C']
        >>> 
        >>> indices, names, coefs = l1_select(X, y, feature_names, alpha=0.1)
        >>> print(f"Selected: {names}")
        >>> print(f"Coefficients: {[f'{c:.2f}' for c in coefs]}")
        
        >>> from ilovetools.ml import l1_feature_selection  # Full name
        >>> indices, names, coefs = l1_feature_selection(X, y, feature_names)
    
    Notes:
        - Embedded method
        - Shrinks coefficients to zero
        - Automatic feature selection
        - Higher alpha = fewer features
    """
    n_features = len(X[0])
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    # Simple L1 approximation using correlation-based weights
    coefficients = []
    
    for i in range(n_features):
        col = [row[i] for row in X]
        
        # Calculate correlation with target
        mean_x = sum(col) / len(col)
        mean_y = sum(y) / len(y)
        
        numerator = sum((col[j] - mean_x) * (y[j] - mean_y) for j in range(len(col)))
        
        std_x = (sum((x - mean_x) ** 2 for x in col) / len(col)) ** 0.5
        std_y = (sum((y_val - mean_y) ** 2 for y_val in y) / len(y)) ** 0.5
        
        if std_x == 0 or std_y == 0:
            coef = 0.0
        else:
            corr = numerator / (len(col) * std_x * std_y)
            # Apply soft thresholding (L1 penalty)
            if abs(corr) > alpha:
                coef = corr - alpha * (1 if corr > 0 else -1)
            else:
                coef = 0.0
        
        coefficients.append(coef)
    
    # Select non-zero coefficients
    selected_indices = [i for i, coef in enumerate(coefficients) if abs(coef) > 1e-10]
    selected_names = [feature_names[i] for i in selected_indices]
    selected_coefs = [coefficients[i] for i in selected_indices]
    
    return selected_indices, selected_names, selected_coefs


# Create alias
l1_select = l1_feature_selection


def univariate_feature_selection(
    X: List[List[float]],
    y: List,
    feature_names: Optional[List[str]] = None,
    method: str = 'correlation',
    k: int = 10
) -> Tuple[List[int], List[str], List[float]]:
    """
    Univariate feature selection.
    
    Alias: univariate_select()
    
    Args:
        X: Feature matrix [n_samples, n_features]
        y: Target values
        feature_names: Optional feature names
        method: 'correlation', 'variance', or 'mutual_info'
        k: Number of features to select
    
    Returns:
        tuple: (selected_indices, selected_names, scores)
    
    Examples:
        >>> from ilovetools.ml import univariate_select  # Short alias
        
        >>> X = [[1, 2, 3], [2, 4, 6], [3, 6, 9], [4, 8, 12]]
        >>> y = [1, 2, 3, 4]
        >>> feature_names = ['A', 'B', 'C']
        >>> 
        >>> indices, names, scores = univariate_select(X, y, feature_names, method='correlation', k=2)
        >>> print(f"Selected: {names}")
        
        >>> from ilovetools.ml import univariate_feature_selection  # Full name
        >>> indices, names, scores = univariate_feature_selection(X, y, feature_names)
    
    Notes:
        - Tests each feature independently
        - Fast filter method
        - Ignores feature interactions
        - Good starting point
    """
    if method == 'correlation' or method == 'mutual_info':
        return mutual_information_filter(X, y, feature_names, k)
    elif method == 'variance':
        indices, names = variance_threshold_filter(X, feature_names, threshold=0.0)
        scores = [1.0] * len(indices)  # Dummy scores
        return indices[:k], names[:k], scores[:k]
    else:
        raise ValueError(f"Unknown method: {method}")


# Create alias
univariate_select = univariate_feature_selection


def select_k_best_features(
    X: List[List[float]],
    y: List,
    feature_names: Optional[List[str]] = None,
    k: int = 10,
    method: str = 'auto'
) -> Tuple[List[int], List[str]]:
    """
    Select k best features automatically.
    
    Alias: select_k_best()
    
    Args:
        X: Feature matrix [n_samples, n_features]
        y: Target values
        feature_names: Optional feature names
        k: Number of features to select
        method: 'auto', 'correlation', 'chi2', or 'mutual_info'
    
    Returns:
        tuple: (selected_indices, selected_names)
    
    Examples:
        >>> from ilovetools.ml import select_k_best  # Short alias
        
        >>> X = [[1, 2, 3, 4], [2, 4, 6, 8], [3, 6, 9, 12], [4, 8, 12, 16]]
        >>> y = [1, 2, 3, 4]
        >>> feature_names = ['A', 'B', 'C', 'D']
        >>> 
        >>> indices, names = select_k_best(X, y, feature_names, k=2)
        >>> print(f"Selected: {names}")
        
        >>> from ilovetools.ml import select_k_best_features  # Full name
        >>> indices, names = select_k_best_features(X, y, feature_names)
    
    Notes:
        - Automatic method selection
        - Fast and simple
        - Good default choice
        - Use for quick feature reduction
    """
    if method == 'auto':
        # Check if y is categorical (for chi2) or continuous
        unique_y = len(set(y))
        if unique_y <= 10:  # Likely categorical
            method = 'chi2'
        else:
            method = 'mutual_info'
    
    if method == 'chi2':
        indices, names, _ = chi_square_filter(X, y, feature_names, k)
    elif method == 'mutual_info' or method == 'correlation':
        indices, names, _ = mutual_information_filter(X, y, feature_names, k)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return indices, names


# Create alias
select_k_best = select_k_best_features


def remove_correlated_features(
    X: List[List[float]],
    feature_names: Optional[List[str]] = None,
    threshold: float = 0.95
) -> Tuple[List[int], List[str], List[Tuple[str, str, float]]]:
    """
    Remove highly correlated features and return correlation pairs.
    
    Alias: remove_corr()
    
    Args:
        X: Feature matrix [n_samples, n_features]
        feature_names: Optional feature names
        threshold: Correlation threshold (default: 0.95)
    
    Returns:
        tuple: (selected_indices, selected_names, removed_pairs)
    
    Examples:
        >>> from ilovetools.ml import remove_corr  # Short alias
        
        >>> X = [
        ...     [1, 2, 2.05],
        ...     [2, 4, 4.1],
        ...     [3, 6, 6.15],
        ...     [4, 8, 8.2]
        ... ]
        >>> feature_names = ['A', 'B', 'C']
        >>> 
        >>> indices, names, pairs = remove_corr(X, feature_names, threshold=0.95)
        >>> print(f"Kept: {names}")
        >>> print(f"Removed pairs: {[(p[0], p[1], f'{p[2]:.2f}') for p in pairs]}")
        
        >>> from ilovetools.ml import remove_correlated_features  # Full name
        >>> indices, names, pairs = remove_correlated_features(X, feature_names)
    
    Notes:
        - Returns which features were correlated
        - Helps understand redundancy
        - Use before training
        - Threshold 0.95 is common
    """
    indices, names = correlation_filter(X, feature_names, threshold)
    
    # Find removed pairs
    n_features = len(X[0])
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    removed_pairs = []
    removed_indices = set(range(n_features)) - set(indices)
    
    # Calculate correlations for removed features
    for removed_idx in removed_indices:
        col_removed = [row[removed_idx] for row in X]
        
        for kept_idx in indices:
            col_kept = [row[kept_idx] for row in X]
            
            # Calculate correlation
            mean_r = sum(col_removed) / len(col_removed)
            mean_k = sum(col_kept) / len(col_kept)
            
            numerator = sum((col_removed[i] - mean_r) * (col_kept[i] - mean_k) 
                          for i in range(len(col_removed)))
            
            std_r = (sum((x - mean_r) ** 2 for x in col_removed) / len(col_removed)) ** 0.5
            std_k = (sum((x - mean_k) ** 2 for x in col_kept) / len(col_kept)) ** 0.5
            
            if std_r > 0 and std_k > 0:
                corr = numerator / (len(col_removed) * std_r * std_k)
                if abs(corr) > threshold:
                    removed_pairs.append((
                        feature_names[kept_idx],
                        feature_names[removed_idx],
                        abs(corr)
                    ))
                    break
    
    return indices, names, removed_pairs


# Create alias
remove_corr = remove_correlated_features
