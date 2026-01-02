"""
Data preprocessing utilities
"""

import random
from typing import Tuple, List, Union, Optional
import numpy as np

__all__ = ['train_test_split', 'normalize_data', 'standardize_data']


def train_test_split(
    X: Union[List, np.ndarray],
    y: Optional[Union[List, np.ndarray]] = None,
    test_size: float = 0.2,
    random_state: Optional[int] = None,
    shuffle: bool = True,
    stratify: bool = False
) -> Union[Tuple[List, List], Tuple[List, List, List, List]]:
    """
    Split arrays or lists into random train and test subsets.
    
    Perfect for ML workflows - implements the fundamental train-test split
    pattern without requiring scikit-learn. Supports stratified splitting
    to maintain class distribution.
    
    Args:
        X: Features array/list to split
        y: Target array/list to split (optional)
        test_size: Proportion of dataset for test set (0.0 to 1.0). Default: 0.2
        random_state: Random seed for reproducibility. Default: None
        shuffle: Whether to shuffle data before splitting. Default: True
        stratify: Maintain class distribution in splits (requires y). Default: False
    
    Returns:
        If y is None: (X_train, X_test)
        If y is provided: (X_train, X_test, y_train, y_test)
    
    Examples:
        >>> from ilovetools.data import train_test_split
        
        # Basic split
        >>> X = [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]]
        >>> y = [0, 1, 0, 1, 0]
        >>> X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        >>> len(X_train), len(X_test)
        (4, 1)
        
        # With random seed for reproducibility
        >>> X_train, X_test, y_train, y_test = train_test_split(
        ...     X, y, test_size=0.3, random_state=42
        ... )
        
        # Stratified split (maintains class distribution)
        >>> X_train, X_test, y_train, y_test = train_test_split(
        ...     X, y, test_size=0.2, stratify=True, random_state=42
        ... )
        
        # Split features only (no labels)
        >>> data = list(range(100))
        >>> train, test = train_test_split(data, test_size=0.2)
        >>> len(train), len(test)
        (80, 20)
        
        # Real-world example: Email spam detection
        >>> emails = ["email1", "email2", "email3", "email4", "email5"]
        >>> labels = [1, 0, 1, 0, 1]  # 1=spam, 0=not spam
        >>> X_train, X_test, y_train, y_test = train_test_split(
        ...     emails, labels, test_size=0.2, random_state=42
        ... )
        
        # 70-30 split
        >>> X_train, X_test, y_train, y_test = train_test_split(
        ...     X, y, test_size=0.3
        ... )
        
        # 60-20-20 split (train-val-test)
        >>> X_temp, X_test, y_temp, y_test = train_test_split(
        ...     X, y, test_size=0.2, random_state=42
        ... )
        >>> X_train, X_val, y_train, y_val = train_test_split(
        ...     X_temp, y_temp, test_size=0.25, random_state=42  # 0.25 * 0.8 = 0.2
        ... )
    
    Notes:
        - Always split data BEFORE any preprocessing to avoid data leakage
        - Use random_state for reproducible results
        - Stratified splitting ensures balanced class distribution
        - Common splits: 80-20, 70-30, 60-20-20 (train-val-test)
        - Test data should NEVER be seen during training
    
    Raises:
        ValueError: If test_size is not between 0 and 1
        ValueError: If stratify=True but y is None
        ValueError: If X and y have different lengths
    
    References:
        - scikit-learn train_test_split: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.train_test_split.html
        - ML best practices: https://developers.google.com/machine-learning/crash-course/training-and-test-sets/splitting-data
    """
    
    # Validation
    if not 0 < test_size < 1:
        raise ValueError(f"test_size must be between 0 and 1, got {test_size}")
    
    if stratify and y is None:
        raise ValueError("stratify=True requires y to be provided")
    
    # Convert to lists if numpy arrays
    if isinstance(X, np.ndarray):
        X = X.tolist()
    if y is not None and isinstance(y, np.ndarray):
        y = y.tolist()
    
    # Check lengths match
    if y is not None and len(X) != len(y):
        raise ValueError(f"X and y must have same length. Got X: {len(X)}, y: {len(y)}")
    
    n_samples = len(X)
    n_test = int(n_samples * test_size)
    n_train = n_samples - n_test
    
    # Set random seed
    if random_state is not None:
        random.seed(random_state)
    
    # Create indices
    indices = list(range(n_samples))
    
    if stratify and y is not None:
        # Stratified split - maintain class distribution
        X_train, X_test = [], []
        y_train, y_test = [], []
        
        # Group indices by class
        class_indices = {}
        for idx, label in enumerate(y):
            if label not in class_indices:
                class_indices[label] = []
            class_indices[label].append(idx)
        
        # Split each class proportionally
        for label, class_idx in class_indices.items():
            if shuffle:
                random.shuffle(class_idx)
            
            n_class_test = max(1, int(len(class_idx) * test_size))
            
            test_idx = class_idx[:n_class_test]
            train_idx = class_idx[n_class_test:]
            
            X_test.extend([X[i] for i in test_idx])
            y_test.extend([y[i] for i in test_idx])
            X_train.extend([X[i] for i in train_idx])
            y_train.extend([y[i] for i in train_idx])
        
        return X_train, X_test, y_train, y_test
    
    else:
        # Regular split
        if shuffle:
            random.shuffle(indices)
        
        test_indices = indices[:n_test]
        train_indices = indices[n_test:]
        
        X_train = [X[i] for i in train_indices]
        X_test = [X[i] for i in test_indices]
        
        if y is not None:
            y_train = [y[i] for i in train_indices]
            y_test = [y[i] for i in test_indices]
            return X_train, X_test, y_train, y_test
        else:
            return X_train, X_test


def normalize_data(data: Union[List[float], np.ndarray]) -> List[float]:
    """
    Normalize data to range [0, 1] using min-max scaling.
    
    Args:
        data: List or array of numerical values
    
    Returns:
        list: Normalized values between 0 and 1
    
    Example:
        >>> from ilovetools.data import normalize_data
        >>> data = [1, 2, 3, 4, 5]
        >>> normalized = normalize_data(data)
        >>> print(normalized)
        [0.0, 0.25, 0.5, 0.75, 1.0]
    """
    if isinstance(data, np.ndarray):
        data = data.tolist()
    
    min_val = min(data)
    max_val = max(data)
    
    if max_val == min_val:
        return [0.0] * len(data)
    
    return [(x - min_val) / (max_val - min_val) for x in data]


def standardize_data(data: Union[List[float], np.ndarray]) -> List[float]:
    """
    Standardize data to have mean=0 and std=1 (Z-score normalization).
    
    Args:
        data: List or array of numerical values
    
    Returns:
        list: Standardized values with mean=0, std=1
    
    Example:
        >>> from ilovetools.data import standardize_data
        >>> data = [1, 2, 3, 4, 5]
        >>> standardized = standardize_data(data)
        >>> print(standardized)
        [-1.414, -0.707, 0.0, 0.707, 1.414]
    """
    if isinstance(data, np.ndarray):
        data = data.tolist()
    
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std = variance ** 0.5
    
    if std == 0:
        return [0.0] * len(data)
    
    return [(x - mean) / std for x in data]
