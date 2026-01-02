"""
Model evaluation metrics for ML workflows
"""

from typing import List, Tuple, Dict, Union, Optional
import numpy as np

__all__ = [
    'accuracy_score',
    'precision_score',
    'recall_score',
    'f1_score',
    'confusion_matrix',
    'classification_report',
    'mean_squared_error',
    'mean_absolute_error',
    'root_mean_squared_error',
    'r2_score',
    'roc_auc_score',
    # Aliases
    'mse',
    'mae',
    'rmse',
]


def accuracy_score(y_true: List, y_pred: List) -> float:
    """
    Calculate accuracy score for classification.
    
    Accuracy = (Correct Predictions) / (Total Predictions)
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
    
    Returns:
        float: Accuracy score (0.0 to 1.0)
    
    Examples:
        >>> from ilovetools.ml import accuracy_score
        
        # Perfect predictions
        >>> y_true = [1, 0, 1, 1, 0]
        >>> y_pred = [1, 0, 1, 1, 0]
        >>> accuracy_score(y_true, y_pred)
        1.0
        
        # 80% accuracy
        >>> y_true = [1, 0, 1, 1, 0]
        >>> y_pred = [1, 0, 1, 0, 0]
        >>> accuracy_score(y_true, y_pred)
        0.8
        
        # Real-world: Email spam detection
        >>> actual = [1, 1, 0, 0, 1, 0, 1, 0]
        >>> predicted = [1, 0, 0, 0, 1, 0, 1, 1]
        >>> acc = accuracy_score(actual, predicted)
        >>> print(f"Model accuracy: {acc:.2%}")
        Model accuracy: 75.00%
    
    Notes:
        - Use for balanced datasets
        - Don't use for imbalanced datasets
        - Range: 0.0 (worst) to 1.0 (best)
        - Simple and intuitive metric
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have same length")
    
    correct = sum(1 for true, pred in zip(y_true, y_pred) if true == pred)
    return correct / len(y_true)


def precision_score(y_true: List, y_pred: List, positive_label: int = 1) -> float:
    """
    Calculate precision score for binary classification.
    
    Precision = TP / (TP + FP)
    "Of all positive predictions, how many were correct?"
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        positive_label: Label considered as positive class. Default: 1
    
    Returns:
        float: Precision score (0.0 to 1.0)
    
    Examples:
        >>> from ilovetools.ml import precision_score
        
        # High precision (few false positives)
        >>> y_true = [1, 0, 1, 1, 0, 0, 1, 0]
        >>> y_pred = [1, 0, 1, 1, 0, 0, 0, 0]
        >>> precision_score(y_true, y_pred)
        1.0
        
        # Lower precision (some false positives)
        >>> y_true = [1, 0, 1, 1, 0]
        >>> y_pred = [1, 1, 1, 1, 0]
        >>> precision_score(y_true, y_pred)
        0.75
        
        # Spam detection (don't mark important emails as spam)
        >>> actual_spam = [1, 1, 0, 0, 1, 0, 1, 0]
        >>> predicted_spam = [1, 1, 1, 0, 1, 0, 1, 0]
        >>> prec = precision_score(actual_spam, predicted_spam)
        >>> print(f"Precision: {prec:.2%}")
        Precision: 80.00%
    
    Notes:
        - Use when false positives are costly
        - High precision = Few false alarms
        - Example: Spam detection, fraud detection
        - Returns 0.0 if no positive predictions
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have same length")
    
    tp = sum(1 for true, pred in zip(y_true, y_pred) 
             if true == positive_label and pred == positive_label)
    fp = sum(1 for true, pred in zip(y_true, y_pred) 
             if true != positive_label and pred == positive_label)
    
    if tp + fp == 0:
        return 0.0
    
    return tp / (tp + fp)


def recall_score(y_true: List, y_pred: List, positive_label: int = 1) -> float:
    """
    Calculate recall score (sensitivity) for binary classification.
    
    Recall = TP / (TP + FN)
    "Of all actual positives, how many did we catch?"
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        positive_label: Label considered as positive class. Default: 1
    
    Returns:
        float: Recall score (0.0 to 1.0)
    
    Examples:
        >>> from ilovetools.ml import recall_score
        
        # High recall (caught most positives)
        >>> y_true = [1, 0, 1, 1, 0, 0, 1, 0]
        >>> y_pred = [1, 1, 1, 1, 0, 0, 1, 0]
        >>> recall_score(y_true, y_pred)
        1.0
        
        # Lower recall (missed some positives)
        >>> y_true = [1, 0, 1, 1, 0]
        >>> y_pred = [1, 0, 0, 1, 0]
        >>> recall_score(y_true, y_pred)
        0.6666666666666666
        
        # Cancer detection (don't miss any cases)
        >>> actual_cancer = [1, 1, 0, 0, 1, 0, 1, 0]
        >>> predicted_cancer = [1, 1, 0, 1, 1, 0, 0, 0]
        >>> rec = recall_score(actual_cancer, predicted_cancer)
        >>> print(f"Recall: {rec:.2%}")
        Recall: 75.00%
    
    Notes:
        - Use when false negatives are costly
        - High recall = Few missed cases
        - Example: Disease detection, fraud detection
        - Returns 0.0 if no actual positives
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have same length")
    
    tp = sum(1 for true, pred in zip(y_true, y_pred) 
             if true == positive_label and pred == positive_label)
    fn = sum(1 for true, pred in zip(y_true, y_pred) 
             if true == positive_label and pred != positive_label)
    
    if tp + fn == 0:
        return 0.0
    
    return tp / (tp + fn)


def f1_score(y_true: List, y_pred: List, positive_label: int = 1) -> float:
    """
    Calculate F1 score (harmonic mean of precision and recall).
    
    F1 = 2 * (Precision * Recall) / (Precision + Recall)
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        positive_label: Label considered as positive class. Default: 1
    
    Returns:
        float: F1 score (0.0 to 1.0)
    
    Examples:
        >>> from ilovetools.ml import f1_score
        
        # Balanced precision and recall
        >>> y_true = [1, 0, 1, 1, 0, 0, 1, 0]
        >>> y_pred = [1, 0, 1, 1, 0, 0, 1, 1]
        >>> f1_score(y_true, y_pred)
        0.8888888888888888
        
        # Imbalanced dataset
        >>> y_true = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        >>> y_pred = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        >>> f1 = f1_score(y_true, y_pred)
        >>> print(f"F1 Score: {f1:.2%}")
        F1 Score: 100.00%
    
    Notes:
        - Best metric for imbalanced datasets
        - Balances precision and recall
        - Range: 0.0 (worst) to 1.0 (best)
        - Use when both false positives and negatives matter
    """
    precision = precision_score(y_true, y_pred, positive_label)
    recall = recall_score(y_true, y_pred, positive_label)
    
    if precision + recall == 0:
        return 0.0
    
    return 2 * (precision * recall) / (precision + recall)


def confusion_matrix(y_true: List, y_pred: List) -> List[List[int]]:
    """
    Calculate confusion matrix for binary classification.
    
    Returns 2x2 matrix:
    [[TN, FP],
     [FN, TP]]
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
    
    Returns:
        list: 2x2 confusion matrix
    
    Examples:
        >>> from ilovetools.ml import confusion_matrix
        
        # Perfect predictions
        >>> y_true = [1, 0, 1, 1, 0]
        >>> y_pred = [1, 0, 1, 1, 0]
        >>> cm = confusion_matrix(y_true, y_pred)
        >>> print(cm)
        [[2, 0], [0, 3]]
        
        # With errors
        >>> y_true = [1, 0, 1, 1, 0, 0, 1, 0]
        >>> y_pred = [1, 0, 1, 0, 0, 1, 1, 0]
        >>> cm = confusion_matrix(y_true, y_pred)
        >>> print(cm)
        [[3, 1], [1, 3]]
        
        # Interpret results
        >>> tn, fp, fn, tp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]
        >>> print(f"True Negatives: {tn}")
        >>> print(f"False Positives: {fp}")
        >>> print(f"False Negatives: {fn}")
        >>> print(f"True Positives: {tp}")
    
    Notes:
        - Foundation of classification metrics
        - Shows all types of errors
        - Format: [[TN, FP], [FN, TP]]
        - Use to understand model behavior
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have same length")
    
    tn = sum(1 for true, pred in zip(y_true, y_pred) if true == 0 and pred == 0)
    fp = sum(1 for true, pred in zip(y_true, y_pred) if true == 0 and pred == 1)
    fn = sum(1 for true, pred in zip(y_true, y_pred) if true == 1 and pred == 0)
    tp = sum(1 for true, pred in zip(y_true, y_pred) if true == 1 and pred == 1)
    
    return [[tn, fp], [fn, tp]]


def classification_report(y_true: List, y_pred: List) -> Dict[str, float]:
    """
    Generate comprehensive classification report.
    
    Returns accuracy, precision, recall, and F1 score.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
    
    Returns:
        dict: Dictionary with all metrics
    
    Examples:
        >>> from ilovetools.ml import classification_report
        
        >>> y_true = [1, 0, 1, 1, 0, 0, 1, 0]
        >>> y_pred = [1, 0, 1, 0, 0, 1, 1, 0]
        >>> report = classification_report(y_true, y_pred)
        >>> print(report)
        {'accuracy': 0.75, 'precision': 0.75, 'recall': 0.75, 'f1_score': 0.75}
        
        # Pretty print
        >>> for metric, value in report.items():
        ...     print(f"{metric}: {value:.2%}")
        accuracy: 75.00%
        precision: 75.00%
        recall: 75.00%
        f1_score: 75.00%
    
    Notes:
        - Comprehensive overview of model performance
        - All metrics in one call
        - Easy to compare models
        - Returns dictionary for flexibility
    """
    return {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred),
        'recall': recall_score(y_true, y_pred),
        'f1_score': f1_score(y_true, y_pred)
    }


def mean_squared_error(y_true: List[float], y_pred: List[float]) -> float:
    """
    Calculate Mean Squared Error for regression.
    
    Alias: mse()
    
    MSE = Average of (actual - predicted)^2
    
    Args:
        y_true: True values
        y_pred: Predicted values
    
    Returns:
        float: MSE value
    
    Examples:
        >>> from ilovetools.ml import mse  # Short alias
        
        # Perfect predictions
        >>> y_true = [1.0, 2.0, 3.0, 4.0]
        >>> y_pred = [1.0, 2.0, 3.0, 4.0]
        >>> mse(y_true, y_pred)
        0.0
        
        # With errors
        >>> y_true = [100, 200, 300, 400]
        >>> y_pred = [110, 190, 310, 390]
        >>> error = mse(y_true, y_pred)
        >>> print(f"MSE: {error:.2f}")
        MSE: 100.00
        
        >>> from ilovetools.ml import mean_squared_error  # Full name
        >>> error = mean_squared_error(y_true, y_pred)
    
    Notes:
        - Penalizes large errors heavily
        - Not in original units (squared)
        - Sensitive to outliers
        - Lower is better
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have same length")
    
    squared_errors = [(true - pred) ** 2 for true, pred in zip(y_true, y_pred)]
    return sum(squared_errors) / len(squared_errors)


# Create alias
mse = mean_squared_error


def mean_absolute_error(y_true: List[float], y_pred: List[float]) -> float:
    """
    Calculate Mean Absolute Error for regression.
    
    Alias: mae()
    
    MAE = Average of |actual - predicted|
    
    Args:
        y_true: True values
        y_pred: Predicted values
    
    Returns:
        float: MAE value
    
    Examples:
        >>> from ilovetools.ml import mae  # Short alias
        
        # Perfect predictions
        >>> y_true = [1.0, 2.0, 3.0, 4.0]
        >>> y_pred = [1.0, 2.0, 3.0, 4.0]
        >>> mae(y_true, y_pred)
        0.0
        
        # With errors
        >>> y_true = [100, 200, 300, 400]
        >>> y_pred = [110, 190, 310, 390]
        >>> error = mae(y_true, y_pred)
        >>> print(f"MAE: ${error:.2f}")
        MAE: $10.00
        
        >>> from ilovetools.ml import mean_absolute_error  # Full name
        >>> error = mean_absolute_error(y_true, y_pred)
    
    Notes:
        - Easy to interpret
        - Same units as target variable
        - Less sensitive to outliers than MSE
        - Lower is better
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have same length")
    
    absolute_errors = [abs(true - pred) for true, pred in zip(y_true, y_pred)]
    return sum(absolute_errors) / len(absolute_errors)


# Create alias
mae = mean_absolute_error


def root_mean_squared_error(y_true: List[float], y_pred: List[float]) -> float:
    """
    Calculate Root Mean Squared Error for regression.
    
    Alias: rmse()
    
    RMSE = sqrt(MSE)
    
    Args:
        y_true: True values
        y_pred: Predicted values
    
    Returns:
        float: RMSE value
    
    Examples:
        >>> from ilovetools.ml import rmse  # Short alias
        
        # Perfect predictions
        >>> y_true = [1.0, 2.0, 3.0, 4.0]
        >>> y_pred = [1.0, 2.0, 3.0, 4.0]
        >>> rmse(y_true, y_pred)
        0.0
        
        # With errors
        >>> y_true = [100, 200, 300, 400]
        >>> y_pred = [110, 190, 310, 390]
        >>> error = rmse(y_true, y_pred)
        >>> print(f"RMSE: {error:.2f}")
        RMSE: 10.00
        
        >>> from ilovetools.ml import root_mean_squared_error  # Full name
        >>> error = root_mean_squared_error(y_true, y_pred)
    
    Notes:
        - Most common regression metric
        - Same units as target variable
        - Penalizes large errors
        - Lower is better
    """
    mse_value = mean_squared_error(y_true, y_pred)
    return mse_value ** 0.5


# Create alias
rmse = root_mean_squared_error


def r2_score(y_true: List[float], y_pred: List[float]) -> float:
    """
    Calculate R-squared (coefficient of determination) for regression.
    
    R² = 1 - (SS_res / SS_tot)
    Proportion of variance explained by the model.
    
    Args:
        y_true: True values
        y_pred: Predicted values
    
    Returns:
        float: R² value (-inf to 1.0, higher is better)
    
    Examples:
        >>> from ilovetools.ml import r2_score
        
        # Perfect predictions
        >>> y_true = [1.0, 2.0, 3.0, 4.0]
        >>> y_pred = [1.0, 2.0, 3.0, 4.0]
        >>> r2_score(y_true, y_pred)
        1.0
        
        # Good predictions
        >>> y_true = [100, 200, 300, 400, 500]
        >>> y_pred = [110, 190, 310, 390, 510]
        >>> r2 = r2_score(y_true, y_pred)
        >>> print(f"R²: {r2:.2%}")
        R²: 99.00%
        
        # Interpretation
        >>> r2 = 0.85
        >>> print(f"Model explains {r2:.0%} of variance")
        Model explains 85% of variance
    
    Notes:
        - Range: -inf to 1.0 (1.0 is perfect)
        - 0.0 = Model as good as mean baseline
        - Negative = Model worse than mean
        - Easy to interpret as percentage
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have same length")
    
    mean_true = sum(y_true) / len(y_true)
    
    ss_tot = sum((true - mean_true) ** 2 for true in y_true)
    ss_res = sum((true - pred) ** 2 for true, pred in zip(y_true, y_pred))
    
    if ss_tot == 0:
        return 0.0
    
    return 1 - (ss_res / ss_tot)


def roc_auc_score(y_true: List[int], y_scores: List[float]) -> float:
    """
    Calculate ROC AUC score for binary classification.
    
    AUC = Area Under the ROC Curve
    Measures model's ability to distinguish between classes.
    
    Args:
        y_true: True binary labels (0 or 1)
        y_scores: Predicted probabilities or scores
    
    Returns:
        float: AUC score (0.0 to 1.0)
    
    Examples:
        >>> from ilovetools.ml import roc_auc_score
        
        # Perfect separation
        >>> y_true = [0, 0, 1, 1]
        >>> y_scores = [0.1, 0.2, 0.8, 0.9]
        >>> roc_auc_score(y_true, y_scores)
        1.0
        
        # Good separation
        >>> y_true = [0, 0, 1, 1, 0, 1]
        >>> y_scores = [0.2, 0.3, 0.7, 0.8, 0.4, 0.9]
        >>> auc = roc_auc_score(y_true, y_scores)
        >>> print(f"AUC: {auc:.2%}")
        AUC: 91.67%
    
    Notes:
        - 1.0 = Perfect classifier
        - 0.5 = Random guessing
        - < 0.5 = Worse than random
        - Threshold-independent metric
    """
    if len(y_true) != len(y_scores):
        raise ValueError("y_true and y_scores must have same length")
    
    # Sort by scores
    pairs = sorted(zip(y_scores, y_true), reverse=True)
    
    # Count positive and negative samples
    n_pos = sum(y_true)
    n_neg = len(y_true) - n_pos
    
    if n_pos == 0 or n_neg == 0:
        return 0.5
    
    # Calculate AUC using trapezoidal rule
    tp = 0
    fp = 0
    auc = 0.0
    prev_score = None
    
    for score, label in pairs:
        if label == 1:
            tp += 1
        else:
            fp += 1
            auc += tp
    
    return auc / (n_pos * n_neg)
