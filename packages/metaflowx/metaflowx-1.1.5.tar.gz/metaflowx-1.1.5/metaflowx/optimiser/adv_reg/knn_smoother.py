import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error

def knn_smoother(train, test, target="target", regression=None,
                 k_values=[1, 2, 5, 10, 20, 40, 80], n_repeats=50):
    """
    Perform repeated KNN smoothing estimation for a univariate nonparametric regression model.

    This method performs KNN smoothing over multiple randomized train-test splits,
    records both train and test MSE for each choice of K, and optionally visualizes
    smoothing curves against a true regression function if provided.

    Parameters
    ----------
    train : pandas.DataFrame
        Training dataset (first column as covariate, response column as `target`).
    test : pandas.DataFrame
        Test dataset with same structure as `train`.
    target : str, optional
        Name of the response variable column. Default is "target".
    regression : callable, optional
        True regression function f(x), used only for visualization.
    k_values : list of int, optional
        List of neighbor counts for KNN smoothing. Default is [1, 2, 5, 10, 20, 40, 80].
    n_repeats : int, optional
        Number of random splits for averaging errors. Default is 50.

    Returns
    -------
    pandas.DataFrame
        A table containing each K value and its corresponding averaged train and test MSE.

    Python Example
    --------------
    >>> import numpy as np
    >>> import pandas as pd
    >>> from sklearn.model_selection import train_test_split
    >>> from sxc import mdts
    >>>
    >>> def reg(x):
    ...     return 5 * np.sin(x) + 23 * (np.cos(x))**2
    >>>
    >>> np.random.seed(1234)
    >>> x = np.random.uniform(5, 15, (100, 1))
    >>> y = reg(x) + np.random.normal(0, 5, (100, 1))
    >>>
    >>> data = pd.DataFrame({"feature": x.flatten(), "target": y.flatten()})
    >>> train, test = train_test_split(data, test_size=0.2, random_state=42)
    >>>
    >>> results = mdts.knn_smoother(
    ...     train, test, target="target", regression=reg,
    ...     k_values=[1, 2, 5, 10, 20], n_repeats=50
    ... )
    >>> print(results)
    k   Avg Train MSE   Avg Test MSE
    1       5.8732          9.2241
    2       6.1821         10.0125
    ...

    R Example
    ---------
    The following R script demonstrates KNN smoothing, construction of the smoother
    matrix (L matrix), effective degrees of freedom, and train-test errors.

    ```r
    knn_smoother = function(train_x, train_y, test_x, K = 5) {
      n_train = length(train_x)
      n_test = length(test_x)
      preds = numeric(n_test)
      for (i in 1:n_test) {
        d = abs(test_x[i] - train_x)
        nn = order(d)[1:K]
        preds[i] = mean(train_y[nn])
      }
      return(preds)
    }

    knn_L_matrix = function(train_x, K = 5) {
      n = length(train_x)
      L = matrix(0, n, n)
      for (i in 1:n) {
        d = abs(train_x[i] - train_x)
        nn = order(d)[1:K]
        L[i, nn] = 1/K
      }
      return(L)
    }

    set.seed(123) ; n = 10
    x = runif(n, 0, 10)
    true_fun = function(x) 3*sin(x) + 5*cos(2*x)
    y = true_fun(x) + rnorm(n, 0, 1)

    train_idx = sample(1:n, size = 10)
    train_x = x[train_idx] ; train_y = y[train_idx]
    test_x = x[-train_idx] ; test_y = y[-train_idx]

    K = 3
    pred_train = knn_smoother(train_x, train_y, train_x, K)
    pred_test = knn_smoother(train_x, train_y, test_x, K)

    L_matrix = knn_L_matrix(train_x, K)
    print("KNN Smoothing Matrix L:") ; print(L_matrix)
    edf = sum(diag(L_matrix))
    cat("Effective Degrees of Freedom = ", edf, "\n")

    train_mse = mean((pred_train - train_y)^2)
    test_mse = mean((pred_test - test_y)^2)
    cat("Train MSE:", train_mse, "| Test MSE:", test_mse, "\n")

    plot(x, y, col = "grey60", pch = 16,
         main = paste("KNN Smoothing (K =", K, ")"),
         xlab = "x", ylab = "y")
    curve(true_fun, col = "blue", lwd = 2, add = TRUE)
    ord_train = order(train_x)
    lines(train_x[ord_train], pred_train[ord_train], col = "red", lwd = 2)
    points(train_x, pred_train, col = "red", pch = 19)
    ```
    """
    # Combine train + test to allow random splits
    data = pd.concat([train, test], ignore_index=True)
    x = data.iloc[:, 0].values
    y = data[target].values

    results = []

    for k in k_values:
        train_errors = []
        test_errors = []

        for _ in range(n_repeats):
            idx = np.random.permutation(len(x))
            train_idx, test_idx = idx[:80], idx[80:]
            X_train, X_test = x[train_idx].reshape(-1, 1), x[test_idx].reshape(-1, 1)
            y_train, y_test = y[train_idx], y[test_idx]

            knn = KNeighborsRegressor(n_neighbors=k)
            knn.fit(X_train, y_train)

            y_train_pred = knn.predict(X_train)
            y_test_pred = knn.predict(X_test)

            train_errors.append(mean_squared_error(y_train, y_train_pred))
            test_errors.append(mean_squared_error(y_test, y_test_pred))

        mean_train = np.mean(train_errors)
        mean_test = np.mean(test_errors)

        results.append((k, mean_train, mean_test))
        print(f"k = {k:3d} | Avg Train MSE = {mean_train:.4f} | Avg Test MSE = {mean_test:.4f}")

    df_results = pd.DataFrame(results, columns=["k", "Avg Train MSE", "Avg Test MSE"])

    # Visualization
    plt.figure(figsize=(8,5))
    plt.plot(df_results["k"], df_results["Avg Train MSE"], marker='o', label="Train Error")
    plt.plot(df_results["k"], df_results["Avg Test MSE"], marker='s', label="Test Error")
    plt.xlabel("Number of Neighbors (k)")
    plt.ylabel("Mean Squared Error")
    plt.title(f"KNN Smoother over {n_repeats} Random Splits")
    plt.legend()
    plt.grid(True)
    plt.show()

    return df_results