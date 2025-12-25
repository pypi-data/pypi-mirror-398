import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline

def spline_fit(df, response, predictor, smoothing=1.0):
    """
    Smoothing Spline Regression (1D)

    Theoretical background
    ----------------------
    1. Model
       For data (x_i, y_i) we assume the regression model

           y_i = f(x_i) + ε_i,

       where f is an unknown smooth function and ε_i are independent errors
       with mean zero and constant variance.

    2. Smoothing spline estimator
       The smoothing spline estimate of f(x) is obtained by solving:

           minimize_f   Σ (y_i - f(x_i))^2  +  λ ∫ (f''(t))^2 dt

       where λ ≥ 0 is the smoothing parameter.

       - If λ = 0, we interpolate the data (overfit).
       - If λ → ∞, we get a straight-line least-squares fit.
       - Intermediate λ gives a smooth curve balancing bias–variance.

       The minimiser is a *natural cubic spline* with knots at the data points.

    3. Implementation through UnivariateSpline
       SciPy's UnivariateSpline solves the exact penalized least squares
       smoothing spline problem:

           minimize_f  Σ (y_i - f(x_i))^2 + s ∫ (f''(t))^2 dt

       where 's' plays a role analogous to λ.

       Larger s → smoother f.
       Smaller s → wigglier f.

    Parameters
    ----------
    df : pandas.DataFrame
        Data containing predictor and response.
    response : str
        Response variable column name.
    predictor : str
        Predictor variable column name (only 1D spline).
    smoothing : float
        Smoothing parameter 's' passed to UnivariateSpline.

    Returns
    -------
    result : dict
        A dictionary containing:

        - 'spline'  : fitted UnivariateSpline object
        - 'fitted'  : fitted values on the training data
        - 'predict' : prediction function for new x values
    Example
    -------
    from splines import spline_fit
import numpy as np
import pandas as pd

np.random.seed(10)

n = 200
x = np.linspace(0, 1, n)
y_true = np.sin(2 * np.pi * x)
y = y_true + 0.15 * np.random.randn(n)

df = pd.DataFrame({"x": x, "y": y})

model = spline_fit(df, response="y", predictor="x", smoothing=1.0)

print(model["fitted"][:10])

newdata = pd.DataFrame({"x": [0.1, 0.4, 0.8]})
print(model["predict"](newdata))


R code
-------
spline_fit <- function(df, response, predictor, df_spline = NULL, spar = NULL) {

  y <- df[[response]]
  x <- df[[predictor]]

  fit <- smooth.spline(x, y, df = df_spline, spar = spar)

  fitted_vals <- predict(fit, x)$y

  predict_fn <- function(newdata) {
    xnew <- newdata[[predictor]]
    predict(fit, xnew)$y
  }

  list(
    spline = fit,
    fitted = fitted_vals,
    predict = predict_fn
  )
}
Usage
------
source("splines.R")

set.seed(42)

n <- 200
x <- seq(0, 1, length.out = n)
y_true <- sin(2*pi*x)
y <- y_true + rnorm(n, 0, 0.2)

df <- data.frame(x = x, y = y)

model <- spline_fit(df, response = "y", predictor = "x", df_spline = 10)

head(model$fitted)

new_df <- data.frame(x = c(0.1, 0.3, 0.7))
model$predict(new_df)


    """

    # Extract variables
    y = df[response].to_numpy(dtype=float)
    x = df[predictor].to_numpy(dtype=float)

    # Fit smoothing spline
    spline = UnivariateSpline(x, y, k=3, s=smoothing)

    # Fitted values
    fitted = spline(x)

    # Prediction function
    def predict(new_df: pd.DataFrame) -> np.ndarray:
        x_new = new_df[predictor].to_numpy(dtype=float)
        return spline(x_new)

    return {
        "spline": spline,
        "fitted": fitted,
        "predict": predict
    }
