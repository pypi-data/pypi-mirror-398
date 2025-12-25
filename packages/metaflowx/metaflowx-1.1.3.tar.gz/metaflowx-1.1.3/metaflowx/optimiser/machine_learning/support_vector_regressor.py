import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.svm import SVR
from sklearn.model_selection import train_test_split, GridSearchCV, KFold, StratifiedKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score
)
from sklearn.impute import SimpleImputer


def support_vector_regressor(
    df,
    target,
    test_size=0.4,
    random_state=42,
    cv_type="kfold"
):
    """
    Perform Support Vector Regression (SVR) with automated preprocessing,
    hyperparameter tuning, and performance visualization.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataset containing both features and the target column.

    target : str
        Name of the target column representing continuous values.

    test_size : float, default=0.4
        Proportion of the dataset allocated for testing.

    random_state : int, default=42
        Seed used to ensure reproducible train-test splits.

    cv_type : str, default="kfold"
        Cross-validation strategy.
        Options:
            "kfold"       : Standard K-Fold CV.
            "stratified"  : Not supported for regression (raises error).

    Returns
    -------
    dict
        Dictionary containing:
            - "best_model" : Trained SVR model with best hyperparameters
            - "best_params" : Selected hyperparameters from GridSearchCV
            - "MAE" : Mean Absolute Error
            - "MSE" : Mean Squared Error
            - "RMSE" : Root Mean Squared Error
            - "R2" : Coefficient of determination (model performance)

    Workflow
    --------
    1. Splits dataset into training and testing partitions.
    2. Imputes missing numeric values using mean strategy.
    3. One-Hot encodes categorical variables when present.
    4. Standardizes features for optimal SVR performance.
    5. Conducts GridSearchCV with selected hyperparameters.
    6. Evaluates test performance using regression metrics.
    7. Produces:
          • Predicted vs Actual plot
          • Residual error plot

    Notes
    -----
    • Stratified cross validation is unavailable in regression contexts.
    • Automatically detects numeric vs categorical columns.

    Examples
    --------
    >>> from sklearn.datasets import fetch_california_housing
    >>> import pandas as pd
    >>> data = fetch_california_housing()
    >>> df = pd.DataFrame(data.data, columns=data.feature_names)
    >>> df['target'] = data.target
    >>> results = support_vector_regressor(df, target='target')
    >>> results['R2']
    0.78  # Example output
    """

    # Separate features and target
    X = df.drop(columns=[target])
    y = df[target]

    numeric_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()

    # Split dataset
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Impute numeric
    num_imputer = SimpleImputer(strategy='mean')
    X_train[numeric_cols] = num_imputer.fit_transform(X_train[numeric_cols])
    X_test[numeric_cols] = num_imputer.transform(X_test[numeric_cols])

    # Encode categoricals
    if categorical_cols:
        encoder = OneHotEncoder(drop=None, sparse_output=False, handle_unknown='ignore')
        encoder.fit(X_train[categorical_cols])

        X_train_enc = encoder.transform(X_train[categorical_cols])
        X_test_enc = encoder.transform(X_test[categorical_cols])

        X_train = pd.concat([
            pd.DataFrame(X_train[numeric_cols], index=X_train.index),
            pd.DataFrame(X_train_enc, index=X_train.index)
        ], axis=1)

        X_test = pd.concat([
            pd.DataFrame(X_test[numeric_cols], index=X_test.index),
            pd.DataFrame(X_test_enc, index=X_test.index)
        ], axis=1)
    else:
        X_train = X_train[numeric_cols]
        X_test = X_test[numeric_cols]

    # Scale values
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # SVR model and parameter grid
    svr = SVR()
    param_grid = {
        'C': [0.1, 1],
        'kernel': ['rbf'],
        'gamma': ['scale']
    }

    # Cross Validation strategy
    if cv_type.lower() == "stratified":
        raise ValueError("Stratified CV is not valid for regression tasks.")
    else:
        cv_strategy = KFold(n_splits=5, shuffle=True, random_state=random_state)

    grid = GridSearchCV(svr, param_grid, cv=cv_strategy, scoring='r2', n_jobs=-1)
    grid.fit(X_train, y_train)

    best_model = grid.best_estimator_
    y_pred = best_model.predict(X_test)

    # Performance evaluation
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    # Plot predictions
    plt.figure()
    plt.scatter(y_test, y_pred)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], linestyle='--')
    plt.title("Predicted vs Actual Values")
    plt.xlabel("Actual")
    plt.ylabel("Predicted")
    plt.show()
 

    # Residual plot
    residuals = y_test - y_pred
    plt.figure()
    plt.scatter(y_pred, residuals)
    plt.axhline(0, linestyle='--')
    plt.title("Residual Plot")
    plt.xlabel("Predicted")
    plt.ylabel("Residuals")
    plt.show()

    # Summary
    print("\n Regal SVR Performance Summary")
    print("-------------------------------------------")
    print(f"CV Type: {cv_type}")
    print(f"Best Hyperparameters: {grid.best_params_}")
    print(f"MAE:   {mae:.4f}")
    print(f"MSE:   {mse:.4f}")
    print(f"RMSE:  {rmse:.4f}")
    print(f"R2 Score: {r2:.4f}")

    return {
        "best_model": best_model,
        "best_params": grid.best_params_,
        "MAE": mae,
        "MSE": mse,
        "RMSE": rmse,
        "R2": r2
    }
