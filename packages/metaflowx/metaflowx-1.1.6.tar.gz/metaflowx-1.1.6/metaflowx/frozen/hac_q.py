def hac_q():
    """
    Returns rewritten HAC Q&A in clear, exam-ready language
    while preserving the exact meaning of the original content.
    """

    summary = """
HAC — Important Conceptual Questions & Answers

Q1. What is a dendrogram?
Ans:
    A dendrogram is a tree-shaped diagram that shows how hierarchical clustering builds
    clusters step by step. At the bottom are individual data points, and as you move upward,
    the diagram shows how these points merge into bigger clusters. The vertical height of
    each merge represents the distance or dissimilarity between those clusters. By choosing
    a cutoff height on the dendrogram, you can decide how many clusters to form.

Q2. What is a linkage criterion in HAC?
Ans:
    A linkage criterion describes how the distance between two clusters is calculated.
    It defines the rule used to compare clusters during the merging process. The commonly
    used linkage types are single linkage, complete linkage, and average linkage.

Q3. Define single linkage, complete linkage, and average linkage.
Ans:
    - Single Linkage: The distance between two clusters is the smallest distance between
      any pair of points from the two clusters.
    - Complete Linkage: The distance between two clusters is the largest distance between
      any pair of points from the two clusters.
    - Average Linkage: The distance between two clusters is the average of all pairwise
      distances between points from the two clusters.

Q4. Why is hierarchical clustering considered deterministic?
Ans:
    HAC is deterministic because it does not involve any randomness. There is no random
    initialization step like in K-Means. Given the same data and distance metric, HAC will
    always produce exactly the same result every time.

Q5. What does “agglomerative” mean in the context of clustering?
Ans:
    “Agglomerative” refers to the bottom-up approach used in HAC. The algorithm starts
    with each data point as its own cluster and repeatedly merges the closest clusters until
    larger clusters form.

Q6. What is the stopping criterion in HAC?
Ans:
    The algorithm stops either when all points have merged into one single cluster or when
    the desired number of clusters has been reached. The merging process simply halts at
    that chosen level.
    """

    return summary
