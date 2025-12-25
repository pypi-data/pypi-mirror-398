import numpy as np
from scipy.optimize import approx_fprime
import pandas as pd

def conjugate_gradient_without_direction(f, x0, Theta, tol=1e-6, max_iter=100, verbose=True):
    """
    Conjugate Gradient Method (Without Predefined Directions)
    ---------------------------------------------------------
    Minimizes a quadratic function f(x) = 0.5 * x^T * Θ * x + b^T * x + c
    using the conjugate gradient algorithm.

    Parameters
    ----------
    f : callable
        Objective function f(x)
    x0 : array_like
        Initial guess vector
    Theta : ndarray
        Symmetric positive-definite matrix (for quadratic case)
    tol : float, optional
        Convergence tolerance on gradient norm (default: 1e-6)
    max_iter : int, optional
        Maximum number of iterations
    verbose : bool, optional
        Print iteration table

    Returns
    -------
    dict
        {
            "x_min": final x,
            "f_min": f(x_min),
            "iterations": total iterations,
            "converged": True/False,
            "iter_df": iteration DataFrame
        }

    Steps
    -----
    1. Initialize x₀, compute gradient g₀ = ∇f(x₀)
    2. Set search direction d₀ = -g₀
    3. For each iteration k:
        a. Compute step size αₖ = -(gₖᵀ dₖ) / (dₖᵀ Θ dₖ)
        b. Update xₖ₊₁ = xₖ + αₖ dₖ
        c. Compute new gradient gₖ₊₁ = ∇f(xₖ₊₁)
        d. Compute βₖ = (gₖ₊₁ᵀ gₖ₊₁) / (gₖᵀ gₖ)
        e. Update direction dₖ₊₁ = -gₖ₊₁ + βₖ dₖ
        f. Stop if ||gₖ₊₁|| < tol

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

    ===================== R Code =====================
    conjugate_gradient_without_direction = function(f, x0, Theta, tol = 1e-6, max_iter = 100) {
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
  x = as.numeric(x0) ; g = grad_f(x) ; d = -g
  
  cat("Iter |     α      |     β      |   x-values   |   f(x)   | ||grad||\n")
  cat("-----------------------------------------------------------------\n")
  
  for (k in 1:max_iter) {
    grad_norm = sqrt(sum(g^2))
    if (grad_norm < tol) {
      cat("Converged at iteration", k, "\n")
      break
    }
    alpha = -sum(g * d) / sum(d * (Theta %*% d))
    x_new = x + alpha * d ; g_new = grad_f(x_new)
    beta = sum(g_new * g_new) / sum(g * g)
    d_new = -g_new + beta * d
    
    cat(sprintf("%4d | %9.6f | %9.6f | %8.4f %8.4f | %8.4f | %8.6f\n",
                k, alpha, beta, x_new[1], x_new[2], f(x_new), grad_norm))
    
    # Update
    x = x_new
    g = g_new
    d = d_new
  }
  return(list(
    x_min = x,
    f_min = f(x),
    iterations = k
  ))
}

# Example 
# ----------------
Theta = matrix(c(4, 1, 1, 3), 2, 2)
b = c(-1, -2)
f = function(x) 0.5 * t(x) %*% Theta %*% x + sum(b * x)
res = conjugate_gradient_without_direction(f, c(0, 0), Theta)
cat("\nMinimum point:", res$x_min, "\n")
cat("Minimum value:", res$f_min, "\n")


    """

    def grad_f(x, h=1e-8):
        return approx_fprime(np.array(x), f, h)

    x = np.array(x0, dtype=float)
    g = grad_f(x)
    d = -g
    iter_data = []
    converged = False

    for k in range(1, max_iter + 1):
        if np.linalg.norm(g) < tol:
            converged = True
            break

        alpha = -np.dot(g, d) / np.dot(d, Theta @ d)
        x_new = x + alpha * d
        g_new = grad_f(x_new)
        beta = np.dot(g_new, g_new) / np.dot(g, g)
        d_new = -g_new + beta * d

        iter_data.append({
            "iter": k,
            "alpha_k": round(alpha, 6),
            "beta_k": round(beta, 6),
            "grad_norm": round(np.linalg.norm(g_new), 6),
            **{f"x{i+1}": round(val, 6) for i, val in enumerate(x_new)},
            "f_val": round(f(x_new), 6)
        })

        x, g, d = x_new, g_new, d_new

    df = pd.DataFrame(iter_data)
    if verbose:
        print(df)

    return {
        "x_min": x,
        "f_min": f(x),
        "iterations": len(df),
        "converged": converged,
        "iter_df": df
    }