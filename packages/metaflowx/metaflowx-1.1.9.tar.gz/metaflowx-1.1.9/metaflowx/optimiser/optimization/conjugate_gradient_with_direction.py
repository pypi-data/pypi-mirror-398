import numpy as np
from scipy.optimize import approx_fprime
import pandas as pd
def conjugate_gradient_with_direction(f, x0, directions, Theta=None, tol=1e-6, verbose=True):
    """
    Conjugate Gradient Method (With Predefined Directions)
    ------------------------------------------------------
    Minimizes a function when specific conjugate directions are given.

    Parameters
    ----------
    f : callable
        Objective function f(x)
    x0 : array_like
        Initial point
    directions : list of array_like
        Predefined conjugate directions [d₁, d₂, ...]
    Theta : ndarray, optional
        Quadratic matrix (if available for exact α computation)
    tol : float, optional
        Convergence tolerance on gradient norm
    verbose : bool, optional
        Print iteration table

    Returns
    -------
    dict
        {
            "x_min": final x,
            "f_min": f(x_min),
            "iterations": len(directions),
            "iter_df": iteration DataFrame
        }

    Steps
    -----
    1. Start from x₀
    2. For each direction dₖ:
        a. Compute step size αₖ
           - If Θ known: αₖ = -(∇f(xₖ)ᵀ dₖ) / (dₖᵀ Θ dₖ)
           - Else: perform a line search
        b. Update xₖ₊₁ = xₖ + αₖ dₖ
        c. Check convergence (||∇f(xₖ₊₁)|| < tol)

    Example
    --------
    >>> # Define quadratic function
    >>> import numpy as np
    >>> from scipy.optimize import approx_fprime
    >>> import pandas as pd
    >>> Theta = np.array([[4, 1], [1, 3]])
    >>> b = np.array([-1, -2])
    >>> f = lambda x: 0.5 * x @ Theta @ x + b @ x
    >>> # Case 1: Without directions
    >>> res1 = conjugate_gradient_without_direction(f, x0=[0, 0], Theta=Theta)
    >>> print(" Without directions:", res1["x_min"])
    >>> # Case 2: With predefined directions
    >>> dirs = [np.array([-1, 0]), np.array([0, -1])]
    >>> res2 = conjugate_gradient_with_direction(f, x0=[0, 0], Theta=Theta, directions=dirs)
    >>> print(" With directions:", res2["x_min"])

    ===================================== R Code =============================
    conjugate_gradient_with_direction = function(f, x0, directions, Theta = NULL, tol = 1e-6, max_iter = NULL) {
  
  # Numerical gradient (central difference)
  grad_f = function(x, h = 1e-8) {
    n = length(x)
    grad = numeric(n)
    for (i in 1:n) {
      x1 = x2 = x
      x1[i] = x[i] + h
      x2[i] = x[i] - h
      grad[i] = (f(x1) - f(x2)) / (2 * h)
    }
    grad
  }
  # Simple backtracking line search
  line_search = function(f, x, d, grad, alpha_init = 1.0, rho = 0.5, c = 1e-4) {
    alpha = alpha_init
    fx = f(x)
    while (f(x + alpha * d) > fx + c * alpha * sum(grad * d)) {
      alpha = alpha * rho
      if (alpha < 1e-10) break
    }
    return(alpha)
  }
  # Initialization
  x = as.numeric(x0)
  grad = grad_f(x)
  n_iter = if (is.null(max_iter)) length(directions) else max_iter
  
  cat("Iter |     α      |   x-values   |   f(x)   | ||grad||\n")
  cat("------------------------------------------------------\n")
  
  for (k in 1:n_iter) {
    d = as.numeric(directions[[k]])
    # Compute step size
    if (!is.null(Theta)) {
      alpha = -sum(grad * d) / sum(d * (Theta %*% d))
    } else {
      alpha = line_search(f, x, d, grad)
    }
    # Update
    x_new = x + alpha * d
    grad_new = grad_f(x_new)
    cat(sprintf("%4d | %9.6f | %8.4f %8.4f | %8.4f | %8.6f\n",
                k, alpha, x_new[1], x_new[2], f(x_new), sqrt(sum(grad_new^2))))
    
    if (sqrt(sum(grad_new^2)) < tol) {
      cat("Converged at iteration", k, "\n")
      break
    }
    x = x_new
    grad = grad_new
  }
  return(list(
    x_min = x,
    f_min = f(x),
    iterations = k
  ))
}
# Example
# ------------------------------
Theta = matrix(c(4, 1, 1, 3), 2, 2)
b = c(-1, -2)
f = function(x) 0.5 * t(x) %*% Theta %*% x + sum(b * x)
# Predefined conjugate directions
dirs = list(c(-1, 0), c(0, -1))
# Run method
res2 = conjugate_gradient_with_direction(f, x0 = c(0, 0), Theta = Theta, directions = dirs)
cat("\nMinimum point:", res2$x_min, "\n")
cat("Minimum value:", res2$f_min, "\n")

    """

    def grad_f(x, h=1e-8):
        return approx_fprime(np.array(x), f, h)

    def line_search(f, x, d, grad, alpha_init=1.0, rho=0.5, c=1e-4):
        alpha = alpha_init
        fx = f(x)
        while f(x + alpha * d) > fx + c * alpha * np.dot(grad, d):
            alpha *= rho
            if alpha < 1e-10:
                break
        return alpha

    x = np.array(x0, dtype=float)
    grad = grad_f(x)
    iter_data = []

    for k, d in enumerate(directions, 1):
        d = np.array(d, dtype=float)

        if Theta is not None:
            alpha = -np.dot(grad, d) / np.dot(d, Theta @ d)
        else:
            alpha = line_search(f, x, d, grad)

        x_new = x + alpha * d
        grad_new = grad_f(x_new)

        iter_data.append({
            "iter": k,
            "alpha_k": round(alpha, 6),
            "grad_norm": round(np.linalg.norm(grad_new), 6),
            **{f"x{i+1}": round(val, 6) for i, val in enumerate(x_new)},
            "f_val": round(f(x_new), 6)
        })

        if np.linalg.norm(grad_new) < tol:
            break

        x, grad = x_new, grad_new

    df = pd.DataFrame(iter_data)
    if verbose:
        print(df)

    return {
        "x_min": x,
        "f_min": f(x),
        "iterations": len(df),
        "iter_df": df
    }
