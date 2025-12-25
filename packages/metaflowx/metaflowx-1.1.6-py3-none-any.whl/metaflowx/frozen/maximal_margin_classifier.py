def maximal_margin_classifier():
    """
    Print a step-by-step derivation of the maximal margin classifier (hard-margin SVM)
    for a simple, linearly separable 2D toy dataset.

    This does NOT rely on scikit-learn or any optimization library.
    Its purpose is *pedagogical*: to show how the maximal margin classifier is
    defined and developed from first principles.

    Toy dataset:
        Class +1: (2, 3), (3, 3)
        Class -1: (-2, 1), (-3, 2)

    Notation follows the standard:
        - Training data: (x_i, y_i),  i = 1,...,n
        - x_i ∈ R^p, here p = 2
        - y_i ∈ {+1, -1}
        - Hyperplane: f(x) = β0 + β^T x = 0
        - β = (β1, β2)^T
        - Margin: M
    """

    # 1. Toy data
    print("=" * 80)
    print("STEP 1: Define a simple linearly separable training set")
    print("=" * 80)

    X_pos = [(2, 3), (3, 3)]     # Class +1
    X_neg = [(-2, 1), (-3, 2)]   # Class -1

    print("\nClass +1 points:")
    for x in X_pos:
        print(f"  x = {x}")
    print("Class -1 points:")
    for x in X_neg:
        print(f"  x = {x}")

    print("\nWe will denote:")
    print("  x1 = (2, 3)^T,   y1 = +1")
    print("  x2 = (3, 3)^T,   y2 = +1")
    print("  x3 = (-2, 1)^T,  y3 = -1")
    print("  x4 = (-3, 2)^T,  y4 = -1")

    # 2. Hyperplane definition
    print("\n" + "=" * 80)
    print("STEP 2: Define the separating hyperplane in R^2")
    print("=" * 80)

    print("""
We use the standard form of a hyperplane:

    f(x) = β0 + β1 * x1 + β2 * x2 = 0

In vector notation:
    x = (x1, x2)^T
    β = (β1, β2)^T

so
    f(x) = β0 + β^T x

Classification rule:
    if f(x) > 0  ⇒  predict class +1
    if f(x) < 0  ⇒  predict class -1
""")

    # 3. Separating hyperplane constraints
    print("=" * 80)
    print("STEP 3: Express perfect separation using y_i f(x_i) > 0")
    print("=" * 80)

    print("""
For each training point (x_i, y_i), perfect separation means:

    y_i * f(x_i) > 0

That is:
    - If y_i = +1, we need f(x_i) > 0
    - If y_i = -1, we need f(x_i) < 0

This guarantees that every point is on the correct side of the hyperplane.

We will now strengthen this condition to enforce a MARGIN.
""")

    # 4. Margin and normalization
    print("=" * 80)
    print("STEP 4: Define the margin and normalize β")
    print("=" * 80)

    print(r"""
Geometric idea:
    The distance of x_i from the hyperplane f(x) = 0 is

        dist(x_i, hyperplane) = |β0 + β^T x_i| / ||β||

For classification, we also care about the sign of f(x_i), so we use
the signed distance:

        signed_dist(x_i) = y_i * (β0 + β^T x_i) / ||β||

The MARGIN M is defined as the minimum signed distance among all training
points:

        M = min_i  [ y_i * (β0 + β^T x_i) / ||β|| ]

To make the optimization cleaner, we impose a scaling constraint:

        ||β|| = 1

Under this normalization, the margin simplifies to:

        M = min_i  [ y_i * (β0 + β^T x_i) ]

So we want to choose β0 and β to make this minimum as large as possible.
""")

    # 5. Maximal margin optimization (max form)
    print("=" * 80)
    print("STEP 5: Set up the maximal margin problem (maximization form)")
    print("=" * 80)

    print(r"""
We introduce an explicit margin variable M and write:

    Maximize   M
    Subject to
        ||β|| = 1
        y_i * (β0 + β^T x_i) ≥ M   for all i

This means:
    - Every point is at least M units away from the hyperplane
      (in the signed sense).
    - We search for the largest possible M.
""")

    # 6. Standard SVM formulation (minimize ||β||^2 with margin = 1)
    print("=" * 80)
    print("STEP 6: Convert to the standard hard-margin SVM formulation")
    print("=" * 80)

    print(r"""
An equivalent and more common formulation rescales (β0, β, M) so that
the functional margin becomes 1. We enforce:

        y_i * (β0 + β^T x_i) ≥ 1   for all i

Under this convention, the margin in geometric terms is:

        geometric_margin = 1 / ||β||

So maximizing the geometric margin is equivalent to minimizing ||β||.

We obtain the standard primal hard-margin SVM problem:

    Minimize    (1/2) * ||β||^2
    Subject to  y_i * (β0 + β^T x_i) ≥ 1   for all i

Here:
    - (1/2) * ||β||^2 is the objective to be minimized.
    - The constraints enforce correct classification with margin at least 1.
""")

    # 7. Apply to our toy dataset: explicitly write constraints
    print("=" * 80)
    print("STEP 7: Write the constraints for the toy dataset explicitly")
    print("=" * 80)

    print("""
For our 4 points:

  1) x1 = (2, 3)^T,  y1 = +1:
       y1 * (β0 + β1 * 2 + β2 * 3) ≥ 1
    ⇒  β0 + 2β1 + 3β2 ≥ 1

  2) x2 = (3, 3)^T,  y2 = +1:
       β0 + 3β1 + 3β2 ≥ 1

  3) x3 = (-2, 1)^T, y3 = -1:
       y3 * (β0 + β1 * (-2) + β2 * 1) ≥ 1
    ⇒  -[β0 - 2β1 + β2] ≥ 1
    ⇒  -β0 + 2β1 - β2 ≥ 1

  4) x4 = (-3, 2)^T, y4 = -1:
       y4 * (β0 + β1 * (-3) + β2 * 2) ≥ 1
    ⇒  -[β0 - 3β1 + 2β2] ≥ 1
    ⇒  -β0 + 3β1 - 2β2 ≥ 1

Optimization problem becomes:

    Minimize    (1/2) * (β1^2 + β2^2)
    Subject to
        β0 + 2β1 + 3β2 ≥ 1
        β0 + 3β1 + 3β2 ≥ 1
       -β0 + 2β1 - β2 ≥ 1
       -β0 + 3β1 - 2β2 ≥ 1
""")

    # 8. Conceptual solution structure
    print("=" * 80)
    print("STEP 8: Conceptual understanding of the solution")
    print("=" * 80)

    print("""
A quadratic optimization solver would find (β0, β1, β2) that:

    - Satisfies all 4 inequalities
    - Minimizes (1/2)(β1^2 + β2^2)

The points that become tight in the solution (i.e. for which
    y_i * (β0 + β^T x_i) = 1
) are the SUPPORT VECTORS.

Only these support vectors determine the final maximal margin hyperplane.
All other points could move slightly without changing the solution.
""")

    # 9. Summary
    print("=" * 80)
    print("STEP 9: Summary of the development of the maximal margin classifier")
    print("=" * 80)

    print("""
1. Assume linearly separable data with labels y_i ∈ {+1, -1}.
2. Choose a hyperplane f(x) = β0 + β^T x.
3. Define signed distance and margin using y_i * f(x_i) / ||β||.
4. Normalize β (or equivalently fix functional margin = 1).
5. Set up the optimization:

       Minimize    (1/2) * ||β||^2
       Subject to  y_i * (β0 + β^T x_i) ≥ 1  ∀ i.

6. Solve this quadratic program → obtain β0, β.
7. Classify any new point x* using sign(β0 + β^T x*).

This is the maximal margin classifier (hard-margin SVM),
developed fully from its geometric definition.
""")

    print("=" * 80)
    print("End of gen_maximal_margin_classifier() demonstration")
    print("=" * 80)
