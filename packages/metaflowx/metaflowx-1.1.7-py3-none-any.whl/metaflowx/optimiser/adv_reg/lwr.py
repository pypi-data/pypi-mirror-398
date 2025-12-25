import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

def lwr(train, test, target="target",
        kernel="gaussian",
        bandwidths=[0.1, 0.25, 0.5, 1],
        n_repeats=10,
        plot=True):
    """
    Perform Locally Weighted Regression (LWR) with a local linear fit on univariate data.

    This function applies kernel-based weighted least squares to fit a local line
    at each prediction point, smoothing a regression curve using different kernel
    functions and bandwidth values. Performance is evaluated by repeatedly computing
    training and testing Mean Squared Error (MSE).

    Parameters
    ----------
    train : pandas.DataFrame
        Training dataset containing a feature column and the target column.
        (Assumes the feature column is the first non-target column).

    test : pandas.DataFrame
        Testing dataset containing the same columns as the training dataset.

    target : str, default="target"
        Name of the target variable column.

    kernel : str or list, default="gaussian"
        Kernel or list of kernels to use for weighting. Available options:
        ["gaussian", "uniform", "epanechnikov", "triangular",
         "biweight", "triweight", "tricube"].

    bandwidths : list, default=[0.1, 0.25, 0.5, 1]
        Bandwidth values (h) controlling the width of the kernel smoothing window.

    n_repeats : int, default=10
        Number of repetitions for MSE computation to reduce randomness.

    plot : bool, default=True
        Controls whether smoothing plots are displayed for each kernel-bandwidth
        combination.

    Returns
    -------
    pandas.DataFrame
        A table summarizing average training and testing MSE for each combination
        of kernel and bandwidth.
    Example
    -------
    >>> import numpy as np
    >>> import pandas as pd
    >>> from sxc import mdts
    >>> from sklearn.model_selection import train_test_split
    >>> np.random.seed(1234)
    >>> def reg(x): return 5 * np.sin(x) + 23 * (np.cos(x))**2
    >>> x = np.random.uniform(5, 15, (100, 1))
    >>> y = reg(x) + np.random.normal(0, 5, (100, 1))
    >>> data = pd.DataFrame({"feature": x.flatten(), "target": y.flatten()})
    >>> train, test = train_test_split(data, test_size=0.2, random_state=42)
    >>> mdts.lwr(train, test,
    ...        target="target",
    ...        kernel=["uniform", "triangular", "epanechnikov"],
    ...        n_repeats=50,
    ...        plot=True)
    """

    # --- Kernel Functions (Same as original) ---
    def gaussian_kernel(u):
        # Uses standard normal distribution formula
        return (1/np.sqrt(2*np.pi)) * np.exp(-u**2 / 2)

    def uniform_kernel(u):
        return np.where(np.abs(u) <= 1, 1/2, 0)

    def epanechnikov_kernel(u):
        return np.where(np.abs(u) <= 1, 3/4 * (1 - u**2), 0)

    def triangular_kernel(u):
        return np.where(np.abs(u) <= 1, 1 - np.abs(u), 0)

    def biweight_kernel(u):
        return np.where(np.abs(u) <= 1, 15/16 * (1 - u**2)**2, 0)

    def triweight_kernel(u):
        return np.where(np.abs(u) <= 1, 35/32 * (1 - u**2)**3, 0)

    def tricube_kernel(u):
        # Note: The tricube kernel is usually defined as (1-|u|^3)^3 * I(|u|<=1)
        # This implementation uses a common variation but includes the required normalization constant
        return np.where(np.abs(u) <= 1, 70/81 * (1 - np.abs(u)**3)**3, 0)

    kernels = {
        "gaussian": gaussian_kernel,
        "uniform": uniform_kernel,
        "epanechnikov": epanechnikov_kernel,
        "triangular": triangular_kernel,
        "biweight": biweight_kernel,
        "triweight": triweight_kernel,
        "tricube": tricube_kernel
    }

    # --- Input Validation ---
    if isinstance(kernel, str):
        kernel_list = [kernel]
    else:
        kernel_list = list(kernel)

    for ker in kernel_list:
        if ker not in kernels:
            raise ValueError(f"Choose kernel from: {list(kernels.keys())}")

    # Assuming univariate input (only one feature column)
    feature_col = [col for col in train.columns if col != target][0]
    X_train = train[feature_col].values.flatten()
    y_train = train[target].values.flatten()
    X_test = test[feature_col].values.flatten()
    y_test = test[target].values.flatten()

    results = []

    # --- Core Smoothing Function (Local Linear Fit) ---
    def smooth(x_query, X, Y, h, kernel_func):
        """
        Calculates the predicted value at x_query using local linear regression.

        This uses the Weighted Least Squares (WLS) solution:
        beta_hat = (X_mat^T W_mat X_mat)^-1 X_mat^T W_mat Y
        The prediction is beta_hat[0] (the intercept).
        """
        # 1. Calculate the scaled distances (u) and weights (w)
        u = (X - x_query) / h
        w = kernel_func(u)

        # Handle cases with zero weights (e.g., query point is far from all data)
        # In this case, we fall back to the nearest neighbor's Y value.
        if np.sum(w) == 0:
            nearest_index = np.argmin(np.abs(X - x_query))
            return Y[nearest_index]

        # 2. Construct the design matrix (X_mat)
        # We use a centered design matrix: [1, X - x_query].
        # The prediction at x_query (where X-x_query = 0) is then simply the intercept (beta_0).
        X_centered = X - x_query
        X_mat = np.vstack([np.ones(len(X_centered)), X_centered]).T # Shape: (N, 2)

        # 3. Create the diagonal weight matrix (W_mat)
        # We use a shortcut for matrix multiplication involving a diagonal matrix:
        # X^T W Y is equivalent to (X * w[:, None]).T @ Y
        W_mat = np.diag(w)

        # 4. Compute the core WLS matrices (A and B)
        # A = X_mat^T W_mat X_mat
        # B = X_mat^T W_mat Y
        A = X_mat.T @ W_mat @ X_mat # (2, N) @ (N, N) @ (N, 2) -> (2, 2)
        B = X_mat.T @ W_mat @ Y     # (2, N) @ (N, N) @ (N,) -> (2,)

        # 5. Solve for coefficients (beta_hat)
        try:
            # Solve A * beta_hat = B
            beta_hat = np.linalg.solve(A, B)
        except np.linalg.LinAlgError:
            # Fallback if matrix is singular (e.g., all X values are identical)
            return np.average(Y, weights=w)

        # 6. Prediction: Since X is centered, prediction at x_query is beta_hat[0]
        return beta_hat[0]

    # --- Main Loop for Evaluation and Plotting ---
    for ker in kernel_list:
        kernel_func = kernels[ker]

        for h in bandwidths:
            train_mse_list = []
            test_mse_list = []

            # Repeat smoothing and MSE calculation
            for _ in range(n_repeats):
                # Apply smoothing to generate predictions for all data points
                y_pred_train = np.array([smooth(x, X_train, y_train, h, kernel_func) for x in X_train])
                y_pred_test = np.array([smooth(x, X_train, y_train, h, kernel_func) for x in X_test])

                train_mse_list.append(mean_squared_error(y_train, y_pred_train))
                test_mse_list.append(mean_squared_error(y_test, y_pred_test))

            # Store summary results
            results.append({
                "Kernel": ker,
                "Bandwidth (h)": h,
                "Avg Train MSE": np.mean(train_mse_list),
                "Avg Test MSE": np.mean(test_mse_list)
            })

            # Plotting the smooth curve
            if plot:
                # Generate smooth line points over the feature range
                x_min, x_max = np.min(X_train), np.max(X_train)
                x_grid = np.linspace(x_min, x_max, 300)
                y_grid = np.array([smooth(x, X_train, y_train, h, kernel_func) for x in x_grid])

                plt.figure(figsize=(9, 6))
                plt.scatter(X_train, y_train, s=20, alpha=0.6, label="Training Data", color='#3b82f6')
                plt.scatter(X_test, y_test, s=20, alpha=0.6, label="Test Data", color='#ef4444')
                plt.plot(x_grid, y_grid, label=f"LWR Fit: {ker} (h={h})", linewidth=1, color='#10b981')
                plt.title(f"Locally Weighted Regression (LWR) - Kernel={ker}, Bandwidth (h)={h}", fontsize=14)
                plt.xlabel(feature_col, fontsize=12)
                plt.ylabel(target, fontsize=12)
                plt.legend(fontsize=10)
                plt.grid(True, linestyle='--', alpha=0.5)
                plt.tight_layout()
                plt.show()

    return pd.DataFrame(results)
