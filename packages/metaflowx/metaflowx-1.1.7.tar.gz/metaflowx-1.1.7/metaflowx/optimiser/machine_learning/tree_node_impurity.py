import math
def tree_node_impurity(forest):
    """
    Compute and display impurity calculations and variable importance for 
    an entire random forest (collection of decision trees).

    This function prints:
        • The Gini impurity calculation for every node (symbolic + numeric form).
        • The ΔI(t, x_j) for every split: 
              ΔI = I(parent) − average_child_impurity
        • The final averaged variable importance across all trees.

    ------------------------------------------------------------------------
    INPUT FORMAT
    ------------------------------------------------------------------------
    forest : dict
        A dictionary where each key is a tree name (string) and each value 
        is a decision tree represented as a dictionary of the form:

            tree = {
                "node_name": (counts_dict, split_variable),
                ...
            }

        - "node_name" is a string representing the path in the tree:
              "root", "root->L", "root->R", "root->L->R", etc.

        - counts_dict is a dictionary of class counts at that node:
              {"Yes": 12, "No": 8}

        - split_variable is the predictor used at that node (e.g., "x1", "x2").
          If the node is terminal, pass None.

    ------------------------------------------------------------------------
    EXAMPLE
    ------------------------------------------------------------------------
    import math
        tree_1 = {
            "root": ({"Yes":12, "No":8}, "x2"),
            "root->L": ({"Yes":9, "No":3}, "x1"),
            "root->R": ({"Yes":3, "No":5}, None),
            "root->L->R": ({"Yes":3, "No":2}, None),
            "root->L->L": ({"Yes":6, "No":1}, None),
        }

        tree_2 = {
            "root": ({"Yes":15, "No":5}, "x1"),
            "root->L": ({"Yes":10, "No":2}, None),
            "root->R": ({"Yes":5, "No":3}, "x2"),
            "root->R->L": ({"Yes":5, "No":3}, "x2"),
            "root->R->R": ({"Yes":5, "No":3}, "x2"),
        }

        tree_3 = {
            "root": ({"Yes":14, "No":6}, "x2"),
            "root->L": ({"Yes":8, "No":2}, None),
            "root->R": ({"Yes":6, "No":4}, None),
        }

        forest = {
            "Tree 1": tree_1,
            "Tree 2": tree_2,
            "Tree 3": tree_3,
        }

        tree_node_impurity(forest)

    ------------------------------------------------------------------------
    OUTPUT
    ------------------------------------------------------------------------
    Prints detailed impurity computation for each node, each ΔI(t, x_j) 
    for every split, and the final averaged variable importance across
    all trees in the forest. 

    Returns:
        None
    """
    
    # ---- Helper: pretty fraction strings ----
    def frac(a, b):
        return f"{a}/{b}"

    def sq_prob(a, b):
        return f"({a}/{b})^2"

    # ---- Helper: compute impurity with verbose symbolic + numeric print ----
    def compute_impurity_full(counts):
        total = sum(counts.values())

        terms_symbolic = []
        terms_numeric = []
        for k in counts.values():
            terms_symbolic.append(sq_prob(k, total))
            terms_numeric.append((k/total)**2)

        symbolic_line = "I(t) = 1 − [ " + " + ".join(terms_symbolic) + " ]"
        numeric_line = "      = 1 − [ " + " + ".join(f"{v:.4f}" for v in terms_numeric) + " ]"
        final_val = 1 - sum(terms_numeric)
        final_line = f"      = {final_val:.4f}"

        return symbolic_line + "\n" + numeric_line + "\n" + final_line, final_val

    # ---- MAIN COMPUTATION BEGINS ----
    all_imp = {}

    for tree_name, tree in forest.items():

        print(f"\n====================================================")
        print(f"                 TREE: {tree_name}")
        print(f"====================================================\n")

        # find children inside this single tree
        children = {}
        impurities = {}
        verbose = {}

        for node in tree:
            parts = node.split("->")
            if len(parts) > 1:
                parent = "->".join(parts[:-1])
                children.setdefault(parent, []).append(node)

        # compute impurity for each node
        for node, (counts, feature) in tree.items():
            txt, I = compute_impurity_full(counts)
            verbose[node] = txt
            impurities[node] = I

        # compute ΔI for each split
        var_imp = {}

        for parent in children:
            parent_counts, var = tree[parent]
            I_parent = impurities[parent]
            child_nodes = children[parent]

            print(f"Parent node {parent}:")
            print(verbose[parent], "\n")

            # equal weights
            w = 1 / len(child_nodes)
            weighted_child_sum = 0

            for child in child_nodes:
                print(f"Child node {child}:")
                print(verbose[child])
                print(f"Weight = 1/{len(child_nodes)} = {w:.4f}\n")

                weighted_child_sum += w * impurities[child]

            join_terms = " + ".join([f"{w:.4f}×I({child})" for child in child_nodes])

            print(f"ΔI({parent}, {var}) = I({parent}) − ( {join_terms} )")
            print(f"               = {I_parent:.4f} − ({weighted_child_sum:.4f})")
            Δ = I_parent - weighted_child_sum
            print(f"               = {Δ:.4f}\n")

            if var:
                var_imp.setdefault(var, []).append(Δ)

        # merge into forest-level dictionary
        for var, vals in var_imp.items():
            all_imp.setdefault(var, []).extend(vals)

    # ---- FINAL FOREST RESULTS ----
    print("\n====================================================")
    print("            FINAL FOREST AVERAGE IMPORTANCE")
    print("====================================================\n")

    for var, vals in all_imp.items():
        s = " + ".join(f"{v:.4f}" for v in vals)
        avg = sum(vals) / len(vals)
        print(f"{var}: avg Δ = ({s}) / {len(vals)} = {avg:.4f}")

    best = max(all_imp, key=lambda v: sum(all_imp[v])/len(all_imp[v]))
    print(f"\nIncrease in impurity due to predictor {best} is greater than others.")
    print(f"{best} → more important\n")
