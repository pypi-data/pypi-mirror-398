"""
Hyperparameter tuning utilities for ML workflows
Each function has TWO names: full descriptive name + abbreviated alias
"""

from typing import List, Dict, Any, Callable, Optional, Tuple
import random
import itertools

__all__ = [
    # Full names
    'grid_search_cv',
    'random_search_cv',
    'generate_param_grid',
    'extract_best_params',
    'format_cv_results',
    'learning_curve_data',
    'validation_curve_data',
    'early_stopping_monitor',
    'compare_models_cv',
    'bayesian_search_simple',
    # Abbreviated aliases
    'gridsearch',
    'randomsearch',
    'param_grid',
    'best_params',
    'cv_results',
    'learning_curve',
    'val_curve',
    'early_stop',
    'compare_models',
    'bayesopt',
]


def grid_search_cv(
    X: List,
    y: List,
    model_func: Callable,
    param_grid: Dict[str, List],
    metric_func: Callable,
    cv_splits: int = 5
) -> Dict[str, Any]:
    """
    Grid Search Cross-Validation for hyperparameter tuning.
    
    Alias: gridsearch()
    
    Exhaustively searches all parameter combinations.
    
    Args:
        X: Feature data
        y: Target data
        model_func: Function(params, X_train, y_train, X_val) -> predictions
        param_grid: Dictionary of parameter lists
        metric_func: Function(y_true, y_pred) -> score
        cv_splits: Number of CV folds. Default: 5
    
    Returns:
        dict: Best parameters, best score, all results
    
    Examples:
        >>> from ilovetools.ml import gridsearch  # Short alias
        >>> X = [[1], [2], [3], [4], [5]]
        >>> y = [1, 2, 3, 4, 5]
        >>> 
        >>> def model(params, X_tr, y_tr, X_val):
        ...     # Simple model with threshold param
        ...     threshold = params['threshold']
        ...     avg = sum(y_tr) / len(y_tr)
        ...     return [avg + threshold] * len(X_val)
        >>> 
        >>> def metric(y_true, y_pred):
        ...     return -sum(abs(t - p) for t, p in zip(y_true, y_pred)) / len(y_true)
        >>> 
        >>> param_grid = {'threshold': [0, 0.5, 1.0]}
        >>> results = gridsearch(X, y, model, param_grid, metric, cv_splits=3)
        >>> print(results['best_params'])
        
        >>> from ilovetools.ml import grid_search_cv  # Full name
        >>> results = grid_search_cv(X, y, model, param_grid, metric)
    
    Notes:
        - Tries all combinations
        - Exhaustive but slow
        - Good for small parameter spaces
        - Guaranteed to find best in grid
    """
    from .cross_validation import k_fold_cross_validation
    
    # Generate all parameter combinations
    param_names = list(param_grid.keys())
    param_values = [param_grid[name] for name in param_names]
    param_combinations = list(itertools.product(*param_values))
    
    results = []
    
    for combo in param_combinations:
        params = dict(zip(param_names, combo))
        
        # Perform CV
        splits = k_fold_cross_validation(X, y, k=cv_splits)
        scores = []
        
        for train_idx, val_idx in splits:
            X_train = [X[i] for i in train_idx]
            y_train = [y[i] for i in train_idx]
            X_val = [X[i] for i in val_idx]
            y_val = [y[i] for i in val_idx]
            
            y_pred = model_func(params, X_train, y_train, X_val)
            score = metric_func(y_val, y_pred)
            scores.append(score)
        
        mean_score = sum(scores) / len(scores)
        
        results.append({
            'params': params,
            'mean_score': mean_score,
            'scores': scores
        })
    
    # Find best
    best_result = max(results, key=lambda x: x['mean_score'])
    
    return {
        'best_params': best_result['params'],
        'best_score': best_result['mean_score'],
        'all_results': results,
        'n_combinations': len(param_combinations)
    }


# Create alias
gridsearch = grid_search_cv


def random_search_cv(
    X: List,
    y: List,
    model_func: Callable,
    param_distributions: Dict[str, List],
    metric_func: Callable,
    n_iter: int = 10,
    cv_splits: int = 5,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Random Search Cross-Validation for hyperparameter tuning.
    
    Alias: randomsearch()
    
    Randomly samples parameter combinations. Faster than grid search.
    
    Args:
        X: Feature data
        y: Target data
        model_func: Function(params, X_train, y_train, X_val) -> predictions
        param_distributions: Dictionary of parameter lists
        metric_func: Function(y_true, y_pred) -> score
        n_iter: Number of random combinations to try. Default: 10
        cv_splits: Number of CV folds. Default: 5
        random_state: Random seed for reproducibility
    
    Returns:
        dict: Best parameters, best score, all results
    
    Examples:
        >>> from ilovetools.ml import randomsearch  # Short alias
        >>> X = [[1], [2], [3], [4], [5]]
        >>> y = [1, 2, 3, 4, 5]
        >>> 
        >>> def model(params, X_tr, y_tr, X_val):
        ...     alpha = params['alpha']
        ...     avg = sum(y_tr) / len(y_tr)
        ...     return [avg * alpha] * len(X_val)
        >>> 
        >>> def metric(y_true, y_pred):
        ...     return -sum(abs(t - p) for t, p in zip(y_true, y_pred)) / len(y_true)
        >>> 
        >>> param_dist = {'alpha': [0.5, 0.8, 1.0, 1.2, 1.5]}
        >>> results = randomsearch(X, y, model, param_dist, metric, n_iter=3)
        
        >>> from ilovetools.ml import random_search_cv  # Full name
        >>> results = random_search_cv(X, y, model, param_dist, metric)
    
    Notes:
        - Faster than grid search
        - Often finds good params quickly
        - Good for large parameter spaces
        - May miss optimal combination
    """
    from .cross_validation import k_fold_cross_validation
    
    if random_state is not None:
        random.seed(random_state)
    
    param_names = list(param_distributions.keys())
    results = []
    
    for _ in range(n_iter):
        # Random sample
        params = {name: random.choice(param_distributions[name]) for name in param_names}
        
        # Perform CV
        splits = k_fold_cross_validation(X, y, k=cv_splits)
        scores = []
        
        for train_idx, val_idx in splits:
            X_train = [X[i] for i in train_idx]
            y_train = [y[i] for i in train_idx]
            X_val = [X[i] for i in val_idx]
            y_val = [y[i] for i in val_idx]
            
            y_pred = model_func(params, X_train, y_train, X_val)
            score = metric_func(y_val, y_pred)
            scores.append(score)
        
        mean_score = sum(scores) / len(scores)
        
        results.append({
            'params': params,
            'mean_score': mean_score,
            'scores': scores
        })
    
    # Find best
    best_result = max(results, key=lambda x: x['mean_score'])
    
    return {
        'best_params': best_result['params'],
        'best_score': best_result['mean_score'],
        'all_results': results,
        'n_iterations': n_iter
    }


# Create alias
randomsearch = random_search_cv


def generate_param_grid(
    param_ranges: Dict[str, Tuple[float, float, int]]
) -> Dict[str, List[float]]:
    """
    Generate parameter grid from ranges.
    
    Alias: param_grid()
    
    Creates evenly spaced parameter values.
    
    Args:
        param_ranges: Dict of (min, max, n_values) tuples
    
    Returns:
        dict: Parameter grid
    
    Examples:
        >>> from ilovetools.ml import param_grid  # Short alias
        >>> ranges = {
        ...     'learning_rate': (0.001, 0.1, 5),
        ...     'max_depth': (3, 10, 4)
        ... }
        >>> grid = param_grid(ranges)
        >>> print(grid)
        {'learning_rate': [0.001, 0.02575, 0.0505, 0.07525, 0.1], 'max_depth': [3.0, 5.333, 7.667, 10.0]}
        
        >>> from ilovetools.ml import generate_param_grid  # Full name
        >>> grid = generate_param_grid(ranges)
    
    Notes:
        - Creates evenly spaced values
        - Useful for continuous parameters
        - Combine with grid_search_cv
        - Adjust n_values for granularity
    """
    grid = {}
    
    for param_name, (min_val, max_val, n_values) in param_ranges.items():
        if n_values == 1:
            grid[param_name] = [min_val]
        else:
            step = (max_val - min_val) / (n_values - 1)
            grid[param_name] = [min_val + i * step for i in range(n_values)]
    
    return grid


# Create alias
param_grid = generate_param_grid


def extract_best_params(search_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract best parameters from search results.
    
    Alias: best_params()
    
    Args:
        search_results: Results from grid_search_cv or random_search_cv
    
    Returns:
        dict: Best parameters
    
    Examples:
        >>> from ilovetools.ml import best_params  # Short alias
        >>> results = {'best_params': {'alpha': 0.5}, 'best_score': 0.95}
        >>> params = best_params(results)
        >>> print(params)
        {'alpha': 0.5}
        
        >>> from ilovetools.ml import extract_best_params  # Full name
        >>> params = extract_best_params(results)
    
    Notes:
        - Simple extraction utility
        - Works with any search method
        - Returns clean parameter dict
        - Use for model training
    """
    return search_results.get('best_params', {})


# Create alias
best_params = extract_best_params


def format_cv_results(search_results: Dict[str, Any], top_n: int = 5) -> List[Dict]:
    """
    Format CV results for easy viewing.
    
    Alias: cv_results()
    
    Args:
        search_results: Results from search
        top_n: Number of top results to return. Default: 5
    
    Returns:
        list: Formatted top results
    
    Examples:
        >>> from ilovetools.ml import cv_results  # Short alias
        >>> results = {
        ...     'all_results': [
        ...         {'params': {'a': 1}, 'mean_score': 0.8},
        ...         {'params': {'a': 2}, 'mean_score': 0.9}
        ...     ]
        ... }
        >>> top = cv_results(results, top_n=2)
        
        >>> from ilovetools.ml import format_cv_results  # Full name
        >>> top = format_cv_results(results)
    
    Notes:
        - Shows top performing combinations
        - Sorted by score
        - Easy comparison
        - Use for analysis
    """
    all_results = search_results.get('all_results', [])
    sorted_results = sorted(all_results, key=lambda x: x['mean_score'], reverse=True)
    
    return sorted_results[:top_n]


# Create alias
cv_results = format_cv_results


def learning_curve_data(
    X: List,
    y: List,
    model_func: Callable,
    metric_func: Callable,
    train_sizes: List[float] = None
) -> Dict[str, List]:
    """
    Generate learning curve data.
    
    Alias: learning_curve()
    
    Shows how model performance changes with training set size.
    
    Args:
        X: Feature data
        y: Target data
        model_func: Function(X_train, y_train, X_val) -> predictions
        metric_func: Function(y_true, y_pred) -> score
        train_sizes: List of training set proportions. Default: [0.2, 0.4, 0.6, 0.8, 1.0]
    
    Returns:
        dict: Training sizes, train scores, validation scores
    
    Examples:
        >>> from ilovetools.ml import learning_curve  # Short alias
        >>> X = list(range(20))
        >>> y = [i * 2 for i in X]
        >>> 
        >>> def model(X_tr, y_tr, X_val):
        ...     avg = sum(y_tr) / len(y_tr)
        ...     return [avg] * len(X_val)
        >>> 
        >>> def metric(y_true, y_pred):
        ...     return -sum(abs(t - p) for t, p in zip(y_true, y_pred)) / len(y_true)
        >>> 
        >>> curve = learning_curve(X, y, model, metric)
        
        >>> from ilovetools.ml import learning_curve_data  # Full name
        >>> curve = learning_curve_data(X, y, model, metric)
    
    Notes:
        - Diagnose overfitting/underfitting
        - Shows if more data helps
        - Plot train vs val scores
        - Use for model selection
    """
    if train_sizes is None:
        train_sizes = [0.2, 0.4, 0.6, 0.8, 1.0]
    
    from .cross_validation import holdout_validation_split
    
    train_scores = []
    val_scores = []
    
    for size in train_sizes:
        # Split data
        X_train, X_val, y_train, y_val = holdout_validation_split(
            X, y, test_size=1-size
        )
        
        # Train and evaluate
        y_train_pred = model_func(X_train, y_train, X_train)
        y_val_pred = model_func(X_train, y_train, X_val)
        
        train_score = metric_func(y_train, y_train_pred)
        val_score = metric_func(y_val, y_val_pred)
        
        train_scores.append(train_score)
        val_scores.append(val_score)
    
    return {
        'train_sizes': train_sizes,
        'train_scores': train_scores,
        'val_scores': val_scores
    }


# Create alias
learning_curve = learning_curve_data


def validation_curve_data(
    X: List,
    y: List,
    model_func: Callable,
    metric_func: Callable,
    param_name: str,
    param_range: List
) -> Dict[str, List]:
    """
    Generate validation curve data.
    
    Alias: val_curve()
    
    Shows how model performance changes with a hyperparameter.
    
    Args:
        X: Feature data
        y: Target data
        model_func: Function(param_value, X_train, y_train, X_val) -> predictions
        metric_func: Function(y_true, y_pred) -> score
        param_name: Name of parameter to vary
        param_range: List of parameter values to try
    
    Returns:
        dict: Parameter values, train scores, validation scores
    
    Examples:
        >>> from ilovetools.ml import val_curve  # Short alias
        >>> X = list(range(10))
        >>> y = [i * 2 for i in X]
        >>> 
        >>> def model(param_val, X_tr, y_tr, X_val):
        ...     avg = sum(y_tr) / len(y_tr)
        ...     return [avg * param_val] * len(X_val)
        >>> 
        >>> def metric(y_true, y_pred):
        ...     return -sum(abs(t - p) for t, p in zip(y_true, y_pred)) / len(y_true)
        >>> 
        >>> curve = val_curve(X, y, model, metric, 'alpha', [0.5, 1.0, 1.5])
        
        >>> from ilovetools.ml import validation_curve_data  # Full name
        >>> curve = validation_curve_data(X, y, model, metric, 'alpha', [0.5, 1.0])
    
    Notes:
        - Visualize hyperparameter impact
        - Find optimal parameter value
        - Detect overfitting
        - Use for tuning guidance
    """
    from .cross_validation import holdout_validation_split
    
    train_scores = []
    val_scores = []
    
    for param_value in param_range:
        # Split data
        X_train, X_val, y_train, y_val = holdout_validation_split(X, y)
        
        # Train and evaluate
        y_train_pred = model_func(param_value, X_train, y_train, X_train)
        y_val_pred = model_func(param_value, X_train, y_train, X_val)
        
        train_score = metric_func(y_train, y_train_pred)
        val_score = metric_func(y_val, y_val_pred)
        
        train_scores.append(train_score)
        val_scores.append(val_score)
    
    return {
        'param_name': param_name,
        'param_range': param_range,
        'train_scores': train_scores,
        'val_scores': val_scores
    }


# Create alias
val_curve = validation_curve_data


def early_stopping_monitor(
    scores: List[float],
    patience: int = 5,
    min_delta: float = 0.001
) -> bool:
    """
    Monitor for early stopping.
    
    Alias: early_stop()
    
    Stops training if no improvement for patience epochs.
    
    Args:
        scores: List of validation scores (higher is better)
        patience: Number of epochs to wait. Default: 5
        min_delta: Minimum improvement threshold. Default: 0.001
    
    Returns:
        bool: True if should stop, False otherwise
    
    Examples:
        >>> from ilovetools.ml import early_stop  # Short alias
        >>> scores = [0.7, 0.75, 0.78, 0.78, 0.78, 0.78]
        >>> should_stop = early_stop(scores, patience=3)
        >>> print(should_stop)
        True
        
        >>> from ilovetools.ml import early_stopping_monitor  # Full name
        >>> should_stop = early_stopping_monitor(scores, patience=5)
    
    Notes:
        - Prevents overfitting
        - Saves training time
        - Common in neural networks
        - Adjust patience for stability
    """
    if len(scores) < patience + 1:
        return False
    
    best_score = max(scores[:-patience])
    recent_scores = scores[-patience:]
    
    # Check if any recent score improved
    for score in recent_scores:
        if score > best_score + min_delta:
            return False
    
    return True


# Create alias
early_stop = early_stopping_monitor


def compare_models_cv(
    X: List,
    y: List,
    models: Dict[str, Callable],
    metric_func: Callable,
    cv_splits: int = 5
) -> Dict[str, Dict]:
    """
    Compare multiple models using cross-validation.
    
    Alias: compare_models()
    
    Args:
        X: Feature data
        y: Target data
        models: Dict of model_name: model_func
        metric_func: Function(y_true, y_pred) -> score
        cv_splits: Number of CV folds. Default: 5
    
    Returns:
        dict: Results for each model
    
    Examples:
        >>> from ilovetools.ml import compare_models  # Short alias
        >>> X = [[1], [2], [3], [4], [5]]
        >>> y = [1, 2, 3, 4, 5]
        >>> 
        >>> def model1(X_tr, y_tr, X_val):
        ...     avg = sum(y_tr) / len(y_tr)
        ...     return [avg] * len(X_val)
        >>> 
        >>> def model2(X_tr, y_tr, X_val):
        ...     avg = sum(y_tr) / len(y_tr)
        ...     return [avg + 0.5] * len(X_val)
        >>> 
        >>> def metric(y_true, y_pred):
        ...     return -sum(abs(t - p) for t, p in zip(y_true, y_pred)) / len(y_true)
        >>> 
        >>> models = {'Model1': model1, 'Model2': model2}
        >>> results = compare_models(X, y, models, metric)
        
        >>> from ilovetools.ml import compare_models_cv  # Full name
        >>> results = compare_models_cv(X, y, models, metric)
    
    Notes:
        - Compare multiple algorithms
        - Fair comparison with same CV splits
        - Returns mean and std for each
        - Use for model selection
    """
    from .cross_validation import k_fold_cross_validation
    
    splits = k_fold_cross_validation(X, y, k=cv_splits)
    results = {}
    
    for model_name, model_func in models.items():
        scores = []
        
        for train_idx, val_idx in splits:
            X_train = [X[i] for i in train_idx]
            y_train = [y[i] for i in train_idx]
            X_val = [X[i] for i in val_idx]
            y_val = [y[i] for i in val_idx]
            
            y_pred = model_func(X_train, y_train, X_val)
            score = metric_func(y_val, y_pred)
            scores.append(score)
        
        results[model_name] = {
            'mean_score': sum(scores) / len(scores),
            'std_score': (sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)) ** 0.5,
            'scores': scores
        }
    
    return results


# Create alias
compare_models = compare_models_cv


def bayesian_search_simple(
    X: List,
    y: List,
    model_func: Callable,
    param_bounds: Dict[str, Tuple[float, float]],
    metric_func: Callable,
    n_iter: int = 10,
    cv_splits: int = 5
) -> Dict[str, Any]:
    """
    Simple Bayesian optimization for hyperparameter tuning.
    
    Alias: bayesopt()
    
    Uses past results to guide search. More efficient than random search.
    
    Args:
        X: Feature data
        y: Target data
        model_func: Function(params, X_train, y_train, X_val) -> predictions
        param_bounds: Dict of (min, max) tuples
        metric_func: Function(y_true, y_pred) -> score
        n_iter: Number of iterations. Default: 10
        cv_splits: Number of CV folds. Default: 5
    
    Returns:
        dict: Best parameters, best score, all results
    
    Examples:
        >>> from ilovetools.ml import bayesopt  # Short alias
        >>> X = [[1], [2], [3], [4], [5]]
        >>> y = [1, 2, 3, 4, 5]
        >>> 
        >>> def model(params, X_tr, y_tr, X_val):
        ...     alpha = params['alpha']
        ...     avg = sum(y_tr) / len(y_tr)
        ...     return [avg * alpha] * len(X_val)
        >>> 
        >>> def metric(y_true, y_pred):
        ...     return -sum(abs(t - p) for t, p in zip(y_true, y_pred)) / len(y_true)
        >>> 
        >>> bounds = {'alpha': (0.5, 1.5)}
        >>> results = bayesopt(X, y, model, bounds, metric, n_iter=5)
        
        >>> from ilovetools.ml import bayesian_search_simple  # Full name
        >>> results = bayesian_search_simple(X, y, model, bounds, metric)
    
    Notes:
        - More efficient than random search
        - Learns from past evaluations
        - Good for expensive models
        - Simplified implementation
    """
    from .cross_validation import k_fold_cross_validation
    
    results = []
    
    # Initial random samples
    n_random = min(3, n_iter)
    
    for i in range(n_iter):
        if i < n_random:
            # Random sampling initially
            params = {
                name: random.uniform(bounds[0], bounds[1])
                for name, bounds in param_bounds.items()
            }
        else:
            # Exploit best region
            best_params = max(results, key=lambda x: x['mean_score'])['params']
            params = {
                name: best_params[name] + random.uniform(-0.1, 0.1) * (bounds[1] - bounds[0])
                for name, bounds in param_bounds.items()
            }
            # Clip to bounds
            params = {
                name: max(param_bounds[name][0], min(param_bounds[name][1], val))
                for name, val in params.items()
            }
        
        # Evaluate
        splits = k_fold_cross_validation(X, y, k=cv_splits)
        scores = []
        
        for train_idx, val_idx in splits:
            X_train = [X[i] for i in train_idx]
            y_train = [y[i] for i in train_idx]
            X_val = [X[i] for i in val_idx]
            y_val = [y[i] for i in val_idx]
            
            y_pred = model_func(params, X_train, y_train, X_val)
            score = metric_func(y_val, y_pred)
            scores.append(score)
        
        mean_score = sum(scores) / len(scores)
        
        results.append({
            'params': params,
            'mean_score': mean_score,
            'scores': scores
        })
    
    # Find best
    best_result = max(results, key=lambda x: x['mean_score'])
    
    return {
        'best_params': best_result['params'],
        'best_score': best_result['mean_score'],
        'all_results': results,
        'n_iterations': n_iter
    }


# Create alias
bayesopt = bayesian_search_simple
