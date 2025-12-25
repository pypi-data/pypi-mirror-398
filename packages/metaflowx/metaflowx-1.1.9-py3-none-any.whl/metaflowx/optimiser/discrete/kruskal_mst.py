import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

def kruskal_mst(num_nodes, edges):
    """
    Examples
    --------
    >>> num_nodes = 6
    >>> edges = [
    >>> (1, 2, 3),
    >>> (1, 3, 5),
    >>> (2, 3, 4),
    >>> (2, 4, 6),
    >>> (3, 4, 2),
    >>> (4, 5, 7),
    >>> (5, 6, 1),
    >>> (3, 6, 8)
    >>> ]
    >>> kruskal_mst(num_nodes, edges)

    Goal
    ----
    Given an undirected, weighted graph G = (V, E), Kruskal’s
    algorithm finds a Minimum Spanning Tree (MST). An MST is
    a subset of edges connecting all vertices with minimum
    total weight and **no cycles**.

    Core Idea
    ---------
    Build the MST by repeatedly selecting the *cheapest* edge
    that does NOT form a cycle with the edges already chosen.
    To detect cycles efficiently, a **Disjoint Set Union (DSU)**
    / **Union–Find** structure is used.

    Detailed Algorithm (Kruskal)
    ----------------------------
    1. Sort all edges of G in **non-decreasing order** of weight.

       Formally: sort E such that 
           w(e₁) ≤ w(e₂) ≤ ... ≤ w(eₘ)

    2. Create a DSU/Union–Find data structure where initially:
           parent[v] = v       for every vertex v
           rank[v] = 0         (rank is used for union-by-rank)

    3. Initialize:
           MST = ∅
           total_weight = 0

    4. Process edges in sorted order.
       For each edge e = (u, v, w):

           (a) Use find(u) and find(v)
               to check if u and v belong to the same set.

           (b) If find(u) == find(v):
                   The edge would create a **cycle**.
                   Reject the edge.

               Else:
                   Accept the edge:
                       MST ← MST ∪ {e}
                       total_weight ← total_weight + w
                   Perform union(u, v)
                   to merge the two components.

    5. Continue until:
           |MST| = |V| − 1
       which is the number of edges in any spanning tree.

    6. The set MST is returned as the Minimum Spanning Tree.

    Union–Find Data Structure
    -------------------------
    The DSU supports two operations:

    • find(x):
        Returns the representative (root) of the set containing x.
        With *path compression*, each node points directly to root
        for near-constant amortized complexity.

    • union(x, y):
        Merges the sets of x and y.
        Uses *union by rank* to keep the tree shallow.
        If both roots are equal, merging is impossible → cycle.

    Correctness Sketch
    ------------------
    Kruskal’s algorithm is correct because it always chooses 
    the **lightest safe edge** — an edge that does not create a cycle
    and connects two different components. This uses the 
    **Cut Property** of MSTs:

        For any cut (partition of vertices),
        the minimum-weight edge crossing the cut
        must belong to every MST.

    Since Kruskal always picks the minimum-weight edge crossing
    some cut, every chosen edge is safe. Eventually, the algorithm
    forms a spanning tree with minimum total weight.

    Complexity
    ----------
    Sorting edges:       O(E log E)
    DSU operations:      O(E α(V))   where α is inverse Ackermann (tiny)
    Total:               O(E log E)

    Graph Type
    ----------
    • Undirected
    • Weighted
    • No self-loops required
    • Parallel edges allowed (cheapest one wins)

    This implementation
    --------------------
    • Draws the original graph using NetworkX
    • Shows sorted edges in a DataFrame
    • Shows each DSU decision (accepted / rejected)
    • Builds and displays the MST
    • Returns:
        mst_edges : list of (u, v, w)
        total_weight : numeric
    """

    # -----------------------------------------
    # DRAW ORIGINAL GRAPH
    # -----------------------------------------
    G = nx.Graph()
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)

    pos = nx.spring_layout(G, seed=42)

    plt.figure(figsize=(8, 6))
    nx.draw(
        G, pos,
        with_labels=True,
        node_size=1400,
        node_color="#f7c4d6",
        font_size=12,
        font_weight="bold"
    )
    labels = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    plt.title("Original Graph (Weighted)")
    plt.axis("off")
    plt.show()

    # -----------------------------------------
    # SORT EDGES BY WEIGHT
    # -----------------------------------------
    edges_sorted = sorted(edges, key=lambda x: x[2])

    print("Sorted edges (by increasing weight):")
    display(pd.DataFrame(edges_sorted, columns=["u", "v", "weight"]))

    # -----------------------------------------
    # DISJOINT SET (UNION–FIND)
    # -----------------------------------------
    parent = [i for i in range(num_nodes + 1)]
    rank = [0] * (num_nodes + 1)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path compression
            x = parent[x]
        return x

    def union(x, y):
        rootX, rootY = find(x), find(y)
        if rootX == rootY:
            return False  # cycle, cannot merge

        if rank[rootX] < rank[rootY]:
            parent[rootX] = rootY
        elif rank[rootX] > rank[rootY]:
            parent[rootY] = rootX
        else:
            parent[rootY] = rootX
            rank[rootX] += 1

        return True

    # -----------------------------------------
    # KRUSKAL ALGORITHM
    # -----------------------------------------
    mst_edges = []
    total_weight = 0
    logs = []

    for u, v, w in edges_sorted:
        before = (find(u), find(v))

        if union(u, v):
            mst_edges.append((u, v, w))
            total_weight += w
            logs.append((u, v, w, "ACCEPTED", before, (find(u), find(v))))
        else:
            logs.append((u, v, w, "REJECTED (cycle)", before, before))

    # -----------------------------------------
    # STEP-BY-STEP LOG TABLE
    # -----------------------------------------
    print("Kruskal Step-by-step Decisions:")
    df_log = pd.DataFrame(
        logs,
        columns=["u", "v", "weight", "decision", "roots_before", "roots_after"]
    )
    display(df_log)

    # -----------------------------------------
    # FINAL MST TABLE
    # -----------------------------------------
    print("MST Edges (Final):")
    df_mst = pd.DataFrame(mst_edges, columns=["u", "v", "weight"])
    display(df_mst)
    print("Total MST Weight:", total_weight)

    # -----------------------------------------
    # DRAW THE MST
    # -----------------------------------------
    MST = nx.Graph()
    MST.add_nodes_from(range(1, num_nodes + 1))
    for u, v, w in mst_edges:
        MST.add_edge(u, v, weight=w)

    plt.figure(figsize=(8, 6))
    nx.draw(
        MST, pos,
        with_labels=True,
        node_size=1400,
        node_color="#b4e8a3",
        font_size=13,
        font_weight="bold",
        width=3
    )
    mst_labels = nx.get_edge_attributes(MST, "weight")
    nx.draw_networkx_edge_labels(MST, pos, edge_labels=mst_labels)
    plt.title("Minimum Spanning Tree (Kruskal)")
    plt.axis("off")
    plt.show()

    return mst_edges, total_weight