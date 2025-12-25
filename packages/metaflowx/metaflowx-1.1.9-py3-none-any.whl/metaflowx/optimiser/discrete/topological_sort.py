import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from collections import deque

def topological_sort(num_nodes, edges):
    """
    Step-by-step Topological Sorting using Kahn's Algorithm.
    
    Parameters
    ----------
    num_nodes : int
        Nodes labeled 1..num_nodes
        
    edges : list of (u, v)
        Directed edges u → v
        
    Behavior
    --------
    • Draws the graph
    • Computes in-degrees
    • Shows which node is removed in each step
    • Shows in-degree table at each iteration
    • Detects cycles
    
    Returns
    -------
    order : list
        A valid topological ordering (if DAG)

    Examples
    -------
    >>> num_nodes = 6
    >>> edges = [
    >>> (1, 2),
    >>> (1, 3),
    >>> (3, 4),
    >>> (2, 4),
    >>> (4, 5),
    >>> (5, 6)
    >>> ]
    >>> topological_sort(num_nodes, edges)
    """

    # -----------------------------------------
    # DRAW GRAPH
    # -----------------------------------------
    G = nx.DiGraph()
    for u, v in edges:
        G.add_edge(u, v)
    
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(8, 6))
    nx.draw(
        G, pos,
        with_labels=True,
        node_size=1200,
        node_color="#c7f2a7",
        font_size=12,
        font_weight="bold"
    )
    plt.title("Graph Structure (Topological Sort)")
    plt.axis("off")
    plt.show()

    # -----------------------------------------
    # BUILD IN-DEGREE ARRAY
    # -----------------------------------------
    indeg = [0] * num_nodes
    for u, v in edges:
        indeg[v - 1] += 1

    def show_table(step, chosen, indeg):
        df = pd.DataFrame([indeg], 
                          columns=[f"V{i+1}" for i in range(num_nodes)],
                          index=[f"Step {step} – removed: {chosen}"])
        display(df)

    # Initial table (before any removals)
    show_table(0, "-", indeg)

    # -----------------------------------------
    # KAHN'S ALGORITHM
    # -----------------------------------------
    q = deque()
    for i in range(num_nodes):
        if indeg[i] == 0:
            q.append(i + 1)

    order = []
    step = 1

    while q:
        u = q.popleft()
        order.append(u)

        # Decrease in-degree of neighbors
        for x, y in edges:
            if x == u:
                indeg[y - 1] -= 1
                if indeg[y - 1] == 0:
                    q.append(y)

        # Show table after removing `u`
        show_table(step, u, indeg)
        step += 1

    # -----------------------------------------
    # CYCLE CHECK
    # -----------------------------------------
    if len(order) != num_nodes:
        print(" Graph contains a cycle — topological ordering impossible.")
        return None

    print("Topological Order:", order)
    return order
