"""
Model interpretation utilities for ML workflows
Each function has TWO names: full descriptive name + abbreviated alias
"""

from typing import List, Dict, Any, Callable, Optional, Tuple
import random

__all__ = [
    # Full names
    'feature_importance_scores',
    'permutation_importance',
    'partial_dependence',
    'shap_values_approximation',
    'lime_explanation',
    'decision_path_explanation',
    'model_coefficients_interpretation',
    'prediction_breakdown',
    'feature_contribution_analysis',
    'global_feature_importance',
    'local_feature_importance',
    'model_summary_statistics',
    # Abbreviated aliases
    'feat_importance_scores',
    'perm_importance',
    'pdp',
    'shap_approx',
    'lime_explain',
    'decision_path',
    'coef_interpret',
    'pred_breakdown',
    'feat_contrib',
    'global_importance',
    'local_importance',
    'model_summary',
]


def feature_importance_scores(
    importances: List[float],
    feature_names: Optional[List[str]] = None,
    normalize: bool = True
) -> Dict[str, float]:
    """
    Calculate and format feature importance scores.
    
    Alias: feat_importance_scores()
    
    Args:
        importances: Raw importance scores
        feature_names: Optional feature names
        normalize: Normalize to sum to 1.0
    
    Returns:
        dict: Feature name to importance mapping
    
    Examples:
        >>> from ilovetools.ml import feat_importance_scores  # Short alias
        
        >>> importances = [0.5, 0.3, 0.2]
        >>> feature_names = ['age', 'income', 'debt']
        >>> 
        >>> scores = feat_importance_scores(importances, feature_names)
        >>> print(scores)
        {'age': 0.5, 'income': 0.3, 'debt': 0.2}
        
        >>> # Normalized
        >>> scores = feat_importance_scores([10, 20, 30], feature_names, normalize=True)
        >>> print(scores)
        {'age': 0.167, 'income': 0.333, 'debt': 0.5}
        
        >>> from ilovetools.ml import feature_importance_scores  # Full name
        >>> scores = feature_importance_scores(importances, feature_names)
    
    Notes:
        - Works with any importance scores
        - Random Forest, XGBoost, etc.
        - Normalize for percentages
        - Easy to visualize
    """
    n_features = len(importances)
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    if normalize:
        total = sum(importances)
        if total > 0:
            importances = [imp / total for imp in importances]
    
    return {name: imp for name, imp in zip(feature_names, importances)}


# Create alias
feat_importance_scores = feature_importance_scores


def permutation_importance(
    X: List[List[float]],
    y: List,
    model_func: Callable,
    metric_func: Callable,
    feature_names: Optional[List[str]] = None,
    n_repeats: int = 10,
    random_state: Optional[int] = None
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Calculate permutation importance for features.
    
    Alias: perm_importance()
    
    Args:
        X: Feature matrix [n_samples, n_features]
        y: Target values
        model_func: Function(X) -> predictions
        metric_func: Function(y_true, y_pred) -> score (higher is better)
        feature_names: Optional feature names
        n_repeats: Number of permutation repeats
        random_state: Random seed
    
    Returns:
        tuple: (mean_importances, std_importances)
    
    Examples:
        >>> from ilovetools.ml import perm_importance  # Short alias
        
        >>> X = [[1, 2], [2, 4], [3, 6], [4, 8]]
        >>> y = [1, 2, 3, 4]
        >>> 
        >>> def model(X_test):
        ...     return [sum(row) / len(row) for row in X_test]
        >>> 
        >>> def metric(y_true, y_pred):
        ...     return -sum(abs(y_true[i] - y_pred[i]) for i in range(len(y_true)))
        >>> 
        >>> mean_imp, std_imp = perm_importance(X, y, model, metric, n_repeats=5)
        >>> print(f"Importances: {mean_imp}")
        
        >>> from ilovetools.ml import permutation_importance  # Full name
        >>> mean_imp, std_imp = permutation_importance(X, y, model, metric)
    
    Notes:
        - Model-agnostic method
        - Measures true importance
        - Shuffle feature, measure drop
        - Higher drop = more important
    """
    if random_state is not None:
        random.seed(random_state)
    
    n_features = len(X[0])
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    # Baseline score
    baseline_preds = model_func(X)
    baseline_score = metric_func(y, baseline_preds)
    
    # Calculate importance for each feature
    importances = {name: [] for name in feature_names}
    
    for _ in range(n_repeats):
        for i, name in enumerate(feature_names):
            # Copy X and shuffle feature i
            X_permuted = [row[:] for row in X]
            col_values = [row[i] for row in X_permuted]
            random.shuffle(col_values)
            for j, row in enumerate(X_permuted):
                row[i] = col_values[j]
            
            # Calculate score with permuted feature
            permuted_preds = model_func(X_permuted)
            permuted_score = metric_func(y, permuted_preds)
            
            # Importance = drop in score
            importance = baseline_score - permuted_score
            importances[name].append(importance)
    
    # Calculate mean and std
    mean_importances = {name: sum(vals) / len(vals) for name, vals in importances.items()}
    std_importances = {
        name: (sum((x - mean_importances[name]) ** 2 for x in vals) / len(vals)) ** 0.5
        for name, vals in importances.items()
    }
    
    return mean_importances, std_importances


# Create alias
perm_importance = permutation_importance


def partial_dependence(
    X: List[List[float]],
    model_func: Callable,
    feature_index: int,
    grid_resolution: int = 20
) -> Tuple[List[float], List[float]]:
    """
    Calculate partial dependence for a feature.
    
    Alias: pdp()
    
    Args:
        X: Feature matrix [n_samples, n_features]
        model_func: Function(X) -> predictions
        feature_index: Index of feature to analyze
        grid_resolution: Number of grid points
    
    Returns:
        tuple: (grid_values, pd_values)
    
    Examples:
        >>> from ilovetools.ml import pdp  # Short alias
        
        >>> X = [[1, 10], [2, 20], [3, 30], [4, 40]]
        >>> 
        >>> def model(X_test):
        ...     return [row[0] * 2 + row[1] * 0.5 for row in X_test]
        >>> 
        >>> grid, pd_vals = pdp(X, model, feature_index=0, grid_resolution=5)
        >>> print(f"Grid: {grid}")
        >>> print(f"PD values: {pd_vals}")
        
        >>> from ilovetools.ml import partial_dependence  # Full name
        >>> grid, pd_vals = partial_dependence(X, model, feature_index=0)
    
    Notes:
        - Shows feature effect on prediction
        - Marginal effect
        - Model-agnostic
        - Good for visualization
    """
    # Get feature values
    feature_values = [row[feature_index] for row in X]
    min_val = min(feature_values)
    max_val = max(feature_values)
    
    # Create grid
    step = (max_val - min_val) / (grid_resolution - 1) if grid_resolution > 1 else 0
    grid_values = [min_val + i * step for i in range(grid_resolution)]
    
    # Calculate PD for each grid point
    pd_values = []
    
    for grid_val in grid_values:
        # Create modified X with feature set to grid_val
        X_modified = [row[:] for row in X]
        for row in X_modified:
            row[feature_index] = grid_val
        
        # Get predictions and average
        predictions = model_func(X_modified)
        avg_prediction = sum(predictions) / len(predictions)
        pd_values.append(avg_prediction)
    
    return grid_values, pd_values


# Create alias
pdp = partial_dependence


def shap_values_approximation(
    X: List[List[float]],
    model_func: Callable,
    instance_index: int,
    feature_names: Optional[List[str]] = None,
    n_samples: int = 100
) -> Dict[str, float]:
    """
    Approximate SHAP values for an instance.
    
    Alias: shap_approx()
    
    Args:
        X: Feature matrix [n_samples, n_features]
        model_func: Function(X) -> predictions
        instance_index: Index of instance to explain
        feature_names: Optional feature names
        n_samples: Number of samples for approximation
    
    Returns:
        dict: Feature name to SHAP value mapping
    
    Examples:
        >>> from ilovetools.ml import shap_approx  # Short alias
        
        >>> X = [[1, 2], [2, 4], [3, 6], [4, 8]]
        >>> 
        >>> def model(X_test):
        ...     return [row[0] * 2 + row[1] * 0.5 for row in X_test]
        >>> 
        >>> shap_vals = shap_approx(X, model, instance_index=0, n_samples=50)
        >>> print(f"SHAP values: {shap_vals}")
        
        >>> from ilovetools.ml import shap_values_approximation  # Full name
        >>> shap_vals = shap_values_approximation(X, model, instance_index=0)
    
    Notes:
        - Simplified SHAP approximation
        - Fair feature attribution
        - Game theory based
        - Explains individual predictions
    """
    n_features = len(X[0])
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    instance = X[instance_index]
    
    # Base prediction (average of all predictions)
    all_preds = model_func(X)
    base_value = sum(all_preds) / len(all_preds)
    
    # Instance prediction
    instance_pred = model_func([instance])[0]
    
    # Approximate SHAP values using marginal contributions
    shap_values = {}
    
    for i, name in enumerate(feature_names):
        # Calculate contribution by comparing with and without feature
        contributions = []
        
        for _ in range(min(n_samples, len(X))):
            # Random background instance
            bg_idx = random.randint(0, len(X) - 1)
            background = X[bg_idx][:]
            
            # With feature
            with_feature = background[:]
            with_feature[i] = instance[i]
            pred_with = model_func([with_feature])[0]
            
            # Without feature (background value)
            pred_without = model_func([background])[0]
            
            contribution = pred_with - pred_without
            contributions.append(contribution)
        
        # Average contribution
        shap_values[name] = sum(contributions) / len(contributions)
    
    return shap_values


# Create alias
shap_approx = shap_values_approximation


def lime_explanation(
    X: List[List[float]],
    model_func: Callable,
    instance_index: int,
    feature_names: Optional[List[str]] = None,
    n_samples: int = 100,
    random_state: Optional[int] = None
) -> Dict[str, float]:
    """
    LIME local explanation for an instance.
    
    Alias: lime_explain()
    
    Args:
        X: Feature matrix [n_samples, n_features]
        model_func: Function(X) -> predictions
        instance_index: Index of instance to explain
        feature_names: Optional feature names
        n_samples: Number of perturbed samples
        random_state: Random seed
    
    Returns:
        dict: Feature name to coefficient mapping
    
    Examples:
        >>> from ilovetools.ml import lime_explain  # Short alias
        
        >>> X = [[1, 2], [2, 4], [3, 6], [4, 8]]
        >>> 
        >>> def model(X_test):
        ...     return [row[0] * 2 + row[1] * 0.5 for row in X_test]
        >>> 
        >>> explanation = lime_explain(X, model, instance_index=0, n_samples=50)
        >>> print(f"LIME coefficients: {explanation}")
        
        >>> from ilovetools.ml import lime_explanation  # Full name
        >>> explanation = lime_explanation(X, model, instance_index=0)
    
    Notes:
        - Local linear approximation
        - Model-agnostic
        - Easy to understand
        - Perturbs features locally
    """
    if random_state is not None:
        random.seed(random_state)
    
    n_features = len(X[0])
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    instance = X[instance_index]
    
    # Generate perturbed samples around instance
    perturbed_X = []
    for _ in range(n_samples):
        perturbed = []
        for i in range(n_features):
            # Add random noise
            noise = random.gauss(0, 0.1 * abs(instance[i]) if instance[i] != 0 else 0.1)
            perturbed.append(instance[i] + noise)
        perturbed_X.append(perturbed)
    
    # Get predictions for perturbed samples
    perturbed_preds = model_func(perturbed_X)
    
    # Fit simple linear model (simplified)
    # Calculate correlation-based coefficients
    coefficients = {}
    
    for i, name in enumerate(feature_names):
        feature_values = [row[i] for row in perturbed_X]
        
        # Calculate correlation with predictions
        mean_feat = sum(feature_values) / len(feature_values)
        mean_pred = sum(perturbed_preds) / len(perturbed_preds)
        
        numerator = sum((feature_values[j] - mean_feat) * (perturbed_preds[j] - mean_pred)
                       for j in range(len(feature_values)))
        
        denominator = sum((f - mean_feat) ** 2 for f in feature_values)
        
        if denominator > 0:
            coef = numerator / denominator
        else:
            coef = 0.0
        
        coefficients[name] = coef
    
    return coefficients


# Create alias
lime_explain = lime_explanation


def decision_path_explanation(
    tree_structure: List[Dict],
    instance: List[float],
    feature_names: Optional[List[str]] = None
) -> List[str]:
    """
    Explain decision path through a tree.
    
    Alias: decision_path()
    
    Args:
        tree_structure: List of decision nodes
        instance: Feature values for instance
        feature_names: Optional feature names
    
    Returns:
        list: Human-readable decision path
    
    Examples:
        >>> from ilovetools.ml import decision_path  # Short alias
        
        >>> tree = [
        ...     {'feature': 0, 'threshold': 2.5, 'left': 1, 'right': 2},
        ...     {'value': 'Class A'},
        ...     {'value': 'Class B'}
        ... ]
        >>> instance = [3.0, 10.0]
        >>> feature_names = ['age', 'income']
        >>> 
        >>> path = decision_path(tree, instance, feature_names)
        >>> for step in path:
        ...     print(step)
        
        >>> from ilovetools.ml import decision_path_explanation  # Full name
        >>> path = decision_path_explanation(tree, instance, feature_names)
    
    Notes:
        - For decision trees
        - Shows exact reasoning
        - Naturally interpretable
        - Follow the path
    """
    n_features = len(instance)
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    path = []
    node_idx = 0
    
    while node_idx < len(tree_structure):
        node = tree_structure[node_idx]
        
        if 'value' in node:
            # Leaf node
            path.append(f"Prediction: {node['value']}")
            break
        
        # Decision node
        feature_idx = node['feature']
        threshold = node['threshold']
        feature_name = feature_names[feature_idx]
        feature_value = instance[feature_idx]
        
        if feature_value <= threshold:
            path.append(f"{feature_name} ({feature_value:.2f}) <= {threshold:.2f}")
            node_idx = node['left']
        else:
            path.append(f"{feature_name} ({feature_value:.2f}) > {threshold:.2f}")
            node_idx = node['right']
    
    return path


# Create alias
decision_path = decision_path_explanation


def model_coefficients_interpretation(
    coefficients: List[float],
    feature_names: Optional[List[str]] = None,
    intercept: float = 0.0
) -> Dict[str, Any]:
    """
    Interpret linear model coefficients.
    
    Alias: coef_interpret()
    
    Args:
        coefficients: Model coefficients
        feature_names: Optional feature names
        intercept: Model intercept
    
    Returns:
        dict: Interpretation details
    
    Examples:
        >>> from ilovetools.ml import coef_interpret  # Short alias
        
        >>> coefficients = [2.5, -1.3, 0.8]
        >>> feature_names = ['age', 'debt', 'income']
        >>> intercept = 10.0
        >>> 
        >>> interpretation = coef_interpret(coefficients, feature_names, intercept)
        >>> print(interpretation['positive_features'])
        >>> print(interpretation['negative_features'])
        
        >>> from ilovetools.ml import model_coefficients_interpretation  # Full name
        >>> interpretation = model_coefficients_interpretation(coefficients, feature_names)
    
    Notes:
        - For linear models
        - Shows feature effects
        - Positive/negative impact
        - Magnitude matters
    """
    n_features = len(coefficients)
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    # Separate positive and negative
    positive_features = []
    negative_features = []
    
    for name, coef in zip(feature_names, coefficients):
        if coef > 0:
            positive_features.append((name, coef))
        elif coef < 0:
            negative_features.append((name, abs(coef)))
    
    # Sort by magnitude
    positive_features.sort(key=lambda x: x[1], reverse=True)
    negative_features.sort(key=lambda x: x[1], reverse=True)
    
    return {
        'intercept': intercept,
        'positive_features': positive_features,
        'negative_features': negative_features,
        'strongest_positive': positive_features[0] if positive_features else None,
        'strongest_negative': negative_features[0] if negative_features else None,
    }


# Create alias
coef_interpret = model_coefficients_interpretation


def prediction_breakdown(
    instance: List[float],
    coefficients: List[float],
    feature_names: Optional[List[str]] = None,
    intercept: float = 0.0
) -> Dict[str, Any]:
    """
    Break down prediction into feature contributions.
    
    Alias: pred_breakdown()
    
    Args:
        instance: Feature values
        coefficients: Model coefficients
        feature_names: Optional feature names
        intercept: Model intercept
    
    Returns:
        dict: Prediction breakdown
    
    Examples:
        >>> from ilovetools.ml import pred_breakdown  # Short alias
        
        >>> instance = [30, 50000, 10000]
        >>> coefficients = [0.5, 0.0001, -0.0002]
        >>> feature_names = ['age', 'income', 'debt']
        >>> intercept = 10.0
        >>> 
        >>> breakdown = pred_breakdown(instance, coefficients, feature_names, intercept)
        >>> print(f"Base: {breakdown['base']}")
        >>> print(f"Contributions: {breakdown['contributions']}")
        >>> print(f"Total: {breakdown['prediction']}")
        
        >>> from ilovetools.ml import prediction_breakdown  # Full name
        >>> breakdown = prediction_breakdown(instance, coefficients, feature_names)
    
    Notes:
        - Shows exact calculation
        - Feature-by-feature contribution
        - Transparent prediction
        - Easy to verify
    """
    n_features = len(instance)
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    contributions = {}
    total = intercept
    
    for name, value, coef in zip(feature_names, instance, coefficients):
        contribution = value * coef
        contributions[name] = contribution
        total += contribution
    
    return {
        'base': intercept,
        'contributions': contributions,
        'prediction': total,
        'feature_values': {name: val for name, val in zip(feature_names, instance)},
    }


# Create alias
pred_breakdown = prediction_breakdown


def feature_contribution_analysis(
    X: List[List[float]],
    coefficients: List[float],
    feature_names: Optional[List[str]] = None
) -> Dict[str, Dict[str, float]]:
    """
    Analyze feature contributions across dataset.
    
    Alias: feat_contrib()
    
    Args:
        X: Feature matrix [n_samples, n_features]
        coefficients: Model coefficients
        feature_names: Optional feature names
    
    Returns:
        dict: Contribution statistics per feature
    
    Examples:
        >>> from ilovetools.ml import feat_contrib  # Short alias
        
        >>> X = [[1, 2], [2, 4], [3, 6]]
        >>> coefficients = [2.0, 0.5]
        >>> feature_names = ['age', 'income']
        >>> 
        >>> analysis = feat_contrib(X, coefficients, feature_names)
        >>> print(analysis['age'])
        {'mean': ..., 'min': ..., 'max': ...}
        
        >>> from ilovetools.ml import feature_contribution_analysis  # Full name
        >>> analysis = feature_contribution_analysis(X, coefficients, feature_names)
    
    Notes:
        - Global contribution view
        - Mean, min, max contributions
        - Understand feature impact
        - Across all predictions
    """
    n_features = len(X[0])
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    # Calculate contributions for each instance
    contributions = {name: [] for name in feature_names}
    
    for instance in X:
        for i, (name, value, coef) in enumerate(zip(feature_names, instance, coefficients)):
            contribution = value * coef
            contributions[name].append(contribution)
    
    # Calculate statistics
    analysis = {}
    
    for name, contribs in contributions.items():
        analysis[name] = {
            'mean': sum(contribs) / len(contribs),
            'min': min(contribs),
            'max': max(contribs),
            'std': (sum((c - sum(contribs) / len(contribs)) ** 2 for c in contribs) / len(contribs)) ** 0.5,
        }
    
    return analysis


# Create alias
feat_contrib = feature_contribution_analysis


def global_feature_importance(
    importances: List[float],
    feature_names: Optional[List[str]] = None,
    top_k: Optional[int] = None
) -> List[Tuple[str, float]]:
    """
    Get global feature importance ranking.
    
    Alias: global_importance()
    
    Args:
        importances: Feature importance scores
        feature_names: Optional feature names
        top_k: Return only top k features
    
    Returns:
        list: Sorted list of (feature_name, importance) tuples
    
    Examples:
        >>> from ilovetools.ml import global_importance  # Short alias
        
        >>> importances = [0.5, 0.3, 0.15, 0.05]
        >>> feature_names = ['age', 'income', 'debt', 'credit']
        >>> 
        >>> ranking = global_importance(importances, feature_names, top_k=3)
        >>> for name, score in ranking:
        ...     print(f"{name}: {score:.2f}")
        
        >>> from ilovetools.ml import global_feature_importance  # Full name
        >>> ranking = global_feature_importance(importances, feature_names)
    
    Notes:
        - Overall model behavior
        - Ranked by importance
        - Top features first
        - Global view
    """
    n_features = len(importances)
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(n_features)]
    
    # Create and sort pairs
    pairs = list(zip(feature_names, importances))
    pairs.sort(key=lambda x: x[1], reverse=True)
    
    if top_k is not None:
        pairs = pairs[:top_k]
    
    return pairs


# Create alias
global_importance = global_feature_importance


def local_feature_importance(
    instance: List[float],
    shap_values: Dict[str, float],
    base_value: float
) -> Dict[str, Any]:
    """
    Get local feature importance for an instance.
    
    Alias: local_importance()
    
    Args:
        instance: Feature values
        shap_values: SHAP values for features
        base_value: Base prediction value
    
    Returns:
        dict: Local importance details
    
    Examples:
        >>> from ilovetools.ml import local_importance  # Short alias
        
        >>> instance = [30, 50000]
        >>> shap_values = {'age': 0.2, 'income': 0.15}
        >>> base_value = 0.5
        >>> 
        >>> local_imp = local_importance(instance, shap_values, base_value)
        >>> print(f"Prediction: {local_imp['prediction']}")
        >>> print(f"Top contributor: {local_imp['top_contributor']}")
        
        >>> from ilovetools.ml import local_feature_importance  # Full name
        >>> local_imp = local_feature_importance(instance, shap_values, base_value)
    
    Notes:
        - Individual prediction explanation
        - Feature contributions
        - Local view
        - Instance-specific
    """
    # Sort by absolute SHAP value
    sorted_features = sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)
    
    # Calculate prediction
    prediction = base_value + sum(shap_values.values())
    
    # Separate positive and negative
    positive_contrib = [(k, v) for k, v in sorted_features if v > 0]
    negative_contrib = [(k, abs(v)) for k, v in sorted_features if v < 0]
    
    return {
        'base_value': base_value,
        'prediction': prediction,
        'shap_values': shap_values,
        'top_contributor': sorted_features[0] if sorted_features else None,
        'positive_contributors': positive_contrib,
        'negative_contributors': negative_contrib,
    }


# Create alias
local_importance = local_feature_importance


def model_summary_statistics(
    predictions: List[float],
    actuals: Optional[List[float]] = None,
    feature_importances: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Generate model summary statistics.
    
    Alias: model_summary()
    
    Args:
        predictions: Model predictions
        actuals: Optional actual values
        feature_importances: Optional feature importance scores
    
    Returns:
        dict: Summary statistics
    
    Examples:
        >>> from ilovetools.ml import model_summary  # Short alias
        
        >>> predictions = [1.2, 2.1, 2.9, 4.1]
        >>> actuals = [1.0, 2.0, 3.0, 4.0]
        >>> importances = {'age': 0.5, 'income': 0.3, 'debt': 0.2}
        >>> 
        >>> summary = model_summary(predictions, actuals, importances)
        >>> print(f"Mean prediction: {summary['mean_prediction']}")
        >>> print(f"MAE: {summary['mae']}")
        
        >>> from ilovetools.ml import model_summary_statistics  # Full name
        >>> summary = model_summary_statistics(predictions, actuals, importances)
    
    Notes:
        - Overall model performance
        - Prediction statistics
        - Error metrics
        - Feature importance summary
    """
    summary = {
        'n_predictions': len(predictions),
        'mean_prediction': sum(predictions) / len(predictions),
        'min_prediction': min(predictions),
        'max_prediction': max(predictions),
        'std_prediction': (sum((p - sum(predictions) / len(predictions)) ** 2 
                              for p in predictions) / len(predictions)) ** 0.5,
    }
    
    if actuals is not None:
        errors = [abs(predictions[i] - actuals[i]) for i in range(len(predictions))]
        summary['mae'] = sum(errors) / len(errors)
        summary['mse'] = sum(e ** 2 for e in errors) / len(errors)
        summary['rmse'] = summary['mse'] ** 0.5
    
    if feature_importances is not None:
        sorted_features = sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)
        summary['top_features'] = sorted_features[:5]
        summary['n_features'] = len(feature_importances)
    
    return summary


# Create alias
model_summary = model_summary_statistics
