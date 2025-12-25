import heapq
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx


def dijkstra(num_nodes, edges, start):
    """
    Run Dijkstra's algorithm and return a step-by-step trace as a pandas DataFrame.

    Parameters
    ----------
    num_nodes : int
        Total number of nodes in the graph. Nodes are assumed to be labeled
        as integers from 1 to `num_nodes`.

    edges : list of tuples (u, v, w)
        Each tuple represents an undirected edge between nodes `u` and `v`
        with weight `w`. All weights must be non-negative for Dijkstra's
        algorithm to be valid.

    start : int
        The starting/source node from which shortest paths will be computed.

    Returns
    -------
    pandas.DataFrame
        A DataFrame where each row represents one step of Dijkstra's algorithm.
        Columns include:
            * 'Step'    – The step count
            * 'Visited' – The list of visited nodes up to that step
            * Node columns (2, 3, …) – The shortest known distances at each step

        Updated values compared to the previous step are shown in parentheses,
        e.g., "(20)" indicates the value was updated during that step.
    
    Pseudocode
    ----------
    Algorithm Dijkstra(G, source):
    1.  For each vertex v in G:
        dist[v] ← ∞
        prev[v] ← undefined

    2.  dist[source] ← 0

    3.  Initialize a priority queue Q containing all vertices,
        keyed by dist[·]

    4.  While Q is not empty:
        u ← Extract-Min(Q)

        For each neighbor v of u:
                alt ← dist[u] + weight(u, v)

                If alt < dist[v]:
                        dist[v] ← alt
                        prev[v] ← u
                        Decrease-Key(Q, v, alt)
    5.  Output dist[·] and prev[·] for all vertices
    Notes
    -----
    • This implementation assumes an undirected graph.
    • Infinity is displayed as "∞".
    • The function tracks the *order of node visitation*, mirroring textbook
      Dijkstra tables.
    • The DataFrame makes this ideal for teaching, debugging, or exporting to CSV.

    Example
    -------
    >>> edges = [
    >>>     (1, 2, 7), # node 1 and 2 are connected with weight 7
    ...     (1, 3, 9), # node 1 and 3 are connected with weight 9
    ...     (1, 6, 14), # node 1 and 6 are connected with weight 14
    ...     (2, 3, 10), # node 2 and 3 are connected with weight 10
    ...     (2, 4, 15), # node 2 and 4 are connected with weight 15
    ...     (3, 4, 11), # node 3 and 4 are connected with weight 11
    ...     (3, 6, 2),  # node 3 and 6 are connected with weight 2
    ...     (4, 5, 6),  # node 4 and 5 are connected with weight 6
    ...     (5, 6, 9)   # node 5 and 6 are connected with weight 9
    ... ]
    >>> df = dijkstra(6, edges, start=1)
    >>> print(df)

    """

    # ---------------------------------------------------
    # Build adjacency list
    # ---------------------------------------------------
    adj = {i: [] for i in range(1, num_nodes + 1)}
    for u, v, w in edges:
        adj[u].append((v, w))
        adj[v].append((u, w))  # undirected

    INF = float("inf")
    dist = {i: INF for i in adj}
    dist[start] = 0
    visited = set()
    pq = [(0, start)]

    # ---------------------------------------------------
    # Prepare table
    # ---------------------------------------------------
    table_rows = []
    nodes = [i for i in range(1, num_nodes + 1) if i != start]

    def record_row(step, visited_order, old, new):
        row = {
            "Step": step,
            "Visited": ",".join(map(str, visited_order)) if visited_order else "-"
        }

        for n in nodes:
            if new[n] == INF:
                row[n] = "∞"
            else:
                if new[n] != old[n]:
                    row[n] = f"({new[n]})"
                else:
                    row[n] = new[n]
        table_rows.append(row)

    # Initial row
    prev = dist.copy()
    visited_order = []
    record_row(0, visited_order, prev, dist)
    step = 0

    # ---------------------------------------------------
    # Main Dijkstra loop
    # ---------------------------------------------------
    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue

        visited.add(u)
        visited_order.append(u)
        step += 1
        prev = dist.copy()

        for v, w in adj[u]:
            if v not in visited:
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    heapq.heappush(pq, (dist[v], v))

        record_row(step, visited_order, prev, dist)

    # ---------------------------------------------------
    # Create DataFrame
    # ---------------------------------------------------
    df = pd.DataFrame(table_rows)

    # ---------------------------------------------------
    # Plot the original graph using NetworkX
    # ---------------------------------------------------
    G = nx.Graph()
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)

    pos = nx.spring_layout(G, seed=42)  # good default layout

    plt.figure(figsize=(8, 6))
    nx.draw_networkx_nodes(G, pos, node_size=900, node_color="#79a6f6")
    nx.draw_networkx_edges(G, pos, width=2)
    nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold")

    # Draw weights
    edge_labels = {(u, v): w for u, v, w in edges}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)

    plt.title("Original Graph")
    plt.axis("off")
    plt.tight_layout()
    plt.show()

    return df
