"""
Anomaly Detection Utilities
Detect outliers and anomalies in data using various methods
"""

import numpy as np
from typing import List, Tuple, Optional, Union

__all__ = [
    'detect_zscore',
    'detect_iqr',
    'detect_isolation_forest',
    'detect_local_outlier_factor',
    'detect_dbscan',
    'detect_statistical',
    'remove_outliers',
    'get_outlier_scores',
    'visualize_anomalies',
]


def detect_zscore(
    data: Union[List[float], np.ndarray],
    threshold: float = 3.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Detect anomalies using Z-score method.
    
    Args:
        data: Input data
        threshold: Z-score threshold (default: 3.0)
    
    Returns:
        tuple: (anomaly_indices, z_scores)
    
    Examples:
        >>> from ilovetools.ml import detect_zscore
        
        >>> data = [1, 2, 3, 4, 5, 100]
        >>> anomalies, scores = detect_zscore(data)
        >>> print(anomalies)
        [5]
    """
    data = np.array(data)
    
    # Calculate mean and std
    mean = np.mean(data)
    std = np.std(data)
    
    # Calculate z-scores
    z_scores = np.abs((data - mean) / std)
    
    # Find anomalies
    anomaly_mask = z_scores > threshold
    anomaly_indices = np.where(anomaly_mask)[0]
    
    return anomaly_indices, z_scores


def detect_iqr(
    data: Union[List[float], np.ndarray],
    multiplier: float = 1.5
) -> Tuple[np.ndarray, Tuple[float, float]]:
    """
    Detect anomalies using IQR (Interquartile Range) method.
    
    Args:
        data: Input data
        multiplier: IQR multiplier (default: 1.5)
    
    Returns:
        tuple: (anomaly_indices, (lower_bound, upper_bound))
    
    Examples:
        >>> from ilovetools.ml import detect_iqr
        
        >>> data = [1, 2, 3, 4, 5, 100]
        >>> anomalies, bounds = detect_iqr(data)
        >>> print(anomalies)
        [5]
    """
    data = np.array(data)
    
    # Calculate quartiles
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    
    # Calculate bounds
    lower_bound = q1 - (multiplier * iqr)
    upper_bound = q3 + (multiplier * iqr)
    
    # Find anomalies
    anomaly_mask = (data < lower_bound) | (data > upper_bound)
    anomaly_indices = np.where(anomaly_mask)[0]
    
    return anomaly_indices, (lower_bound, upper_bound)


def detect_isolation_forest(
    data: Union[List[List[float]], np.ndarray],
    contamination: float = 0.1,
    n_estimators: int = 100,
    random_state: Optional[int] = None
) -> np.ndarray:
    """
    Detect anomalies using Isolation Forest algorithm.
    
    Args:
        data: Input data (2D array)
        contamination: Expected proportion of outliers
        n_estimators: Number of trees
        random_state: Random seed
    
    Returns:
        np.ndarray: Anomaly indices
    
    Examples:
        >>> from ilovetools.ml import detect_isolation_forest
        
        >>> data = [[1, 2], [2, 3], [3, 4], [100, 100]]
        >>> anomalies = detect_isolation_forest(data)
        >>> print(anomalies)
        [3]
    """
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        raise ImportError("sklearn required. Install: pip install scikit-learn")
    
    data = np.array(data)
    
    # Create and fit model
    clf = IsolationForest(
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=random_state
    )
    
    # Predict (-1 for anomalies, 1 for normal)
    predictions = clf.fit_predict(data)
    
    # Get anomaly indices
    anomaly_indices = np.where(predictions == -1)[0]
    
    return anomaly_indices


def detect_local_outlier_factor(
    data: Union[List[List[float]], np.ndarray],
    n_neighbors: int = 20,
    contamination: float = 0.1
) -> np.ndarray:
    """
    Detect anomalies using Local Outlier Factor (LOF).
    
    Args:
        data: Input data (2D array)
        n_neighbors: Number of neighbors
        contamination: Expected proportion of outliers
    
    Returns:
        np.ndarray: Anomaly indices
    
    Examples:
        >>> from ilovetools.ml import detect_local_outlier_factor
        
        >>> data = [[1, 2], [2, 3], [3, 4], [100, 100]]
        >>> anomalies = detect_local_outlier_factor(data)
        >>> print(anomalies)
        [3]
    """
    try:
        from sklearn.neighbors import LocalOutlierFactor
    except ImportError:
        raise ImportError("sklearn required. Install: pip install scikit-learn")
    
    data = np.array(data)
    
    # Create and fit model
    clf = LocalOutlierFactor(
        n_neighbors=n_neighbors,
        contamination=contamination
    )
    
    # Predict (-1 for anomalies, 1 for normal)
    predictions = clf.fit_predict(data)
    
    # Get anomaly indices
    anomaly_indices = np.where(predictions == -1)[0]
    
    return anomaly_indices


def detect_dbscan(
    data: Union[List[List[float]], np.ndarray],
    eps: float = 0.5,
    min_samples: int = 5
) -> np.ndarray:
    """
    Detect anomalies using DBSCAN clustering.
    Points labeled as -1 are considered anomalies.
    
    Args:
        data: Input data (2D array)
        eps: Maximum distance between samples
        min_samples: Minimum samples in neighborhood
    
    Returns:
        np.ndarray: Anomaly indices
    
    Examples:
        >>> from ilovetools.ml import detect_dbscan
        
        >>> data = [[1, 2], [2, 3], [3, 4], [100, 100]]
        >>> anomalies = detect_dbscan(data)
        >>> print(anomalies)
        [3]
    """
    try:
        from sklearn.cluster import DBSCAN
    except ImportError:
        raise ImportError("sklearn required. Install: pip install scikit-learn")
    
    data = np.array(data)
    
    # Create and fit model
    clf = DBSCAN(eps=eps, min_samples=min_samples)
    labels = clf.fit_predict(data)
    
    # Get anomaly indices (label -1)
    anomaly_indices = np.where(labels == -1)[0]
    
    return anomaly_indices


def detect_statistical(
    data: Union[List[float], np.ndarray],
    method: str = 'zscore',
    **kwargs
) -> np.ndarray:
    """
    Detect anomalies using statistical methods.
    
    Args:
        data: Input data
        method: Method to use ('zscore', 'iqr', 'mad')
        **kwargs: Additional arguments for the method
    
    Returns:
        np.ndarray: Anomaly indices
    
    Examples:
        >>> from ilovetools.ml import detect_statistical
        
        >>> data = [1, 2, 3, 4, 5, 100]
        >>> anomalies = detect_statistical(data, method='zscore')
        >>> print(anomalies)
        [5]
    """
    data = np.array(data)
    
    if method == 'zscore':
        threshold = kwargs.get('threshold', 3.0)
        anomalies, _ = detect_zscore(data, threshold)
        return anomalies
    
    elif method == 'iqr':
        multiplier = kwargs.get('multiplier', 1.5)
        anomalies, _ = detect_iqr(data, multiplier)
        return anomalies
    
    elif method == 'mad':
        # Median Absolute Deviation
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        threshold = kwargs.get('threshold', 3.5)
        
        modified_z_scores = 0.6745 * (data - median) / mad
        anomaly_mask = np.abs(modified_z_scores) > threshold
        return np.where(anomaly_mask)[0]
    
    else:
        raise ValueError(f"Unknown method: {method}")


def remove_outliers(
    data: Union[List[float], np.ndarray],
    method: str = 'zscore',
    **kwargs
) -> np.ndarray:
    """
    Remove outliers from data.
    
    Args:
        data: Input data
        method: Detection method
        **kwargs: Additional arguments
    
    Returns:
        np.ndarray: Data without outliers
    
    Examples:
        >>> from ilovetools.ml import remove_outliers
        
        >>> data = [1, 2, 3, 4, 5, 100]
        >>> clean_data = remove_outliers(data)
        >>> print(clean_data)
        [1, 2, 3, 4, 5]
    """
    data = np.array(data)
    anomalies = detect_statistical(data, method, **kwargs)
    
    # Create mask
    mask = np.ones(len(data), dtype=bool)
    mask[anomalies] = False
    
    return data[mask]


def get_outlier_scores(
    data: Union[List[float], np.ndarray],
    method: str = 'zscore'
) -> np.ndarray:
    """
    Get outlier scores for each data point.
    
    Args:
        data: Input data
        method: Scoring method ('zscore', 'mad')
    
    Returns:
        np.ndarray: Outlier scores
    
    Examples:
        >>> from ilovetools.ml import get_outlier_scores
        
        >>> data = [1, 2, 3, 4, 5, 100]
        >>> scores = get_outlier_scores(data)
        >>> print(scores)
    """
    data = np.array(data)
    
    if method == 'zscore':
        mean = np.mean(data)
        std = np.std(data)
        return np.abs((data - mean) / std)
    
    elif method == 'mad':
        median = np.median(data)
        mad = np.median(np.abs(data - median))
        return 0.6745 * np.abs(data - median) / mad
    
    else:
        raise ValueError(f"Unknown method: {method}")


def visualize_anomalies(
    data: Union[List[float], np.ndarray],
    anomalies: np.ndarray,
    title: str = 'Anomaly Detection'
) -> dict:
    """
    Create visualization data for anomalies.
    
    Args:
        data: Input data
        anomalies: Anomaly indices
        title: Plot title
    
    Returns:
        dict: Visualization data
    
    Examples:
        >>> from ilovetools.ml import detect_zscore, visualize_anomalies
        
        >>> data = [1, 2, 3, 4, 5, 100]
        >>> anomalies, _ = detect_zscore(data)
        >>> viz_data = visualize_anomalies(data, anomalies)
    """
    data = np.array(data)
    
    # Create mask for normal points
    normal_mask = np.ones(len(data), dtype=bool)
    normal_mask[anomalies] = False
    
    return {
        'title': title,
        'normal_data': data[normal_mask].tolist(),
        'anomaly_data': data[anomalies].tolist(),
        'normal_indices': np.where(normal_mask)[0].tolist(),
        'anomaly_indices': anomalies.tolist(),
        'total_points': len(data),
        'anomaly_count': len(anomalies),
        'anomaly_percentage': (len(anomalies) / len(data)) * 100
    }
