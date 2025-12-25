def dbscan_point_differences():
    """
    Returns a simple and clear explanation of the differences between
    Border Point, Noise Point, and Outlier in DBSCAN.
    """

    summary = """
DBSCAN — Difference Between Border Point, Noise Point, and Outlier

1. Border Point:
   - A border point does NOT have enough neighbors to be a core point
     (i.e., neighbors < MinPts).
   - But it lies inside the ε-neighborhood of AT LEAST ONE core point.
   - It belongs to the cluster formed by that core point.
   - It cannot expand the cluster any further.
   Summary: It is inside a cluster, but too weak to grow it.

2. Noise Point:
   - A noise point has fewer neighbors than MinPts
     AND it is not within ε of any core point.
   - It does NOT belong to any cluster.
   - Remains labeled as noise.
   Summary: It is isolated AND far from all core points.

3. Outlier:
   - In DBSCAN, “outlier” is simply another name for “noise point”.
   - An outlier is a point that fails both conditions:
        # Not a core point
        # Not a border point
   - It lies in a sparse region with no density connection.
   Summary: Outlier = Noise point (same meaning in DBSCAN).

Final Difference:
   Border Point → Inside a cluster, but cannot expand it.
   Noise Point  → Outside all clusters.
   Outlier      → Same as Noise Point.
    """

    return summary
