import itertools
import networkx as nx
import matplotlib.pyplot as plt


def hasse_diagram(elements, leq_func, title="Hasse Diagram"):
    """
    Generate and plot a Hasse diagram for a user-defined poset.

    Parameters
    ----------
    elements : list
        List of nodes in any order (automatically sorted).
    leq_func : function(a, b) -> bool
        User-defined partial order function. 
        Must return True if and only if a <= b in the poset.
    title : str
        Title of the diagram.

    Returns
    -------
    networkx.DiGraph
        The transitive-reduced directed graph representing
        the Hasse diagram (cover relations only).

    Notes
    -----
    • Performs automatic transitive reduction.
    • Automatically assigns hierarchical levels.
    • Supports numbers, strings, tuples, or any hashable node type.
    • Designed for integration into a Python package.

    Examples
    --------
    Draw the Hasse diagram for divisibility on the set 
    {1, 2, 3, 4, 6, 12}:

    >>> elements = [1, 2, 3, 4, 6, 12]
    >>> def divides(a, b):
    ...     return b % a == 0
    >>> hasse_diagram(elements, divides, 
    ...               title="Divisibility: {1,2,3,4,6,12}")

    """

    # ---- STEP 1: Normalize and sort elements ----
    elements = sorted(elements)

    # ---- STEP 2: Build full comparability graph (a < b) ----
    G = nx.DiGraph()
    G.add_nodes_from(elements)

    for a, b in itertools.permutations(elements, 2):
        if a != b and leq_func(a, b):
            G.add_edge(a, b)

    # ---- Transitive Reduction → Hasse edges only ----
    H = nx.DiGraph()
    H.add_nodes_from(G.nodes())

    for u, v in G.edges():
        is_cover = True
        for w in elements:
            if w != u and w != v:
                if G.has_edge(u, w) and G.has_edge(w, v):
                    is_cover = False
                    break
        if is_cover:
            H.add_edge(u, v)

    # ---- Compute node levels by topological rank ----
    topo = list(nx.topological_sort(H))
    level = {}

    for node in topo:
        preds = list(H.predecessors(node))
        level[node] = 0 if not preds else 1 + max(level[p] for p in preds)

    # group by level
    layers = {}
    for node, r in level.items():
        layers.setdefault(r, []).append(node)

    # ---- Assign coordinates ----
    pos = {}
    for r, nodes_at_level in layers.items():
        nodes_at_level = sorted(nodes_at_level)
        count = len(nodes_at_level)
        for i, node in enumerate(nodes_at_level):
            x = i - (count - 1) / 2.0
            y = -r
            pos[node] = (x, y)

    # ---- Draw diagram ----
    plt.figure(figsize=(7, 7))
    nx.draw(
        H,
        pos,
        with_labels=True,
        arrows=False,
        node_size=1000,
        node_color="lightgray",
        font_size=10,
        edge_color="black"
    )
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.show()
    return H