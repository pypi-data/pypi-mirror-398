def dbscan_t():
    """
    Returns a detailed but simplified summary of DBSCAN, including
    the full working mechanism and point-type definitions rewritten
    in simple, clear language.
    """

    summary = """
DBSCAN — Key Points

1. Definition:
   DBSCAN is a density-based clustering algorithm that groups points located in dense
   regions, while points in sparse regions are marked as noise. Clusters are formed
   based on how many neighbors lie within a distance ε, so DBSCAN does not assume any
   specific cluster shape.

2. How DBSCAN Groups Points:
   DBSCAN checks each unvisited point to see if it is a core point (has at least MinPts
   neighbors inside ε). If it is a core point, a new cluster starts and expands using
   breadth-first search. Border points join clusters but cannot expand them. Points not
   close to any core point are treated as noise.

3. Types of Points in DBSCAN (Core, Border, Noise):
   - Core Point:
       A core point is any point that has at least MinPts neighbors within its ε-neighborhood.
       The ε-neighborhood is defined by the distance function and the ε hyperparameter.
       Core points represent dense areas, and clusters grow outward from these dense regions.
       This dense group of points essentially forms the “heart” of the cluster.

   - Border Point:
       A border point does not have enough neighbors to be a core point. However, it lies
       inside the ε-neighborhood of at least one core point. It belongs to the cluster but
       cannot expand the cluster further. Think of it as the outer boundary or shell of the
       cluster.

   - Noise Point (Outlier):
       A noise point is neither a core point nor a border point. It has too few neighbors
       and is not within ε of any core point. Therefore, it stays unassigned and is treated
       as noise or an outlier.

4. INITIAL STEPS (Simplified):
   - Pick any point A.
   - Mark A as VISITED.
   - If A is a core point:
       * Enqueue all its ε-neighbors.
       * Start a new cluster and add A.
   - If A is not a core point:
       * Temporarily mark it as noise.
       * Do not enqueue neighbors.
       * Move to the next unvisited point.

5. REPEATING STEPS (Cluster Expansion):
   - Remove a point X from the queue.
   - Mark X as VISITED.
   - Add X to the current cluster.
   - If X is a core point:
       * Add all its ε-neighbors to the queue **only if** they are not already in a cluster
         and not already in the queue.
       * (X itself is never re-added to the queue.)
   - If X is a border point:
       * Add X to the cluster but do not expand from it.

6. Restarting New Clusters:
   When the queue becomes empty, DBSCAN looks for any remaining unvisited points.
   If another unvisited core point is found, a new cluster is started. This repeats until
   all points have been processed.

7. Stopping Criteria:
   DBSCAN stops when:
       - All points have been visited.
       - All expansion queues are empty.
   At this point, all core, border, and noise points have been correctly identified.

8. Important Notes:
   - Only ε-neighbors are enqueued; the generating point is never re-enqueued.
   - DBSCAN forms clusters of arbitrary shape.
   - Outliers are automatically detected.

9. Use Cases:
   DBSCAN works well when cluster shapes are irregular, the data contains noise, or
   the number of clusters is not known beforehand.

Discussion Questions:
--------------------
What happens if a border point lies in the ε-neighborhood of two or more clusters? Which cluster does it belong to?**

In DBSCAN, a border point may fall within the ε-neighborhood of core points from multiple clusters. However, DBSCAN is a sequential algorithm, meaning clusters are discovered one after another in the order the algorithm traverses points. The cluster that expands first and reaches that border point first will assign it to its cluster.
Once the border point is labeled, it is never reassigned to another cluster, even if later another core point from a different cluster could have included it. 
Therefore:
The border point becomes part of only one cluster (the one that reaches it first).
Other clusters cannot include it afterward.
As a result, DBSCAN never produces overlapping clusters.
    """

    return summary
