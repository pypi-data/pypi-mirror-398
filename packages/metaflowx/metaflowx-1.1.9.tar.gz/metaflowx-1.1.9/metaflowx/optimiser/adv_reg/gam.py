import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline


def gam(df, response, predictors, smoothing=1.0, max_iter=50, tol=1e-4):
    """
    Generalized Additive Model (GAM) via backfitting with cubic smoothing splines.

    Theoretical background
    ----------------------
    1. Model
       We observe (x_{i1}, ..., x_{ip}, y_i), i = 1,...,n and assume the additive
       regression model

           Y_i = α + f_1(X_{i1}) + f_2(X_{i2}) + ... + f_p(X_{ip}) + ε_i,

       where ε_i are i.i.d. with E[ε_i] = 0, Var(ε_i) = σ^2 and the f_j are
       unknown smooth functions. This is the (Gaussian) Generalized Additive
       Model (GAM).

    2. Identifiability constraint
       The model is not identifiable unless we constrain the smooth functions.
       A standard choice is

           ∑_{i=1}^n f_j(X_{ij}) = 0   for each j = 1,...,p.

       With this constraint the intercept α absorbs the global mean of Y and
       each f_j represents a *deviation* from that mean due to predictor X_j.

    3. Estimation as penalized least squares
       In practice each f_j is represented by a flexible basis (e.g. splines)
       and estimated by minimizing a penalized sum of squares, for example

           min_{α, f_1,...,f_p}
               ∑_{i=1}^n (y_i - α - ∑_{j=1}^p f_j(x_{ij}))^2
               + ∑_{j=1}^p λ_j ∫ (f_j''(x))^2 dx,

       where λ_j ≥ 0 control the smoothness of each f_j. When each f_j is a
       cubic spline and we penalize the integrated squared second derivative,
       the solution is a *natural cubic spline* (smoothing spline).

    4. Backfitting algorithm (Hastie & Tibshirani, 1990)
       The additive least-squares solution can be obtained by the backfitting
       algorithm:

       - Step 0 (initialisation):
           α̂  = ȳ = (1/n) ∑_i y_i
           f_j^{(0)}(·) ≡ 0 for all j.

       - Step 1 (cycling over predictors):
           For iteration t = 1,2,... and for each j = 1,...,p:

               (a) Compute the partial residuals for X_j:

                       r_{ij}^{(t)} = y_i - α̂
                                     - ∑_{k ≠ j} f_k^{(t)}(x_{ik}).

               (b) Fit a univariate smoother g_j^{(t)} to (x_{ij}, r_{ij}^{(t)}).

               (c) Enforce the identifiability constraint by centering:

                       f_j^{(t)}(x_{ij})
                           = g_j^{(t)}(x_{ij}) - (1/n) ∑_{i=1}^n g_j^{(t)}(x_{ij}).

           Cycle through j = 1,...,p until the functions change by less than a
           specified tolerance. Under standard conditions this procedure
           converges to the additive least-squares solution.

       This function implements Step 1(b) with cubic smoothing splines using
       `scipy.interpolate.UnivariateSpline`.

    5. Smoothing parameter
       `UnivariateSpline` fits a spline g_j to (x_{ij}, r_{ij}) by minimizing

           ∑_i (r_{ij} - g_j(x_{ij}))^2 + s ∫ (g_j''(x))^2 dx,

       where `s` is a non-negative smoothing parameter. In this function the
       argument `smoothing` is passed as `s`. Larger values of `smoothing`
       produce smoother estimated functions f_j; smaller values allow more
       wiggle (risk of overfitting).

    Parameters
    ----------
    df : pandas.DataFrame
        Input data frame containing both the response and predictor variables.
    response : str
        Column name of the response variable Y.
    predictors : sequence of str
        Column names of the predictor variables X1,...,Xp to be included in the
        additive model.
    smoothing : float, optional (default=1.0)
        Smoothing parameter `s` passed to `UnivariateSpline` for each univariate
        smoother. Larger values give smoother functions.
    max_iter : int, optional (default=50)
        Maximum number of backfitting iterations.
    tol : float, optional (default=1e-4)
        Convergence tolerance for the maximum absolute change in the fitted
        smooths between successive iterations.

    Returns
    -------
    result : dict
        A dictionary with the following entries:

        - 'alpha'  : float
            Estimate of the intercept α̂.
        - 'smooths': numpy.ndarray of shape (n, p)
            The fitted smooth contributions f̂_j(x_{ij}) evaluated at the
            training points.
        - 'fitted' : numpy.ndarray of shape (n,)
            The fitted values ŷ_i = α̂ + ∑_j f̂_j(x_{ij}).
        - 'predict': callable
            A function that takes a new pandas.DataFrame with the same
            predictor columns and returns predicted values from the fitted GAM.

    Notes
    -----
    * This implementation is intended for teaching and small experiments. It
      handles only Gaussian responses and uses the same smoothing parameter for
      all predictors.
    * For serious applications and automatic smoothing selection, use
      established libraries such as `mgcv` in R or `pygam` / `statsmodels.gam`
      in Python.

    R code
    ----------
    gam_fit <- function(df, response, predictors, df_spline = 6,
                    max_iter = 50, tol = 1e-4) {

  y <- df[[response]]
  X <- as.matrix(df[predictors])

  n <- length(y)
  p <- ncol(X)

  alpha <- mean(y)
  fhat <- matrix(0, n, p)
  splines <- vector("list", p)
  centers <- rep(0, p)

  for (iter in 1:max_iter) {
    f_old <- fhat

    for (j in 1:p) {
      r_j <- y - alpha - (rowSums(fhat) - fhat[, j])

      fit_j <- smooth.spline(X[, j], r_j, df = df_spline)
      g_vals <- predict(fit_j, X[, j])$y

      c_j <- mean(g_vals)
      fhat[, j] <- g_vals - c_j

      splines[[j]] <- fit_j
      centers[j] <- c_j
    }

    if (max(abs(fhat - f_old)) < tol) break
  }

  fitted <- alpha + rowSums(fhat)

  predict_fn <- function(newdata) {
    Xnew <- as.matrix(newdata[predictors])
    preds <- rep(alpha, nrow(Xnew))
    for (j in 1:p) {
      g_new <- predict(splines[[j]], Xnew[, j])$y
      preds <- preds + (g_new - centers[j])
    }
    preds
  }

  list(
    alpha = alpha,
    smooths = fhat,
    fitted = fitted,
    predict = predict_fn
  )
}
Example 
--------
import numpy as np
import pandas as pd
import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline

np.random.seed(42)

n = 300
x1 = np.random.uniform(0, 1, n)
x2 = np.random.uniform(0, 1, n)

f1 = np.sin(2 * np.pi * x1)
f2 = (x2 - 0.5)**2

y = 3 + f1 + f2 + np.random.normal(0, 0.15, n)

df = pd.DataFrame({
    "y": y,
    "x1": x1,
    "x2": x2
})
model = gam(df, response="y", predictors=["x1", "x2"], smoothing=1.0)

    """

    # --- implementation starts here ---

    # Extract response and predictor matrices
    y = df[response].to_numpy(dtype=float)
    X = df[predictors].to_numpy(dtype=float)

    n, p = X.shape

    # Intercept and smooth components
    alpha = np.mean(y)
    fhat = np.zeros((n, p))

    # We'll store the spline objects and their centering constants
    splines = [None] * p
    centers = np.zeros(p)

    for _ in range(max_iter):
        f_old = fhat.copy()

        for j in range(p):
            # Partial residuals for predictor j
            # subtract intercept and all other smooth components
            r_j = y - alpha - (fhat.sum(axis=1) - fhat[:, j])

            # Fit cubic smoothing spline to (X[:, j], r_j)
            spline_j = UnivariateSpline(X[:, j], r_j, k=3, s=smoothing)

            g_vals = spline_j(X[:, j])
            c_j = g_vals.mean()

            # Center to satisfy sum_i f_j(x_ij) = 0
            fhat[:, j] = g_vals - c_j
            splines[j] = spline_j
            centers[j] = c_j

        # Check convergence
        if np.max(np.abs(fhat - f_old)) < tol:
            break

    fitted = alpha + fhat.sum(axis=1)

    def predict(new_df: pd.DataFrame) -> np.ndarray:
        """
        Predict response values for new data using the fitted GAM.

        Parameters
        ----------
        new_df : pandas.DataFrame
            New data containing the predictor columns specified in `predictors`.

        Returns
        -------
        numpy.ndarray
            Predicted values for each row in `new_df`.
        """
        X_new = new_df[predictors].to_numpy(dtype=float)
        preds = np.full(X_new.shape[0], alpha, dtype=float)

        for j in range(p):
            # Apply the same spline and centering as in training
            g_new = splines[j](X_new[:, j])
            preds += g_new - centers[j]

        return preds

    return {
        "alpha": alpha,
        "smooths": fhat,
        "fitted": fitted,
        "predict": predict,
    }
