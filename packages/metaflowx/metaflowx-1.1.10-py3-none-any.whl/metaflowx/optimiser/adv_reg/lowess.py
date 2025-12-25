import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

def lowess(train, test, target="target",
           kernel="gaussian",
           bandwidths=[10, 0.25, 0.5, 1],
           n_repeats=10,
           plot=True):
    """
    Perform Local Weighted Scatterplot Smoothing (LOWESS) on univariate data.

    This function applies kernel-based weighted averaging to smooth a regression curve
    using different kernel functions and bandwidth values. Performance is evaluated by
    repeatedly computing training and testing mean squared error (MSE) across several runs.

    Parameters
    ----------
    train : pandas.DataFrame
        Training dataset containing a feature column and the target column.

    test : pandas.DataFrame
        Testing dataset containing the same columns as the training dataset.

    target : str, default="target"
        Name of the target variable column.

    kernel : str or list, default="gaussian"
        Kernel or list of kernels to use for weighting. Available options:
        ["gaussian", "uniform", "epanechnikov", "triangular",
         "biweight", "triweight", "tricube"].

    bandwidths : list, default=[10, 0.25, 0.5, 1]
        Bandwidth values controlling the width of the kernel smoothing window.

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

    Example (Python)
    --------
    import numpy as np
    import pandas as pd
    from sxc import mdts
    from sklearn.model_selection import train_test_split
    np.random.seed(1234)
    def reg(x): return 5 * np.sin(x) + 23 * (np.cos(x))**2
    x = np.random.uniform(5, 15, (100, 1))
    y = reg(x) + np.random.normal(0, 5, (100, 1))
    data = pd.DataFrame({"feature": x.flatten(), "target": y.flatten()})
    train, test = train_test_split(data, test_size=0.2, random_state=42)
    mdts.lowess(train, test, target="target",
                kernel=["uniform", "triangular", "epanechnikov"],
                n_repeats=50, plot=True)

    Example (R)
    --------
    # Sample data
    set.seed(1234)
    reg <- function(x) 5 * sin(x) + 23 * (cos(x))^2
    n <- 100
    x <- runif(n, 5, 15)
    y <- reg(x) + rnorm(n, 0, 5)

    # Split into train and test
    train_idx <- sample(1:n, size = 0.8 * n)
    train <- data.frame(feature = x[train_idx], target = y[train_idx])
    test  <- data.frame(feature = x[-train_idx], target = y[-train_idx])

    # Extract
    X_train <- train$feature
    y_train <- train$target
    X_test  <- test$feature
    y_test  <- test$target

    # Gaussian Kernel
    gaussian_kernel <- function(u) (1 / sqrt(2 * pi)) * exp(-u^2 / 2)

    # Smoothing function
    smooth <- function(x_query, X, Y, h, kernel_func) {
      u <- (X - x_query) / h
      w <- kernel_func(u)
      if (sum(w) == 0) {
        idx <- which.min(abs(X - x_query))
        return(Y[idx])
      }
      return(sum(w * Y) / sum(w))
    }

    # Parameters
    bandwidths <- c(10, 0.25, 0.5, 1)
    n_repeats <- 10
    results <- data.frame()

    # Loop
    for (h in bandwidths) {
      train_mse_vec <- numeric(n_repeats)
      test_mse_vec  <- numeric(n_repeats)

      for (r in seq_len(n_repeats)) {
        y_pred_train <- sapply(X_train, function(v) smooth(v, X_train, y_train, h, gaussian_kernel))
        y_pred_test  <- sapply(X_test,  function(v) smooth(v, X_train, y_train, h, gaussian_kernel))

        train_mse_vec[r] <- mean((y_train - y_pred_train)^2)
        test_mse_vec[r]  <- mean((y_test  - y_pred_test)^2)
      }

      results <- rbind(
        results,
        data.frame(
          Kernel = "Gaussian",
          Bandwidth = h,
          Avg_Train_MSE = mean(train_mse_vec),
          Avg_Test_MSE  = mean(test_mse_vec)
        )
      )

      cat("Bandwidth =", h,
          " Train MSE =", round(mean(train_mse_vec), 4),
          " Test MSE =", round(mean(test_mse_vec), 4))

      # Plotting
      x_grid <- seq(min(X_train), max(X_train), length.out = 300)
      y_grid <- sapply(x_grid, function(v) smooth(v, X_train, y_train, h, gaussian_kernel))
      y_true <- reg(x_grid)  # True regression curve

      plot(X_train, y_train, pch = 16,
           main = paste("LOWESS Gaussian (h =", h, ")"),
           xlab = "Feature", ylab = "Target")
      points(X_test, y_test, pch = 16, col = "blue")
      lines(x_grid, y_grid, lwd = 2, col = "red")
      lines(x_grid, y_true, lwd = 2, col = "darkgreen", lty = 2)

      legend("topleft", legend = c("Train", "Test", "LOWESS Fit", "True Function"),
             col = c("black", "blue", "red", "darkgreen"),
             pch = c(16, 16, NA, NA),
             lty = c(NA, NA, 1, 2))
      grid()
    }

    results
    """

    def gaussian_kernel(u): 
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

    if isinstance(kernel, str):
        kernel_list = [kernel]
    else:
        kernel_list = list(kernel)

    for ker in kernel_list:
        if ker not in kernels:
            raise ValueError(f"Choose kernel from: {list(kernels.keys())}")

    X_train = train.drop(columns=[target]).values.flatten()
    y_train = train[target].values.flatten()
    X_test = test.drop(columns=[target]).values.flatten()
    y_test = test[target].values.flatten()

    results = []

    def smooth(x_query, X, Y, h, kernel_func):
        u = (X - x_query) / h
        w = kernel_func(u)

        if np.sum(w) == 0:
            nearest_index = np.argmin(np.abs(X - x_query))
            return Y[nearest_index]

        return np.sum(w * Y) / np.sum(w)

    for ker in kernel_list:
        kernel_func = kernels[ker]

        for h in bandwidths:
            train_mse_list = []
            test_mse_list = []

            for _ in range(n_repeats):
                y_pred_train = np.array([smooth(x, X_train, y_train, h, kernel_func) for x in X_train])
                y_pred_test = np.array([smooth(x, X_train, y_train, h, kernel_func) for x in X_test])

                train_mse_list.append(mean_squared_error(y_train, y_pred_train))
                test_mse_list.append(mean_squared_error(y_test, y_pred_test))

            results.append({
                "Kernel": ker,
                "Bandwidth": h,
                "Avg Train MSE": np.mean(train_mse_list),
                "Avg Test MSE": np.mean(test_mse_list)
            })

            if plot:
                x_grid = np.linspace(min(X_train), max(X_train), 300)
                y_grid = np.array([smooth(x, X_train, y_train, h, kernel_func) for x in x_grid])

                plt.figure(figsize=(7, 5))
                plt.scatter(X_train, y_train, s=15, label="Train Data")
                plt.scatter(X_test, y_test, s=15, label="Test Data")
                plt.plot(x_grid, y_grid, label=f"{ker} (h={h})", linewidth=2)
                plt.title(f"LOWESS: Kernel={ker}, Bandwidth={h}")
                plt.xlabel("Feature")
                plt.ylabel(target)
                plt.legend()
                plt.grid()
                plt.show()

    return pd.DataFrame(results)
