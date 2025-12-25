def hac():
    """
    Returns a detailed but simple summary of Hierarchical Agglomerative Clustering (HAC),
    rewritten in clear language while keeping all meaning correct for exam use.
    """

    summary = """
Hierarchical Agglomerative Clustering (HAC) — Key Points

1. Definition:
   HAC is a bottom-up clustering algorithm that starts by treating every data point as its
   own individual cluster. It then repeatedly merges the two closest clusters until only one
   big cluster remains or until the required number of clusters is obtained.

2. How HAC Works:
   HAC begins with N clusters (each containing a single point). At each step, it computes
   the distance between all current clusters based on a chosen linkage method. The two
   clusters that are closest according to that linkage rule are merged. This merging continues
   step by step, building a hierarchy of clusters.

3. Linkage Criteria (Cluster Distance Rules):
   - Single Linkage:
       Distance between two clusters is the minimum distance between any pair of points
       (one from each cluster). This tends to form long, chain-like clusters.
   - Complete Linkage:
       Distance is the maximum distance between any pair of points across clusters. This
       produces compact, tight clusters.
   - Average Linkage:
       Distance is the average of all pairwise distances between points in the two clusters.

4. Dendrogram:
   HAC is visualized using a dendrogram — a tree-like diagram that shows how clusters
   merge step by step. The height at which two clusters merge represents how similar
   or dissimilar they are. Cutting the dendrogram at a chosen height gives the desired
   number of clusters.

5. Deterministic Nature:
   HAC always produces the same result for a given dataset because it involves no
   randomness. There is no random initialization like in K-Means, making HAC fully
   deterministic and repeatable.

6. Stopping Criteria:
   HAC stops when all points merge into a single cluster or when the number of clusters
   you want (k clusters) has been reached. The merging process simply halts at that level
   of the dendrogram.

7. Use Cases:
   HAC is useful when you want to understand the structure of data at multiple levels,
   compare how clusters merge, or when the number of clusters is not known beforehand.
   It is also widely used because the dendrogram gives a clear visual interpretation.
    """

    return summary
