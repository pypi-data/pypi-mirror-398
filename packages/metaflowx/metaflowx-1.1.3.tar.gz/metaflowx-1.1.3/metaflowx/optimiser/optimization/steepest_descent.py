import numpy as np
import pandas as pd
from scipy.optimize import approx_fprime, minimize_scalar

def numerical_gradient(f, x, h=1e-8):
    x = np.array(x, dtype=float)
    return approx_fprime(x, f, h)

def steepest_descent(
    f,
    x0,
    tol=1e-4,
    max_iter=1000,
    alpha=None,
    verbose=True
):
   
   
    """
    ==================== HELP ==========================
    Steepest Descent Optimization with Exact Line Search
    ============ Algorithm Steps =======
    Step 1: Initialize
        Choose a starting point x₀ and set iteration counter k = 0.
    
    Step 2: Compute Gradient
        Evaluate the gradient gₖ = ∇f(xₖ).
        If ||gₖ|| < tol, stop — convergence achieved.

    Step 3: Compute Step Size (Line Search)
        - If alpha is None:
              Perform exact line search:
              αₖ = argmin_{α ≥ 0} f(xₖ - α ∇f(xₖ))
        - Else:
              Use fixed step size αₖ = alpha.
        
        For a quadratic function f(x) = ½xᵀΘx − bᵀx,
        the optimal step size is:
              αₖ = (gₖᵀgₖ) / (gₖᵀΘgₖ)

    Step 4: Update Rule
        Update the current point:
              xₖ₊₁ = xₖ − αₖ ∇f(xₖ)

    Step 5: Repeat
        Increment k ← k + 1 and return to Step 2 
        until convergence (||∇f(xₖ)|| < tol) or max_iter is reached.
    
    ================== Mathematical Summary ===================
        Update equation:  xₖ₊₁ = xₖ − αₖ ∇f(xₖ)
        Convergence condition: ||∇f(xₖ)|| < tol
    
    =====================  Parameters =====================
    f : function
        Objective function to minimize.
    x0 : array-like
        Initial point (starting guess).
    tol : float, optional (default=1e-4)
        Convergence tolerance based on gradient norm.
    max_iter : int, optional (default=1000)
        Maximum allowed iterations.
    alpha : float or None, optional (default=None)
        Fixed step size. If None, performs exact line search.
    verbose : bool, optional (default=True)
        If True, prints iteration progress.

    ------------------------------------------------------------
    Returns
    ------------------------------------------------------------
    result : dict
        Contains:
        - x_min: Estimated minimizer (final point)
        - f_min: Function value at minimizer
        - iterations: Number of iterations
        - converged: Whether convergence was achieved
        - history: List of iteration records (x, f(x), gradient norm, step size)

    ------------------------------------------------------------
    Example 1: Simple Quadratic Function
    ------------------------------------------------------------
    >>> import numpy as np
    >>> def f(x):
    ...     return 0.5 * x.T @ np.array([[3, 1], [1, 2]]) @ x - np.array([1, 1]).T @ x
    >>> def grad_f(x):
    ...     return np.array([[3, 1], [1, 2]]) @ x - np.array([1, 1])
    >>> result = steepest_descent(f, x0=[0, 0], tol=1e-6, verbose=True)
    >>> print("x_min:", result["x_min"])
    >>> print("f_min:", result["f_min"])

    ------------------------------------------------------------
    Example 2: Non-Quadratic Function (e.g., Rosenbrock)
    ------------------------------------------------------------
    >>> def rosenbrock(x):
    ...     return (1 - x[0])**2 + 100 * (x[1] - x[0]**2)**2
    >>> def grad_rosenbrock(x):
    ...     return np.array([
    ...         -2*(1 - x[0]) - 400*x[0]*(x[1] - x[0]**2),
    ...         200*(x[1] - x[0]**2)
    ...     ])
    >>> result = steepest_descent(rosenbrock, x0=[-1.2, 1.0], tol=1e-6)
    >>> print("x_min:", result["x_min"])
    >>> print("f_min:", result["f_min"])

    ------------------------------------------------------------
    Example : Sample R Code
    ------------------------------------------------------------
    rm(list=ls())
    steepest_descent = function(A, b, initial_point = c(0,0), tol = 1e-4, max_iter = 10) {
    x = initial_point
    for (k in 1:max_iter) {
        gradient = A %*% x - b
        if (sqrt(sum(gradient^2)) < tol) break
        alpha = drop(t(gradient) %*% gradient) / drop(t(gradient) %*% A %*% gradient)
        f_val = 0.5 * t(x) %*% A %*% x - t(b) %*% x
        cat(sprintf("Iter %d: x = (%.6f, %.6f), f(x) = %.6f, alpha = %.6f\n",
                k, x[1], x[2], f_val, alpha))
        x = x - alpha * gradient
        }
        cat(sprintf("\nFinal x = (%.6f, %.6f)\nFinal f(x) = %.6f\n",
              x[1], x[2], 0.5 * t(x) %*% A %*% x - t(b) %*% x))
    }
    # Example
    A = matrix(c(3, 1, 1, 2), 2, 2)
    b = c(1, 1)
    steepest_descent(A, b, c(0, 0))
    """ 
    x = np.array(x0, dtype=float)
    records = []

    for k in range(1, max_iter + 1):
        grad = numerical_gradient(f, x)
        grad_norm = np.linalg.norm(grad)
        f_val = f(x)

        # Record current iteration info
        record = {
            "iter": k,
            "x1": x[0],
            "x2": x[1] if len(x) > 1 else np.nan,
            "f(x)": f_val,
            "||grad||": grad_norm
        }

        # Check convergence
        if grad_norm < tol:
            records.append(record)
            break

        # Line search or fixed step size
        if alpha is None:
            line_search_fn = lambda a: f(x - a * grad)
            res = minimize_scalar(line_search_fn, bounds=(0, 1), method='bounded')
            alpha_k = res.x
        else:
            alpha_k = alpha

        # Update position
        x = x - alpha_k * grad
        record["alpha"] = alpha_k
        records.append(record)

    # Add clean final info row (no NaN alpha)
    records.append({
        "iter": "Final",
        "x1": x[0],
        "x2": x[1] if len(x) > 1 else np.nan,
        "f(x)": f(x),
        "||grad||": np.linalg.norm(numerical_gradient(f, x)),
        "alpha": alpha_k if 'alpha_k' in locals() else np.nan
    })

    # Return DataFrame only (no print)
    return pd.DataFrame(records)