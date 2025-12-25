import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

def bellman_ford(num_nodes, edges, source):
    """
    Step-by-step Bellman-Ford algorithm with visual trace.

    Parameters
    ----------
    num_nodes : int
        Nodes labeled 1..num_nodes
    edges : list of (u, v, w)
        Directed edges with weights
    source : int
        Starting node

    Behavior
    --------
    • Prints graph
    • Shows distance table for each iteration
    • Marks improved values with parentheses
    • Detects negative-weight cycles

    Returns
    -------
    trace : list of pandas.DataFrame

    Examples
    --------
    # Example to test Bellman–Ford
    num_nodes = 4
    edges = [
    (1, 2, 4),
    (1, 3, 5),
    (2, 3, -3),
    (2, 4, 6),
    (3, 4, 2)
    ]
    source = 1
    trace = bellman_ford(num_nodes, edges, source)
    """

    # -----------------------------------------
    # DRAW GRAPH
    # -----------------------------------------
    G = nx.DiGraph()
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)

    pos = nx.spring_layout(G, seed=42)

    plt.figure(figsize=(8, 6))
    nx.draw(
        G, pos,
        with_labels=True,
        node_size=1200,
        node_color="#ffcf9f",
        font_size=12,
        font_weight="bold"
    )
    labels = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    plt.title("Graph Structure (Bellman–Ford)")
    plt.axis("off")
    plt.show()

    # -----------------------------------------
    # INITIALIZATION
    # -----------------------------------------
    INF = float("inf")
    dist = [INF] * num_nodes
    dist[source - 1] = 0

    trace = []

    def make_df(dist_list, prev):
        row = []
        for i, val in enumerate(dist_list):
            if val == INF:
                row.append("∞")
            else:
                if prev is not None and val != prev[i]:
                    row.append(f"({val})")
                else:
                    row.append(val)

        return pd.DataFrame(
            [row],
            index=[f"Iteration"],
            columns=[f"V{i+1}" for i in range(num_nodes)]
        )

    # D0
    df0 = make_df(dist, prev=None)
    display(df0)
    trace.append(df0)

    # -----------------------------------------
    # RELAX |V|-1 TIMES
    # -----------------------------------------
    for k in range(1, num_nodes):
        prev = dist.copy()

        for u, v, w in edges:
            if prev[u - 1] + w < dist[v - 1]:
                dist[v - 1] = prev[u - 1] + w

        dfk = make_df(dist, prev)
        display(dfk)
        trace.append(dfk)

    # -----------------------------------------
    # NEGATIVE CYCLE CHECK
    # -----------------------------------------
    for u, v, w in edges:
        if dist[u - 1] + w < dist[v - 1]:
            print("Negative-weight cycle detected!")
            break

    return trace
