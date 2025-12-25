import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar, approx_fprime

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar, approx_fprime

def quassi_newton(
    f,
    x0,
    B0=None,
    tol=1e-6,
    max_iter=100,
    verbose=False,
    grad_eps=1e-8,
    line_search_interval=(0, 1)
):
    """
    Quasi-Newton Optimization using BFGS
    -------------------------------------------------------
    Implements the Quasi-Newton method for unconstrained minimization
    using the **BFGS** (Broyden–Fletcher–Goldfarb–Shanno) update.

    ----------------------------------------------------------------------
    Step-by-Step BFGS Algorithm
    ----------------------------------------------------------------------

    Step 1: **Initialization**
        Choose starting point x₀.
        Set iteration counter k = 0.
        Initialize the Hessian (or its inverse) approximation:
            B₀ = I  (or H₀ = I if using inverse form).
        Choose convergence tolerance (tol) and maximum iterations.

    Step 2: **Compute Gradient**
        Evaluate gₖ = ∇f(xₖ).

    Step 3: **Check Convergence**
        If ||gₖ|| < tol, stop. We’ve reached a local minimum.

    Step 4: **Compute Search Direction**
        - If storing inverse Hessian Hₖ:
              dₖ = -Hₖ gₖ
        - If storing Hessian Bₖ:
              Solve Bₖ dₖ = -gₖ

    Step 5: **Line Search**
        Find step size αₖ by minimizing f(xₖ + α dₖ)
        (or satisfying strong Wolfe conditions).
        Update position:
              xₖ₊₁ = xₖ + αₖ dₖ

    Step 6: **Compute Displacement Vectors**
        sₖ = xₖ₊₁ - xₖ
        yₖ = ∇f(xₖ₊₁) - ∇f(xₖ)

    Step 7: **Check Curvature Condition**
        Ensure yₖᵀ sₖ > 0
        (This guarantees positive-definiteness of the update).
        If violated, skip update or reset Hessian.

    Step 8: **Update Inverse Hessian (preferred form)**
        ρₖ = 1 / (yₖᵀ sₖ)
        Hₖ₊₁ = (I - ρₖ sₖ yₖᵀ) Hₖ (I - ρₖ yₖ sₖᵀ) + ρₖ sₖ sₖᵀ

        (If updating Bₖ instead of Hₖ, use:)
        Bₖ₊₁ = Bₖ - (Bₖ sₖ sₖᵀ Bₖ)/(sₖᵀ Bₖ sₖ) + (yₖ yₖᵀ)/(yₖᵀ sₖ)

    Step 9: **Repeat**
        Increment k → k+1 and return to Step 2.

    Step 10: **Stopping and Output**
        Algorithm terminates when:
            - ||∇f(x)|| < tol
            - Maximum iterations reached
        Returns final x, f(x), and iteration log.

    ----------------------------------------------------------------------
    Parameters
    ----------------------------------------------------------------------
    f : callable
        Objective function f(x).
    x0 : array-like
        Starting point.
    B0 : ndarray or None
        Initial Hessian approximation. Identity if None.
    tol : float
        Convergence tolerance based on gradient norm.
    max_iter : int
        Maximum number of iterations.
    verbose : bool
        If True, prints iteration progress.
    grad_eps : float
        Step size for numerical gradient.
    line_search_interval : tuple
        Interval for 1D line search along direction d.

    ----------------------------------------------------------------------
    Returns
    ----------------------------------------------------------------------
    result : dict
        {
          'x_min': Minimizer,
          'f_min': Function value at minimizer,
          'iterations': Number of iterations,
          'converged': Bool,
          'iter_df': Pandas DataFrame with iteration info
        }

    ----------------------------------------------------------------------
    Example
    ----------------------------------------------------------------------
    >>> import numpy as np
    >>> import pandas as pd
    >>> from scipy.optimize import minimize_scalar, approx_fprime
    >>> # (Paste your quassi_newton() function definition above this line)
    >>> 
    >>> # ---------- Example 1: Quadratic Function ----------
    >>> def quad(x):
    ...     return 0.5 * (2*x[0]**2 - 6*x[0]*x[1] + 5*x[1]**2) - x[1]
    >>> 
    >>> res_q = quassi_newton(quad, x0=[0, 0], verbose=True)
    >>> print("n--- Quadratic Function Results ---")
    >>> print("x_min:", res_q["x_min"])
    >>> print("f_min:", res_q["f_min"])
    >>> print("Converged:", res_q["converged"])
    >>> print(res_q["iter_df"][["iteration", "x", "grad_norm", "alpha_k", "f_x"]])

    >>> # ---------- Example 2: Rosenbrock Function ----------
    >>> def rosenbrock(x):
    ...     return 100*(x[1] - x[0]**2)**2 + (1 - x[0])**2
    >>> 
    >>> res_rb = quassi_newton(rosenbrock, x0=[-1.2, 1.0], verbose=True)
    >>> print("\\n--- Rosenbrock Function Results ---")
    >>> print("x_min:", res_rb["x_min"])
    >>> print("f_min:", res_rb["f_min"])
    >>> print("Converged:", res_rb["converged"])
    >>> print(res_rb["iter_df"][["iteration", "x", "grad_norm", "alpha_k", "f_x"]])
    """

    x = np.array(x0, dtype=float)
    n = len(x)
    B = np.eye(n) if B0 is None else np.array(B0, dtype=float)
    grad = approx_fprime(x, f, grad_eps)
    grad_norm = np.linalg.norm(grad)
    converged = False
    records = []

    if verbose:
        print(f"{'iter':<6} {'grad_norm':<12} {'f(x)':<12} {'alpha':<8} {'||d||':<10} x")
        print("-" * 70)

    for k in range(1, max_iter + 1):
        grad_norm = np.linalg.norm(grad)
        if grad_norm < tol:
            converged = True
            break

        # Search direction: d = -B^{-1} * grad
        try:
            d = -np.linalg.solve(B, grad)
        except np.linalg.LinAlgError:
            d = -grad  # fallback: steepest descent

        # --- Line search ---
        phi = lambda alpha: f(x + alpha * d)
        a, b = line_search_interval
        res = minimize_scalar(phi, bounds=(a, b), method="bounded")
        alpha = res.x if res.success else 1.0

        # --- Step update ---
        x_new = x + alpha * d
        f_x = f(x)
        grad_new = approx_fprime(x_new, f, grad_eps)
        S = x_new - x
        y = grad_new - grad

        sTy = float(np.dot(S, y))
        sTBs = float(S @ B @ S)

        # Damping / safeguard if sTy <= 0
        if sTy <= 0 or not np.isfinite(sTy):
            c_val = 0.2
            theta = ((c_val * sTBs) - sTy) / ((c_val * sTBs) - sTy + 1e-16)
            theta = np.clip(theta, 0, 1)
            y = theta * y + (1 - theta) * (B @ S)
            sTy = float(np.dot(S, y))

        if sTy > 0 and np.isfinite(sTy):
            BS = B @ S
            denom1 = float(S @ BS)
            denom2 = sTy
            denom1 = denom1 if abs(denom1) > 1e-12 else np.sign(denom1) * 1e-12
            denom2 = denom2 if abs(denom2) > 1e-12 else np.sign(denom2) * 1e-12
            B = B - np.outer(BS, BS) / denom1 + np.outer(y, y) / denom2
            B = 0.5 * (B + B.T)  # keep symmetric
        else:
            if verbose:
                print(f"Iteration {k}: curvature condition failed (s^T y = {sTy:g})")

        # Record iteration
        records.append({
            "iteration": k,
            "x": x.copy(),
            "grad_norm": np.linalg.norm(grad),
            "alpha_k": alpha,
            "f_x": f_x,
            "d_k": d.copy(),
            "B_k": B.copy()
        })

        if verbose:
            short_x = ", ".join(f"{xi:.4f}" for xi in x[:4])
            print(f"{k:<6d} {grad_norm:<12.4e} {f_x:<12.6g} {alpha:<8.4g} {np.linalg.norm(d):<10.4g} {short_x}")

        x, grad = x_new, grad_new

    iter_df = pd.DataFrame(records)
    result = {
        "x_min": x,
        "f_min": f(x),
        "iterations": len(records),
        "converged": converged,
        "iter_df": iter_df
    }

    if verbose:
        print("-" * 70)
        print(f"Converged: {converged} | Iterations: {len(records)} | f_min: {result['f_min']:.6g}")

    return result
