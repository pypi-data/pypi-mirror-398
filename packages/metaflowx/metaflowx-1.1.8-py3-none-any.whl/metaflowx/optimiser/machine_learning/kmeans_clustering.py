import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

# ==========================================================
# Custom K-Means function (provided by the user)
# ==========================================================
def kmeans(X, k, max_iter=100):
    X = np.array(X)
    np.random.seed(444)

    centroids = X[np.random.choice(len(X), k, replace=False)]

    for i in range(max_iter):
        distances = np.linalg.norm(X[:, None] - centroids, axis=2)
        labels = np.argmin(distances, axis=1)

        new_centroids = np.array([X[labels == j].mean(axis=0) for j in range(k)])

        if np.allclose(centroids, new_centroids):
            print(f"Converged after {i+1} iterations for k={k}")
            break

        centroids = new_centroids

    wcss = np.sum((X - centroids[labels]) ** 2)
    return labels, centroids, wcss


# ==========================================================
# Main KMeans Clustering Wrapper
# ==========================================================
def kmeans_clustering(df, features, max_k=10):
    """
    Perform K-Means clustering with automatic scaling and elbow method visualization.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataset containing the feature columns used for clustering.
    features : list of str
        Names of two feature columns for visualization and clustering.
        Must contain exactly two numerical features.
    max_k : int, optional, default=10
        Maximum number of clusters to evaluate for the elbow method.

    Workflow
    --------
    1. Extract feature matrix from the provided columns
    2. Standardize the feature space
    3. Evaluate cluster compactness using Within-Cluster Sum of Squares (WCSS)
       for k = 1 to max_k
    4. Plot the Elbow Curve to visualize optimal k
    5. Determine the best k by analyzing change in WCSS
    6. Perform final clustering using the best k
    7. Visualize the clusters and centroids

    Returns
    -------
    labels : numpy.ndarray
        Cluster labels assigned to each data point.
    centroids : numpy.ndarray
        Coordinates of final cluster centroids.
    best_k : int
        Automatically selected optimal number of clusters.

    Notes
    -----
    This function is intended for exploratory data analysis and 
    supports only 2D visualization. The elbow-based heuristic may 
    not always yield a definitive optimal k in complex datasets.

    Example
    -------
    >>> labels, centroids, best_k = kmeans_clustering(
    ...     df,
    ...     features=["Feature1", "Feature2"],
    ...     max_k=8
    ... )
    """
    X = df[features].values

    # Scale the data for better results
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    wcss_list = []

    # Elbow method
    for k in range(1, max_k + 1):
        labels, centroids, wcss = kmeans(X_scaled, k)
        wcss_list.append(wcss)

    # Plot elbow
    plt.figure(figsize=(7, 5))
    plt.plot(range(1, max_k + 1), wcss_list, marker='o')
    plt.title("Elbow Method to Determine Optimal k")
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("WCSS")
    plt.grid(True)
    plt.show()

    # Determine best k as the "elbow"
    best_k = np.diff(wcss_list).argmin() + 1
    print(f"\nBest estimated k = {best_k}")

    # Final clustering
    labels, centroids, _ = kmeans(X_scaled, best_k)

    # Final plot of clusters
    plt.figure(figsize=(7, 5))
    for cluster_num in range(best_k):
        plt.scatter(
            X_scaled[labels == cluster_num, 0],
            X_scaled[labels == cluster_num, 1],
            label=f"Cluster {cluster_num}"
        )
    plt.scatter(
        centroids[:, 0], centroids[:, 1],
        s=200, marker="X", linewidths=2,
    )
    plt.title(f"K-Means Clustering (k={best_k})")
    plt.xlabel(features[0])
    plt.ylabel(features[1])
    plt.legend()
    plt.grid(True)
    plt.show()

    return labels, centroids, best_k
