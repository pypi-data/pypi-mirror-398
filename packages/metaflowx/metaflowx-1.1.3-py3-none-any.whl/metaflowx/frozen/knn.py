def knn():
    """
    Returns a short, crisp, exam-ready explanation of:
    - K-Nearest Neighbors (KNN) theory
    - K-Means++ theory
    - Simple example (walkthrough)
    - Why improved centroid selection is needed in K-Means++
    """

    summary = """
KNN — Key Points (Theory in Brief)

1. Definition:
   K-Nearest Neighbors (KNN) is a lazy, instance-based learning algorithm used for
   classification and regression. It makes predictions based on the labels of the
   'k' closest data points using a distance metric (usually Euclidean distance).

2. How KNN Works:
   - Choose a value of k.
   - Compute distances from the query point to all training points.
   - Select the k nearest points.
   - For classification: choose the majority class among these k points.
   - For regression: take the average of their values.
   KNN does not build a model; it simply uses stored data during prediction.

3. Properties:
   - Non-parametric (makes no assumptions about data distribution).
   - Sensitive to feature scaling.
   - Works well for smaller datasets but slow for very large ones.

------------------------------------------------------------

K-Means++ — Theory (Short & Crisp)

4. Definition:
   K-Means++ is an improved initialization method for K-Means that selects
   well-spaced initial centroids. This reduces poor clustering and speeds up convergence.

5. Why We Need Better Centroid Selection:
   - Random initialization may pick centroids too close together.
   - This leads to:
       * bad clusters,
       * slow convergence,
       * getting stuck in poor local minima.
   - K-Means++ spreads initial centroids far apart → better starting point.

6. How K-Means++ Works:
   Step 1: Pick the first centroid randomly.
   Step 2: For each remaining point, compute its distance D(x) to the nearest chosen centroid.
   Step 3: Select the next centroid with probability proportional to D(x)^2.
   Step 4: Repeat until k centroids are chosen, then run regular K-Means.

------------------------------------------------------------

K-Means++ Example (Walkthrough)

7. Example:
   Data points = {2, 3, 10, 12}, need k = 2.
   - Randomly choose first centroid → say 3.
   - Compute distance to 3:
       2→1, 3→0, 10→7, 12→9
   - Square: 1, 0, 49, 81
   - Points with larger squared distances (10 and 12) are more likely to be picked.
   - Suppose next centroid becomes 12.
   - Final initial centroids = {3, 12} — well separated.

8. Benefits:
   - Faster convergence.
   - Better clustering quality.
   - Lower chance of K-Means failing due to random poor starts.
   - More stable results across multiple runs.
    """

    return summary
