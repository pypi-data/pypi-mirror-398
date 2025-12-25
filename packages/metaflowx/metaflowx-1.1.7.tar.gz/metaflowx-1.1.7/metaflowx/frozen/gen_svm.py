def gen_svm():
    """
    Develop the full Support Vector Machine (SVM) from scratch (conceptually).
    Prints every major step:
        • Hard-margin (maximal margin) recap
        • Problems with separability
        • Soft-margin SVM (slack variables + C)
        • Primal → Dual transformation
        • Kernel trick
        • Final SVM decision function
    This is a teaching function, not a numerical solver.
    """

    print("="*90)
    print("STEP 1: STARTING POINT — HARD-MARGIN MAXIMAL MARGIN CLASSIFIER")
    print("="*90)
    print(r"""
Given training data (x_i, y_i),  y_i ∈ {+1, -1}, the hard-margin classifier requires:

        y_i (β0 + β^T x_i) ≥ 1       for all i

Objective:
        Minimize   (1/2)‖β‖²

This finds the hyperplane with the largest geometric margin:
        margin = 1 / ‖β‖
    
But this ONLY works when the data is perfectly separable.
If any point violates the constraint, the optimization collapses.
""")

    print("="*90)
    print("STEP 2: WHY HARD-MARGIN FAILS")
    print("="*90)
    print(r"""
Real datasets are messy. Overlap, noise, outliers → perfect separation rarely exists.

Hard-margin tries to force perfection → becomes extremely sensitive.

This motivates SOFT-MARGIN SVM.
""")

    print("="*90)
    print("STEP 3: SOFT-MARGIN SVM WITH SLACK VARIABLES ξ_i")
    print("="*90)
    print(r"""
Introduce slack ξ_i ≥ 0 to allow controlled violations of the margin:

        y_i(β0 + β^T x_i) ≥ 1 - ξ_i

Interpretation:
    ξ_i = 0   → correctly classified, outside margin  
    0 < ξ_i ≤ 1 → inside margin but correct  
    ξ_i > 1  → misclassified  

Budget for total violation:
        Σ ξ_i ≤ C

Soft-margin objective:

        Minimize   (1/2)‖β‖²  + C Σ ξ_i

C = tuning parameter controlling strictness:
    Large C → strict, smaller margin, low bias, high variance
    Small C → tolerant, wider margin, high bias, low variance
""")

    print("="*90)
    print("STEP 4: PRIMAL → DUAL TRANSFORMATION")
    print("="*90)
    print(r"""
Convert the constrained optimization into its dual using Lagrange multipliers α_i.

Dual problem:

    Maximize
            Σ α_i  -  (1/2) Σ Σ α_i α_j y_i y_j (x_i · x_j)

    Subject to:
            0 ≤ α_i ≤ C
            Σ α_i y_i = 0

Important:
    Only points with α_i > 0 become SUPPORT VECTORS.
    All others have α_i = 0 and do NOT affect the boundary.

Recovered classifier:

        f(x) = β0 + Σ α_i y_i (x_i · x)
""")

    print("="*90)
    print("STEP 5: LIMITATION OF LINEAR SVM — CANNOT HANDLE NONLINEAR BOUNDARIES")
    print("="*90)
    print(r"""
If classes are not linearly separable in original space, no linear hyperplane helps.

We need nonlinear features: x1, x2, x1², x2², x1x2, ...

But explicitly computing high-dimensional φ(x) is expensive.

SOLUTION → KERNEL TRICK.
""")

    print("="*90)
    print("STEP 6: KERNEL TRICK — WHY WE USE IT AND HOW IT WORKS")
    print("="*90)
    print(r"""
Linear SVM only finds a straight hyperplane in the original feature space.
If the classes are arranged in a nonlinear pattern, no linear boundary
can separate them.

Classical solution:
        Transform x → φ(x)
        (map each point into a higher-dimensional feature space)

In higher dimensions, many patterns that were inseparable in the original
space become linearly separable. For example:
    • Two concentric circles cannot be separated in 2D,
      but become linearly separable after mapping to 3D.
    • XOR pattern is not separable in original space,
      but becomes separable after adding interaction terms.

Problem:
        Explicitly computing φ(x) may require thousands or millions of
        dimensions → computationally infeasible.

Kernel Trick:
        Replace the inner product φ(x_i)^T φ(x_j) with a kernel function:

                K(x_i, x_j) = φ(x_i)^T φ(x_j)

Key insight:
        We never compute φ(x) explicitly.
        We only compute the inner product in the transformed space.

This allows SVM to operate in an extremely high (even infinite)
dimensional feature space while performing all calculations in the
original input space.

Common kernels:
    Linear Kernel:      K(x,z) = x^T z
    Polynomial Kernel:  K(x,z) = (1 + x^T z)^d
    RBF Kernel:         K(x,z) = exp(-γ ||x - z||²)
        (corresponds to an infinite-dimensional φ(x))

With the kernel trick, the dual SVM classifier becomes:

        f(x) = β0 + Σ α_i y_i K(x_i, x)

This allows SVM to form highly flexible, nonlinear decision boundaries
without ever computing the high-dimensional mapping explicitly.
""")


    print("="*90)
    print("END OF gen_svm() — COMPLETE SVM DEVELOPMENT FROM SCRATCH")
    print("="*90)