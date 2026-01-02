"""
Feature engineering utilities for ML workflows
"""

from typing import List, Union, Dict, Tuple, Optional
import numpy as np
from datetime import datetime

__all__ = [
    'create_polynomial_features',
    'bin_numerical_feature',
    'one_hot_encode',
    'label_encode',
    'extract_datetime_features',
    'handle_missing_values',
    'create_interaction_features'
]


def create_polynomial_features(
    data: Union[List[float], np.ndarray],
    degree: int = 2,
    include_bias: bool = False
) -> List[List[float]]:
    """
    Create polynomial features from numerical data.
    
    Transforms [x] into [x, x^2, x^3, ...] to capture non-linear relationships.
    Essential for models that need to learn curved patterns.
    
    Args:
        data: List or array of numerical values
        degree: Maximum polynomial degree. Default: 2
        include_bias: Include bias term (column of 1s). Default: False
    
    Returns:
        list: Polynomial features as list of lists
    
    Examples:
        >>> from ilovetools.data import create_polynomial_features
        
        # Basic usage
        >>> ages = [20, 25, 30, 35, 40]
        >>> poly_features = create_polynomial_features(ages, degree=2)
        >>> print(poly_features)
        [[20, 400], [25, 625], [30, 900], [35, 1225], [40, 1600]]
        
        # With bias term
        >>> poly_features = create_polynomial_features(ages, degree=2, include_bias=True)
        >>> print(poly_features[0])
        [1, 20, 400]
        
        # Degree 3
        >>> poly_features = create_polynomial_features([2, 3, 4], degree=3)
        >>> print(poly_features)
        [[2, 4, 8], [3, 9, 27], [4, 16, 64]]
        
        # Real-world: Age features for insurance pricing
        >>> customer_ages = [25, 35, 45, 55, 65]
        >>> age_features = create_polynomial_features(customer_ages, degree=2)
        # Now model can learn: premium = a*age + b*age^2
    
    Notes:
        - Useful for capturing non-linear relationships
        - Common in regression problems
        - Be careful with high degrees (overfitting risk)
        - Normalize features after polynomial expansion
    """
    if isinstance(data, np.ndarray):
        data = data.tolist()
    
    result = []
    for value in data:
        features = []
        if include_bias:
            features.append(1)
        for d in range(1, degree + 1):
            features.append(value ** d)
        result.append(features)
    
    return result


def bin_numerical_feature(
    data: Union[List[float], np.ndarray],
    bins: Union[int, List[float]] = 5,
    labels: Optional[List[str]] = None
) -> List[Union[int, str]]:
    """
    Bin continuous numerical data into discrete categories.
    
    Converts continuous values into groups/bins. Useful for creating
    categorical features from numerical data.
    
    Args:
        data: List or array of numerical values
        bins: Number of equal-width bins OR list of bin edges
        labels: Optional labels for bins. If None, returns bin indices
    
    Returns:
        list: Binned values (indices or labels)
    
    Examples:
        >>> from ilovetools.data import bin_numerical_feature
        
        # Age groups
        >>> ages = [5, 15, 25, 35, 45, 55, 65, 75]
        >>> age_groups = bin_numerical_feature(
        ...     ages,
        ...     bins=[0, 18, 35, 60, 100],
        ...     labels=["Child", "Young Adult", "Adult", "Senior"]
        ... )
        >>> print(age_groups)
        ['Child', 'Child', 'Young Adult', 'Adult', 'Adult', 'Senior', 'Senior', 'Senior']
        
        # Income brackets
        >>> incomes = [25000, 45000, 65000, 85000, 120000]
        >>> income_brackets = bin_numerical_feature(
        ...     incomes,
        ...     bins=[0, 40000, 80000, 150000],
        ...     labels=["Low", "Medium", "High"]
        ... )
        
        # Equal-width bins
        >>> scores = [45, 67, 89, 92, 78, 56, 34, 88]
        >>> score_bins = bin_numerical_feature(scores, bins=3)
        >>> print(score_bins)
        [0, 1, 2, 2, 2, 1, 0, 2]
    
    Notes:
        - Useful for creating categorical features
        - Helps models learn threshold effects
        - Can reduce noise in continuous data
        - Choose bins based on domain knowledge
    """
    if isinstance(data, np.ndarray):
        data = data.tolist()
    
    if isinstance(bins, int):
        # Create equal-width bins
        min_val = min(data)
        max_val = max(data)
        bin_width = (max_val - min_val) / bins
        bin_edges = [min_val + i * bin_width for i in range(bins + 1)]
        bin_edges[-1] += 0.001  # Ensure max value is included
    else:
        bin_edges = bins
    
    result = []
    for value in data:
        bin_idx = 0
        for i in range(len(bin_edges) - 1):
            if bin_edges[i] <= value < bin_edges[i + 1]:
                bin_idx = i
                break
        
        if labels:
            result.append(labels[bin_idx])
        else:
            result.append(bin_idx)
    
    return result


def one_hot_encode(
    data: List[str],
    categories: Optional[List[str]] = None
) -> Dict[str, List[int]]:
    """
    One-hot encode categorical data.
    
    Converts categories into binary columns. Each category becomes
    a separate binary feature.
    
    Args:
        data: List of categorical values
        categories: Optional list of all possible categories
    
    Returns:
        dict: Dictionary with category names as keys, binary lists as values
    
    Examples:
        >>> from ilovetools.data import one_hot_encode
        
        # Basic encoding
        >>> colors = ["Red", "Blue", "Green", "Red", "Blue"]
        >>> encoded = one_hot_encode(colors)
        >>> print(encoded)
        {'Red': [1, 0, 0, 1, 0], 'Blue': [0, 1, 0, 0, 1], 'Green': [0, 0, 1, 0, 0]}
        
        # With predefined categories
        >>> sizes = ["S", "M", "L", "M"]
        >>> encoded = one_hot_encode(sizes, categories=["XS", "S", "M", "L", "XL"])
        
        # Real-world: Product categories
        >>> products = ["Electronics", "Clothing", "Electronics", "Food"]
        >>> encoded = one_hot_encode(products)
        # Use in ML: Each category becomes a feature
    
    Notes:
        - Standard encoding for categorical features
        - Creates sparse features (mostly zeros)
        - Number of features = number of categories
        - Use for nominal categories (no order)
    """
    if categories is None:
        categories = sorted(list(set(data)))
    
    result = {cat: [] for cat in categories}
    
    for value in data:
        for cat in categories:
            result[cat].append(1 if value == cat else 0)
    
    return result


def label_encode(data: List[str]) -> Tuple[List[int], Dict[str, int]]:
    """
    Label encode categorical data to integers.
    
    Converts categories to integer labels. Useful for ordinal categories
    or when one-hot encoding creates too many features.
    
    Args:
        data: List of categorical values
    
    Returns:
        tuple: (encoded_data, label_mapping)
    
    Examples:
        >>> from ilovetools.data import label_encode
        
        # Basic encoding
        >>> sizes = ["Small", "Large", "Medium", "Small", "Large"]
        >>> encoded, mapping = label_encode(sizes)
        >>> print(encoded)
        [2, 0, 1, 2, 0]
        >>> print(mapping)
        {'Large': 0, 'Medium': 1, 'Small': 2}
        
        # Education levels (ordinal)
        >>> education = ["High School", "Bachelor", "Master", "Bachelor"]
        >>> encoded, mapping = label_encode(education)
        
        # Decode back
        >>> reverse_mapping = {v: k for k, v in mapping.items()}
        >>> original = [reverse_mapping[code] for code in encoded]
    
    Notes:
        - More memory efficient than one-hot encoding
        - Use for ordinal categories (has order)
        - Model may assume order exists
        - Returns mapping for decoding
    """
    unique_values = sorted(list(set(data)))
    mapping = {val: idx for idx, val in enumerate(unique_values)}
    encoded = [mapping[val] for val in data]
    
    return encoded, mapping


def extract_datetime_features(
    timestamps: List[str],
    format: str = "%Y-%m-%d %H:%M:%S"
) -> Dict[str, List[int]]:
    """
    Extract useful features from datetime strings.
    
    Converts timestamps into multiple temporal features like hour,
    day of week, month, etc. Essential for time-series ML.
    
    Args:
        timestamps: List of datetime strings
        format: Datetime format string. Default: "%Y-%m-%d %H:%M:%S"
    
    Returns:
        dict: Dictionary with feature names and values
    
    Examples:
        >>> from ilovetools.data import extract_datetime_features
        
        # Basic usage
        >>> dates = [
        ...     "2024-03-15 14:30:00",
        ...     "2024-03-16 09:15:00",
        ...     "2024-03-17 18:45:00"
        ... ]
        >>> features = extract_datetime_features(dates)
        >>> print(features.keys())
        dict_keys(['year', 'month', 'day', 'hour', 'minute', 'day_of_week', 'is_weekend'])
        
        # E-commerce: Purchase patterns
        >>> purchase_times = ["2024-12-25 10:30:00", "2024-12-26 15:45:00"]
        >>> features = extract_datetime_features(purchase_times)
        >>> print(features['is_weekend'])
        [0, 0]
        >>> print(features['hour'])
        [10, 15]
        
        # Different format
        >>> dates = ["15/03/2024", "16/03/2024"]
        >>> features = extract_datetime_features(dates, format="%d/%m/%Y")
    
    Notes:
        - Captures temporal patterns
        - Essential for time-series forecasting
        - Helps model learn seasonality
        - Common features: hour, day, month, is_weekend
    """
    result = {
        'year': [],
        'month': [],
        'day': [],
        'hour': [],
        'minute': [],
        'day_of_week': [],  # 0=Monday, 6=Sunday
        'is_weekend': []
    }
    
    for ts in timestamps:
        dt = datetime.strptime(ts, format)
        result['year'].append(dt.year)
        result['month'].append(dt.month)
        result['day'].append(dt.day)
        result['hour'].append(dt.hour)
        result['minute'].append(dt.minute)
        result['day_of_week'].append(dt.weekday())
        result['is_weekend'].append(1 if dt.weekday() >= 5 else 0)
    
    return result


def handle_missing_values(
    data: List[Optional[float]],
    strategy: str = "mean"
) -> List[float]:
    """
    Handle missing values in numerical data.
    
    Fills None/NaN values using various strategies. Essential
    preprocessing step for ML models.
    
    Args:
        data: List with potential None values
        strategy: Fill strategy - "mean", "median", "mode", "forward", "backward", "zero"
    
    Returns:
        list: Data with missing values filled
    
    Examples:
        >>> from ilovetools.data import handle_missing_values
        
        # Mean imputation
        >>> data = [1.0, 2.0, None, 4.0, 5.0]
        >>> filled = handle_missing_values(data, strategy="mean")
        >>> print(filled)
        [1.0, 2.0, 3.0, 4.0, 5.0]
        
        # Median imputation
        >>> data = [1.0, 2.0, None, 100.0]
        >>> filled = handle_missing_values(data, strategy="median")
        
        # Forward fill
        >>> data = [1.0, None, None, 4.0]
        >>> filled = handle_missing_values(data, strategy="forward")
        >>> print(filled)
        [1.0, 1.0, 1.0, 4.0]
        
        # Zero fill
        >>> data = [1.0, None, 3.0]
        >>> filled = handle_missing_values(data, strategy="zero")
        >>> print(filled)
        [1.0, 0.0, 3.0]
    
    Notes:
        - Most ML models can't handle missing values
        - Choose strategy based on data distribution
        - Mean: Sensitive to outliers
        - Median: Robust to outliers
        - Forward/Backward: For time-series data
    """
    valid_values = [x for x in data if x is not None]
    
    if not valid_values:
        return [0.0] * len(data)
    
    if strategy == "mean":
        fill_value = sum(valid_values) / len(valid_values)
    elif strategy == "median":
        sorted_vals = sorted(valid_values)
        n = len(sorted_vals)
        fill_value = sorted_vals[n // 2] if n % 2 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
    elif strategy == "mode":
        fill_value = max(set(valid_values), key=valid_values.count)
    elif strategy == "zero":
        fill_value = 0.0
    else:
        fill_value = sum(valid_values) / len(valid_values)
    
    result = []
    last_valid = fill_value
    
    for value in data:
        if value is None:
            if strategy == "forward":
                result.append(last_valid)
            else:
                result.append(fill_value)
        else:
            result.append(value)
            last_valid = value
    
    # Backward fill if needed
    if strategy == "backward":
        result_reversed = []
        last_valid = fill_value
        for value in reversed(result):
            if value is None:
                result_reversed.append(last_valid)
            else:
                result_reversed.append(value)
                last_valid = value
        result = list(reversed(result_reversed))
    
    return result


def create_interaction_features(
    feature1: Union[List[float], np.ndarray],
    feature2: Union[List[float], np.ndarray],
    operation: str = "multiply"
) -> List[float]:
    """
    Create interaction features between two features.
    
    Combines two features to capture their joint effect. Useful when
    features interact in meaningful ways.
    
    Args:
        feature1: First feature
        feature2: Second feature
        operation: "multiply", "add", "subtract", "divide"
    
    Returns:
        list: Interaction feature values
    
    Examples:
        >>> from ilovetools.data import create_interaction_features
        
        # Multiply interaction
        >>> height = [170, 180, 160, 175]
        >>> weight = [70, 85, 60, 80]
        >>> bmi_proxy = create_interaction_features(height, weight, "multiply")
        
        # Real-world: Price per square foot
        >>> prices = [300000, 450000, 250000]
        >>> sqft = [1500, 2000, 1200]
        >>> price_per_sqft = create_interaction_features(prices, sqft, "divide")
        >>> print(price_per_sqft)
        [200.0, 225.0, 208.33]
        
        # Add interaction
        >>> feature1 = [1, 2, 3]
        >>> feature2 = [4, 5, 6]
        >>> combined = create_interaction_features(feature1, feature2, "add")
        >>> print(combined)
        [5, 7, 9]
    
    Notes:
        - Captures feature interactions
        - Common in real estate (price * sqft)
        - Useful in e-commerce (quantity * price)
        - Can significantly improve model performance
    """
    if isinstance(feature1, np.ndarray):
        feature1 = feature1.tolist()
    if isinstance(feature2, np.ndarray):
        feature2 = feature2.tolist()
    
    if len(feature1) != len(feature2):
        raise ValueError("Features must have same length")
    
    result = []
    for v1, v2 in zip(feature1, feature2):
        if operation == "multiply":
            result.append(v1 * v2)
        elif operation == "add":
            result.append(v1 + v2)
        elif operation == "subtract":
            result.append(v1 - v2)
        elif operation == "divide":
            result.append(v1 / v2 if v2 != 0 else 0.0)
        else:
            result.append(v1 * v2)
    
    return result
