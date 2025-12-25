def quassi_newton_documentation():
    """
rm(list=ls())
library(numDeriv)
quasi_newton = function(f, x0, tol=1e-6, max_iter=100, grad_eps=1e-8) {
  x = x0 ; n = length(x0) ; B = diag(n)
  cat(sprintf("%-6s %-12s %-12s %-10s %-10s\n",
              "Iter", "||grad||", "f(x)", "alpha", "||d||"))
  cat(strrep("-", 60), "\n")
  for (k in 1:max_iter) {
    g = grad(f, x)
    grad_norm = sqrt(sum(g^2))
    
    if (grad_norm < tol) {
      cat("Converged!\n")
      return(list(x_min = x, f_min = f(x), iterations = k, converged = TRUE))
    }
    
    d = tryCatch(-solve(B, g), error = function(e) -g)
    phi = function(alpha) f(x + alpha * d)
    alpha = optimize(phi, c(0, 1))$minimum
    x_new = x + alpha * d
    s = x_new - x
    y = grad(f, x_new) - g
    sTy = sum(s * y)
    if (sTy <= 0) {
      cat(sprintf("Iter %d: curvature condition failed (sTy=%.4e)\n", k, sTy))
      y = y + 1e-6 * s
      sTy = sum(s * y)
    }
    Bs = B %*% s
    B = B - (Bs %*% t(Bs)) / as.numeric(t(s) %*% Bs) + (y %*% t(y)) / as.numeric(t(y) %*% s)
    B = 0.5 * (B + t(B))
    cat(sprintf("%-6d %-12.4e %-12.6g %-10.4f %-10.4f\n",
                k, grad_norm, f(x), alpha, sqrt(sum(d^2))))
    x = x_new
  }
  cat("Max iterations reached.\n")
  return(list(x_min = x, f_min = f(x), iterations = max_iter, converged = FALSE))
}

# ==================  Examples ====================
f = function(x) 0.5*(2*x[1]^2 - 6*x[1]*x[2] + 5*x[2]^2) - x[2]
quasi_newton(f, c(0,0))

"""