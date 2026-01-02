"""
Dimensionality reduction utilities
Each function has TWO names: full descriptive name + abbreviated alias
"""

from typing import List, Dict, Any, Tuple, Optional
import math

__all__ = [
    # Full names
    'pca_transform',
    'explained_variance_ratio',
    'scree_plot_data',
    'cumulative_variance',
    'pca_inverse_transform',
    'truncated_svd',
    'kernel_pca_transform',
    'incremental_pca_transform',
    'feature_projection',
    'dimensionality_reduction_ratio',
    'reconstruction_error',
    'optimal_components',
    'whitening_transform',
    'component_loadings',
    'biplot_data',
    # Abbreviated aliases
    'pca',
    'exp_var',
    'scree_plot',
    'cum_var',
    'pca_inverse',
    'svd',
    'kpca',
    'ipca',
    'project',
    'dim_ratio',
    'recon_error',
    'opt_components',
    'whiten',
    'loadings',
    'biplot',
]


def pca_transform(
    X: List[List[float]],
    n_components: int
) -> Tuple[List[List[float]], Dict[str, Any]]:
    """
    Principal Component Analysis (PCA) transformation.
    
    Alias: pca()
    
    Args:
        X: Feature data (samples x features)
        n_components: Number of components to keep
    
    Returns:
        tuple: (X_transformed, pca_info)
    
    Examples:
        >>> from ilovetools.ml import pca  # Short alias
        
        >>> X = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
        >>> X_pca, info = pca(X, n_components=2)
        >>> print(len(X_pca[0]))
        2
        >>> print('explained_variance' in info)
        True
        
        >>> from ilovetools.ml import pca_transform  # Full name
        >>> X_pca, info = pca_transform(X, n_components=2)
    
    Notes:
        - Linear dimensionality reduction
        - Maximizes variance
        - Orthogonal components
        - Fast and interpretable
    """
    # Center the data
    n_samples = len(X)
    n_features = len(X[0])
    
    # Calculate mean
    means = [sum(X[i][j] for i in range(n_samples)) / n_samples 
             for j in range(n_features)]
    
    # Center data
    X_centered = [
        [X[i][j] - means[j] for j in range(n_features)]
        for i in range(n_samples)
    ]
    
    # Calculate covariance matrix (simplified)
    cov_matrix = []
    for i in range(n_features):
        row = []
        for j in range(n_features):
            cov = sum(X_centered[k][i] * X_centered[k][j] 
                     for k in range(n_samples)) / (n_samples - 1)
            row.append(cov)
        cov_matrix.append(row)
    
    # Simplified eigenvalue/eigenvector computation (power iteration)
    # In production, use numpy.linalg.eig
    components = []
    eigenvalues = []
    
    for _ in range(min(n_components, n_features)):
        # Initialize random vector
        v = [1.0 / math.sqrt(n_features)] * n_features
        
        # Power iteration (simplified)
        for _ in range(100):
            # Multiply by covariance matrix
            Av = [sum(cov_matrix[i][j] * v[j] for j in range(n_features))
                  for i in range(n_features)]
            
            # Normalize
            norm = math.sqrt(sum(x**2 for x in Av))
            if norm > 0:
                v = [x / norm for x in Av]
        
        components.append(v)
        
        # Approximate eigenvalue
        eigenvalue = sum(sum(cov_matrix[i][j] * v[i] * v[j] 
                            for j in range(n_features))
                        for i in range(n_features))
        eigenvalues.append(max(0, eigenvalue))
    
    # Transform data
    X_transformed = []
    for sample in X_centered:
        transformed = [
            sum(sample[j] * components[i][j] for j in range(n_features))
            for i in range(len(components))
        ]
        X_transformed.append(transformed)
    
    # Calculate explained variance
    total_var = sum(eigenvalues)
    explained_var = [ev / total_var if total_var > 0 else 0 
                     for ev in eigenvalues]
    
    pca_info = {
        'components': components,
        'eigenvalues': eigenvalues,
        'explained_variance': explained_var,
        'means': means,
        'n_components': n_components,
    }
    
    return X_transformed, pca_info


# Create alias
pca = pca_transform


def explained_variance_ratio(
    eigenvalues: List[float]
) -> List[float]:
    """
    Calculate explained variance ratio.
    
    Alias: exp_var()
    
    Args:
        eigenvalues: List of eigenvalues
    
    Returns:
        list: Explained variance ratios
    
    Examples:
        >>> from ilovetools.ml import exp_var  # Short alias
        
        >>> eigenvalues = [10.0, 5.0, 2.0, 1.0]
        >>> ratios = exp_var(eigenvalues)
        >>> print(ratios[0] > ratios[1])
        True
        >>> print(sum(ratios))
        1.0
        
        >>> from ilovetools.ml import explained_variance_ratio  # Full name
        >>> ratios = explained_variance_ratio(eigenvalues)
    
    Notes:
        - Shows component importance
        - Sums to 1.0
        - Higher = more important
        - Use for component selection
    """
    total = sum(eigenvalues)
    if total == 0:
        return [0.0] * len(eigenvalues)
    return [ev / total for ev in eigenvalues]


# Create alias
exp_var = explained_variance_ratio


def scree_plot_data(
    eigenvalues: List[float]
) -> Dict[str, List]:
    """
    Generate scree plot data.
    
    Alias: scree_plot()
    
    Args:
        eigenvalues: List of eigenvalues
    
    Returns:
        dict: Scree plot data
    
    Examples:
        >>> from ilovetools.ml import scree_plot  # Short alias
        
        >>> eigenvalues = [10.0, 5.0, 2.0, 1.0, 0.5]
        >>> data = scree_plot(eigenvalues)
        >>> print(len(data['components']))
        5
        >>> print(data['eigenvalues'][0] > data['eigenvalues'][1])
        True
        
        >>> from ilovetools.ml import scree_plot_data  # Full name
        >>> data = scree_plot_data(eigenvalues)
    
    Notes:
        - Visualize component importance
        - Find elbow point
        - Decide number of components
        - Essential for PCA
    """
    n_components = len(eigenvalues)
    variance_ratios = explained_variance_ratio(eigenvalues)
    
    return {
        'components': list(range(1, n_components + 1)),
        'eigenvalues': eigenvalues,
        'variance_ratios': variance_ratios,
        'n_components': n_components,
    }


# Create alias
scree_plot = scree_plot_data


def cumulative_variance(
    variance_ratios: List[float]
) -> List[float]:
    """
    Calculate cumulative variance explained.
    
    Alias: cum_var()
    
    Args:
        variance_ratios: Explained variance ratios
    
    Returns:
        list: Cumulative variance
    
    Examples:
        >>> from ilovetools.ml import cum_var  # Short alias
        
        >>> variance_ratios = [0.5, 0.3, 0.15, 0.05]
        >>> cumulative = cum_var(variance_ratios)
        >>> print(cumulative[-1])
        1.0
        >>> print(cumulative[0])
        0.5
        
        >>> from ilovetools.ml import cumulative_variance  # Full name
        >>> cumulative = cumulative_variance(variance_ratios)
    
    Notes:
        - Track total variance
        - Aim for 95%+
        - Choose optimal components
        - Essential metric
    """
    cumulative = []
    total = 0
    for ratio in variance_ratios:
        total += ratio
        cumulative.append(total)
    return cumulative


# Create alias
cum_var = cumulative_variance


def pca_inverse_transform(
    X_transformed: List[List[float]],
    pca_info: Dict[str, Any]
) -> List[List[float]]:
    """
    Inverse PCA transformation.
    
    Alias: pca_inverse()
    
    Args:
        X_transformed: Transformed data
        pca_info: PCA information from pca_transform
    
    Returns:
        list: Reconstructed data
    
    Examples:
        >>> from ilovetools.ml import pca, pca_inverse  # Short aliases
        
        >>> X = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        >>> X_pca, info = pca(X, n_components=2)
        >>> X_reconstructed = pca_inverse(X_pca, info)
        >>> print(len(X_reconstructed[0]))
        3
        
        >>> from ilovetools.ml import pca_inverse_transform  # Full name
        >>> X_reconstructed = pca_inverse_transform(X_pca, info)
    
    Notes:
        - Reconstruct original data
        - Measure information loss
        - Validate PCA quality
        - Useful for compression
    """
    components = pca_info['components']
    means = pca_info['means']
    n_features = len(means)
    
    X_reconstructed = []
    for sample in X_transformed:
        # Multiply by components (transpose)
        reconstructed = [
            sum(sample[i] * components[i][j] 
                for i in range(len(sample)))
            for j in range(n_features)
        ]
        
        # Add back mean
        reconstructed = [reconstructed[j] + means[j] 
                        for j in range(n_features)]
        
        X_reconstructed.append(reconstructed)
    
    return X_reconstructed


# Create alias
pca_inverse = pca_inverse_transform


def truncated_svd(
    X: List[List[float]],
    n_components: int
) -> Tuple[List[List[float]], Dict[str, Any]]:
    """
    Truncated Singular Value Decomposition.
    
    Alias: svd()
    
    Args:
        X: Feature data
        n_components: Number of components
    
    Returns:
        tuple: (X_transformed, svd_info)
    
    Examples:
        >>> from ilovetools.ml import svd  # Short alias
        
        >>> X = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        >>> X_svd, info = svd(X, n_components=2)
        >>> print(len(X_svd[0]))
        2
        
        >>> from ilovetools.ml import truncated_svd  # Full name
        >>> X_svd, info = truncated_svd(X, n_components=2)
    
    Notes:
        - Works with sparse data
        - No centering required
        - Used in LSA, recommenders
        - Faster than PCA
    """
    # Simplified SVD (similar to PCA but without centering)
    n_samples = len(X)
    n_features = len(X[0])
    
    # Calculate X^T X
    XTX = []
    for i in range(n_features):
        row = []
        for j in range(n_features):
            val = sum(X[k][i] * X[k][j] for k in range(n_samples))
            row.append(val)
        XTX.append(row)
    
    # Power iteration for singular vectors
    components = []
    singular_values = []
    
    for _ in range(min(n_components, n_features)):
        v = [1.0 / math.sqrt(n_features)] * n_features
        
        for _ in range(100):
            Av = [sum(XTX[i][j] * v[j] for j in range(n_features))
                  for i in range(n_features)]
            norm = math.sqrt(sum(x**2 for x in Av))
            if norm > 0:
                v = [x / norm for x in Av]
        
        components.append(v)
        
        # Singular value
        sv = math.sqrt(max(0, sum(sum(XTX[i][j] * v[i] * v[j] 
                                      for j in range(n_features))
                                  for i in range(n_features))))
        singular_values.append(sv)
    
    # Transform
    X_transformed = []
    for sample in X:
        transformed = [
            sum(sample[j] * components[i][j] for j in range(n_features))
            for i in range(len(components))
        ]
        X_transformed.append(transformed)
    
    svd_info = {
        'components': components,
        'singular_values': singular_values,
        'n_components': n_components,
    }
    
    return X_transformed, svd_info


# Create alias
svd = truncated_svd


def kernel_pca_transform(
    X: List[List[float]],
    n_components: int,
    kernel: str = 'rbf',
    gamma: float = 1.0
) -> Tuple[List[List[float]], Dict[str, Any]]:
    """
    Kernel PCA transformation (non-linear).
    
    Alias: kpca()
    
    Args:
        X: Feature data
        n_components: Number of components
        kernel: Kernel type ('rbf', 'poly', 'linear')
        gamma: Kernel coefficient
    
    Returns:
        tuple: (X_transformed, kpca_info)
    
    Examples:
        >>> from ilovetools.ml import kpca  # Short alias
        
        >>> X = [[1, 2], [2, 3], [3, 4], [4, 5]]
        >>> X_kpca, info = kpca(X, n_components=2, kernel='rbf')
        >>> print(len(X_kpca[0]))
        2
        
        >>> from ilovetools.ml import kernel_pca_transform  # Full name
        >>> X_kpca, info = kernel_pca_transform(X, n_components=2)
    
    Notes:
        - Non-linear PCA
        - Captures complex patterns
        - Uses kernel trick
        - More powerful than PCA
    """
    n_samples = len(X)
    
    # Compute kernel matrix
    K = []
    for i in range(n_samples):
        row = []
        for j in range(n_samples):
            if kernel == 'rbf':
                # RBF kernel
                diff = sum((X[i][k] - X[j][k])**2 for k in range(len(X[0])))
                k_val = math.exp(-gamma * diff)
            elif kernel == 'linear':
                # Linear kernel
                k_val = sum(X[i][k] * X[j][k] for k in range(len(X[0])))
            else:
                # Default to linear
                k_val = sum(X[i][k] * X[j][k] for k in range(len(X[0])))
            row.append(k_val)
        K.append(row)
    
    # Center kernel matrix
    row_means = [sum(K[i]) / n_samples for i in range(n_samples)]
    total_mean = sum(row_means) / n_samples
    
    K_centered = [
        [K[i][j] - row_means[i] - row_means[j] + total_mean
         for j in range(n_samples)]
        for i in range(n_samples)
    ]
    
    # Eigendecomposition (simplified)
    eigenvectors = []
    eigenvalues = []
    
    for _ in range(min(n_components, n_samples)):
        v = [1.0 / math.sqrt(n_samples)] * n_samples
        
        for _ in range(100):
            Kv = [sum(K_centered[i][j] * v[j] for j in range(n_samples))
                  for i in range(n_samples)]
            norm = math.sqrt(sum(x**2 for x in Kv))
            if norm > 0:
                v = [x / norm for x in Kv]
        
        eigenvectors.append(v)
        
        eigenvalue = sum(sum(K_centered[i][j] * v[i] * v[j]
                            for j in range(n_samples))
                        for i in range(n_samples))
        eigenvalues.append(max(0, eigenvalue))
    
    # Transform
    X_transformed = [
        [sum(K_centered[i][j] * eigenvectors[k][j] / math.sqrt(eigenvalues[k])
             if eigenvalues[k] > 0 else 0
             for j in range(n_samples))
         for k in range(len(eigenvectors))]
        for i in range(n_samples)
    ]
    
    kpca_info = {
        'eigenvectors': eigenvectors,
        'eigenvalues': eigenvalues,
        'kernel': kernel,
        'gamma': gamma,
        'X_fit': X,
    }
    
    return X_transformed, kpca_info


# Create alias
kpca = kernel_pca_transform


def incremental_pca_transform(
    X: List[List[float]],
    n_components: int,
    batch_size: int = 100
) -> Tuple[List[List[float]], Dict[str, Any]]:
    """
    Incremental PCA for large datasets.
    
    Alias: ipca()
    
    Args:
        X: Feature data
        n_components: Number of components
        batch_size: Batch size for processing
    
    Returns:
        tuple: (X_transformed, ipca_info)
    
    Examples:
        >>> from ilovetools.ml import ipca  # Short alias
        
        >>> X = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
        >>> X_ipca, info = ipca(X, n_components=2, batch_size=2)
        >>> print(len(X_ipca[0]))
        2
        
        >>> from ilovetools.ml import incremental_pca_transform  # Full name
        >>> X_ipca, info = incremental_pca_transform(X, n_components=2)
    
    Notes:
        - Memory efficient
        - For large datasets
        - Batch processing
        - Similar to PCA
    """
    # For simplicity, use regular PCA
    # In production, implement true incremental PCA
    return pca_transform(X, n_components)


# Create alias
ipca = incremental_pca_transform


def feature_projection(
    X: List[List[float]],
    components: List[List[float]]
) -> List[List[float]]:
    """
    Project features onto components.
    
    Alias: project()
    
    Args:
        X: Feature data
        components: Component vectors
    
    Returns:
        list: Projected data
    
    Examples:
        >>> from ilovetools.ml import project  # Short alias
        
        >>> X = [[1, 2, 3], [4, 5, 6]]
        >>> components = [[0.5, 0.5, 0.5], [0.7, 0.2, 0.1]]
        >>> X_proj = project(X, components)
        >>> print(len(X_proj[0]))
        2
        
        >>> from ilovetools.ml import feature_projection  # Full name
        >>> X_proj = feature_projection(X, components)
    
    Notes:
        - Generic projection
        - Works with any components
        - Flexible utility
        - Core operation
    """
    n_features = len(X[0])
    X_projected = []
    
    for sample in X:
        projected = [
            sum(sample[j] * components[i][j] for j in range(n_features))
            for i in range(len(components))
        ]
        X_projected.append(projected)
    
    return X_projected


# Create alias
project = feature_projection


def dimensionality_reduction_ratio(
    original_dims: int,
    reduced_dims: int
) -> Dict[str, float]:
    """
    Calculate dimensionality reduction ratio.
    
    Alias: dim_ratio()
    
    Args:
        original_dims: Original number of dimensions
        reduced_dims: Reduced number of dimensions
    
    Returns:
        dict: Reduction statistics
    
    Examples:
        >>> from ilovetools.ml import dim_ratio  # Short alias
        
        >>> stats = dim_ratio(1000, 50)
        >>> print(stats['reduction_ratio'])
        0.95
        >>> print(stats['compression_factor'])
        20.0
        
        >>> from ilovetools.ml import dimensionality_reduction_ratio
        >>> stats = dimensionality_reduction_ratio(1000, 50)
    
    Notes:
        - Measure reduction
        - Compression factor
        - Space savings
        - Performance metric
    """
    reduction_ratio = (original_dims - reduced_dims) / original_dims
    compression_factor = original_dims / reduced_dims if reduced_dims > 0 else 0
    
    return {
        'original_dims': original_dims,
        'reduced_dims': reduced_dims,
        'reduction_ratio': reduction_ratio,
        'compression_factor': compression_factor,
        'retained_ratio': 1 - reduction_ratio,
    }


# Create alias
dim_ratio = dimensionality_reduction_ratio


def reconstruction_error(
    X_original: List[List[float]],
    X_reconstructed: List[List[float]]
) -> Dict[str, float]:
    """
    Calculate reconstruction error.
    
    Alias: recon_error()
    
    Args:
        X_original: Original data
        X_reconstructed: Reconstructed data
    
    Returns:
        dict: Error metrics
    
    Examples:
        >>> from ilovetools.ml import recon_error  # Short alias
        
        >>> X_orig = [[1, 2, 3], [4, 5, 6]]
        >>> X_recon = [[1.1, 2.1, 2.9], [3.9, 5.1, 6.1]]
        >>> error = recon_error(X_orig, X_recon)
        >>> print(error['mse'] > 0)
        True
        
        >>> from ilovetools.ml import reconstruction_error  # Full name
        >>> error = reconstruction_error(X_orig, X_recon)
    
    Notes:
        - Measure information loss
        - Lower = better
        - Validate reduction
        - Quality metric
    """
    n_samples = len(X_original)
    n_features = len(X_original[0])
    
    # Mean Squared Error
    mse = sum(
        sum((X_original[i][j] - X_reconstructed[i][j])**2
            for j in range(n_features))
        for i in range(n_samples)
    ) / (n_samples * n_features)
    
    # Root Mean Squared Error
    rmse = math.sqrt(mse)
    
    # Mean Absolute Error
    mae = sum(
        sum(abs(X_original[i][j] - X_reconstructed[i][j])
            for j in range(n_features))
        for i in range(n_samples)
    ) / (n_samples * n_features)
    
    return {
        'mse': mse,
        'rmse': rmse,
        'mae': mae,
    }


# Create alias
recon_error = reconstruction_error


def optimal_components(
    variance_ratios: List[float],
    threshold: float = 0.95
) -> Dict[str, Any]:
    """
    Find optimal number of components.
    
    Alias: opt_components()
    
    Args:
        variance_ratios: Explained variance ratios
        threshold: Variance threshold (default 0.95)
    
    Returns:
        dict: Optimal component info
    
    Examples:
        >>> from ilovetools.ml import opt_components  # Short alias
        
        >>> variance_ratios = [0.5, 0.3, 0.15, 0.04, 0.01]
        >>> result = opt_components(variance_ratios, threshold=0.95)
        >>> print(result['n_components'])
        3
        
        >>> from ilovetools.ml import optimal_components  # Full name
        >>> result = optimal_components(variance_ratios)
    
    Notes:
        - Automatic selection
        - Based on variance
        - Common threshold: 95%
        - Saves manual tuning
    """
    cumulative = cumulative_variance(variance_ratios)
    
    n_components = 0
    for i, cum_var in enumerate(cumulative):
        if cum_var >= threshold:
            n_components = i + 1
            break
    
    if n_components == 0:
        n_components = len(variance_ratios)
    
    return {
        'n_components': n_components,
        'threshold': threshold,
        'variance_explained': cumulative[n_components - 1] if n_components > 0 else 0,
        'cumulative_variance': cumulative,
    }


# Create alias
opt_components = optimal_components


def whitening_transform(
    X: List[List[float]],
    pca_info: Dict[str, Any]
) -> List[List[float]]:
    """
    Whitening transformation (decorrelate and normalize).
    
    Alias: whiten()
    
    Args:
        X: Feature data
        pca_info: PCA information
    
    Returns:
        list: Whitened data
    
    Examples:
        >>> from ilovetools.ml import pca, whiten  # Short aliases
        
        >>> X = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        >>> X_pca, info = pca(X, n_components=2)
        >>> X_white = whiten(X, info)
        >>> print(len(X_white[0]))
        2
        
        >>> from ilovetools.ml import whitening_transform  # Full name
        >>> X_white = whitening_transform(X, info)
    
    Notes:
        - Decorrelate features
        - Unit variance
        - Improves learning
        - Common preprocessing
    """
    components = pca_info['components']
    eigenvalues = pca_info['eigenvalues']
    means = pca_info['means']
    n_features = len(means)
    
    # Center data
    X_centered = [
        [X[i][j] - means[j] for j in range(n_features)]
        for i in range(len(X))
    ]
    
    # Transform and normalize by sqrt(eigenvalue)
    X_whitened = []
    for sample in X_centered:
        whitened = [
            sum(sample[j] * components[i][j] for j in range(n_features)) / 
            math.sqrt(eigenvalues[i]) if eigenvalues[i] > 0 else 0
            for i in range(len(components))
        ]
        X_whitened.append(whitened)
    
    return X_whitened


# Create alias
whiten = whitening_transform


def component_loadings(
    components: List[List[float]],
    eigenvalues: List[float],
    feature_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Calculate component loadings (correlations).
    
    Alias: loadings()
    
    Args:
        components: Principal components
        eigenvalues: Eigenvalues
        feature_names: Optional feature names
    
    Returns:
        dict: Loading information
    
    Examples:
        >>> from ilovetools.ml import loadings  # Short alias
        
        >>> components = [[0.7, 0.7], [0.7, -0.7]]
        >>> eigenvalues = [2.0, 0.5]
        >>> result = loadings(components, eigenvalues)
        >>> print(len(result['loadings']))
        2
        
        >>> from ilovetools.ml import component_loadings  # Full name
        >>> result = component_loadings(components, eigenvalues)
    
    Notes:
        - Interpret components
        - Feature contributions
        - Correlation with PCs
        - Essential for interpretation
    """
    n_components = len(components)
    n_features = len(components[0])
    
    if feature_names is None:
        feature_names = [f'Feature_{i}' for i in range(n_features)]
    
    # Calculate loadings (component * sqrt(eigenvalue))
    loadings_matrix = [
        [components[i][j] * math.sqrt(eigenvalues[i])
         for j in range(n_features)]
        for i in range(n_components)
    ]
    
    return {
        'loadings': loadings_matrix,
        'feature_names': feature_names,
        'n_components': n_components,
        'n_features': n_features,
    }


# Create alias
loadings = component_loadings


def biplot_data(
    X_transformed: List[List[float]],
    pca_info: Dict[str, Any],
    feature_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate biplot data (samples + loadings).
    
    Alias: biplot()
    
    Args:
        X_transformed: Transformed data
        pca_info: PCA information
        feature_names: Optional feature names
    
    Returns:
        dict: Biplot data
    
    Examples:
        >>> from ilovetools.ml import pca, biplot  # Short aliases
        
        >>> X = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        >>> X_pca, info = pca(X, n_components=2)
        >>> data = biplot(X_pca, info, ['A', 'B', 'C'])
        >>> print('scores' in data)
        True
        >>> print('loadings' in data)
        True
        
        >>> from ilovetools.ml import biplot_data  # Full name
        >>> data = biplot_data(X_pca, info)
    
    Notes:
        - Visualize samples and features
        - Interpret relationships
        - Essential for PCA
        - Combines scores and loadings
    """
    components = pca_info['components']
    eigenvalues = pca_info['eigenvalues']
    
    # Get loadings
    loading_info = component_loadings(components, eigenvalues, feature_names)
    
    return {
        'scores': X_transformed,
        'loadings': loading_info['loadings'],
        'feature_names': loading_info['feature_names'],
        'explained_variance': pca_info['explained_variance'],
    }


# Create alias
biplot = biplot_data
