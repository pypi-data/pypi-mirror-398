import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from scipy.stats import norm

# Kernel Regression Function
def kernel_smoother(train, test, target="target",
                    kernel=["gaussian", "uniform", "triangular", "epanechnikov"],
                    n_repeats=50):
    """
Kernel Smoother: Documentation
---------------------------------------------------------------------------
Parameters
---------------------------------------------------------------------------
train : pandas.DataFrame
    Training dataset with columns:
        • "feature" (predictor)
        • "target"  (response)

test : pandas.DataFrame
    Testing dataset with the same structure as train.

target : str, default = "target"
    Target column name.

kernel : list of str
    Names of kernels to apply. Supported options:
        • "gaussian"
        • "uniform"
        • "epanechnikov"
        • "triangular"
        • "biweight"
        • "triweight"
        • "tricube"

n_repeats : int, default = 50
    Number of repeated evaluations for stable error estimates.
---------------------------------------------------------------------------
R Equivalent Example (Kernel Smoothing with Train/Test Errors)
---------------------------------------------------------------------------
rm(list=ls())
set.seed(1234)
reg = function(x) 5 * sin(x) + 23 * (cos(x))^2
n = 100 ; x = runif(n, 5, 15)
y = reg(x) + rnorm(n, 0, 5)
train_idx = sample(1:n, size = 0.8 * n)
X_train = x[train_idx] ; Y_train = y[train_idx]
X_test = x[-train_idx] ; Y_test = y[-train_idx]

# Kernels
gaussian = function(u) exp(-0.5 * u^2) / sqrt(2*pi)
kernels = list( gaussian = gaussian )
bandwidths = c(0.1, 0.25, 0.5, 1, 2)
n_repeats = 50
results = data.frame()

# Kernel smoothing evaluation
for (kname in names(kernels)) {
  cat("Processing Kernel:", toupper(kname)")
  K = kernels[[kname]]
  for (h in bandwidths) {
    train_err = c()
    test_err = c()
    
    for (r in 1:n_repeats) {
      n_train = length(X_train)
      L = matrix(0, n_train, n_train)
      for (i in 1:n_train) {
        u = (X_train[i] - X_train) / h
        w = K(u)
        L[i, ] = w / sum(w)
      }
      
      Y_pred_train = L %*% Y_train
      train_mse = mean((Y_pred_train - Y_train)^2)
      
      Y_pred_test = numeric(length(X_test))
      for (i in 1:length(X_test)) {
        u = (X_test[i] - X_train) / h
        w = K(u)
        Y_pred_test[i] = sum(w * Y_train) / sum(w)
      }
      test_mse = mean((Y_pred_test - Y_test)^2)
      
      train_err = c(train_err, train_mse)
      test_err = c(test_err, test_mse)
    }
    
    results = rbind(results, data.frame(
      Kernel = kname,
      h = h,
      Avg_Train_MSE = mean(train_err),
      Avg_Test_MSE = mean(test_err)
    ))
  }
}

print(results)

for (kname in names(kernels)) {
  df = subset(results, Kernel == kname)
  best_h = df$h[which.min(df$Avg_Test_MSE)]
  K = kernels[[kname]]
  cat("Best bandwidth for", kname, "=", best_h)
  
  x_grid = seq(min(X_train), max(X_train), length.out = 200)
  y_smooth = numeric(length(x_grid))
  
  for (i in 1:length(x_grid)) {
    u = (x_grid[i] - X_train) / best_h
    w = K(u)
    y_smooth[i] = sum(w * Y_train) / sum(w)
  }
  
  plot(X_train, Y_train, col="blue", pch=16,
       main=paste(kname, "Kernel Regression Fit"),
       xlab="X", ylab="Y")
  points(X_test, Y_test, col="orange", pch=16)
  lines(x_grid, y_smooth, col="red", lwd=2)
  legend("topleft", legend=c("Train","Test","Fit"),
         col=c("blue","orange","red"), pch=c(16,16,NA), lty=c(NA,NA,1))
}

---------------------------------------------------------------------------
Returns
---------------------------------------------------------------------------
pandas.DataFrame
    Summary of training/testing MSE for each kernel-bandwidth combination.
"""
    X_train = train["feature"].values
    y_train = train[target].values
    X_test = test["feature"].values
    y_test = test[target].values

    # Bandwidth values (h or σ)
    bandwidths = [0.1, 0.25, 0.5, 1, 2]
    def gaussian_kernel(u): return (1/np.sqrt(2*np.pi)) * np.exp(-u**2 / 2)
    def uniform_kernel(u): return np.where(np.abs(u) <= 1, 1/2, 0)
    def epanechnikov_kernel(u): return np.where(np.abs(u) <= 1, 3/4 * (1 - u**2), 0)
    def triangular_kernel(u): return np.where(np.abs(u) < 1, (35/32) * (1 - u**2)**3, 0)
    def biweight_kernel(u): return np.where(np.abs(u) <= 1, 15/16 * (1 - u**2)**2, 0)
    def triweight_kernel(u): return np.where(np.abs(u) <= 1, 35/32 * (1 - u**2)**3, 0)
    def tricube_kernel(u): return np.where(np.abs(u) <= 1, 70/81 * (1 - np.abs(u)**3)**3, 0)


    kernels = {
    "gaussian": gaussian_kernel,
    "uniform": uniform_kernel,
    "epanechnikov": epanechnikov_kernel,
    "triangular": triangular_kernel,
    "biweight": biweight_kernel,
    "triweight": triweight_kernel,
    "tricube": tricube_kernel
    }
    results = []

    # Compute Regression for Each Kernel
    for k_name in kernel:
        K = kernels[k_name]
        print(f"\nProcessing Kernel: {k_name.upper()}")

        for h in bandwidths:
            train_errors = []
            test_errors = []

            for _ in range(n_repeats):
                # Predict on train and test
                def kernel_regression(x_query, X, Y, h):
                    weights = K((x_query - X[:, None]) / h)
                    numer = np.dot(weights.T, Y)
                    denom = np.sum(weights, axis=0)
                    denom = np.where(denom == 0, 1e-8, denom) 
                    return numer / denom

                y_pred_train = kernel_regression(X_train, X_train, y_train, h)
                y_pred_test = kernel_regression(X_test, X_train, y_train, h)

                train_mse = mean_squared_error(y_train, y_pred_train)
                test_mse = mean_squared_error(y_test, y_pred_test)

                train_errors.append(train_mse)
                test_errors.append(test_mse)

            avg_train_err = np.mean(train_errors)
            avg_test_err = np.mean(test_errors)
            results.append({
                "Kernel": k_name,
                "h": h,
                "Avg Train error": avg_train_err,
                "Avg Test error": avg_test_err
            })

    Res_df = pd.DataFrame(results)

    # Plot Average Train/Test MSE vs h
    for k_name in kernel:
        df_k = Res_df[Res_df["Kernel"] == k_name]
        plt.figure(figsize=(8, 5))
        plt.plot(df_k["h"], df_k["Avg Train error"], label="Avg Train error", marker="o")
        plt.plot(df_k["h"], df_k["Avg Test error"], label="Avg Test error", marker="s")
        plt.xlabel("Bandwidth (h)", fontsize=14)
        plt.ylabel("Average MSE", fontsize=14)
        plt.title(f"{k_name.capitalize()} Kernel: Train vs Test Error", fontsize=16)
        plt.legend()
        plt.grid(True)
        plt.show()

        # Plot Scatter + Smoothed Line
        plt.figure(figsize=(8, 5))
        plt.scatter(X_train, y_train, color="blue", alpha=0.6, label="Train Data")
        plt.scatter(X_test, y_test, color="orange", alpha=0.6, label="Test Data")

        x_grid = np.linspace(min(X_train), max(X_train), 200)
        y_smooth = []

        best_h = df_k.loc[df_k["Avg Test error"].idxmin(), "h"]
        for xq in x_grid:
            weights = K((xq - X_train) / best_h)
            y_hat = np.sum(weights * y_train) / np.sum(weights)
            y_smooth.append(y_hat)

        plt.plot(x_grid, y_smooth, color="blue", linewidth=1,
                 label=f"Smoothed ({k_name}, h={best_h})")
        plt.xlabel("Feature", fontsize=14)
        plt.ylabel("Target", fontsize=14)
        plt.title(f"{k_name.capitalize()} Kernel Regression Fit", fontsize=16)
        plt.legend()
        plt.grid(True)
        plt.show()

    return Res_df