import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

def floyd_warshall(num_nodes, edges):
    """
    Compute all-pairs shortest paths using the Floyd–Warshall algorithm,
    while displaying a step-by-step trace of the distance matrix updates.

    This version:
        • Treats the graph as **directed**
        • Plots the graph once at the beginning using NetworkX
        • Constructs the initial D⁰ matrix from the given edges
        • Displays each matrix D⁰, D¹, …, Dⁿ as a pandas DataFrame
        • Marks updated entries during each iteration with parentheses, e.g. "(7)"
        • Returns a list of all DataFrames representing every Dᵏ matrix

    Parameters
    ----------
    num_nodes : int
        Total number of nodes in the graph. Nodes must be labeled 1 to num_nodes.

    edges : list of tuples (u, v, w)
        Directed weighted edges of the form:
            u → v  with weight w
        All weights must be non-negative for the algorithm to behave correctly.

    Behavior
    --------
    • A directed graph is drawn before the algorithm starts.
    • The initial distance matrix D⁰ contains:
          0 on the diagonal,
          edge weights where edges exist,
          ∞ where no direct path exists.
    • At each iteration k (k = 1..n), the algorithm checks whether paths
      that go through node k provide shorter distances, updating entries
      accordingly.
    • Each updated entry is wrapped in parentheses in the displayed DataFrame.

    Returns
    -------
    trace : list of pandas.DataFrame
        A list containing D⁰, D¹, …, Dⁿ in order. Each matrix reflects the
        state of distances after using nodes {1, …, k} as intermediates.

    Notes
    -----
    • This implementation is intended for teaching and visualization.
    • The function directly displays the matrices; it does not return plots.
    • Distances that remain unreachable are shown as "∞".
    """

    # -----------------------------------------
    # PLOT THE GRAPH FIRST (hierarchy-style)
    # -----------------------------------------
    G = nx.DiGraph()

    # Add weighted edges
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)   # directed only

    # Use a tree-like hierarchical layout
    pos = nx.spring_layout(G, seed=42)  # spring layout gives nice structure

    plt.figure(figsize=(8, 6))
    nx.draw(
        G, pos,
        with_labels=True,
        node_size=1200,
        node_color="#90c2f8",
        font_size=12,
        font_weight="bold"
    )

    # Draw edge weights
    labels = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)

    plt.title("Graph Structure (Weighted)")
    plt.axis("off")
    plt.show()

    # -----------------------------------------
    # BEGIN FLOYD–WARSHALL
    # -----------------------------------------

    INF = float("inf")
    D = np.full((num_nodes, num_nodes), INF)

    for i in range(num_nodes):
        D[i][i] = 0
    for u, v, w in edges:
        D[u-1][v-1] = w    # directed only


    trace = []

    # Convert matrix → Formatted DataFrame
    def make_df(matrix, prev):
        formatted = []
        for i in range(num_nodes):
            row = []
            for j in range(num_nodes):
                val = matrix[i][j]
                if val == INF:
                    row.append("∞")
                else:
                    if prev is not None and val != prev[i][j]:
                        row.append(f"({int(val)})")
                    else:
                        row.append(int(val))
            formatted.append(row)

        return pd.DataFrame(
            formatted,
            index=[f"V{i+1}" for i in range(num_nodes)],
            columns=[f"V{j+1}" for j in range(num_nodes)]
        )

    # Show D0
    df0 = make_df(D, prev=None)
    display(df0)
    trace.append(df0)

    # Floyd–Warshall iterations
    for k in range(num_nodes):

        prev = D.copy()

        for i in range(num_nodes):
            for j in range(num_nodes):
                alt = prev[i][k] + prev[k][j]
                if alt < prev[i][j]:
                    D[i][j] = alt

        dfk = make_df(D, prev)
        display(dfk)
        trace.append(dfk)