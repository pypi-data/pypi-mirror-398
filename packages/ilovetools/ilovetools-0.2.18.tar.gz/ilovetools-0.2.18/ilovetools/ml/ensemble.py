"""
Ensemble methods utilities for ML workflows
Each function has TWO names: full descriptive name + abbreviated alias
"""

from typing import List, Dict, Any, Callable, Optional, Tuple
import random

__all__ = [
    # Full names
    'voting_classifier',
    'voting_regressor',
    'bagging_predictions',
    'boosting_sequential',
    'stacking_ensemble',
    'weighted_average_ensemble',
    'majority_vote',
    'soft_vote',
    'bootstrap_sample',
    'out_of_bag_score',
    'ensemble_diversity',
    'blend_predictions',
    # Abbreviated aliases
    'vote_clf',
    'vote_reg',
    'bagging',
    'boosting',
    'stacking',
    'weighted_avg',
    'hard_vote',
    'soft_vote_alias',
    'bootstrap',
    'oob_score',
    'diversity',
    'blend',
]


def voting_classifier(
    predictions: List[List[int]],
    method: str = 'hard',
    weights: Optional[List[float]] = None
) -> List[int]:
    """
    Combine multiple classifier predictions using voting.
    
    Alias: vote_clf()
    
    Args:
        predictions: List of prediction arrays from different models
        method: 'hard' (majority vote) or 'soft' (average probabilities)
        weights: Optional weights for each model
    
    Returns:
        list: Combined predictions
    
    Examples:
        >>> from ilovetools.ml import vote_clf  # Short alias
        
        # Hard voting (majority)
        >>> model1_pred = [0, 1, 1, 0, 1]
        >>> model2_pred = [0, 1, 0, 0, 1]
        >>> model3_pred = [1, 1, 1, 0, 1]
        >>> predictions = [model1_pred, model2_pred, model3_pred]
        >>> result = vote_clf(predictions, method='hard')
        >>> print(result)
        [0, 1, 1, 0, 1]
        
        # Weighted voting
        >>> weights = [0.5, 0.3, 0.2]  # Trust model1 more
        >>> result = vote_clf(predictions, weights=weights)
        
        >>> from ilovetools.ml import voting_classifier  # Full name
        >>> result = voting_classifier(predictions, method='hard')
    
    Notes:
        - Hard voting: Majority class wins
        - Soft voting: Average probabilities (need predict_proba)
        - Weighted: Give more importance to better models
        - Odd number of models avoids ties
    """
    if not predictions:
        raise ValueError("predictions cannot be empty")
    
    n_samples = len(predictions[0])
    n_models = len(predictions)
    
    if weights is None:
        weights = [1.0] * n_models
    
    if len(weights) != n_models:
        raise ValueError("weights must match number of models")
    
    result = []
    
    for i in range(n_samples):
        votes = {}
        for model_idx, model_preds in enumerate(predictions):
            pred = model_preds[i]
            weight = weights[model_idx]
            votes[pred] = votes.get(pred, 0) + weight
        
        # Get class with highest weighted vote
        final_pred = max(votes.items(), key=lambda x: x[1])[0]
        result.append(final_pred)
    
    return result


# Create alias
vote_clf = voting_classifier


def voting_regressor(
    predictions: List[List[float]],
    method: str = 'mean',
    weights: Optional[List[float]] = None
) -> List[float]:
    """
    Combine multiple regressor predictions.
    
    Alias: vote_reg()
    
    Args:
        predictions: List of prediction arrays from different models
        method: 'mean', 'median', or 'weighted'
        weights: Optional weights for weighted average
    
    Returns:
        list: Combined predictions
    
    Examples:
        >>> from ilovetools.ml import vote_reg  # Short alias
        
        # Mean averaging
        >>> model1_pred = [100, 200, 300]
        >>> model2_pred = [110, 190, 310]
        >>> model3_pred = [105, 195, 305]
        >>> predictions = [model1_pred, model2_pred, model3_pred]
        >>> result = vote_reg(predictions, method='mean')
        >>> print(result)
        [105.0, 195.0, 305.0]
        
        # Weighted average
        >>> weights = [0.5, 0.3, 0.2]
        >>> result = vote_reg(predictions, method='weighted', weights=weights)
        
        # Median (robust to outliers)
        >>> result = vote_reg(predictions, method='median')
        
        >>> from ilovetools.ml import voting_regressor  # Full name
        >>> result = voting_regressor(predictions, method='mean')
    
    Notes:
        - Mean: Simple average
        - Median: Robust to outliers
        - Weighted: Trust better models more
        - Use median for noisy predictions
    """
    if not predictions:
        raise ValueError("predictions cannot be empty")
    
    n_samples = len(predictions[0])
    n_models = len(predictions)
    
    result = []
    
    for i in range(n_samples):
        values = [model_preds[i] for model_preds in predictions]
        
        if method == 'mean':
            combined = sum(values) / len(values)
        elif method == 'median':
            sorted_values = sorted(values)
            mid = len(sorted_values) // 2
            if len(sorted_values) % 2 == 0:
                combined = (sorted_values[mid-1] + sorted_values[mid]) / 2
            else:
                combined = sorted_values[mid]
        elif method == 'weighted':
            if weights is None:
                raise ValueError("weights required for weighted method")
            if len(weights) != n_models:
                raise ValueError("weights must match number of models")
            combined = sum(v * w for v, w in zip(values, weights)) / sum(weights)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        result.append(combined)
    
    return result


# Create alias
vote_reg = voting_regressor


def bagging_predictions(
    X: List,
    y: List,
    model_func: Callable,
    n_models: int = 10,
    sample_size: float = 1.0,
    random_state: Optional[int] = None
) -> Tuple[List[Any], List[List]]:
    """
    Bootstrap Aggregating (Bagging) ensemble.
    
    Alias: bagging()
    
    Train multiple models on bootstrap samples and average predictions.
    
    Args:
        X: Feature data
        y: Target data
        model_func: Function(X_train, y_train, X_test) -> predictions
        n_models: Number of models to train. Default: 10
        sample_size: Proportion of data for each bootstrap. Default: 1.0
        random_state: Random seed for reproducibility
    
    Returns:
        tuple: (final_predictions, all_model_predictions)
    
    Examples:
        >>> from ilovetools.ml import bagging  # Short alias
        
        >>> X = [[1], [2], [3], [4], [5]]
        >>> y = [1, 2, 3, 4, 5]
        >>> 
        >>> def simple_model(X_tr, y_tr, X_te):
        ...     avg = sum(y_tr) / len(y_tr)
        ...     return [avg] * len(X_te)
        >>> 
        >>> final_pred, all_preds = bagging(X, y, simple_model, n_models=5)
        >>> print(f"Trained {len(all_preds)} models")
        Trained 5 models
        
        >>> from ilovetools.ml import bagging_predictions  # Full name
        >>> final_pred, all_preds = bagging_predictions(X, y, simple_model)
    
    Notes:
        - Reduces variance (overfitting)
        - Each model sees different data
        - Random Forest uses bagging
        - More models = more stable
    """
    if random_state is not None:
        random.seed(random_state)
    
    n_samples = len(X)
    bootstrap_size = int(n_samples * sample_size)
    
    all_predictions = []
    
    for _ in range(n_models):
        # Bootstrap sample (with replacement)
        indices = [random.randint(0, n_samples - 1) for _ in range(bootstrap_size)]
        X_bootstrap = [X[i] for i in indices]
        y_bootstrap = [y[i] for i in indices]
        
        # Train model and predict on original data
        predictions = model_func(X_bootstrap, y_bootstrap, X)
        all_predictions.append(predictions)
    
    # Average predictions
    final_predictions = []
    for i in range(n_samples):
        avg = sum(preds[i] for preds in all_predictions) / n_models
        final_predictions.append(avg)
    
    return final_predictions, all_predictions


# Create alias
bagging = bagging_predictions


def boosting_sequential(
    X: List,
    y: List,
    model_func: Callable,
    n_models: int = 10,
    learning_rate: float = 0.1
) -> Tuple[List[float], List[List]]:
    """
    Sequential Boosting ensemble.
    
    Alias: boosting()
    
    Train models sequentially, each focusing on previous errors.
    
    Args:
        X: Feature data
        y: Target data
        model_func: Function(X_train, y_train, weights) -> predictions
        n_models: Number of models to train. Default: 10
        learning_rate: Shrinkage parameter. Default: 0.1
    
    Returns:
        tuple: (final_predictions, all_model_predictions)
    
    Examples:
        >>> from ilovetools.ml import boosting  # Short alias
        
        >>> X = [[1], [2], [3], [4], [5]]
        >>> y = [1.0, 2.0, 3.0, 4.0, 5.0]
        >>> 
        >>> def simple_model(X_tr, y_tr, weights):
        ...     # Weighted average
        ...     total_weight = sum(weights)
        ...     weighted_sum = sum(y * w for y, w in zip(y_tr, weights))
        ...     avg = weighted_sum / total_weight
        ...     return [avg] * len(X_tr)
        >>> 
        >>> final_pred, all_preds = boosting(X, y, simple_model, n_models=3)
        
        >>> from ilovetools.ml import boosting_sequential  # Full name
        >>> final_pred, all_preds = boosting_sequential(X, y, simple_model)
    
    Notes:
        - Reduces bias (underfitting)
        - Each model fixes previous errors
        - XGBoost, AdaBoost use boosting
        - Lower learning_rate = more models needed
    """
    n_samples = len(X)
    
    # Initialize weights uniformly
    weights = [1.0 / n_samples] * n_samples
    
    all_predictions = []
    final_predictions = [0.0] * n_samples
    
    for _ in range(n_models):
        # Train model with current weights
        predictions = model_func(X, y, weights)
        all_predictions.append(predictions)
        
        # Update final predictions
        for i in range(n_samples):
            final_predictions[i] += learning_rate * predictions[i]
        
        # Calculate errors
        errors = [abs(y[i] - final_predictions[i]) for i in range(n_samples)]
        
        # Update weights (focus on high error samples)
        total_error = sum(errors)
        if total_error > 0:
            weights = [e / total_error for e in errors]
        else:
            weights = [1.0 / n_samples] * n_samples
    
    return final_predictions, all_predictions


# Create alias
boosting = boosting_sequential


def stacking_ensemble(
    base_predictions: List[List],
    y_true: List,
    meta_model_func: Callable
) -> List:
    """
    Stacking ensemble with meta-model.
    
    Alias: stacking()
    
    Train meta-model to combine base model predictions.
    
    Args:
        base_predictions: List of prediction arrays from base models
        y_true: True target values
        meta_model_func: Function(X_meta, y_meta) -> meta_model
    
    Returns:
        list: Meta-model predictions
    
    Examples:
        >>> from ilovetools.ml import stacking  # Short alias
        
        >>> # Base model predictions
        >>> model1_pred = [1.0, 2.0, 3.0, 4.0, 5.0]
        >>> model2_pred = [1.1, 1.9, 3.1, 3.9, 5.1]
        >>> model3_pred = [0.9, 2.1, 2.9, 4.1, 4.9]
        >>> base_preds = [model1_pred, model2_pred, model3_pred]
        >>> y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        >>> 
        >>> def meta_model(X_meta, y_meta):
        ...     # Simple weighted average learner
        ...     def predict(X_test):
        ...         return [sum(x) / len(x) for x in X_test]
        ...     return predict
        >>> 
        >>> meta_preds = stacking(base_preds, y_true, meta_model)
        
        >>> from ilovetools.ml import stacking_ensemble  # Full name
        >>> meta_preds = stacking_ensemble(base_preds, y_true, meta_model)
    
    Notes:
        - Most powerful ensemble method
        - Meta-model learns optimal combination
        - Kaggle winners use stacking
        - Requires more data and compute
    """
    if not base_predictions:
        raise ValueError("base_predictions cannot be empty")
    
    n_samples = len(base_predictions[0])
    n_models = len(base_predictions)
    
    # Create meta-features (transpose predictions)
    X_meta = []
    for i in range(n_samples):
        meta_features = [base_preds[i] for base_preds in base_predictions]
        X_meta.append(meta_features)
    
    # Train meta-model
    meta_model = meta_model_func(X_meta, y_true)
    
    # Get meta-predictions
    meta_predictions = meta_model(X_meta)
    
    return meta_predictions


# Create alias
stacking = stacking_ensemble


def weighted_average_ensemble(
    predictions: List[List[float]],
    weights: List[float]
) -> List[float]:
    """
    Weighted average of predictions.
    
    Alias: weighted_avg()
    
    Args:
        predictions: List of prediction arrays
        weights: Weight for each model
    
    Returns:
        list: Weighted average predictions
    
    Examples:
        >>> from ilovetools.ml import weighted_avg  # Short alias
        
        >>> model1 = [100, 200, 300]
        >>> model2 = [110, 190, 310]
        >>> model3 = [105, 195, 305]
        >>> predictions = [model1, model2, model3]
        >>> weights = [0.5, 0.3, 0.2]  # Trust model1 most
        >>> result = weighted_avg(predictions, weights)
        >>> print(result)
        [105.0, 196.5, 304.5]
        
        >>> from ilovetools.ml import weighted_average_ensemble  # Full name
        >>> result = weighted_average_ensemble(predictions, weights)
    
    Notes:
        - Give more weight to better models
        - Weights should sum to 1.0
        - Use CV to find optimal weights
        - Simple but effective
    """
    if len(predictions) != len(weights):
        raise ValueError("predictions and weights must have same length")
    
    n_samples = len(predictions[0])
    result = []
    
    for i in range(n_samples):
        weighted_sum = sum(preds[i] * w for preds, w in zip(predictions, weights))
        result.append(weighted_sum)
    
    return result


# Create alias
weighted_avg = weighted_average_ensemble


def majority_vote(predictions: List[List[int]]) -> List[int]:
    """
    Hard voting (majority vote) for classification.
    
    Alias: hard_vote()
    
    Args:
        predictions: List of prediction arrays
    
    Returns:
        list: Majority vote predictions
    
    Examples:
        >>> from ilovetools.ml import hard_vote  # Short alias
        
        >>> model1 = [0, 1, 1, 0, 1]
        >>> model2 = [0, 1, 0, 0, 1]
        >>> model3 = [1, 1, 1, 0, 1]
        >>> predictions = [model1, model2, model3]
        >>> result = hard_vote(predictions)
        >>> print(result)
        [0, 1, 1, 0, 1]
        
        >>> from ilovetools.ml import majority_vote  # Full name
        >>> result = majority_vote(predictions)
    
    Notes:
        - Simple majority wins
        - Use odd number of models
        - Fast and interpretable
        - Good for balanced models
    """
    n_samples = len(predictions[0])
    result = []
    
    for i in range(n_samples):
        votes = [preds[i] for preds in predictions]
        # Count votes
        vote_counts = {}
        for vote in votes:
            vote_counts[vote] = vote_counts.get(vote, 0) + 1
        # Get majority
        majority = max(vote_counts.items(), key=lambda x: x[1])[0]
        result.append(majority)
    
    return result


# Create alias
hard_vote = majority_vote


def soft_vote(
    probabilities: List[List[List[float]]],
    weights: Optional[List[float]] = None
) -> List[int]:
    """
    Soft voting using predicted probabilities.
    
    Alias: soft_vote_alias()
    
    Args:
        probabilities: List of probability arrays [n_models][n_samples][n_classes]
        weights: Optional weights for each model
    
    Returns:
        list: Predicted classes based on averaged probabilities
    
    Examples:
        >>> from ilovetools.ml import soft_vote_alias  # Short alias
        
        # Binary classification probabilities
        >>> model1_proba = [[0.8, 0.2], [0.3, 0.7], [0.6, 0.4]]
        >>> model2_proba = [[0.7, 0.3], [0.4, 0.6], [0.5, 0.5]]
        >>> probabilities = [model1_proba, model2_proba]
        >>> result = soft_vote_alias(probabilities)
        >>> print(result)
        [0, 1, 0]
        
        >>> from ilovetools.ml import soft_vote  # Full name
        >>> result = soft_vote(probabilities)
    
    Notes:
        - Uses probability information
        - More nuanced than hard voting
        - Requires predict_proba
        - Better for uncertain predictions
    """
    n_models = len(probabilities)
    n_samples = len(probabilities[0])
    n_classes = len(probabilities[0][0])
    
    if weights is None:
        weights = [1.0] * n_models
    
    result = []
    
    for i in range(n_samples):
        # Average probabilities across models
        avg_proba = [0.0] * n_classes
        for model_idx, model_proba in enumerate(probabilities):
            for class_idx in range(n_classes):
                avg_proba[class_idx] += model_proba[i][class_idx] * weights[model_idx]
        
        # Normalize
        total = sum(avg_proba)
        avg_proba = [p / total for p in avg_proba]
        
        # Get class with highest probability
        predicted_class = avg_proba.index(max(avg_proba))
        result.append(predicted_class)
    
    return result


# Create alias
soft_vote_alias = soft_vote


def bootstrap_sample(
    X: List,
    y: List,
    sample_size: Optional[int] = None,
    random_state: Optional[int] = None
) -> Tuple[List, List, List[int]]:
    """
    Create bootstrap sample (sampling with replacement).
    
    Alias: bootstrap()
    
    Args:
        X: Feature data
        y: Target data
        sample_size: Size of bootstrap sample. Default: len(X)
        random_state: Random seed
    
    Returns:
        tuple: (X_bootstrap, y_bootstrap, indices)
    
    Examples:
        >>> from ilovetools.ml import bootstrap  # Short alias
        
        >>> X = [1, 2, 3, 4, 5]
        >>> y = [10, 20, 30, 40, 50]
        >>> X_boot, y_boot, indices = bootstrap(X, y, random_state=42)
        >>> print(f"Bootstrap size: {len(X_boot)}")
        Bootstrap size: 5
        >>> print(f"Unique samples: {len(set(indices))}")
        
        >>> from ilovetools.ml import bootstrap_sample  # Full name
        >>> X_boot, y_boot, indices = bootstrap_sample(X, y)
    
    Notes:
        - Sampling with replacement
        - Some samples appear multiple times
        - ~63% unique samples on average
        - Foundation of bagging
    """
    if random_state is not None:
        random.seed(random_state)
    
    n = len(X)
    if sample_size is None:
        sample_size = n
    
    indices = [random.randint(0, n - 1) for _ in range(sample_size)]
    X_bootstrap = [X[i] for i in indices]
    y_bootstrap = [y[i] for i in indices]
    
    return X_bootstrap, y_bootstrap, indices


# Create alias
bootstrap = bootstrap_sample


def out_of_bag_score(
    X: List,
    y: List,
    model_func: Callable,
    n_models: int = 10,
    random_state: Optional[int] = None
) -> float:
    """
    Calculate Out-of-Bag (OOB) score for bagging.
    
    Alias: oob_score()
    
    Args:
        X: Feature data
        y: Target data
        model_func: Function(X_train, y_train, X_test) -> predictions
        n_models: Number of bootstrap models. Default: 10
        random_state: Random seed
    
    Returns:
        float: OOB score (accuracy for classification)
    
    Examples:
        >>> from ilovetools.ml import oob_score  # Short alias
        
        >>> X = [[1], [2], [3], [4], [5]]
        >>> y = [1, 2, 3, 4, 5]
        >>> 
        >>> def model(X_tr, y_tr, X_te):
        ...     avg = sum(y_tr) / len(y_tr)
        ...     return [avg] * len(X_te)
        >>> 
        >>> score = oob_score(X, y, model, n_models=5, random_state=42)
        >>> print(f"OOB Score: {score:.2f}")
        
        >>> from ilovetools.ml import out_of_bag_score  # Full name
        >>> score = out_of_bag_score(X, y, model)
    
    Notes:
        - Free validation without separate test set
        - Uses samples not in bootstrap
        - ~37% samples are OOB per model
        - Good estimate of generalization
    """
    if random_state is not None:
        random.seed(random_state)
    
    n_samples = len(X)
    oob_predictions = [[] for _ in range(n_samples)]
    
    for _ in range(n_models):
        # Bootstrap sample
        indices = [random.randint(0, n_samples - 1) for _ in range(n_samples)]
        X_bootstrap = [X[i] for i in indices]
        y_bootstrap = [y[i] for i in indices]
        
        # Find OOB samples
        oob_indices = [i for i in range(n_samples) if i not in indices]
        
        if not oob_indices:
            continue
        
        X_oob = [X[i] for i in oob_indices]
        
        # Predict on OOB samples
        predictions = model_func(X_bootstrap, y_bootstrap, X_oob)
        
        # Store OOB predictions
        for idx, pred in zip(oob_indices, predictions):
            oob_predictions[idx].append(pred)
    
    # Calculate OOB score
    correct = 0
    total = 0
    
    for i, preds in enumerate(oob_predictions):
        if preds:  # Has OOB predictions
            avg_pred = sum(preds) / len(preds)
            if abs(avg_pred - y[i]) < 0.5:  # For classification
                correct += 1
            total += 1
    
    return correct / total if total > 0 else 0.0


# Create alias
oob_score = out_of_bag_score


def ensemble_diversity(
    predictions: List[List[int]]
) -> float:
    """
    Calculate diversity among ensemble models.
    
    Alias: diversity()
    
    Higher diversity = Better ensemble potential
    
    Args:
        predictions: List of prediction arrays
    
    Returns:
        float: Diversity score (0.0 to 1.0)
    
    Examples:
        >>> from ilovetools.ml import diversity  # Short alias
        
        # High diversity (different predictions)
        >>> model1 = [0, 1, 0, 1, 0]
        >>> model2 = [1, 0, 1, 0, 1]
        >>> model3 = [0, 0, 1, 1, 0]
        >>> predictions = [model1, model2, model3]
        >>> div = diversity(predictions)
        >>> print(f"Diversity: {div:.2%}")
        
        # Low diversity (similar predictions)
        >>> model1 = [0, 1, 0, 1, 0]
        >>> model2 = [0, 1, 0, 1, 0]
        >>> model3 = [0, 1, 0, 1, 1]
        >>> predictions = [model1, model2, model3]
        >>> div = diversity(predictions)
        
        >>> from ilovetools.ml import ensemble_diversity  # Full name
        >>> div = ensemble_diversity(predictions)
    
    Notes:
        - High diversity = Models make different errors
        - Low diversity = Models too similar
        - Aim for diverse but accurate models
        - Use different algorithms for diversity
    """
    n_models = len(predictions)
    n_samples = len(predictions[0])
    
    if n_models < 2:
        return 0.0
    
    # Calculate pairwise disagreement
    total_disagreement = 0
    pairs = 0
    
    for i in range(n_models):
        for j in range(i + 1, n_models):
            disagreement = sum(1 for k in range(n_samples) 
                             if predictions[i][k] != predictions[j][k])
            total_disagreement += disagreement / n_samples
            pairs += 1
    
    return total_disagreement / pairs if pairs > 0 else 0.0


# Create alias
diversity = ensemble_diversity


def blend_predictions(
    train_predictions: List[List],
    test_predictions: List[List],
    y_train: List,
    blend_func: Callable
) -> List:
    """
    Blend predictions using a blending function.
    
    Alias: blend()
    
    Args:
        train_predictions: Base model predictions on training set
        test_predictions: Base model predictions on test set
        y_train: Training labels
        blend_func: Function to learn blending weights
    
    Returns:
        list: Blended test predictions
    
    Examples:
        >>> from ilovetools.ml import blend  # Short alias
        
        >>> train_preds = [[1, 2, 3], [1.1, 1.9, 3.1]]
        >>> test_preds = [[4, 5], [3.9, 5.1]]
        >>> y_train = [1, 2, 3]
        >>> 
        >>> def simple_blend(train_p, y_tr):
        ...     # Learn to average
        ...     def predict(test_p):
        ...         return [sum(p)/len(p) for p in zip(*test_p)]
        ...     return predict
        >>> 
        >>> result = blend(train_preds, test_preds, y_train, simple_blend)
        
        >>> from ilovetools.ml import blend_predictions  # Full name
        >>> result = blend_predictions(train_preds, test_preds, y_train, simple_blend)
    
    Notes:
        - Similar to stacking but simpler
        - Uses holdout set for blending
        - Less prone to overfitting than stacking
        - Popular in Kaggle competitions
    """
    # Learn blending function on training predictions
    blender = blend_func(train_predictions, y_train)
    
    # Apply to test predictions
    blended_predictions = blender(test_predictions)
    
    return blended_predictions


# Create alias
blend = blend_predictions
