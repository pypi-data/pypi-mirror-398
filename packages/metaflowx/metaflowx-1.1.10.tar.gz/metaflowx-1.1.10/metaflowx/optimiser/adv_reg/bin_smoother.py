import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def bin_smoother(train, test, target="target", regression=None, bin=5):
    """
    Perform bin smoothing estimation for a univariate nonparametric regression model.

    The method divides the range of the covariate variable into a specified number of
    equal-width bins using only the training set. It then estimates a stepwise regression
    curve by computing the mean of the regression function values within each bin.

    Parameters
    ----------
    train : pandas.DataFrame
        Training dataset containing the covariate in the first column and the response
        specified by the target parameter.
    test : pandas.DataFrame
        Test dataset with similar structure as train.
    target : str, optional
        Name of the response variable column. Default is "target".
    regression : callable, optional
        A function that represents the true regression function f(x). It must accept
        a NumPy array of x values and return predicted y values of equal length.
    bin : int, optional
        Number of equal-width bins for bin smoothing. Default is 5.
        
    Example
    -------
    >>> from sxc import mdts
    >>> import numpy as np
    >>> import pandas as pd
    >>>
    >>> np.random.seed(1234)
    >>> def reg(x):
    ...     return 5*np.sin(x) + 23*(np.cos(x)**2)
    >>>
    >>> x = np.random.uniform(5, 15, 100)
    >>> y = reg(x) + np.random.normal(0, 5, 100)
    >>> data = pd.DataFrame({"feature": x, "target": y})
    >>> train = data.iloc[:80]
    >>> test = data.iloc[80:]
    >>>
    >>> mdts.bin_smoother(train, test, target="target", regression=reg, bin=10)
    """
    # Function body continues here...

    X_train = train.iloc[:, 0].values
    y_train = train[target].values

    X_test = test.iloc[:, 0].values
    y_test = test[target].values

    # Create bins using training data
    bins = np.linspace(X_train.min(), X_train.max(), bin + 1)
    bin_indices = np.digitize(X_train, bins) - 1

    # Compute mean predicted value in each bin
    bin_means = []
    for i in range(bin):
        in_bin = bin_indices == i
        if np.any(in_bin):
            bin_means.append(np.mean(regression(X_train[in_bin])))
        else:
            bin_means.append(0)

    bin_means = np.array(bin_means)

    # Step smoother prediction helper
    def step_predict(x_values):
        preds = np.zeros_like(x_values, float)
        idx = np.digitize(x_values, bins) - 1
        for i in range(bin):
            preds[idx == i] = bin_means[i]
        return preds

    # Compute errors
    train_pred = step_predict(X_train)
    test_pred = step_predict(X_test)

    train_mse = np.mean((y_train - train_pred)**2)
    test_mse = np.mean((y_test - test_pred)**2)

    # Plotting
    plt.figure(figsize=(10, 6))
    
    # Scatter
    plt.scatter(X_train, y_train, label="Train", alpha=0.7)
    plt.scatter(X_test, y_test, label="Test", marker='s')

    # True function curve
    x_curve = np.linspace(X_train.min(), X_train.max(), 400)
    plt.plot(x_curve, regression(x_curve), label="True function", color='blue')

    # Step horizontal segments
    for i in range(bin):
        plt.hlines(bin_means[i], bins[i], bins[i+1], colors='red', linewidth=2)

    # Vertical dotted bin edges
    for b in bins:
        plt.axvline(x=b, linestyle='dotted', color='gray')

    plt.title(f'k = {bin}')
    
    # Legend at top right corner
    plt.legend(loc='upper right')

    plt.grid(True)
    plt.show()

    print(f"Train MSE: {train_mse:.4f}")
    print(f"Test  MSE: {test_mse:.4f}")

    bin_summary = pd.DataFrame({
    "Bin": [f"{i+1}" for i in range(bin)],
    "Range Start": [round(bins[i], 3) for i in range(bin)],
    "Range End": [round(bins[i+1], 3) for i in range(bin)],
    "Mean Estimate": [round(bin_means[i], 3) for i in range(bin)]
    })
    print("Summary Table:")
    print(bin_summary.to_string(index=False))

    # return {
    #     "train_mse": train_mse,
    #     "test_mse": test_mse,
    #     "bin_means": bin_means,
    #     "bin_edges": bins
    # }