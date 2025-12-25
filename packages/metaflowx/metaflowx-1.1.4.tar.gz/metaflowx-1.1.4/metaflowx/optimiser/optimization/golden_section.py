import numpy as np
import pandas as pd

def golden_section(f, a, b, tol=1e-6, max_iter=100, verbose=True):
    """
    Golden Section Search Optimization
    ----------------------------------
    The **Golden Section Search (GSS)** is a **classical first-order-free optimization algorithm**
    for finding a **local minimum** of a **1-dimensional scalar function**. It is particularly efficient
    because it reduces the interval of uncertainty using the **golden ratio** (φ).

    The algorithm maintains an interval [a, b] containing the minimum and successively evaluates
    the function at points inside the interval, discarding subintervals that cannot contain the minimum.
    The key ratio φ = (sqrt(5) - 1)/2 ≈ 0.618 ensures minimal function evaluations at each iteration.

    **Update Rules:**
        x1 = b - φ (b - a)
        x2 = a + φ (b - a)

    Evaluate f(x1) and f(x2), then reduce the interval based on which side has the larger function value.
    Repeat until (b - a) < tol or maximum iterations reached.

    Parameters
    ----------------
    f : callable
        Function to minimize. Must take a scalar input and return a scalar output.
    a : float
        Left bound of the initial interval [a, b].
    b : float
        Right bound of the initial interval [a, b].
    tol : float, optional
        Convergence tolerance for interval length. Default is 1e-6.
    max_iter : int, optional
        Maximum number of iterations. Default is 100.
    verbose : bool, optional
        If True, prints iteration details. Default is True.

    Returns
    -----------------
    result : dict
        A dictionary containing:
        - x_min : Estimated minimum point.
        - f_min : Function value at the minimum.
        - iterations : Number of iterations executed.
        - converged : Boolean flag indicating successful convergence.
        - iter_df : pandas.DataFrame containing iteration history with columns:
            ['Iteration', 'a', 'b', 'x1', 'x2', 'f_x1', 'f_x2'].

    Notes
    ---------------
    The **Golden Ratio Constant**:
        φ = (√5 - 1) / 2 ≈ 0.618

    Each iteration reduces the interval length by approximately 61.8%, achieving
    efficient convergence with minimal function evaluations.

    Example
    -------
    >>> import numpy as np
    >>> f = lambda x: (x - 2)**2
    >>> result = golden_section(f, 0, 5)
    >>> print(result["x_min"], result["f_min"])

    ======================== R Code ============================
    golden_section <- function(f, a, b, tol = 1e-6, max_iter = 100) {
    phi <- (sqrt(5) - 1) / 2
    x1 <- b - phi * (b - a)
    x2 <- a + phi * (b - a)
    f1 <- f(x1)
    f2 <- f(x2)
    i <- 0
    while ((b - a) > tol && i < max_iter) {
    i <- i + 1
    cat("Iter", i, 
        ": a=", round(a,6), 
        "b=", round(b,6), 
        "x1=", round(x1,6), "f(x1)=", round(f1,6), 
        "x2=", round(x2,6), "f(x2)=", round(f2,6), "\n")
    
    if (f1 < f2) {
      b <- x2; x2 <- x1; f2 <- f1
      x1 <- b - phi * (b - a); f1 <- f(x1)
    } else {
      a <- x1; x1 <- x2; f1 <- f2
      x2 <- a + phi * (b - a); f2 <- f(x2)
    }
  }
  
    x_min <- (a + b) / 2
    cat("\nMinimum at x =", round(x_min,6), "f(x) =", round(f(x_min),6), "\n")
    }

    ==================== Example: =====================================
    f = function(x) (x - 2)^2
    golden_section(f, 0, 5)
    """

    # Golden ratio constant
    phi = (np.sqrt(5) - 1) / 2

    # Ensure numerical stability for tolerance
    tol = max(tol, 10 * np.finfo(float).eps)

    # Store iteration data
    iter_data = []

    # Initial test points
    x1 = b - phi * (b - a)
    x2 = a + phi * (b - a)
    f_x1 = f(x1)
    f_x2 = f(x2)
    iter_count = 0
    converged = False
    # Iterative interval reduction
    while (b - a) > tol and iter_count < max_iter:
        iter_count += 1
        # Log current state
        iter_data.append([iter_count, a, b, x1, x2, f_x1, f_x2])
        # Determine which side to discard
        if f_x1 < f_x2:
            b = x2
            x2 = x1
            f_x2 = f_x1
            x1 = b - phi * (b - a)
            f_x1 = f(x1)
        else:
            a = x1
            x1 = x2
            f_x1 = f_x2
            x2 = a + phi * (b - a)
            f_x2 = f(x2)

        # Optional iteration printout
        if verbose:
            print(f"Iter {iter_count:3d} | "
                  f"a = {a:.6f}, b = {b:.6f} | "
                  f"x1 = {x1:.6f}, f(x1) = {f_x1:.6f} | "
                  f"x2 = {x2:.6f}, f(x2) = {f_x2:.6f}")

    # Final estimated minimum
    x_min = (a + b) / 2.0
    f_min = f(x_min)

    if (b - a) <= tol:
        converged = True
    if verbose:
        print(f"\nEstimated minimum at x = {x_min:.6f}, f(x) = {f_min:.6f}")
    # Convert iteration log to DataFrame
    iter_df = pd.DataFrame(
        iter_data,
        columns=["Iteration", "a", "b", "x1", "x2", "f_x1", "f_x2"]
    )
    return {
        "x_min": x_min,
        "f_min": f_min,
        "iterations": iter_count,
        "converged": converged,
        "iter_df": iter_df
    }
