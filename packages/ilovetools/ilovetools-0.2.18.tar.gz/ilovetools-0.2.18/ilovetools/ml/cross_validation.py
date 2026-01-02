"""
Cross-validation utilities for ML workflows
Each function has TWO names: full descriptive name + abbreviated alias
"""

from typing import List, Tuple, Dict, Callable, Any, Optional
import random

__all__ = [
    # Full names
    'k_fold_cross_validation',
    'stratified_k_fold',
    'time_series_split',
    'leave_one_out_cv',
    'shuffle_split_cv',
    'cross_validate_score',
    'holdout_validation_split',
    'train_val_test_split',
    # Abbreviated aliases
    'kfold',
    'skfold',
    'tssplit',
    'loocv',
    'shuffle_cv',
    'cv_score',
    'holdout',
    'tvt_split',
]


def k_fold_cross_validation(
    X: List,
    y: List,
    k: int = 5,
    shuffle: bool = True,
    random_state: Optional[int] = None
) -> List[Tuple[List[int], List[int]]]:
    """
    K-Fold Cross-Validation split.
    
    Alias: kfold()
    
    Splits data into K folds. Each fold is used once as validation
    while remaining K-1 folds form training set.
    
    Args:
        X: Feature data
        y: Target data
        k: Number of folds. Default: 5
        shuffle: Shuffle data before splitting. Default: True
        random_state: Random seed for reproducibility
    
    Returns:
        list: List of (train_indices, val_indices) tuples
    
    Examples:
        >>> from ilovetools.ml import kfold  # Short alias
        >>> X = list(range(10))
        >>> y = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
        >>> folds = kfold(X, y, k=5)
        >>> len(folds)
        5
        >>> train_idx, val_idx = folds[0]
        >>> len(train_idx), len(val_idx)
        (8, 2)
        
        >>> from ilovetools.ml import k_fold_cross_validation  # Full name
        >>> folds = k_fold_cross_validation(X, y, k=3)
    
    Notes:
        - Most common CV method
        - Use k=5 or k=10 typically
        - Larger k = more training data per fold
        - Smaller k = faster computation
    """
    if len(X) != len(y):
        raise ValueError("X and y must have same length")
    
    n = len(X)
    indices = list(range(n))
    
    if shuffle:
        if random_state is not None:
            random.seed(random_state)
        random.shuffle(indices)
    
    fold_size = n // k
    folds = []
    
    for i in range(k):
        start = i * fold_size
        end = start + fold_size if i < k - 1 else n
        
        val_indices = indices[start:end]
        train_indices = indices[:start] + indices[end:]
        
        folds.append((train_indices, val_indices))
    
    return folds


# Create alias
kfold = k_fold_cross_validation


def stratified_k_fold(
    X: List,
    y: List,
    k: int = 5,
    shuffle: bool = True,
    random_state: Optional[int] = None
) -> List[Tuple[List[int], List[int]]]:
    """
    Stratified K-Fold Cross-Validation split.
    
    Alias: skfold()
    
    Like K-Fold but maintains class distribution in each fold.
    Essential for imbalanced datasets.
    
    Args:
        X: Feature data
        y: Target data (class labels)
        k: Number of folds. Default: 5
        shuffle: Shuffle data before splitting. Default: True
        random_state: Random seed for reproducibility
    
    Returns:
        list: List of (train_indices, val_indices) tuples
    
    Examples:
        >>> from ilovetools.ml import skfold  # Short alias
        >>> X = list(range(10))
        >>> y = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]  # Balanced
        >>> folds = skfold(X, y, k=5)
        
        >>> from ilovetools.ml import stratified_k_fold  # Full name
        >>> folds = stratified_k_fold(X, y, k=3)
        
        # Imbalanced dataset
        >>> y_imbalanced = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]  # 80-20 split
        >>> folds = skfold(X, y_imbalanced, k=5)
        # Each fold maintains 80-20 ratio
    
    Notes:
        - Use for imbalanced datasets
        - Maintains class distribution
        - More reliable than regular K-Fold
        - Slightly slower than K-Fold
    """
    if len(X) != len(y):
        raise ValueError("X and y must have same length")
    
    # Group indices by class
    class_indices = {}
    for idx, label in enumerate(y):
        if label not in class_indices:
            class_indices[label] = []
        class_indices[label].append(idx)
    
    # Shuffle within each class
    if shuffle:
        if random_state is not None:
            random.seed(random_state)
        for label in class_indices:
            random.shuffle(class_indices[label])
    
    # Create folds maintaining class distribution
    folds = [[] for _ in range(k)]
    
    for label, indices in class_indices.items():
        fold_size = len(indices) // k
        for i in range(k):
            start = i * fold_size
            end = start + fold_size if i < k - 1 else len(indices)
            folds[i].extend(indices[start:end])
    
    # Convert to train/val splits
    result = []
    all_indices = list(range(len(X)))
    
    for val_indices in folds:
        train_indices = [idx for idx in all_indices if idx not in val_indices]
        result.append((train_indices, val_indices))
    
    return result


# Create alias
skfold = stratified_k_fold


def time_series_split(
    X: List,
    y: List,
    n_splits: int = 5,
    test_size: Optional[int] = None
) -> List[Tuple[List[int], List[int]]]:
    """
    Time Series Cross-Validation split.
    
    Alias: tssplit()
    
    Respects temporal order. Training set always comes before test set.
    No future data leakage!
    
    Args:
        X: Feature data (time-ordered)
        y: Target data (time-ordered)
        n_splits: Number of splits. Default: 5
        test_size: Size of test set. If None, uses expanding window
    
    Returns:
        list: List of (train_indices, test_indices) tuples
    
    Examples:
        >>> from ilovetools.ml import tssplit  # Short alias
        >>> X = list(range(10))
        >>> y = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> splits = tssplit(X, y, n_splits=3)
        >>> len(splits)
        3
        
        >>> from ilovetools.ml import time_series_split  # Full name
        >>> splits = time_series_split(X, y, n_splits=5)
        
        # Stock price prediction
        >>> prices = [100, 102, 101, 105, 103, 107, 110, 108, 112, 115]
        >>> dates = list(range(len(prices)))
        >>> splits = tssplit(dates, prices, n_splits=3)
        # Each split: train on past, test on future
    
    Notes:
        - Essential for time series data
        - Prevents future data leakage
        - Training set grows over time
        - Use for: Stock prices, weather, sales
    """
    if len(X) != len(y):
        raise ValueError("X and y must have same length")
    
    n = len(X)
    
    if test_size is None:
        test_size = n // (n_splits + 1)
    
    splits = []
    
    for i in range(n_splits):
        test_start = (i + 1) * test_size
        test_end = test_start + test_size
        
        if test_end > n:
            break
        
        train_indices = list(range(test_start))
        test_indices = list(range(test_start, test_end))
        
        splits.append((train_indices, test_indices))
    
    return splits


# Create alias
tssplit = time_series_split


def leave_one_out_cv(X: List, y: List) -> List[Tuple[List[int], List[int]]]:
    """
    Leave-One-Out Cross-Validation.
    
    Alias: loocv()
    
    Each sample is used once as validation, rest as training.
    Maximum training data but computationally expensive.
    
    Args:
        X: Feature data
        y: Target data
    
    Returns:
        list: List of (train_indices, val_indices) tuples
    
    Examples:
        >>> from ilovetools.ml import loocv  # Short alias
        >>> X = [1, 2, 3, 4, 5]
        >>> y = [10, 20, 30, 40, 50]
        >>> splits = loocv(X, y)
        >>> len(splits)
        5
        >>> train_idx, val_idx = splits[0]
        >>> len(train_idx), len(val_idx)
        (4, 1)
        
        >>> from ilovetools.ml import leave_one_out_cv  # Full name
        >>> splits = leave_one_out_cv(X, y)
    
    Notes:
        - Maximum training data per fold
        - Very computationally expensive
        - Use for small datasets only
        - n_splits = n_samples
    """
    if len(X) != len(y):
        raise ValueError("X and y must have same length")
    
    n = len(X)
    splits = []
    
    for i in range(n):
        train_indices = list(range(i)) + list(range(i + 1, n))
        val_indices = [i]
        splits.append((train_indices, val_indices))
    
    return splits


# Create alias
loocv = leave_one_out_cv


def shuffle_split_cv(
    X: List,
    y: List,
    n_splits: int = 10,
    test_size: float = 0.2,
    random_state: Optional[int] = None
) -> List[Tuple[List[int], List[int]]]:
    """
    Shuffle Split Cross-Validation.
    
    Alias: shuffle_cv()
    
    Random permutation CV. Creates random train/test splits.
    
    Args:
        X: Feature data
        y: Target data
        n_splits: Number of splits. Default: 10
        test_size: Proportion of test set. Default: 0.2
        random_state: Random seed for reproducibility
    
    Returns:
        list: List of (train_indices, test_indices) tuples
    
    Examples:
        >>> from ilovetools.ml import shuffle_cv  # Short alias
        >>> X = list(range(10))
        >>> y = [0, 1] * 5
        >>> splits = shuffle_cv(X, y, n_splits=5, test_size=0.3)
        >>> len(splits)
        5
        
        >>> from ilovetools.ml import shuffle_split_cv  # Full name
        >>> splits = shuffle_split_cv(X, y, n_splits=3)
    
    Notes:
        - Random train/test splits
        - Samples can appear in multiple test sets
        - Good for large datasets
        - More flexible than K-Fold
    """
    if len(X) != len(y):
        raise ValueError("X and y must have same length")
    
    n = len(X)
    n_test = int(n * test_size)
    
    if random_state is not None:
        random.seed(random_state)
    
    splits = []
    
    for _ in range(n_splits):
        indices = list(range(n))
        random.shuffle(indices)
        
        test_indices = indices[:n_test]
        train_indices = indices[n_test:]
        
        splits.append((train_indices, test_indices))
    
    return splits


# Create alias
shuffle_cv = shuffle_split_cv


def cross_validate_score(
    X: List,
    y: List,
    model_func: Callable,
    metric_func: Callable,
    cv_method: str = 'kfold',
    k: int = 5
) -> Dict[str, Any]:
    """
    Perform cross-validation and return scores.
    
    Alias: cv_score()
    
    Args:
        X: Feature data
        y: Target data
        model_func: Function that trains and returns predictions
        metric_func: Function that calculates metric
        cv_method: CV method ('kfold', 'stratified', 'timeseries')
        k: Number of folds
    
    Returns:
        dict: CV results with scores and statistics
    
    Examples:
        >>> from ilovetools.ml import cv_score  # Short alias
        >>> X = [[1], [2], [3], [4], [5]]
        >>> y = [1, 2, 3, 4, 5]
        >>> 
        >>> def simple_model(X_train, y_train, X_val):
        ...     # Simple average predictor
        ...     avg = sum(y_train) / len(y_train)
        ...     return [avg] * len(X_val)
        >>> 
        >>> def mae_metric(y_true, y_pred):
        ...     return sum(abs(t - p) for t, p in zip(y_true, y_pred)) / len(y_true)
        >>> 
        >>> results = cv_score(X, y, simple_model, mae_metric, k=3)
        >>> print(results['mean_score'])
        
        >>> from ilovetools.ml import cross_validate_score  # Full name
        >>> results = cross_validate_score(X, y, simple_model, mae_metric)
    
    Notes:
        - Automates CV workflow
        - Returns mean, std, all scores
        - Flexible with any model/metric
        - Easy model comparison
    """
    # Get CV splits
    if cv_method == 'kfold':
        splits = k_fold_cross_validation(X, y, k=k)
    elif cv_method == 'stratified':
        splits = stratified_k_fold(X, y, k=k)
    elif cv_method == 'timeseries':
        splits = time_series_split(X, y, n_splits=k)
    else:
        splits = k_fold_cross_validation(X, y, k=k)
    
    scores = []
    
    for train_idx, val_idx in splits:
        X_train = [X[i] for i in train_idx]
        y_train = [y[i] for i in train_idx]
        X_val = [X[i] for i in val_idx]
        y_val = [y[i] for i in val_idx]
        
        # Train and predict
        y_pred = model_func(X_train, y_train, X_val)
        
        # Calculate metric
        score = metric_func(y_val, y_pred)
        scores.append(score)
    
    return {
        'scores': scores,
        'mean_score': sum(scores) / len(scores),
        'std_score': (sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)) ** 0.5,
        'n_splits': len(splits)
    }


# Create alias
cv_score = cross_validate_score


def holdout_validation_split(
    X: List,
    y: List,
    test_size: float = 0.2,
    random_state: Optional[int] = None
) -> Tuple[List, List, List, List]:
    """
    Simple holdout validation split.
    
    Alias: holdout()
    
    Single train/test split. Fast but less reliable than CV.
    
    Args:
        X: Feature data
        y: Target data
        test_size: Proportion of test set. Default: 0.2
        random_state: Random seed for reproducibility
    
    Returns:
        tuple: (X_train, X_test, y_train, y_test)
    
    Examples:
        >>> from ilovetools.ml import holdout  # Short alias
        >>> X = list(range(10))
        >>> y = [0, 1] * 5
        >>> X_train, X_test, y_train, y_test = holdout(X, y, test_size=0.3)
        >>> len(X_train), len(X_test)
        (7, 3)
        
        >>> from ilovetools.ml import holdout_validation_split  # Full name
        >>> X_train, X_test, y_train, y_test = holdout_validation_split(X, y)
    
    Notes:
        - Fastest validation method
        - Less reliable than CV
        - Use for quick experiments
        - Good for large datasets
    """
    if len(X) != len(y):
        raise ValueError("X and y must have same length")
    
    n = len(X)
    n_test = int(n * test_size)
    
    indices = list(range(n))
    
    if random_state is not None:
        random.seed(random_state)
    random.shuffle(indices)
    
    test_indices = indices[:n_test]
    train_indices = indices[n_test:]
    
    X_train = [X[i] for i in train_indices]
    X_test = [X[i] for i in test_indices]
    y_train = [y[i] for i in train_indices]
    y_test = [y[i] for i in test_indices]
    
    return X_train, X_test, y_train, y_test


# Create alias
holdout = holdout_validation_split


def train_val_test_split(
    X: List,
    y: List,
    val_size: float = 0.2,
    test_size: float = 0.2,
    random_state: Optional[int] = None
) -> Tuple[List, List, List, List, List, List]:
    """
    Three-way split: train, validation, test.
    
    Alias: tvt_split()
    
    Creates separate train, validation, and test sets.
    
    Args:
        X: Feature data
        y: Target data
        val_size: Proportion of validation set. Default: 0.2
        test_size: Proportion of test set. Default: 0.2
        random_state: Random seed for reproducibility
    
    Returns:
        tuple: (X_train, X_val, X_test, y_train, y_val, y_test)
    
    Examples:
        >>> from ilovetools.ml import tvt_split  # Short alias
        >>> X = list(range(10))
        >>> y = [0, 1] * 5
        >>> X_tr, X_val, X_te, y_tr, y_val, y_te = tvt_split(X, y)
        >>> len(X_tr), len(X_val), len(X_te)
        (6, 2, 2)
        
        >>> from ilovetools.ml import train_val_test_split  # Full name
        >>> splits = train_val_test_split(X, y, val_size=0.15, test_size=0.15)
    
    Notes:
        - Standard ML workflow split
        - Train: Model training
        - Val: Hyperparameter tuning
        - Test: Final evaluation
        - Typical: 60-20-20 or 70-15-15
    """
    if len(X) != len(y):
        raise ValueError("X and y must have same length")
    
    n = len(X)
    n_test = int(n * test_size)
    n_val = int(n * val_size)
    
    indices = list(range(n))
    
    if random_state is not None:
        random.seed(random_state)
    random.shuffle(indices)
    
    test_indices = indices[:n_test]
    val_indices = indices[n_test:n_test + n_val]
    train_indices = indices[n_test + n_val:]
    
    X_train = [X[i] for i in train_indices]
    X_val = [X[i] for i in val_indices]
    X_test = [X[i] for i in test_indices]
    y_train = [y[i] for i in train_indices]
    y_val = [y[i] for i in val_indices]
    y_test = [y[i] for i in test_indices]
    
    return X_train, X_val, X_test, y_train, y_val, y_test


# Create alias
tvt_split = train_val_test_split
