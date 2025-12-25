import math
import matplotlib.pyplot as plt
import networkx as nx

def tree_classification_error(tree_dict, figsize=(6, 6)):
    """
    Draw a hierarchical decision tree and compute impurity measures for every node.
    
    =============================================================================
    OVERVIEW
    =============================================================================
    This function visualizes a decision tree and computes *three fundamental 
    impurity measures* for each node:

        (1) Classification Error       E_t
        (2) Gini Index                G_t
        (3) Cross Entropy / Deviance  D_t

    It is designed as an educational + exam preparation tool. 
    Every step that would normally be written in a theoretical exam is printed 
    explicitly, including:

        • proportions p_{t,k} = n_k / n_t
        • expanded summation formulas
        • substituted numerical values
        • final impurity results for each node

    The function does **not** build a tree from data.
    It **takes the tree structure directly** in “easy-tree format” 
    and analyzes the supplied node counts.

    No pygraphviz or external graph libraries are needed:
    the hierarchical layout is computed manually and always displays cleanly.


    =============================================================================
    TREE REPRESENTATION (INPUT FORMAT)
    =============================================================================
    tree_dict is a Python dictionary where keys represent node positions and
    values represent class-count dictionaries.

    Example:
        easy_tree = {
            "root": {"A":500, "B":700},
            "root->L": {"A":300, "B":100},
            "root->R": {"A":100, "B":300},
            "root->L->R": {"A":100, "B":300}
        }
        tree_classification_error(tree)
        
    The key "root->L->R" means:
        • Start at "root"
        • Go to Left child
        • Then go to Right child

    The function automatically infers:
        • node depth from number of "->"
        • parent-child relationships
        • tree hierarchy and layout


    =============================================================================
    IMPURITY MEASURES (THEORY + PROPERTIES)
    =============================================================================

    Let a node contain class counts:
        counts = {A: a, B: b, ..., K: k}
        n_t = total = a + b + ... + k

    The proportion of class k in the node:
        p_{t,k} = count(k) / n_t


    -------------------------------------------------------------------------
    1. CLASSIFICATION ERROR  (E_t)
    -------------------------------------------------------------------------
        E_t = 1 - max(p_{t,k})

    • Measures the probability of misclassification if the node predicts the 
      majority class.
    • Simple and intuitive but not sensitive to changes in class distribution.
    • Used mainly during *tree pruning*, not during tree building.
    • Range: 0 to 1
        0  = pure node (all samples same class)
        1  = maximum impurity (all classes equally common)


    -------------------------------------------------------------------------
    2. GINI INDEX  (G_t)
    -------------------------------------------------------------------------
        G_t = 1 - Σ_k (p_{t,k}²)

    • Measures how often a randomly chosen element would be misclassified 
      if labeled according to the distribution in the node.
    • Sensitive to class distribution.
    • CART (Classification And Regression Trees) uses Gini as the primary 
      splitting criterion.
    • Range: 0 to (1 - 1/K)
        lower  → purer node
        higher → more mixed node

      For 2 classes:
        max Gini = 0.5  at p = 0.5


    -------------------------------------------------------------------------
    3. CROSS ENTROPY / DEVIANCE  (D_t)
    -------------------------------------------------------------------------
        D_t = -Σ_k (p_{t,k} log p_{t,k})

    • Most sensitive impurity measure.
    • Strongly penalizes nodes with many classes mixed together.
    • Used heavily in Logistic Regression and Gradient Boosting (e.g., XGBoost).
    • Always ≥ 0
        0  = perfect purity (one class has probability 1)
        increases as classes mix more equally.

    • Equivalent to Shannon entropy from information theory.
    • Interpreted as expected “amount of information” required to identify class.


    =============================================================================
    HOW THE FUNCTION WORKS INTERNALLY
    =============================================================================

    1. **Extract structure**
       - Count how many "->" in each path to determine depth.
       - Infer edges by splitting node names.

    2. **Tree Layout (Manual Positioning)**
       - For each depth level (root = depth 0), nodes are placed on a horizontal row.
       - x-coordinates are spaced evenly within each row.
       - y-coordinate = negative of depth → deeper nodes appear lower.
       - This ensures:
            * perfect hierarchy
            * no overlap
            * no diagonal bias

    3. **Impurity Computations**
       For each node:
            compute p_{t,k}
            compute E_t, G_t, D_t
            store all results

    4. **Drawing the Tree**
       - Uses NetworkX only for graph structure.
       - Uses matplotlib for drawing.
       - Each node displays:
            name, class counts, E_t, G_t, D_t

    5. **Printing Exam-Style Derivations**
       For each node:
            - Prints p_{t,k} as fractions and decimals
            - Expands summations:
                Σ p_{t,k}²
                Σ p_{t,k} log(p_{t,k})
            - Performs substitutions
            - Computes final numerical values


    =============================================================================
    PARAMETERS
    =============================================================================
    tree_dict : dict
        A dictionary representing the tree in path-based format.
        Each key is a node path.
        Each value is a dict of class counts.

    figsize : tuple (default: (6,6))
        Controls size of the plotted tree.


    =============================================================================
    RETURNS
    =============================================================================
    None.
    The function:
        • draws the tree visually
        • prints impurity measures for all nodes
        • serves as a complete exam-learning tool
    """
    # -------------------------------------------------------------------
    # Helper: compute impurity for ONE node
    # -------------------------------------------------------------------
    def compute_impurity(counts):
        total = sum(counts.values())
        t_k = {k: v / total for k, v in counts.items()}

        classification_error = 1 - max(t_k.values())
        gini_index = 1 - sum(p * p for p in t_k.values())
        cross_entropy = -sum(p * math.log(p) for p in t_k.values() if p > 0)

        return t_k, classification_error, gini_index, cross_entropy

    # -------------------------------------------------------------------
    # Build edges, depths
    # -------------------------------------------------------------------
    edges = []
    depths = {}

    for path in tree_dict:
        depth = path.count("->")
        depths[path] = depth

        parts = path.split("->")
        if len(parts) > 1:
            parent = "->".join(parts[:-1])
            child = path
            edges.append((parent, child))

    # -------------------------------------------------------------------
    # Group nodes by depth
    # -------------------------------------------------------------------
    levels = {}
    for node, depth in depths.items():
        levels.setdefault(depth, []).append(node)

    # -------------------------------------------------------------------
    # Compute positions manually (perfect hierarchy)
    # -------------------------------------------------------------------
    pos = {}
    for depth, nodes in levels.items():
        y = -depth
        step = 1.0 / (len(nodes) + 1)
        for i, node in enumerate(nodes):
            x = (i + 1) * step
            pos[node] = (x, y)

    # -------------------------------------------------------------------
    # Prepare labels with impurity values
    # -------------------------------------------------------------------
    labels = {}
    impurity_info = {}

    for path, counts in tree_dict.items():
        short = path.split("->")[-1]
        t_k, E, G, H = compute_impurity(counts)

        labels[path] = (
            f"{short}\n{counts}\n"
            f"E={E:.3f}\n"
            f"G={G:.3f}\n"
            f"H={H:.3f}"
        )

        impurity_info[path] = {
            "counts": counts,
            "t_k": t_k,
            "E": E,
            "G": G,
            "H": H
        }

    # -------------------------------------------------------------------
    # Draw the decision tree
    # -------------------------------------------------------------------
    Gg = nx.DiGraph()
    Gg.add_edges_from(edges)

    plt.figure(figsize=figsize)
    nx.draw(
        Gg, pos,
        labels=labels,
        with_labels=True,
        node_color="#FDD693",
        node_size=4500,
        font_size=8,
        font_weight="bold",
        arrows=False
    )
    plt.title("Decision Tree with Impurity Measures", fontsize=14)
    plt.show()

    # -------------------------------------------------------------------
    # NODE-BY-NODE impurity calculations (EXAM FORMAT)
    # -------------------------------------------------------------------

    print("\n\n================ NODE-BY-NODE Classsification error CALCULATION ================\n")

    # Sort nodes by depth for nice ordering
    ordered_nodes = sorted(impurity_info.keys(), key=lambda x: depths[x])

    for node in ordered_nodes:
        info = impurity_info[node]
        counts = info["counts"]
        t_k = info["t_k"]
        E = info["E"]
        Gv = info["G"]
        H = info["H"]

        total = sum(counts.values())

        print(f"\nNode: {node}")
        print(f"Counts = {counts}")
        print(f"n_t = {total}\n")

        # --------------------
        # t_k values
        # --------------------
        print("t_k values:")
        for cls, prob in t_k.items():
            print(f"   t_{cls} = {counts[cls]}/{total} = {prob:.4f}")
        print()

        # --------------------
        # Classification Error
        # --------------------
        print("Classification Error (E_t):")
        print("E_t = 1 - max(t_k)")
        print(f"    = 1 - {max(t_k.values()):.4f}")
        print(f"    = {E:.4f}\n")

        # --------------------
        # Gini Index
        # --------------------
        sq_sum_expanded = " + ".join([f"({prob:.4f})²" for prob in t_k.values()])
        print("Gini Index (G_t):")
        print("G_t = 1 - Σ t_k²")
        print(f"    = 1 - ( {sq_sum_expanded} )")
        print(f"    = {Gv:.4f}\n")

        # --------------------
        # Cross Entropy
        # --------------------
        entropy_expanded = " + ".join([
            f"{prob:.4f} ln({prob:.4f})" for prob in t_k.values() if prob > 0
        ])
        print("Cross Entropy / Deviance (D_t):")
        print("D_t = - Σ t_k ln(t_k)")
        print(f"    = - ( {entropy_expanded} )")
        print(f"    = {H:.4f}")

        print("\n---------------------------------------------------------------\n")
