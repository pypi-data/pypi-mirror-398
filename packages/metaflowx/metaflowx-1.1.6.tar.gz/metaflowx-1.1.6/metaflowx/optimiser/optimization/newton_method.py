import autograd.numpy as np
from autograd import grad, hessian
from numpy.linalg import inv, det, norm

def newton_method(f, x0, tol=1e-6, max_iter=100, verbose=True):
    """
    ==========================================================
    Newton's Method is a second-order optimization algorithm designed to
    find a local minimum of a twice-differentiable scalar function f(x).

    ------------------------------------------------------------------
    Algorithmic Steps:
    ------------------------------------------------------------------
    Step 1 : Initialization
        Choose a starting point x₀ ∈ ℝⁿ.
    
    Step 2 : Local Quadratic Approximation
        Approximate f(x) near xₖ using a 2nd-order Taylor expansion:
            f(x) ≈ f(xₖ) + ∇f(xₖ)ᵀ(x - xₖ) + ½(x - xₖ)ᵀH(xₖ)(x - xₖ)

    Step 3 : Set derivative to zero to minimize the local model
        Solving ∇f(xₖ) + H(xₖ)(x - xₖ) = 0 gives:
            x = xₖ - H(xₖ)⁻¹ ∇f(xₖ)
        → This is the **Newton update rule**.

    Step 4 : Iterative Update
        Repeat:
            xₖ₊₁ = xₖ - H(xₖ)⁻¹ ∇f(xₖ)
        until convergence.

    Step 5 : Convergence Check
        Stop when:
            ||∇f(xₖ)|| < tol
        or maximum iterations reached.

    Step 6 : Convergence Behavior
        - Near the true minimum, convergence is **quadratic**:
              ||xₖ₊₁ - x*|| ≤ C * ||xₖ - x*||²
        - However, it may diverge if the Hessian is not positive definite
          or if the initial guess is far from the minimum.

    ------------------------------------------------------------------
    Implementation Details:
    ------------------------------------------------------------------
    • Gradient (∇f) and Hessian (H) are computed automatically using `autograd`.
    • Handles n-dimensional functions.
    • Verbose mode prints iteration details (x, f(x), grad norm).
    • Iteration history is stored for analysis.

    ------------------------------------------------------------------
    Parameters
    ----------
    f : callable
        Objective function to minimize.
    x0 : array_like
        Initial guess for the minimum (1D vector).
    tol : float, optional
        Convergence threshold based on gradient norm (default = 1e-6).
    max_iter : int, optional
        Maximum number of iterations (default = 100).
    verbose : bool, optional
        If True, prints progress (default = True).

    ------------------------------------------------------------------
    Returns
    -------
    dict
        {
            "x_min": estimated minimizer,
            "f_min": function value at the minimum,
            "iterations": total iterations used,
            "converged": True/False,
            "iter_df": iteration history (list of dicts)
        }

    ------------------------------------------------------------------
    Example
    -------
    >>> !pip install autograd
    >>> import autograd.numpy as np
    >>> from autograd import grad, hessian
    >>> from numpy.linalg import inv, det, norm
    >>> f = lambda x: x[0]**2 + x[1]**2 + 2*x[1] + 4
    >>> res = newton_method(f, x0=[2, 1], verbose=True)

   ------------------------------------------------------------------
    R Code
    -------
    newton_method = function(f, x0, tol = 1e-6, max_iter = 100) {
    x = as.numeric(x0)
    for (k in 1:max_iter) {
        g = numDeriv::grad(f, x)
        H = numDeriv::hessian(f, x)
        cat("Iter", k,": x =", paste(round(x, 6), collapse = ", "),"| f(x) =", round(f(x), 6),"| grad =", paste(round(g, 6), collapse = ", "), "\n")
    if (sqrt(sum(g^2)) < tol) break
    if (det(H) == 0) stop("Hessian is singular.")
    x = x - solve(H, g)
    }
    cat(" Result → x_min =", paste(round(x, 6), collapse = ", "),"| f_min =", round(f(x), 6))}
    # Example
    f = function(x) x[1]^2 + x[2]^2 + 2*x[2] + 4
    newton_method(f, x0 = c(2, 1))
    """

    # Initialize
    x = np.asarray(x0, dtype=float)
    grad_f = grad(f)
    hess_f = hessian(f)
    converged = False
    iter_details = []

    # Iterative optimization loop
    for k in range(1, max_iter + 1):
        g = grad_f(x)
        g_norm = norm(g)
        if g_norm < tol:
            converged = True
            break

        H = hess_f(x)
        if det(H) == 0:
            raise ValueError(f"Hessian is singular at iteration {k}")

        # Newton step
        x = x - inv(H).dot(g)

        iter_details.append({
            "Iteration": k,
            "x": x.copy(),
            "grad_norm": g_norm,
            "f_x": f(x)
        })

    # Result summary
    result = {
        "x_min": x,
        "f_min": f(x),
        "iterations": len(iter_details),
        "converged": converged,
        "iter_df": iter_details
    }

    # Verbose output
    if verbose and iter_details:
        print("x_min:", np.round(result["x_min"], 6))
        print("f_min:", round(result["f_min"], 6))
        print("Iterations:", result["iterations"])
        print("Converged:", result["converged"], "\n")
        print("Iteration history:")
        for row in iter_details:
            print(row)

    return result