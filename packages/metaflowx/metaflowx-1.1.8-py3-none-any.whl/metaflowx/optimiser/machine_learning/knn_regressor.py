import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, KFold
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.impute import SimpleImputer


def knn_regressor(df, target, test_size=0.3, random_state=42):
    """
    Perform K-Nearest Neighbors (KNN) regression with automatic preprocessing,
    hyperparameter tuning, and diagnostic visualizations.

    This function handles missing values, encodes categorical variables, scales features,
    selects the optimal value of k through cross-validation, and computes key regression metrics.
    Two plots are generated for validation: K vs Error (Elbow Plot) and Residual Plot.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataset containing predictors and the target column.
    target : str
        Name of the column representing the continuous dependent variable to be predicted.
    test_size : float, optional, default=0.3
        Fraction of the dataset allocated to the test split.
    random_state : int, optional, default=42
        Reproducibility seed for train-test split and hyperparameter search.

    Workflow
    --------
    1. Detect numeric and categorical columns
    2. Impute missing numerical values using median strategy
    3. Encode categorical values using OneHotEncoder with unknown category support
    4. Split dataset into training and testing sets
    5. Standardize features using StandardScaler (fit on training data only)
    6. Tune number of neighbors (k = 1 to 30) via GridSearchCV with KFold
    7. Evaluate best model with regression performance metrics
    8. Visualize:
        • Train/Test MSE vs k
        • Residual Plot on test set predictions

    Returns
    -------
    dict
        Structured results containing:
        - "best_model" : sklearn.neighbors.KNeighborsRegressor
            The final tuned regression model instance.
        - "best_k" : int
            Optimal number of neighbors chosen via cross-validation.
        - "train_MAE" : float
            Mean Absolute Error on training data.
        - "test_MAE" : float
            Mean Absolute Error on test data.
        - "train_RMSE" : float
            Root Mean Squared Error on training predictions.
        - "test_RMSE" : float
            Root Mean Squared Error on test predictions.
        - "r2_score" : float
            R² score measuring predictive performance.
        - "train_errors" : list of float
            MSE values across k values for training data.
        - "test_errors" : list of float
            MSE values across k values for testing data.

    Notes
    -----
    - Converting categories to one-hot vectors may significantly increase feature dimensionality.
    - Test performance should be used to validate generalization and avoid overfitting at low k.

    Example
    -------
    >>> results = knn_regressor(df, target='price')
    >>> print("R2 Score:", results['r2_score'])
    >>> results['best_model'].predict([[3.4, 1.2, 0.5]])
    """

    # Separate features and target
    X = df.drop(columns=[target])
    y = df[target]

    # Detect numeric & categorical columns
    numeric_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()

    # Impute missing numeric data
    num_imputer = SimpleImputer(strategy='median')
    X[numeric_cols] = num_imputer.fit_transform(X[numeric_cols])

    # One-hot encode categorical
    if categorical_cols:
        encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        encoded = encoder.fit_transform(X[categorical_cols])
        X = pd.concat([
            pd.DataFrame(X[numeric_cols], index=X.index),
            pd.DataFrame(encoded, index=X.index)
        ], axis=1)
    else:
        X = X[numeric_cols]

    # Train test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Scale features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Define model
    knn = KNeighborsRegressor()

    # Hyperparameter tuning for best K
    param_grid = {'n_neighbors': list(range(1, 31))}  # Try 1 to 30
    grid = GridSearchCV(knn, param_grid, cv=KFold(5, shuffle=True, random_state=random_state))
    grid.fit(X_train, y_train)

    best_k = grid.best_params_['n_neighbors']
    best_model = grid.best_estimator_

    # Predictions
    y_pred_train = best_model.predict(X_train)
    y_pred_test = best_model.predict(X_test)

    # Metrics
    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    train_rmse = mean_squared_error(y_train, y_pred_train, squared=False)
    test_rmse = mean_squared_error(y_test, y_pred_test, squared=False)
    test_r2 = r2_score(y_test, y_pred_test)

    # Plot 1: Errors vs K values (Elbow style)
    train_errors, test_errors = [], []
    for k in range(1, 31):
        temp = KNeighborsRegressor(n_neighbors=k)
        temp.fit(X_train, y_train)
        train_errors.append(mean_squared_error(y_train, temp.predict(X_train)))
        test_errors.append(mean_squared_error(y_test, temp.predict(X_test)))

    plt.figure(figsize=(10,5))
    plt.plot(range(1,31), train_errors, marker='o', label="Train Error")
    plt.plot(range(1,31), test_errors, marker='s', label="Test Error")
    plt.axvline(best_k, color='red', linestyle='--', label=f"Best K = {best_k}")
    plt.xlabel("K (Neighbors)")
    plt.ylabel("MSE")
    plt.title("K vs Error (Elbow Plot)")
    plt.legend()
    plt.show()

    # Plot 2: Residual Plot
    residuals = y_test - y_pred_test
    plt.figure(figsize=(7,5))
    plt.scatter(y_pred_test, residuals)
    plt.axhline(0, linestyle='--', color='red')
    plt.xlabel("Predicted")
    plt.ylabel("Residuals")
    plt.title("Residual Plot")
    plt.show()

    print("\n💙 KNN Regressor Results 💙")
    print("-------------------------------------------")
    print(f"Best K: {best_k}")
    print(f"Train MAE: {train_mae:.4f}")
    print(f"Test MAE:  {test_mae:.4f}")
    print(f"Train RMSE: {train_rmse:.4f}")
    print(f"Test RMSE:  {test_rmse:.4f}")
    print(f"Test R2 Score: {test_r2:.4f}")

    return {
        'best_model': best_model,
        'best_k': best_k,
        'train_MAE': train_mae,
        'test_MAE': test_mae,
        'train_RMSE': train_rmse,
        'test_RMSE': test_rmse,
        'r2_score': test_r2,
        'train_errors': train_errors,
        'test_errors': test_errors
    }