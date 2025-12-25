def centroid_vs_medoid():
    """
    Returns a clear and exam-ready explanation of the difference
    between a Centroid and a Medoid in clustering.
    """

    summary = """
Difference Between Centroid and Medoid

1. Centroid:
   - A centroid is the mean (average) position of all points in a cluster.
   - It is a **virtual point** — it may not exist as an actual data point.
   - Used in algorithms like K-Means.
   - Sensitive to outliers because it depends on numerical averaging.
   - Represents the "center of gravity" of a cluster.

2. Medoid:
   - A medoid is the **most centrally located ACTUAL data point** in a cluster.
   - It is always a real observation from the dataset.
   - Used in algorithms like K-Medoids and PAM.
   - More robust to noise and outliers because it selects a real point, not an average.
   - Represents the most “representative” or “typical” member of the cluster.

Key Difference:
   - Centroid = mean point (may not exist in data).
   - Medoid = actual data point with minimum total distance to others.

Simple Summary:
   Centroid is an average.  
   Medoid is a real point.
    """

    return summary
