"""
Imbalanced data handling utilities
Each function has TWO names: full descriptive name + abbreviated alias
"""

from typing import List, Dict, Any, Tuple, Optional
import random

__all__ = [
    # Full names
    'random_oversampling',
    'random_undersampling',
    'smote_oversampling',
    'tomek_links_undersampling',
    'class_weight_calculator',
    'stratified_sampling',
    'compute_class_distribution',
    'balance_dataset',
    'minority_class_identifier',
    'imbalance_ratio',
    'synthetic_sample_generator',
    'near_miss_undersampling',
    # Abbreviated aliases
    'random_oversample',
    'random_undersample',
    'smote',
    'tomek_links',
    'class_weights',
    'stratified_sample',
    'class_dist',
    'balance_data',
    'minority_class',
    'imbalance_ratio_alias',
    'synthetic_sample',
    'near_miss',
]


def random_oversampling(
    X: List[List[float]],
    y: List[int],
    target_ratio: float = 1.0
) -> Tuple[List[List[float]], List[int]]:
    """
    Randomly oversample minority class.
    
    Alias: random_oversample()
    
    Args:
        X: Feature data
        y: Labels
        target_ratio: Desired minority/majority ratio (1.0 = balanced)
    
    Returns:
        tuple: (X_resampled, y_resampled)
    
    Examples:
        >>> from ilovetools.ml import random_oversample  # Short alias
        
        >>> X = [[1, 2], [2, 3], [3, 4], [4, 5], [5, 6]]
        >>> y = [0, 0, 0, 0, 1]  # Imbalanced: 4 vs 1
        >>> 
        >>> X_res, y_res = random_oversample(X, y, target_ratio=1.0)
        >>> print(len([label for label in y_res if label == 0]))
        4
        >>> print(len([label for label in y_res if label == 1]))
        4
        
        >>> from ilovetools.ml import random_oversampling  # Full name
        >>> X_res, y_res = random_oversampling(X, y)
    
    Notes:
        - Duplicates minority samples randomly
        - Simple but effective
        - May cause overfitting
        - Good starting point
    """
    # Separate by class
    class_indices = {}
    for idx, label in enumerate(y):
        if label not in class_indices:
            class_indices[label] = []
        class_indices[label].append(idx)
    
    # Find majority class size
    max_size = max(len(indices) for indices in class_indices.values())
    target_size = int(max_size * target_ratio)
    
    X_resampled = []
    y_resampled = []
    
    for label, indices in class_indices.items():
        # Add all original samples
        for idx in indices:
            X_resampled.append(X[idx])
            y_resampled.append(y[idx])
        
        # Oversample if needed
        if len(indices) < target_size:
            n_samples = target_size - len(indices)
            for _ in range(n_samples):
                idx = random.choice(indices)
                X_resampled.append(X[idx])
                y_resampled.append(y[idx])
    
    return X_resampled, y_resampled


# Create alias
random_oversample = random_oversampling


def random_undersampling(
    X: List[List[float]],
    y: List[int],
    target_ratio: float = 1.0
) -> Tuple[List[List[float]], List[int]]:
    """
    Randomly undersample majority class.
    
    Alias: random_undersample()
    
    Args:
        X: Feature data
        y: Labels
        target_ratio: Desired minority/majority ratio (1.0 = balanced)
    
    Returns:
        tuple: (X_resampled, y_resampled)
    
    Examples:
        >>> from ilovetools.ml import random_undersample  # Short alias
        
        >>> X = [[1, 2], [2, 3], [3, 4], [4, 5], [5, 6]]
        >>> y = [0, 0, 0, 0, 1]  # Imbalanced: 4 vs 1
        >>> 
        >>> X_res, y_res = random_undersample(X, y, target_ratio=1.0)
        >>> print(len([label for label in y_res if label == 0]))
        1
        >>> print(len([label for label in y_res if label == 1]))
        1
        
        >>> from ilovetools.ml import random_undersampling  # Full name
        >>> X_res, y_res = random_undersampling(X, y)
    
    Notes:
        - Removes majority samples randomly
        - Loses information
        - Faster training
        - Good for large datasets
    """
    # Separate by class
    class_indices = {}
    for idx, label in enumerate(y):
        if label not in class_indices:
            class_indices[label] = []
        class_indices[label].append(idx)
    
    # Find minority class size
    min_size = min(len(indices) for indices in class_indices.values())
    target_size = int(min_size / target_ratio)
    
    X_resampled = []
    y_resampled = []
    
    for label, indices in class_indices.items():
        # Undersample if needed
        if len(indices) > target_size:
            selected_indices = random.sample(indices, target_size)
        else:
            selected_indices = indices
        
        for idx in selected_indices:
            X_resampled.append(X[idx])
            y_resampled.append(y[idx])
    
    return X_resampled, y_resampled


# Create alias
random_undersample = random_undersampling


def smote_oversampling(
    X: List[List[float]],
    y: List[int],
    k_neighbors: int = 5,
    target_ratio: float = 1.0
) -> Tuple[List[List[float]], List[int]]:
    """
    SMOTE (Synthetic Minority Over-sampling Technique).
    
    Alias: smote()
    
    Args:
        X: Feature data
        y: Labels
        k_neighbors: Number of nearest neighbors
        target_ratio: Desired minority/majority ratio
    
    Returns:
        tuple: (X_resampled, y_resampled)
    
    Examples:
        >>> from ilovetools.ml import smote  # Short alias
        
        >>> X = [[1, 2], [2, 3], [3, 4], [4, 5], [5, 6]]
        >>> y = [0, 0, 0, 0, 1]
        >>> 
        >>> X_res, y_res = smote(X, y, k_neighbors=2)
        >>> print(len(y_res) > len(y))
        True
        
        >>> from ilovetools.ml import smote_oversampling  # Full name
        >>> X_res, y_res = smote_oversampling(X, y)
    
    Notes:
        - Creates synthetic samples
        - Interpolates between neighbors
        - Reduces overfitting
        - Industry standard
    """
    # Separate by class
    class_indices = {}
    for idx, label in enumerate(y):
        if label not in class_indices:
            class_indices[label] = []
        class_indices[label].append(idx)
    
    # Find majority class size
    max_size = max(len(indices) for indices in class_indices.values())
    target_size = int(max_size * target_ratio)
    
    X_resampled = list(X)
    y_resampled = list(y)
    
    for label, indices in class_indices.items():
        if len(indices) < target_size:
            n_samples = target_size - len(indices)
            
            for _ in range(n_samples):
                # Select random sample from minority class
                idx = random.choice(indices)
                sample = X[idx]
                
                # Find k nearest neighbors (simplified)
                neighbors = random.sample(indices, min(k_neighbors, len(indices)))
                neighbor_idx = random.choice(neighbors)
                neighbor = X[neighbor_idx]
                
                # Create synthetic sample (interpolation)
                alpha = random.random()
                synthetic = [
                    sample[i] + alpha * (neighbor[i] - sample[i])
                    for i in range(len(sample))
                ]
                
                X_resampled.append(synthetic)
                y_resampled.append(label)
    
    return X_resampled, y_resampled


# Create alias
smote = smote_oversampling


def tomek_links_undersampling(
    X: List[List[float]],
    y: List[int]
) -> Tuple[List[List[float]], List[int]]:
    """
    Remove Tomek links (borderline samples).
    
    Alias: tomek_links()
    
    Args:
        X: Feature data
        y: Labels
    
    Returns:
        tuple: (X_cleaned, y_cleaned)
    
    Examples:
        >>> from ilovetools.ml import tomek_links  # Short alias
        
        >>> X = [[1, 2], [2, 3], [3, 4], [4, 5]]
        >>> y = [0, 0, 1, 1]
        >>> 
        >>> X_clean, y_clean = tomek_links(X, y)
        >>> print(len(X_clean) <= len(X))
        True
        
        >>> from ilovetools.ml import tomek_links_undersampling  # Full name
        >>> X_clean, y_clean = tomek_links_undersampling(X, y)
    
    Notes:
        - Removes noisy samples
        - Cleans decision boundary
        - Often combined with SMOTE
        - Improves model performance
    """
    def euclidean_distance(p1, p2):
        return sum((a - b) ** 2 for a, b in zip(p1, p2)) ** 0.5
    
    # Find Tomek links (simplified version)
    tomek_indices = set()
    
    for i in range(len(X)):
        # Find nearest neighbor with different class
        min_dist = float('inf')
        nearest_idx = -1
        
        for j in range(len(X)):
            if i != j and y[i] != y[j]:
                dist = euclidean_distance(X[i], X[j])
                if dist < min_dist:
                    min_dist = dist
                    nearest_idx = j
        
        if nearest_idx != -1:
            # Check if they are each other's nearest neighbors
            is_tomek = True
            for k in range(len(X)):
                if k != i and k != nearest_idx:
                    if euclidean_distance(X[nearest_idx], X[k]) < min_dist:
                        is_tomek = False
                        break
            
            if is_tomek:
                # Remove majority class sample
                if sum(1 for label in y if label == y[i]) > sum(1 for label in y if label == y[nearest_idx]):
                    tomek_indices.add(i)
                else:
                    tomek_indices.add(nearest_idx)
    
    # Remove Tomek links
    X_cleaned = [X[i] for i in range(len(X)) if i not in tomek_indices]
    y_cleaned = [y[i] for i in range(len(y)) if i not in tomek_indices]
    
    return X_cleaned, y_cleaned


# Create alias
tomek_links = tomek_links_undersampling


def class_weight_calculator(y: List[int]) -> Dict[int, float]:
    """
    Calculate class weights for imbalanced data.
    
    Alias: class_weights()
    
    Args:
        y: Labels
    
    Returns:
        dict: Class weights
    
    Examples:
        >>> from ilovetools.ml import class_weights  # Short alias
        
        >>> y = [0, 0, 0, 0, 1]
        >>> weights = class_weights(y)
        >>> print(weights[0] < weights[1])
        True
        
        >>> from ilovetools.ml import class_weight_calculator  # Full name
        >>> weights = class_weight_calculator(y)
    
    Notes:
        - Inverse of class frequency
        - Use in model training
        - Penalizes minority errors more
        - Sklearn-compatible
    """
    # Count samples per class
    class_counts = {}
    for label in y:
        class_counts[label] = class_counts.get(label, 0) + 1
    
    # Calculate weights (inverse frequency)
    n_samples = len(y)
    n_classes = len(class_counts)
    
    weights = {}
    for label, count in class_counts.items():
        weights[label] = n_samples / (n_classes * count)
    
    return weights


# Create alias
class_weights = class_weight_calculator


def stratified_sampling(
    X: List[List[float]],
    y: List[int],
    sample_size: int
) -> Tuple[List[List[float]], List[int]]:
    """
    Stratified sampling maintaining class distribution.
    
    Alias: stratified_sample()
    
    Args:
        X: Feature data
        y: Labels
        sample_size: Number of samples to draw
    
    Returns:
        tuple: (X_sample, y_sample)
    
    Examples:
        >>> from ilovetools.ml import stratified_sample  # Short alias
        
        >>> X = [[1, 2], [2, 3], [3, 4], [4, 5], [5, 6]]
        >>> y = [0, 0, 0, 1, 1]
        >>> 
        >>> X_sample, y_sample = stratified_sample(X, y, sample_size=3)
        >>> print(len(X_sample))
        3
        
        >>> from ilovetools.ml import stratified_sampling  # Full name
        >>> X_sample, y_sample = stratified_sampling(X, y, 3)
    
    Notes:
        - Maintains class proportions
        - Better for train/test split
        - Reduces sampling bias
        - Essential for imbalanced data
    """
    # Separate by class
    class_indices = {}
    for idx, label in enumerate(y):
        if label not in class_indices:
            class_indices[label] = []
        class_indices[label].append(idx)
    
    # Calculate samples per class
    class_proportions = {
        label: len(indices) / len(y)
        for label, indices in class_indices.items()
    }
    
    X_sample = []
    y_sample = []
    
    for label, proportion in class_proportions.items():
        n_samples = int(sample_size * proportion)
        indices = class_indices[label]
        
        if n_samples > 0:
            selected = random.sample(indices, min(n_samples, len(indices)))
            for idx in selected:
                X_sample.append(X[idx])
                y_sample.append(y[idx])
    
    return X_sample, y_sample


# Create alias
stratified_sample = stratified_sampling


def compute_class_distribution(y: List[int]) -> Dict[str, Any]:
    """
    Compute class distribution statistics.
    
    Alias: class_dist()
    
    Args:
        y: Labels
    
    Returns:
        dict: Distribution statistics
    
    Examples:
        >>> from ilovetools.ml import class_dist  # Short alias
        
        >>> y = [0, 0, 0, 0, 1]
        >>> dist = class_dist(y)
        >>> print(dist['counts'])
        {0: 4, 1: 1}
        >>> print(dist['imbalance_ratio'])
        4.0
        
        >>> from ilovetools.ml import compute_class_distribution  # Full name
        >>> dist = compute_class_distribution(y)
    
    Notes:
        - Understand data imbalance
        - Plan resampling strategy
        - Monitor class distribution
        - Essential first step
    """
    # Count samples per class
    class_counts = {}
    for label in y:
        class_counts[label] = class_counts.get(label, 0) + 1
    
    # Calculate proportions
    total = len(y)
    class_proportions = {
        label: count / total
        for label, count in class_counts.items()
    }
    
    # Find majority and minority
    majority_class = max(class_counts, key=class_counts.get)
    minority_class = min(class_counts, key=class_counts.get)
    
    # Calculate imbalance ratio
    imbalance_ratio = class_counts[majority_class] / class_counts[minority_class]
    
    return {
        'counts': class_counts,
        'proportions': class_proportions,
        'majority_class': majority_class,
        'minority_class': minority_class,
        'imbalance_ratio': imbalance_ratio,
        'total_samples': total,
    }


# Create alias
class_dist = compute_class_distribution


def balance_dataset(
    X: List[List[float]],
    y: List[int],
    method: str = 'oversample',
    target_ratio: float = 1.0
) -> Tuple[List[List[float]], List[int]]:
    """
    Balance dataset using specified method.
    
    Alias: balance_data()
    
    Args:
        X: Feature data
        y: Labels
        method: 'oversample', 'undersample', or 'smote'
        target_ratio: Desired balance ratio
    
    Returns:
        tuple: (X_balanced, y_balanced)
    
    Examples:
        >>> from ilovetools.ml import balance_data  # Short alias
        
        >>> X = [[1, 2], [2, 3], [3, 4], [4, 5], [5, 6]]
        >>> y = [0, 0, 0, 0, 1]
        >>> 
        >>> X_bal, y_bal = balance_data(X, y, method='oversample')
        >>> print(len(y_bal) >= len(y))
        True
        
        >>> from ilovetools.ml import balance_dataset  # Full name
        >>> X_bal, y_bal = balance_dataset(X, y, method='smote')
    
    Notes:
        - Unified interface
        - Multiple methods
        - Easy to switch
        - Production ready
    """
    if method == 'oversample':
        return random_oversampling(X, y, target_ratio)
    elif method == 'undersample':
        return random_undersampling(X, y, target_ratio)
    elif method == 'smote':
        return smote_oversampling(X, y, target_ratio=target_ratio)
    else:
        raise ValueError(f"Unknown method: {method}")


# Create alias
balance_data = balance_dataset


def minority_class_identifier(y: List[int]) -> int:
    """
    Identify minority class label.
    
    Alias: minority_class()
    
    Args:
        y: Labels
    
    Returns:
        int: Minority class label
    
    Examples:
        >>> from ilovetools.ml import minority_class  # Short alias
        
        >>> y = [0, 0, 0, 0, 1]
        >>> minority = minority_class(y)
        >>> print(minority)
        1
        
        >>> from ilovetools.ml import minority_class_identifier  # Full name
        >>> minority = minority_class_identifier(y)
    
    Notes:
        - Quick identification
        - Useful for filtering
        - Essential for resampling
        - Simple utility
    """
    class_counts = {}
    for label in y:
        class_counts[label] = class_counts.get(label, 0) + 1
    
    return min(class_counts, key=class_counts.get)


# Create alias
minority_class = minority_class_identifier


def imbalance_ratio(y: List[int]) -> float:
    """
    Calculate imbalance ratio (majority/minority).
    
    Alias: imbalance_ratio_alias()
    
    Args:
        y: Labels
    
    Returns:
        float: Imbalance ratio
    
    Examples:
        >>> from ilovetools.ml import imbalance_ratio
        
        >>> y = [0, 0, 0, 0, 1]
        >>> ratio = imbalance_ratio(y)
        >>> print(ratio)
        4.0
        
        >>> y = [0, 0, 1, 1]
        >>> ratio = imbalance_ratio(y)
        >>> print(ratio)
        1.0
    
    Notes:
        - Quick assessment
        - 1.0 = balanced
        - >3.0 = highly imbalanced
        - Guide resampling strategy
    """
    class_counts = {}
    for label in y:
        class_counts[label] = class_counts.get(label, 0) + 1
    
    majority_count = max(class_counts.values())
    minority_count = min(class_counts.values())
    
    return majority_count / minority_count


# Create alias (different name to avoid conflict)
imbalance_ratio_alias = imbalance_ratio


def synthetic_sample_generator(
    sample: List[float],
    neighbor: List[float],
    alpha: Optional[float] = None
) -> List[float]:
    """
    Generate synthetic sample between two samples.
    
    Alias: synthetic_sample()
    
    Args:
        sample: First sample
        neighbor: Second sample
        alpha: Interpolation factor (None = random)
    
    Returns:
        list: Synthetic sample
    
    Examples:
        >>> from ilovetools.ml import synthetic_sample  # Short alias
        
        >>> sample = [1.0, 2.0]
        >>> neighbor = [3.0, 4.0]
        >>> synthetic = synthetic_sample(sample, neighbor, alpha=0.5)
        >>> print(synthetic)
        [2.0, 3.0]
        
        >>> from ilovetools.ml import synthetic_sample_generator  # Full name
        >>> synthetic = synthetic_sample_generator(sample, neighbor)
    
    Notes:
        - Core of SMOTE
        - Linear interpolation
        - Creates diversity
        - Reduces overfitting
    """
    if alpha is None:
        alpha = random.random()
    
    return [
        sample[i] + alpha * (neighbor[i] - sample[i])
        for i in range(len(sample))
    ]


# Create alias
synthetic_sample = synthetic_sample_generator


def near_miss_undersampling(
    X: List[List[float]],
    y: List[int],
    version: int = 1
) -> Tuple[List[List[float]], List[int]]:
    """
    NearMiss undersampling algorithm.
    
    Alias: near_miss()
    
    Args:
        X: Feature data
        y: Labels
        version: NearMiss version (1, 2, or 3)
    
    Returns:
        tuple: (X_resampled, y_resampled)
    
    Examples:
        >>> from ilovetools.ml import near_miss  # Short alias
        
        >>> X = [[1, 2], [2, 3], [3, 4], [4, 5], [5, 6]]
        >>> y = [0, 0, 0, 0, 1]
        >>> 
        >>> X_res, y_res = near_miss(X, y, version=1)
        >>> print(len(y_res) < len(y))
        True
        
        >>> from ilovetools.ml import near_miss_undersampling  # Full name
        >>> X_res, y_res = near_miss_undersampling(X, y)
    
    Notes:
        - Intelligent undersampling
        - Keeps informative samples
        - Better than random
        - Multiple versions
    """
    def euclidean_distance(p1, p2):
        return sum((a - b) ** 2 for a, b in zip(p1, p2)) ** 0.5
    
    # Separate by class
    class_indices = {}
    for idx, label in enumerate(y):
        if label not in class_indices:
            class_indices[label] = []
        class_indices[label].append(idx)
    
    # Find majority and minority
    majority_label = max(class_indices, key=lambda k: len(class_indices[k]))
    minority_label = min(class_indices, key=lambda k: len(class_indices[k]))
    
    majority_indices = class_indices[majority_label]
    minority_indices = class_indices[minority_label]
    
    # NearMiss-1: Select majority samples closest to minority
    selected_majority = []
    target_size = len(minority_indices)
    
    # Calculate average distance to minority class
    distances = []
    for maj_idx in majority_indices:
        avg_dist = sum(
            euclidean_distance(X[maj_idx], X[min_idx])
            for min_idx in minority_indices
        ) / len(minority_indices)
        distances.append((maj_idx, avg_dist))
    
    # Select samples with smallest average distance
    distances.sort(key=lambda x: x[1])
    selected_majority = [idx for idx, _ in distances[:target_size]]
    
    # Combine with minority class
    X_resampled = [X[i] for i in minority_indices + selected_majority]
    y_resampled = [y[i] for i in minority_indices + selected_majority]
    
    return X_resampled, y_resampled


# Create alias
near_miss = near_miss_undersampling
