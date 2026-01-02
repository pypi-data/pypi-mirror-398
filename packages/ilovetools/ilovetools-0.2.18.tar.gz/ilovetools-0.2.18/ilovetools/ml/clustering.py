"""
Clustering algorithm utilities
Each function has TWO names: full descriptive name + abbreviated alias
"""

from typing import List, Dict, Any, Tuple, Optional
import math
import random

__all__ = [
    # Full names
    'kmeans_clustering',
    'hierarchical_clustering',
    'dbscan_clustering',
    'elbow_method',
    'silhouette_score',
    'euclidean_distance',
    'manhattan_distance',
    'cosine_similarity_distance',
    'initialize_centroids',
    'assign_clusters',
    'update_centroids',
    'calculate_inertia',
    'dendrogram_data',
    'cluster_purity',
    'davies_bouldin_index',
    # Abbreviated aliases
    'kmeans',
    'hierarchical',
    'dbscan',
    'elbow',
    'silhouette',
    'euclidean',
    'manhattan',
    'cosine_dist',
    'init_centroids',
    'assign',
    'update',
    'inertia',
    'dendrogram',
    'purity',
    'davies_bouldin',
]


def euclidean_distance(
    point1: List[float],
    point2: List[float]
) -> float:
    """
    Calculate Euclidean distance between two points.
    
    Alias: euclidean()
    
    Args:
        point1: First point coordinates
        point2: Second point coordinates
    
    Returns:
        float: Euclidean distance
    
    Examples:
        >>> from ilovetools.ml import euclidean  # Short alias
        
        >>> p1 = [1, 2, 3]
        >>> p2 = [4, 5, 6]
        >>> dist = euclidean(p1, p2)
        >>> print(round(dist, 2))
        5.2
        
        >>> from ilovetools.ml import euclidean_distance  # Full name
        >>> dist = euclidean_distance(p1, p2)
    
    Notes:
        - Most common distance metric
        - Straight line distance
        - Sensitive to scale
        - Works in any dimension
    """
    if len(point1) != len(point2):
        raise ValueError("Points must have same dimensions")
    
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(point1, point2)))


# Create alias
euclidean = euclidean_distance


def manhattan_distance(
    point1: List[float],
    point2: List[float]
) -> float:
    """
    Calculate Manhattan (L1) distance between two points.
    
    Alias: manhattan()
    
    Args:
        point1: First point coordinates
        point2: Second point coordinates
    
    Returns:
        float: Manhattan distance
    
    Examples:
        >>> from ilovetools.ml import manhattan  # Short alias
        
        >>> p1 = [1, 2, 3]
        >>> p2 = [4, 5, 6]
        >>> dist = manhattan(p1, p2)
        >>> print(dist)
        9.0
        
        >>> from ilovetools.ml import manhattan_distance  # Full name
        >>> dist = manhattan_distance(p1, p2)
    
    Notes:
        - Grid-based distance
        - Sum of absolute differences
        - Less sensitive to outliers
        - Good for high dimensions
    """
    if len(point1) != len(point2):
        raise ValueError("Points must have same dimensions")
    
    return sum(abs(a - b) for a, b in zip(point1, point2))


# Create alias
manhattan = manhattan_distance


def cosine_similarity_distance(
    point1: List[float],
    point2: List[float]
) -> float:
    """
    Calculate cosine distance between two points.
    
    Alias: cosine_dist()
    
    Args:
        point1: First point coordinates
        point2: Second point coordinates
    
    Returns:
        float: Cosine distance (1 - cosine similarity)
    
    Examples:
        >>> from ilovetools.ml import cosine_dist  # Short alias
        
        >>> p1 = [1, 2, 3]
        >>> p2 = [2, 4, 6]
        >>> dist = cosine_dist(p1, p2)
        >>> print(round(dist, 4))
        0.0
        
        >>> from ilovetools.ml import cosine_similarity_distance  # Full name
        >>> dist = cosine_similarity_distance(p1, p2)
    
    Notes:
        - Measures angle between vectors
        - Range: 0 to 2
        - Good for text/sparse data
        - Ignores magnitude
    """
    if len(point1) != len(point2):
        raise ValueError("Points must have same dimensions")
    
    # Calculate dot product
    dot_product = sum(a * b for a, b in zip(point1, point2))
    
    # Calculate magnitudes
    mag1 = math.sqrt(sum(a ** 2 for a in point1))
    mag2 = math.sqrt(sum(b ** 2 for b in point2))
    
    if mag1 == 0 or mag2 == 0:
        return 1.0
    
    # Cosine similarity
    similarity = dot_product / (mag1 * mag2)
    
    # Cosine distance
    return 1 - similarity


# Create alias
cosine_dist = cosine_similarity_distance


def initialize_centroids(
    data: List[List[float]],
    k: int,
    method: str = 'random'
) -> List[List[float]]:
    """
    Initialize cluster centroids.
    
    Alias: init_centroids()
    
    Args:
        data: Dataset
        k: Number of clusters
        method: 'random' or 'kmeans++'
    
    Returns:
        list: Initial centroids
    
    Examples:
        >>> from ilovetools.ml import init_centroids  # Short alias
        
        >>> data = [[1, 2], [2, 3], [3, 4], [8, 9], [9, 10]]
        >>> centroids = init_centroids(data, k=2)
        >>> print(len(centroids))
        2
        
        >>> from ilovetools.ml import initialize_centroids  # Full name
        >>> centroids = initialize_centroids(data, k=2)
    
    Notes:
        - Random: Pick random points
        - KMeans++: Smart initialization
        - Affects convergence speed
        - Critical for K-Means
    """
    if k <= 0 or k > len(data):
        raise ValueError("K must be between 1 and number of data points")
    
    if method == 'random':
        # Random initialization
        indices = random.sample(range(len(data)), k)
        return [data[i][:] for i in indices]
    
    elif method == 'kmeans++':
        # K-Means++ initialization
        centroids = []
        
        # Choose first centroid randomly
        centroids.append(data[random.randint(0, len(data) - 1)][:])
        
        # Choose remaining centroids
        for _ in range(k - 1):
            distances = []
            for point in data:
                # Find minimum distance to existing centroids
                min_dist = min(euclidean_distance(point, c) for c in centroids)
                distances.append(min_dist ** 2)
            
            # Choose next centroid with probability proportional to distance
            total = sum(distances)
            if total == 0:
                # All points are centroids, pick random
                remaining = [p for p in data if p not in centroids]
                if remaining:
                    centroids.append(remaining[0][:])
            else:
                probs = [d / total for d in distances]
                cumsum = []
                total_prob = 0
                for p in probs:
                    total_prob += p
                    cumsum.append(total_prob)
                
                r = random.random()
                for i, cum_p in enumerate(cumsum):
                    if r <= cum_p:
                        centroids.append(data[i][:])
                        break
        
        return centroids
    
    else:
        raise ValueError("Method must be 'random' or 'kmeans++'")


# Create alias
init_centroids = initialize_centroids


def assign_clusters(
    data: List[List[float]],
    centroids: List[List[float]],
    distance_metric: str = 'euclidean'
) -> List[int]:
    """
    Assign each point to nearest centroid.
    
    Alias: assign()
    
    Args:
        data: Dataset
        centroids: Cluster centroids
        distance_metric: 'euclidean', 'manhattan', or 'cosine'
    
    Returns:
        list: Cluster assignments
    
    Examples:
        >>> from ilovetools.ml import assign  # Short alias
        
        >>> data = [[1, 2], [2, 3], [8, 9], [9, 10]]
        >>> centroids = [[1.5, 2.5], [8.5, 9.5]]
        >>> labels = assign(data, centroids)
        >>> print(labels)
        [0, 0, 1, 1]
        
        >>> from ilovetools.ml import assign_clusters  # Full name
        >>> labels = assign_clusters(data, centroids)
    
    Notes:
        - Assigns to nearest centroid
        - Uses specified distance metric
        - Core step in K-Means
        - Fast operation
    """
    # Choose distance function
    if distance_metric == 'euclidean':
        dist_func = euclidean_distance
    elif distance_metric == 'manhattan':
        dist_func = manhattan_distance
    elif distance_metric == 'cosine':
        dist_func = cosine_similarity_distance
    else:
        raise ValueError("Invalid distance metric")
    
    labels = []
    for point in data:
        # Find nearest centroid
        distances = [dist_func(point, c) for c in centroids]
        nearest = distances.index(min(distances))
        labels.append(nearest)
    
    return labels


# Create alias
assign = assign_clusters


def update_centroids(
    data: List[List[float]],
    labels: List[int],
    k: int
) -> List[List[float]]:
    """
    Update centroids based on cluster assignments.
    
    Alias: update()
    
    Args:
        data: Dataset
        labels: Cluster assignments
        k: Number of clusters
    
    Returns:
        list: Updated centroids
    
    Examples:
        >>> from ilovetools.ml import update  # Short alias
        
        >>> data = [[1, 2], [2, 3], [8, 9], [9, 10]]
        >>> labels = [0, 0, 1, 1]
        >>> centroids = update(data, labels, k=2)
        >>> print(len(centroids))
        2
        
        >>> from ilovetools.ml import update_centroids  # Full name
        >>> centroids = update_centroids(data, labels, k=2)
    
    Notes:
        - Calculate mean of each cluster
        - Core step in K-Means
        - Moves centroids to center
        - Iterative process
    """
    dimensions = len(data[0])
    centroids = []
    
    for cluster_id in range(k):
        # Get points in this cluster
        cluster_points = [data[i] for i in range(len(data)) if labels[i] == cluster_id]
        
        if not cluster_points:
            # Empty cluster, keep old centroid or random point
            centroids.append(data[random.randint(0, len(data) - 1)][:])
        else:
            # Calculate mean
            centroid = []
            for dim in range(dimensions):
                mean = sum(point[dim] for point in cluster_points) / len(cluster_points)
                centroid.append(mean)
            centroids.append(centroid)
    
    return centroids


# Create alias
update = update_centroids


def calculate_inertia(
    data: List[List[float]],
    labels: List[int],
    centroids: List[List[float]]
) -> float:
    """
    Calculate within-cluster sum of squares (inertia).
    
    Alias: inertia()
    
    Args:
        data: Dataset
        labels: Cluster assignments
        centroids: Cluster centroids
    
    Returns:
        float: Inertia value
    
    Examples:
        >>> from ilovetools.ml import inertia  # Short alias
        
        >>> data = [[1, 2], [2, 3], [8, 9], [9, 10]]
        >>> labels = [0, 0, 1, 1]
        >>> centroids = [[1.5, 2.5], [8.5, 9.5]]
        >>> score = inertia(data, labels, centroids)
        >>> print(round(score, 2))
        2.0
        
        >>> from ilovetools.ml import calculate_inertia  # Full name
        >>> score = calculate_inertia(data, labels, centroids)
    
    Notes:
        - Lower is better
        - Measures compactness
        - Used in elbow method
        - Always decreases with more K
    """
    total = 0.0
    for i, point in enumerate(data):
        centroid = centroids[labels[i]]
        dist = euclidean_distance(point, centroid)
        total += dist ** 2
    
    return total


# Create alias
inertia = calculate_inertia


def kmeans_clustering(
    data: List[List[float]],
    k: int,
    max_iterations: int = 100,
    distance_metric: str = 'euclidean',
    init_method: str = 'kmeans++'
) -> Dict[str, Any]:
    """
    K-Means clustering algorithm.
    
    Alias: kmeans()
    
    Args:
        data: Dataset
        k: Number of clusters
        max_iterations: Maximum iterations
        distance_metric: Distance metric to use
        init_method: Centroid initialization method
    
    Returns:
        dict: Clustering results
    
    Examples:
        >>> from ilovetools.ml import kmeans  # Short alias
        
        >>> data = [[1, 2], [2, 3], [3, 4], [8, 9], [9, 10], [10, 11]]
        >>> result = kmeans(data, k=2)
        >>> print(len(result['labels']))
        6
        >>> print(len(result['centroids']))
        2
        
        >>> from ilovetools.ml import kmeans_clustering  # Full name
        >>> result = kmeans_clustering(data, k=2)
    
    Notes:
        - Most popular clustering
        - Fast and scalable
        - Requires K specification
        - Sensitive to initialization
    """
    # Initialize centroids
    centroids = initialize_centroids(data, k, method=init_method)
    
    for iteration in range(max_iterations):
        # Assign clusters
        labels = assign_clusters(data, centroids, distance_metric)
        
        # Update centroids
        new_centroids = update_centroids(data, labels, k)
        
        # Check convergence
        converged = True
        for old, new in zip(centroids, new_centroids):
            if euclidean_distance(old, new) > 1e-6:
                converged = False
                break
        
        centroids = new_centroids
        
        if converged:
            break
    
    # Calculate inertia
    inertia_value = calculate_inertia(data, labels, centroids)
    
    return {
        'labels': labels,
        'centroids': centroids,
        'inertia': inertia_value,
        'iterations': iteration + 1,
    }


# Create alias
kmeans = kmeans_clustering


def elbow_method(
    data: List[List[float]],
    max_k: int = 10,
    distance_metric: str = 'euclidean'
) -> Dict[str, Any]:
    """
    Elbow method to find optimal K.
    
    Alias: elbow()
    
    Args:
        data: Dataset
        max_k: Maximum K to try
        distance_metric: Distance metric to use
    
    Returns:
        dict: Inertia values for each K
    
    Examples:
        >>> from ilovetools.ml import elbow  # Short alias
        
        >>> data = [[1, 2], [2, 3], [3, 4], [8, 9], [9, 10], [10, 11]]
        >>> result = elbow(data, max_k=4)
        >>> print(len(result['k_values']))
        4
        >>> print(len(result['inertias']))
        4
        
        >>> from ilovetools.ml import elbow_method  # Full name
        >>> result = elbow_method(data, max_k=4)
    
    Notes:
        - Find optimal K
        - Plot inertia vs K
        - Look for elbow point
        - Subjective interpretation
    """
    k_values = list(range(1, max_k + 1))
    inertias = []
    
    for k in k_values:
        if k > len(data):
            break
        result = kmeans_clustering(data, k, distance_metric=distance_metric)
        inertias.append(result['inertia'])
    
    return {
        'k_values': k_values[:len(inertias)],
        'inertias': inertias,
    }


# Create alias
elbow = elbow_method


def silhouette_score(
    data: List[List[float]],
    labels: List[int],
    distance_metric: str = 'euclidean'
) -> float:
    """
    Calculate silhouette score for clustering.
    
    Alias: silhouette()
    
    Args:
        data: Dataset
        labels: Cluster assignments
        distance_metric: Distance metric to use
    
    Returns:
        float: Silhouette score (-1 to 1)
    
    Examples:
        >>> from ilovetools.ml import silhouette  # Short alias
        
        >>> data = [[1, 2], [2, 3], [8, 9], [9, 10]]
        >>> labels = [0, 0, 1, 1]
        >>> score = silhouette(data, labels)
        >>> print(round(score, 2))
        0.71
        
        >>> from ilovetools.ml import silhouette_score  # Full name
        >>> score = silhouette_score(data, labels)
    
    Notes:
        - Range: -1 to 1
        - Higher is better
        - Measures cluster quality
        - Considers separation and cohesion
    """
    # Choose distance function
    if distance_metric == 'euclidean':
        dist_func = euclidean_distance
    elif distance_metric == 'manhattan':
        dist_func = manhattan_distance
    elif distance_metric == 'cosine':
        dist_func = cosine_similarity_distance
    else:
        raise ValueError("Invalid distance metric")
    
    n = len(data)
    silhouette_values = []
    
    for i in range(n):
        # Get cluster of point i
        cluster_i = labels[i]
        
        # Calculate a(i): mean distance to points in same cluster
        same_cluster = [j for j in range(n) if labels[j] == cluster_i and j != i]
        if not same_cluster:
            silhouette_values.append(0)
            continue
        
        a_i = sum(dist_func(data[i], data[j]) for j in same_cluster) / len(same_cluster)
        
        # Calculate b(i): mean distance to points in nearest cluster
        unique_clusters = set(labels)
        unique_clusters.discard(cluster_i)
        
        if not unique_clusters:
            silhouette_values.append(0)
            continue
        
        b_i = float('inf')
        for cluster_j in unique_clusters:
            other_cluster = [j for j in range(n) if labels[j] == cluster_j]
            mean_dist = sum(dist_func(data[i], data[j]) for j in other_cluster) / len(other_cluster)
            b_i = min(b_i, mean_dist)
        
        # Calculate silhouette value
        s_i = (b_i - a_i) / max(a_i, b_i)
        silhouette_values.append(s_i)
    
    return sum(silhouette_values) / len(silhouette_values)


# Create alias
silhouette = silhouette_score


def hierarchical_clustering(
    data: List[List[float]],
    n_clusters: int,
    linkage: str = 'average',
    distance_metric: str = 'euclidean'
) -> Dict[str, Any]:
    """
    Hierarchical clustering (agglomerative).
    
    Alias: hierarchical()
    
    Args:
        data: Dataset
        n_clusters: Number of clusters
        linkage: 'single', 'complete', or 'average'
        distance_metric: Distance metric to use
    
    Returns:
        dict: Clustering results
    
    Examples:
        >>> from ilovetools.ml import hierarchical  # Short alias
        
        >>> data = [[1, 2], [2, 3], [8, 9], [9, 10]]
        >>> result = hierarchical(data, n_clusters=2)
        >>> print(len(result['labels']))
        4
        
        >>> from ilovetools.ml import hierarchical_clustering  # Full name
        >>> result = hierarchical_clustering(data, n_clusters=2)
    
    Notes:
        - Creates tree structure
        - No need to specify K initially
        - Good for small datasets
        - Computationally expensive
    """
    # Choose distance function
    if distance_metric == 'euclidean':
        dist_func = euclidean_distance
    elif distance_metric == 'manhattan':
        dist_func = manhattan_distance
    elif distance_metric == 'cosine':
        dist_func = cosine_similarity_distance
    else:
        raise ValueError("Invalid distance metric")
    
    n = len(data)
    
    # Initialize: each point is its own cluster
    clusters = [[i] for i in range(n)]
    
    # Merge until we have n_clusters
    while len(clusters) > n_clusters:
        # Find closest pair of clusters
        min_dist = float('inf')
        merge_i, merge_j = 0, 1
        
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                # Calculate distance between clusters
                if linkage == 'single':
                    # Minimum distance
                    dist = min(dist_func(data[p1], data[p2])
                              for p1 in clusters[i] for p2 in clusters[j])
                elif linkage == 'complete':
                    # Maximum distance
                    dist = max(dist_func(data[p1], data[p2])
                              for p1 in clusters[i] for p2 in clusters[j])
                else:  # average
                    # Average distance
                    distances = [dist_func(data[p1], data[p2])
                                for p1 in clusters[i] for p2 in clusters[j]]
                    dist = sum(distances) / len(distances)
                
                if dist < min_dist:
                    min_dist = dist
                    merge_i, merge_j = i, j
        
        # Merge clusters
        clusters[merge_i].extend(clusters[merge_j])
        clusters.pop(merge_j)
    
    # Create labels
    labels = [0] * n
    for cluster_id, cluster in enumerate(clusters):
        for point_id in cluster:
            labels[point_id] = cluster_id
    
    return {
        'labels': labels,
        'n_clusters': len(clusters),
    }


# Create alias
hierarchical = hierarchical_clustering


def dbscan_clustering(
    data: List[List[float]],
    eps: float,
    min_samples: int = 5,
    distance_metric: str = 'euclidean'
) -> Dict[str, Any]:
    """
    DBSCAN density-based clustering.
    
    Alias: dbscan()
    
    Args:
        data: Dataset
        eps: Maximum distance for neighborhood
        min_samples: Minimum points for core point
        distance_metric: Distance metric to use
    
    Returns:
        dict: Clustering results
    
    Examples:
        >>> from ilovetools.ml import dbscan  # Short alias
        
        >>> data = [[1, 2], [2, 3], [3, 4], [8, 9], [9, 10], [10, 11]]
        >>> result = dbscan(data, eps=2.0, min_samples=2)
        >>> print(len(result['labels']))
        6
        
        >>> from ilovetools.ml import dbscan_clustering  # Full name
        >>> result = dbscan_clustering(data, eps=2.0, min_samples=2)
    
    Notes:
        - Density-based clustering
        - Finds arbitrary shapes
        - Handles noise (label -1)
        - No need to specify K
    """
    # Choose distance function
    if distance_metric == 'euclidean':
        dist_func = euclidean_distance
    elif distance_metric == 'manhattan':
        dist_func = manhattan_distance
    elif distance_metric == 'cosine':
        dist_func = cosine_similarity_distance
    else:
        raise ValueError("Invalid distance metric")
    
    n = len(data)
    labels = [-1] * n  # -1 means noise
    cluster_id = 0
    
    for i in range(n):
        if labels[i] != -1:
            continue
        
        # Find neighbors
        neighbors = []
        for j in range(n):
            if dist_func(data[i], data[j]) <= eps:
                neighbors.append(j)
        
        # Check if core point
        if len(neighbors) < min_samples:
            continue  # Noise point
        
        # Start new cluster
        labels[i] = cluster_id
        
        # Expand cluster
        seed_set = neighbors[:]
        while seed_set:
            current = seed_set.pop(0)
            
            if labels[current] == -1:
                labels[current] = cluster_id
            
            if labels[current] != -1:
                continue
            
            labels[current] = cluster_id
            
            # Find neighbors of current
            current_neighbors = []
            for j in range(n):
                if dist_func(data[current], data[j]) <= eps:
                    current_neighbors.append(j)
            
            # If core point, add neighbors to seed set
            if len(current_neighbors) >= min_samples:
                seed_set.extend(current_neighbors)
        
        cluster_id += 1
    
    # Count noise points
    noise_count = sum(1 for label in labels if label == -1)
    
    return {
        'labels': labels,
        'n_clusters': cluster_id,
        'noise_points': noise_count,
    }


# Create alias
dbscan = dbscan_clustering


def dendrogram_data(
    data: List[List[float]],
    linkage: str = 'average',
    distance_metric: str = 'euclidean'
) -> List[Dict[str, Any]]:
    """
    Generate dendrogram data for hierarchical clustering.
    
    Alias: dendrogram()
    
    Args:
        data: Dataset
        linkage: Linkage method
        distance_metric: Distance metric to use
    
    Returns:
        list: Merge history
    
    Examples:
        >>> from ilovetools.ml import dendrogram  # Short alias
        
        >>> data = [[1, 2], [2, 3], [8, 9], [9, 10]]
        >>> merges = dendrogram(data)
        >>> print(len(merges))
        3
        
        >>> from ilovetools.ml import dendrogram_data  # Full name
        >>> merges = dendrogram_data(data)
    
    Notes:
        - Shows merge history
        - Tree structure
        - Cut at desired level
        - Visualize hierarchy
    """
    # Choose distance function
    if distance_metric == 'euclidean':
        dist_func = euclidean_distance
    elif distance_metric == 'manhattan':
        dist_func = manhattan_distance
    elif distance_metric == 'cosine':
        dist_func = cosine_similarity_distance
    else:
        raise ValueError("Invalid distance metric")
    
    n = len(data)
    clusters = [[i] for i in range(n)]
    merges = []
    
    while len(clusters) > 1:
        # Find closest pair
        min_dist = float('inf')
        merge_i, merge_j = 0, 1
        
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                # Calculate distance
                if linkage == 'single':
                    dist = min(dist_func(data[p1], data[p2])
                              for p1 in clusters[i] for p2 in clusters[j])
                elif linkage == 'complete':
                    dist = max(dist_func(data[p1], data[p2])
                              for p1 in clusters[i] for p2 in clusters[j])
                else:  # average
                    distances = [dist_func(data[p1], data[p2])
                                for p1 in clusters[i] for p2 in clusters[j]]
                    dist = sum(distances) / len(distances)
                
                if dist < min_dist:
                    min_dist = dist
                    merge_i, merge_j = i, j
        
        # Record merge
        merges.append({
            'cluster1': clusters[merge_i][:],
            'cluster2': clusters[merge_j][:],
            'distance': min_dist,
            'size': len(clusters[merge_i]) + len(clusters[merge_j]),
        })
        
        # Merge clusters
        clusters[merge_i].extend(clusters[merge_j])
        clusters.pop(merge_j)
    
    return merges


# Create alias
dendrogram = dendrogram_data


def cluster_purity(
    labels_true: List[int],
    labels_pred: List[int]
) -> float:
    """
    Calculate cluster purity score.
    
    Alias: purity()
    
    Args:
        labels_true: True labels
        labels_pred: Predicted cluster labels
    
    Returns:
        float: Purity score (0 to 1)
    
    Examples:
        >>> from ilovetools.ml import purity  # Short alias
        
        >>> true_labels = [0, 0, 1, 1, 2, 2]
        >>> pred_labels = [0, 0, 1, 1, 1, 1]
        >>> score = purity(true_labels, pred_labels)
        >>> print(round(score, 2))
        0.67
        
        >>> from ilovetools.ml import cluster_purity  # Full name
        >>> score = cluster_purity(true_labels, pred_labels)
    
    Notes:
        - Range: 0 to 1
        - Higher is better
        - Measures cluster quality
        - Requires true labels
    """
    if len(labels_true) != len(labels_pred):
        raise ValueError("Label arrays must have same length")
    
    # Get unique clusters
    clusters = set(labels_pred)
    
    correct = 0
    for cluster in clusters:
        # Get points in this cluster
        cluster_indices = [i for i in range(len(labels_pred)) if labels_pred[i] == cluster]
        
        # Get true labels for these points
        cluster_true_labels = [labels_true[i] for i in cluster_indices]
        
        # Find most common true label
        if cluster_true_labels:
            most_common = max(set(cluster_true_labels), key=cluster_true_labels.count)
            correct += cluster_true_labels.count(most_common)
    
    return correct / len(labels_true)


# Create alias
purity = cluster_purity


def davies_bouldin_index(
    data: List[List[float]],
    labels: List[int]
) -> float:
    """
    Calculate Davies-Bouldin index.
    
    Alias: davies_bouldin()
    
    Args:
        data: Dataset
        labels: Cluster assignments
    
    Returns:
        float: Davies-Bouldin index (lower is better)
    
    Examples:
        >>> from ilovetools.ml import davies_bouldin  # Short alias
        
        >>> data = [[1, 2], [2, 3], [8, 9], [9, 10]]
        >>> labels = [0, 0, 1, 1]
        >>> score = davies_bouldin(data, labels)
        >>> print(round(score, 2))
        0.35
        
        >>> from ilovetools.ml import davies_bouldin_index  # Full name
        >>> score = davies_bouldin_index(data, labels)
    
    Notes:
        - Lower is better
        - Measures cluster separation
        - No true labels needed
        - Considers intra and inter cluster distances
    """
    # Get unique clusters
    clusters = list(set(labels))
    k = len(clusters)
    
    if k <= 1:
        return 0.0
    
    # Calculate centroids
    centroids = []
    for cluster_id in clusters:
        cluster_points = [data[i] for i in range(len(data)) if labels[i] == cluster_id]
        if cluster_points:
            dimensions = len(data[0])
            centroid = [sum(p[d] for p in cluster_points) / len(cluster_points) for d in range(dimensions)]
            centroids.append(centroid)
    
    # Calculate average distances within clusters
    avg_distances = []
    for cluster_id in clusters:
        cluster_points = [data[i] for i in range(len(data)) if labels[i] == cluster_id]
        if len(cluster_points) > 0:
            centroid = centroids[cluster_id]
            avg_dist = sum(euclidean_distance(p, centroid) for p in cluster_points) / len(cluster_points)
            avg_distances.append(avg_dist)
        else:
            avg_distances.append(0)
    
    # Calculate DB index
    db_values = []
    for i in range(k):
        max_ratio = 0
        for j in range(k):
            if i != j:
                numerator = avg_distances[i] + avg_distances[j]
                denominator = euclidean_distance(centroids[i], centroids[j])
                if denominator > 0:
                    ratio = numerator / denominator
                    max_ratio = max(max_ratio, ratio)
        db_values.append(max_ratio)
    
    return sum(db_values) / k if k > 0 else 0.0


# Create alias
davies_bouldin = davies_bouldin_index
