import numpy as np
def fibonacci_method(f, a, b, no_of_iter=20, tol=1e-6, verbose=True):
    """
    Fibonacci Search Method
    -----------------------
    Minimizes a one-dimensional function f(x) within a closed interval [a, b]
    without using derivatives. The algorithm progressively reduces the
    interval using Fibonacci ratios, ensuring efficient convergence toward
    the minimum.

    Mathematical Steps
    ------------------
    Step 1: Generate Fibonacci sequence
        Compute Fibonacci numbers F_1, F_2, ..., F_n, where n = no_of_iter + 2.
        These ratios determine how much of the interval [a, b] to discard at each iteration.

    Step 2: Initialize two interior test points
        x1 = a + (F_{n-2} / F_n) * (b - a)
        x2 = a + (F_{n-1} / F_n) * (b - a)
        Evaluate f(x1) and f(x2).

    Step 3: Iterative interval reduction
        For k = 1, 2, ..., no_of_iter:
            • If f(x1) < f(x2):
                  The minimum lies in [a, x2].
                  Update:
                      b ← x2
                      x2 ← x1
                      x1 ← a + (F_{n-k-2} / F_{n-k}) * (b - a)
                      f(x1) ← f(x1)
            • Else:
                  The minimum lies in [x1, b].
                  Update:
                      a ← x1
                      x1 ← x2
                      x2 ← a + (F_{n-k-1} / F_{n-k}) * (b - a)
                      f(x2) ← f(x2)
            • Stop early if |b - a| ≤ tol

    Step 4: Termination
        After (no_of_iter - 1) reductions or when |b - a| ≤ tol,
        the interval [a, b] is sufficiently small.
        The minimum lies near:
            x_min = x1 if f(x1) < f(x2) else x2
            f_min = min(f(x1), f(x2))

    Step 5: Output
        Return x_min, f_min, number of iterations performed, and
        whether convergence was achieved.

    Parameters
    ----------
    f : callable
        Objective function f(x)
    a, b : float
        Interval bounds
    no_of_iter : int, optional
        Number of iterations or maximum Fibonacci reductions (default: 20)
    tol : float, optional
        Convergence tolerance on interval width (default: 1e-6)
    verbose : bool, optional
        If True, prints a formatted iteration table (default: True)

    Returns
    -------
    dict
        {
            'x_min': Estimated minimizer location,
            'f_min': Function value at the minimizer,
            'iterations': Total iterations performed,
            'converged': Boolean flag for tolerance-based convergence
        }

    Notes
    -----
    • Fibonacci Search is a derivative-free method.
    • It guarantees interval reduction at each step.
    • As the number of iterations increases (n → ∞),
      the ratio F_{k}/F_{k+1} approaches the golden ratio,
      making this method closely related to Golden Section Search.
    
    R Code
    -------
    fibonacci_search = function(f, a, b, tol = 1e-6, max_iter = 100) {
    fibs = c(1, 1)
    while (tail(fibs, 1) < (b - a)/tol)
    fibs = c(fibs, sum(tail(fibs, 2)))
    n = length(fibs) - 1
    x1 = a + (fibs[n-1]/fibs[n+1]) * (b - a)
    x2 = a + (fibs[n]/fibs[n+1]) * (b - a)
    f1 = f(x1); f2 = f(x2)
    cat("Iter |    a     |    b     |    x1    |  f(x1)  |    x2    |  f(x2)\n")
    cat(strrep("-", 65), "\n")
    for (k in 1:max_iter) {
    cat(sprintf("%4d | %8.5f | %8.5f | %8.5f | %8.5f | %8.5f | %8.5f\n",
                k, a, b, x1, f1, x2, f2))
    
    if (abs(b - a) < tol) break
    if (f1 < f2) {
      b = x2; x2 = x1; f2 = f1
      n = n - 1
      x1 = a + (fibs[n-1]/fibs[n+1]) * (b - a)
      f1 = f(x1)
    } else {
      a = x1; x1 = x2; f1 = f2
      n = n - 1
      x2 = a + (fibs[n]/fibs[n+1]) * (b - a)
      f2 = f(x2)
    }
    }
    x_min = (a + b)/2
    cat("\nMinimum ≈", round(x_min, 6), "with f(x) =", round(f(x_min), 6), "\n")
    return(invisible(x_min))
    }

    # Examples
    # ===============
    f = function(x) (x - 2)^2 + 1 ; fibonacci_search(f, -2, 5)

    """
    # --- Step 1: Generate Fibonacci sequence ---
    fibs = [1, 1]
    for _ in range(2, no_of_iter + 2):
        fibs.append(fibs[-1] + fibs[-2])

    # --- Step 2: Initialize points ---
    x1 = a + (fibs[no_of_iter - 2] / fibs[no_of_iter]) * (b - a)
    x2 = a + (fibs[no_of_iter - 1] / fibs[no_of_iter]) * (b - a)
    f_x1, f_x2 = f(x1), f(x2)

    if verbose:
        print(f"{'Iter':>4} | {'a':>9} | {'b':>9} | {'x1':>9} | {'f(x1)':>9} | {'x2':>9} | {'f(x2)':>9}")
        print("-" * 70)

    # --- Step 3: Iterate ---
    for k in range(1, no_of_iter):
        if verbose:
            print(f"{k:4d} | {a:9.6f} | {b:9.6f} | {x1:9.6f} | {f_x1:9.6f} | {x2:9.6f} | {f_x2:9.6f}")

        if f_x1 < f_x2:
            b, x2, f_x2 = x2, x1, f_x1
            x1 = a + (fibs[no_of_iter - k - 2] / fibs[no_of_iter - k]) * (b - a)
            f_x1 = f(x1)
        else:
            a, x1, f_x1 = x1, x2, f_x2
            x2 = a + (fibs[no_of_iter - k - 1] / fibs[no_of_iter - k]) * (b - a)
            f_x2 = f(x2)

        if abs(b - a) <= tol:
            break

    # --- Step 4: Determine result ---
    x_min = x1 if f_x1 < f_x2 else x2
    f_min = min(f_x1, f_x2)

    if verbose:
        print("-" * 70)
        print(f"Minimum found at x = {x_min:.6f}, f(x) = {f_min:.6f}")

    return {
        "x_min": x_min,
        "f_min": f_min,
        "iterations": k,
        "converged": abs(b - a) <= tol
    }