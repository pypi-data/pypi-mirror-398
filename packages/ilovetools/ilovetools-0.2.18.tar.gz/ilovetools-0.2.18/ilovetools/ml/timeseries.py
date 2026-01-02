"""
Time series analysis utilities
Each function has TWO names: full descriptive name + abbreviated alias
"""

from typing import List, Dict, Any, Tuple, Optional
import math

__all__ = [
    # Full names
    'moving_average',
    'exponential_moving_average',
    'weighted_moving_average',
    'seasonal_decompose',
    'difference_series',
    'autocorrelation',
    'partial_autocorrelation',
    'detect_trend',
    'detect_seasonality',
    'remove_trend',
    'remove_seasonality',
    'rolling_statistics',
    'lag_features',
    'time_series_split_cv',
    'forecast_accuracy',
    # Abbreviated aliases
    'ma',
    'ema',
    'wma',
    'decompose',
    'diff',
    'acf',
    'pacf',
    'trend',
    'seasonality',
    'detrend',
    'deseasonalize',
    'rolling_stats',
    'lag',
    'ts_cv',
    'forecast_acc',
]


def moving_average(
    series: List[float],
    window: int
) -> List[float]:
    """
    Simple Moving Average (SMA).
    
    Alias: ma()
    
    Args:
        series: Time series data
        window: Window size for averaging
    
    Returns:
        list: Moving averages
    
    Examples:
        >>> from ilovetools.ml import ma  # Short alias
        
        >>> series = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> result = ma(series, window=3)
        >>> print(len(result))
        8
        >>> print(result[0])
        2.0
        
        >>> from ilovetools.ml import moving_average  # Full name
        >>> result = moving_average(series, window=3)
    
    Notes:
        - Smooths noise
        - Reveals trends
        - Simple and effective
        - Lags behind actual data
    """
    if window <= 0 or window > len(series):
        raise ValueError("Window must be positive and <= series length")
    
    result = []
    for i in range(len(series) - window + 1):
        avg = sum(series[i:i + window]) / window
        result.append(avg)
    
    return result


# Create alias
ma = moving_average


def exponential_moving_average(
    series: List[float],
    alpha: float = 0.3
) -> List[float]:
    """
    Exponential Moving Average (EMA).
    
    Alias: ema()
    
    Args:
        series: Time series data
        alpha: Smoothing factor (0 < alpha <= 1)
    
    Returns:
        list: Exponential moving averages
    
    Examples:
        >>> from ilovetools.ml import ema  # Short alias
        
        >>> series = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> result = ema(series, alpha=0.3)
        >>> print(len(result))
        10
        >>> print(result[0])
        1.0
        
        >>> from ilovetools.ml import exponential_moving_average  # Full name
        >>> result = exponential_moving_average(series, alpha=0.3)
    
    Notes:
        - Recent data weighted more
        - Responds faster to changes
        - Less lag than SMA
        - Common in trading
    """
    if not 0 < alpha <= 1:
        raise ValueError("Alpha must be between 0 and 1")
    
    result = [series[0]]
    for i in range(1, len(series)):
        ema_val = alpha * series[i] + (1 - alpha) * result[-1]
        result.append(ema_val)
    
    return result


# Create alias
ema = exponential_moving_average


def weighted_moving_average(
    series: List[float],
    weights: List[float]
) -> List[float]:
    """
    Weighted Moving Average (WMA).
    
    Alias: wma()
    
    Args:
        series: Time series data
        weights: Weights for each position (must sum to 1)
    
    Returns:
        list: Weighted moving averages
    
    Examples:
        >>> from ilovetools.ml import wma  # Short alias
        
        >>> series = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> weights = [0.5, 0.3, 0.2]
        >>> result = wma(series, weights)
        >>> print(len(result))
        8
        
        >>> from ilovetools.ml import weighted_moving_average  # Full name
        >>> result = weighted_moving_average(series, weights)
    
    Notes:
        - Custom weights
        - Flexible averaging
        - Control importance
        - More complex than SMA
    """
    window = len(weights)
    if window > len(series):
        raise ValueError("Weights length must be <= series length")
    
    # Normalize weights
    total = sum(weights)
    if total == 0:
        raise ValueError("Weights must sum to non-zero")
    weights = [w / total for w in weights]
    
    result = []
    for i in range(len(series) - window + 1):
        wma_val = sum(series[i + j] * weights[j] for j in range(window))
        result.append(wma_val)
    
    return result


# Create alias
wma = weighted_moving_average


def seasonal_decompose(
    series: List[float],
    period: int,
    model: str = 'additive'
) -> Dict[str, List[float]]:
    """
    Seasonal decomposition of time series.
    
    Alias: decompose()
    
    Args:
        series: Time series data
        period: Seasonal period
        model: 'additive' or 'multiplicative'
    
    Returns:
        dict: Components (trend, seasonal, residual)
    
    Examples:
        >>> from ilovetools.ml import decompose  # Short alias
        
        >>> series = [10, 12, 13, 12, 10, 12, 13, 12, 10, 12, 13, 12]
        >>> result = decompose(series, period=3)
        >>> print('trend' in result)
        True
        >>> print('seasonal' in result)
        True
        
        >>> from ilovetools.ml import seasonal_decompose  # Full name
        >>> result = seasonal_decompose(series, period=3)
    
    Notes:
        - Separates components
        - Additive: Y = T + S + R
        - Multiplicative: Y = T * S * R
        - Essential for forecasting
    """
    if period <= 0 or period > len(series):
        raise ValueError("Period must be positive and <= series length")
    
    # Calculate trend using moving average
    trend = []
    half_window = period // 2
    
    for i in range(len(series)):
        if i < half_window or i >= len(series) - half_window:
            trend.append(None)
        else:
            start = i - half_window
            end = i + half_window + 1
            trend.append(sum(series[start:end]) / period)
    
    # Calculate seasonal component
    if model == 'additive':
        detrended = [series[i] - trend[i] if trend[i] is not None else None
                     for i in range(len(series))]
    else:  # multiplicative
        detrended = [series[i] / trend[i] if trend[i] is not None and trend[i] != 0 else None
                     for i in range(len(series))]
    
    # Average seasonal pattern
    seasonal_avg = [0.0] * period
    seasonal_count = [0] * period
    
    for i, val in enumerate(detrended):
        if val is not None:
            seasonal_avg[i % period] += val
            seasonal_count[i % period] += 1
    
    seasonal_avg = [seasonal_avg[i] / seasonal_count[i] if seasonal_count[i] > 0 else 0
                    for i in range(period)]
    
    # Normalize seasonal component
    if model == 'additive':
        seasonal_mean = sum(seasonal_avg) / period
        seasonal_avg = [s - seasonal_mean for s in seasonal_avg]
    else:
        seasonal_mean = sum(seasonal_avg) / period
        if seasonal_mean != 0:
            seasonal_avg = [s / seasonal_mean for s in seasonal_avg]
    
    # Extend seasonal pattern
    seasonal = [seasonal_avg[i % period] for i in range(len(series))]
    
    # Calculate residual
    if model == 'additive':
        residual = [series[i] - (trend[i] if trend[i] is not None else 0) - seasonal[i]
                   for i in range(len(series))]
    else:
        residual = [series[i] / ((trend[i] if trend[i] is not None else 1) * seasonal[i])
                   if seasonal[i] != 0 else 0
                   for i in range(len(series))]
    
    return {
        'trend': trend,
        'seasonal': seasonal,
        'residual': residual,
        'original': series,
    }


# Create alias
decompose = seasonal_decompose


def difference_series(
    series: List[float],
    lag: int = 1
) -> List[float]:
    """
    Difference time series for stationarity.
    
    Alias: diff()
    
    Args:
        series: Time series data
        lag: Lag for differencing
    
    Returns:
        list: Differenced series
    
    Examples:
        >>> from ilovetools.ml import diff  # Short alias
        
        >>> series = [1, 3, 6, 10, 15]
        >>> result = diff(series, lag=1)
        >>> print(result)
        [2, 3, 4, 5]
        
        >>> from ilovetools.ml import difference_series  # Full name
        >>> result = difference_series(series, lag=1)
    
    Notes:
        - Remove trend
        - Achieve stationarity
        - Required for ARIMA
        - Can apply multiple times
    """
    if lag <= 0 or lag >= len(series):
        raise ValueError("Lag must be positive and < series length")
    
    return [series[i] - series[i - lag] for i in range(lag, len(series))]


# Create alias
diff = difference_series


def autocorrelation(
    series: List[float],
    max_lag: int = 10
) -> List[float]:
    """
    Calculate autocorrelation function (ACF).
    
    Alias: acf()
    
    Args:
        series: Time series data
        max_lag: Maximum lag to calculate
    
    Returns:
        list: ACF values for each lag
    
    Examples:
        >>> from ilovetools.ml import acf  # Short alias
        
        >>> series = [1, 2, 3, 4, 5, 4, 3, 2, 1]
        >>> result = acf(series, max_lag=3)
        >>> print(len(result))
        4
        >>> print(result[0])
        1.0
        
        >>> from ilovetools.ml import autocorrelation  # Full name
        >>> result = autocorrelation(series, max_lag=3)
    
    Notes:
        - Correlation with past
        - Identifies patterns
        - Determines lag order
        - Essential for ARIMA
    """
    n = len(series)
    mean = sum(series) / n
    
    # Variance
    c0 = sum((x - mean) ** 2 for x in series) / n
    
    if c0 == 0:
        return [1.0] + [0.0] * max_lag
    
    acf_values = [1.0]  # ACF at lag 0 is always 1
    
    for lag in range(1, max_lag + 1):
        if lag >= n:
            acf_values.append(0.0)
            continue
        
        c_lag = sum((series[i] - mean) * (series[i - lag] - mean)
                   for i in range(lag, n)) / n
        acf_values.append(c_lag / c0)
    
    return acf_values


# Create alias
acf = autocorrelation


def partial_autocorrelation(
    series: List[float],
    max_lag: int = 10
) -> List[float]:
    """
    Calculate partial autocorrelation function (PACF).
    
    Alias: pacf()
    
    Args:
        series: Time series data
        max_lag: Maximum lag to calculate
    
    Returns:
        list: PACF values for each lag
    
    Examples:
        >>> from ilovetools.ml import pacf  # Short alias
        
        >>> series = [1, 2, 3, 4, 5, 4, 3, 2, 1]
        >>> result = pacf(series, max_lag=3)
        >>> print(len(result))
        4
        
        >>> from ilovetools.ml import partial_autocorrelation  # Full name
        >>> result = partial_autocorrelation(series, max_lag=3)
    
    Notes:
        - Direct correlation
        - Removes indirect effects
        - Determines AR order
        - Complements ACF
    """
    acf_values = autocorrelation(series, max_lag)
    pacf_values = [1.0]  # PACF at lag 0 is always 1
    
    if max_lag == 0:
        return pacf_values
    
    # Durbin-Levinson algorithm (simplified)
    for k in range(1, max_lag + 1):
        if k >= len(acf_values):
            pacf_values.append(0.0)
            continue
        
        # Simplified PACF calculation
        numerator = acf_values[k]
        denominator = 1.0
        
        for j in range(1, k):
            if j < len(pacf_values):
                numerator -= pacf_values[j] * acf_values[k - j]
        
        if denominator != 0:
            pacf_values.append(numerator / denominator)
        else:
            pacf_values.append(0.0)
    
    return pacf_values


# Create alias
pacf = partial_autocorrelation


def detect_trend(
    series: List[float],
    window: int = 5
) -> Dict[str, Any]:
    """
    Detect trend in time series.
    
    Alias: trend()
    
    Args:
        series: Time series data
        window: Window for trend calculation
    
    Returns:
        dict: Trend information
    
    Examples:
        >>> from ilovetools.ml import trend  # Short alias
        
        >>> series = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> result = trend(series, window=3)
        >>> print(result['direction'])
        'upward'
        
        >>> from ilovetools.ml import detect_trend  # Full name
        >>> result = detect_trend(series, window=3)
    
    Notes:
        - Identify direction
        - Upward, downward, flat
        - Uses moving average
        - Essential for forecasting
    """
    if window > len(series):
        window = len(series)
    
    # Calculate moving average
    ma_values = moving_average(series, window)
    
    # Calculate trend slope
    if len(ma_values) < 2:
        return {
            'direction': 'flat',
            'slope': 0.0,
            'strength': 0.0,
        }
    
    # Simple linear trend
    n = len(ma_values)
    x_mean = (n - 1) / 2
    y_mean = sum(ma_values) / n
    
    numerator = sum((i - x_mean) * (ma_values[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    
    slope = numerator / denominator if denominator != 0 else 0
    
    # Determine direction
    if abs(slope) < 0.01:
        direction = 'flat'
    elif slope > 0:
        direction = 'upward'
    else:
        direction = 'downward'
    
    # Calculate strength (R-squared)
    predictions = [y_mean + slope * (i - x_mean) for i in range(n)]
    ss_res = sum((ma_values[i] - predictions[i]) ** 2 for i in range(n))
    ss_tot = sum((ma_values[i] - y_mean) ** 2 for i in range(n))
    
    strength = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    return {
        'direction': direction,
        'slope': slope,
        'strength': max(0, min(1, strength)),
    }


# Create alias
trend = detect_trend


def detect_seasonality(
    series: List[float],
    max_period: int = 12
) -> Dict[str, Any]:
    """
    Detect seasonality in time series.
    
    Alias: seasonality()
    
    Args:
        series: Time series data
        max_period: Maximum period to check
    
    Returns:
        dict: Seasonality information
    
    Examples:
        >>> from ilovetools.ml import seasonality  # Short alias
        
        >>> series = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2]
        >>> result = seasonality(series, max_period=5)
        >>> print(result['has_seasonality'])
        True
        
        >>> from ilovetools.ml import detect_seasonality  # Full name
        >>> result = detect_seasonality(series, max_period=5)
    
    Notes:
        - Identify repeating patterns
        - Find period length
        - Measure strength
        - Essential for decomposition
    """
    if max_period > len(series) // 2:
        max_period = len(series) // 2
    
    if max_period < 2:
        return {
            'has_seasonality': False,
            'period': None,
            'strength': 0.0,
        }
    
    # Calculate ACF
    acf_values = autocorrelation(series, max_period)
    
    # Find peaks in ACF (excluding lag 0)
    best_period = None
    best_strength = 0.0
    
    for period in range(2, max_period + 1):
        if period < len(acf_values):
            strength = abs(acf_values[period])
            if strength > best_strength and strength > 0.3:
                best_strength = strength
                best_period = period
    
    has_seasonality = best_period is not None
    
    return {
        'has_seasonality': has_seasonality,
        'period': best_period,
        'strength': best_strength,
    }


# Create alias
seasonality = detect_seasonality


def remove_trend(
    series: List[float],
    method: str = 'difference'
) -> List[float]:
    """
    Remove trend from time series.
    
    Alias: detrend()
    
    Args:
        series: Time series data
        method: 'difference' or 'linear'
    
    Returns:
        list: Detrended series
    
    Examples:
        >>> from ilovetools.ml import detrend  # Short alias
        
        >>> series = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> result = detrend(series, method='difference')
        >>> print(len(result))
        9
        
        >>> from ilovetools.ml import remove_trend  # Full name
        >>> result = remove_trend(series, method='difference')
    
    Notes:
        - Achieve stationarity
        - Difference or linear
        - Required for modeling
        - Reversible operation
    """
    if method == 'difference':
        return difference_series(series, lag=1)
    elif method == 'linear':
        # Remove linear trend
        n = len(series)
        x_mean = (n - 1) / 2
        y_mean = sum(series) / n
        
        numerator = sum((i - x_mean) * (series[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        
        return [series[i] - (slope * i + intercept) for i in range(n)]
    else:
        raise ValueError("Method must be 'difference' or 'linear'")


# Create alias
detrend = remove_trend


def remove_seasonality(
    series: List[float],
    period: int
) -> List[float]:
    """
    Remove seasonality from time series.
    
    Alias: deseasonalize()
    
    Args:
        series: Time series data
        period: Seasonal period
    
    Returns:
        list: Deseasonalized series
    
    Examples:
        >>> from ilovetools.ml import deseasonalize  # Short alias
        
        >>> series = [10, 12, 13, 12, 10, 12, 13, 12]
        >>> result = deseasonalize(series, period=4)
        >>> print(len(result))
        8
        
        >>> from ilovetools.ml import remove_seasonality  # Full name
        >>> result = remove_seasonality(series, period=4)
    
    Notes:
        - Remove repeating patterns
        - Achieve stationarity
        - Use decomposition
        - Reversible operation
    """
    decomp = seasonal_decompose(series, period, model='additive')
    seasonal = decomp['seasonal']
    
    return [series[i] - seasonal[i] for i in range(len(series))]


# Create alias
deseasonalize = remove_seasonality


def rolling_statistics(
    series: List[float],
    window: int
) -> Dict[str, List[float]]:
    """
    Calculate rolling statistics.
    
    Alias: rolling_stats()
    
    Args:
        series: Time series data
        window: Window size
    
    Returns:
        dict: Rolling mean, std, min, max
    
    Examples:
        >>> from ilovetools.ml import rolling_stats  # Short alias
        
        >>> series = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> result = rolling_stats(series, window=3)
        >>> print('mean' in result)
        True
        >>> print('std' in result)
        True
        
        >>> from ilovetools.ml import rolling_statistics  # Full name
        >>> result = rolling_statistics(series, window=3)
    
    Notes:
        - Window-based calculations
        - Track changes over time
        - Feature engineering
        - Anomaly detection
    """
    if window <= 0 or window > len(series):
        raise ValueError("Window must be positive and <= series length")
    
    rolling_mean = []
    rolling_std = []
    rolling_min = []
    rolling_max = []
    
    for i in range(len(series) - window + 1):
        window_data = series[i:i + window]
        
        # Mean
        mean = sum(window_data) / window
        rolling_mean.append(mean)
        
        # Std
        variance = sum((x - mean) ** 2 for x in window_data) / window
        rolling_std.append(math.sqrt(variance))
        
        # Min and Max
        rolling_min.append(min(window_data))
        rolling_max.append(max(window_data))
    
    return {
        'mean': rolling_mean,
        'std': rolling_std,
        'min': rolling_min,
        'max': rolling_max,
    }


# Create alias
rolling_stats = rolling_statistics


def lag_features(
    series: List[float],
    lags: List[int]
) -> List[List[Optional[float]]]:
    """
    Create lag features for time series.
    
    Alias: lag()
    
    Args:
        series: Time series data
        lags: List of lag values
    
    Returns:
        list: Lag features matrix
    
    Examples:
        >>> from ilovetools.ml import lag  # Short alias
        
        >>> series = [1, 2, 3, 4, 5]
        >>> result = lag(series, lags=[1, 2])
        >>> print(len(result))
        5
        >>> print(len(result[0]))
        2
        
        >>> from ilovetools.ml import lag_features  # Full name
        >>> result = lag_features(series, lags=[1, 2])
    
    Notes:
        - Use past values as features
        - Essential for ML models
        - t-1, t-2, t-7 common
        - Handle missing values
    """
    n = len(series)
    max_lag = max(lags)
    
    features = []
    for i in range(n):
        row = []
        for lag in lags:
            if i >= lag:
                row.append(series[i - lag])
            else:
                row.append(None)
        features.append(row)
    
    return features


# Create alias
lag = lag_features


def time_series_split_cv(
    series: List[float],
    n_splits: int = 5,
    test_size: Optional[int] = None
) -> List[Dict[str, List[int]]]:
    """
    Time series cross-validation splits.
    
    Alias: ts_cv()
    
    Args:
        series: Time series data
        n_splits: Number of splits
        test_size: Size of test set (optional)
    
    Returns:
        list: Train/test indices for each split
    
    Examples:
        >>> from ilovetools.ml import ts_cv  # Short alias
        
        >>> series = list(range(20))
        >>> splits = ts_cv(series, n_splits=3)
        >>> print(len(splits))
        3
        >>> print('train' in splits[0])
        True
        
        >>> from ilovetools.ml import time_series_split_cv  # Full name
        >>> splits = time_series_split_cv(series, n_splits=3)
    
    Notes:
        - No data leakage
        - Expanding window
        - Respects time order
        - Essential for validation
    """
    n = len(series)
    
    if test_size is None:
        test_size = n // (n_splits + 1)
    
    if test_size <= 0 or test_size * n_splits >= n:
        raise ValueError("Invalid test_size for given n_splits")
    
    splits = []
    for i in range(n_splits):
        test_start = n - (n_splits - i) * test_size
        test_end = test_start + test_size
        
        train_indices = list(range(test_start))
        test_indices = list(range(test_start, test_end))
        
        splits.append({
            'train': train_indices,
            'test': test_indices,
        })
    
    return splits


# Create alias
ts_cv = time_series_split_cv


def forecast_accuracy(
    actual: List[float],
    predicted: List[float]
) -> Dict[str, float]:
    """
    Calculate forecast accuracy metrics.
    
    Alias: forecast_acc()
    
    Args:
        actual: Actual values
        predicted: Predicted values
    
    Returns:
        dict: MAE, RMSE, MAPE metrics
    
    Examples:
        >>> from ilovetools.ml import forecast_acc  # Short alias
        
        >>> actual = [10, 20, 30, 40, 50]
        >>> predicted = [12, 19, 31, 39, 51]
        >>> result = forecast_acc(actual, predicted)
        >>> print('mae' in result)
        True
        >>> print('rmse' in result)
        True
        
        >>> from ilovetools.ml import forecast_accuracy  # Full name
        >>> result = forecast_accuracy(actual, predicted)
    
    Notes:
        - MAE: Mean Absolute Error
        - RMSE: Root Mean Squared Error
        - MAPE: Mean Absolute Percentage Error
        - Lower is better
    """
    if len(actual) != len(predicted):
        raise ValueError("Actual and predicted must have same length")
    
    n = len(actual)
    
    # MAE
    mae = sum(abs(actual[i] - predicted[i]) for i in range(n)) / n
    
    # RMSE
    mse = sum((actual[i] - predicted[i]) ** 2 for i in range(n)) / n
    rmse = math.sqrt(mse)
    
    # MAPE
    mape_sum = 0
    mape_count = 0
    for i in range(n):
        if actual[i] != 0:
            mape_sum += abs((actual[i] - predicted[i]) / actual[i])
            mape_count += 1
    
    mape = (mape_sum / mape_count * 100) if mape_count > 0 else 0
    
    return {
        'mae': mae,
        'rmse': rmse,
        'mape': mape,
    }


# Create alias
forecast_acc = forecast_accuracy
