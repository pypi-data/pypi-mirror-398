import math
from collections import deque
import pandas as pd

def dbscan(points_dict, eps, min_pts):
    """
    Perform a step-by-step DBSCAN clustering process on a set of named points.

    This function accepts a dictionary of point names mapped to their (x, y) coordinates.
    It computes the full pairwise distance matrix, then runs the DBSCAN algorithm while 
    recording every internal step of the clustering process. The function tracks visited 
    points, queue operations, core-point identification, cluster formation, and noise 
    detection. Two pandas DataFrames are returned: one containing the distance matrix, and 
    another containing the detailed step-by-step trace of DBSCAN’s execution.

    Parameters
    ----------
    points_dict : dict
        A dictionary where keys are point labels (e.g., "A", "B", "C") and values are 
        2-dimensional coordinates expressed as tuples, e.g. {"A": (0, 0), "B": (1, 3)}.

    eps : float
        The radius threshold for determining neighborhood membership in DBSCAN.
        A point q is considered a neighbor of point p if distance(p, q) <= eps.

    min_pts : int
        The minimum number of points required in a point’s eps-neighborhood for it to be 
        considered a core point. Core points trigger cluster expansion.

    Returns
    -------
    df_distances : pandas.DataFrame
        A DataFrame representing the pairwise Euclidean distance matrix between all points.
        Row and column labels correspond to the provided point names.

    df_steps : pandas.DataFrame
        A DataFrame capturing the full execution trace of DBSCAN.
        Each row corresponds to one algorithmic step and includes:
            - Step number
            - Mode ("initial" or "expansion")
            - Point being processed
            - Its neighborhood
            - Whether it is a core point
            - Current visited set
            - Current queue contents
            - Current cluster points
            - Current noise points

    Notes
    -----
    - This implementation mirrors the conceptual DBSCAN algorithm using a FIFO queue for 
      cluster expansion (similar to BFS).
    - The function does not perform plotting or return cluster labels directly; instead, 
      it provides a complete procedural trace useful for learning, debugging, and analysis.

    Examples
    --------
    points = {
    "A": (0, 0),
    "B": (1, 0),
    "C": (0, 1),
    "D": (5, 5)
}

dist_df, step_df = dbscan(points, eps=1.5, min_pts=2)
dist_df   # prints beautifully as a DataFrame
step_df   # prints beautifully as a DataFrame
    
    """


    names = list(points_dict.keys())
    points = list(points_dict.values())
    n = len(points)

    # ---------- DISTANCE MATRIX ----------
    dist_matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            d = math.sqrt((points[i][0] - points[j][0])**2 +
                          (points[i][1] - points[j][1])**2)
            row.append(d)
        dist_matrix.append(row)

    df_distances = pd.DataFrame(dist_matrix, index=names, columns=names)

    # ---------- DBSCAN FUNCTIONS ----------
    def region_query(i):
        return [j for j in range(n) if df_distances.iloc[i, j] <= eps]

    visited = set()
    cluster = set()
    noise = set()
    queue = deque()
    step = 1
    rows = []

    # ---------- MAIN LOOP ----------
    for i in range(n):

        if i in visited:
            continue

        visited.add(i)
        neighbors = region_query(i)
        is_core = len(neighbors) >= min_pts

        if is_core:
            cluster.add(i)
            queue.extend([p for p in neighbors if p != i])
        else:
            noise.add(i)

        rows.append({
            "Step": step,
            "Mode": "initial",
            "Point": names[i],
            "Neighbors": [names[x] for x in neighbors],
            "Core": is_core,
            "Visited": [names[x] for x in visited],
            "Queue": [names[x] for x in queue],
            "Cluster": [names[x] for x in cluster],
            "Noise": [names[x] for x in noise]
        })
        step += 1

        # ---------- EXPANSION ----------
        while queue:
            q = queue.popleft()

            if q not in visited:
                visited.add(q)
                q_neighbors = region_query(q)
                q_is_core = len(q_neighbors) >= min_pts

                if q_is_core:
                    cluster.add(q)
                    for nb in q_neighbors:
                        if nb not in visited:
                            queue.append(nb)
                else:
                    noise.add(q)

                rows.append({
                    "Step": step,
                    "Mode": "expansion",
                    "Point": names[q],
                    "Neighbors": [names[x] for x in q_neighbors],
                    "Core": q_is_core,
                    "Visited": [names[x] for x in visited],
                    "Queue": [names[x] for x in queue],
                    "Cluster": [names[x] for x in cluster],
                    "Noise": [names[x] for x in noise]
                })
                step += 1

    df_steps = pd.DataFrame(rows)

    return df_distances, df_steps
