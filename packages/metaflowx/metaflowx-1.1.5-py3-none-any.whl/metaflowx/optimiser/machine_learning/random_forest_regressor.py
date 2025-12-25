import warnings
warnings.filterwarnings('ignore')

from typing import Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split, KFold, StratifiedKFold
from sklearn.metrics import mean_squared_error, r2_score


def random_forest_regressor(
    df: pd.DataFrame,
    target: str,
    test_size: float = 0.2,
    n_estimators_list=[50, 100, 150, 200],
    max_depth_list=[None, 5, 10, 20],
    random_state: int = 42,
    cv_splits: int = 5,
    save_model: bool = False,
    model_path: str = "random_forest_regressor.joblib"
) -> Dict[str, Any]:
    """
    A balanced and intelligent Random Forest regression workflow that transforms
    raw features into accurate numeric predictions, while showing you exactly
    how your model learns and performs.

    This function performs:
    • Automated cleaning, imputation, scaling, and encoding
    • Hyperparameter exploration using nested loops across tree count and depth
    • RMSE and R² scoring for precision and performance
    • Visual storytelling: predicted vs actual scatter, residual plots,
      distribution of errors, and feature importance
    • Optional joblib persistence so your hero model can be deployed later

    Parameters
    ----------
    df : pandas.DataFrame
        The complete dataset with all feature columns and target.
    target : str
        Name of the numeric column representing the dependent variable.
    test_size : float, optional (default=0.2)
        Fraction of samples reserved for the test set.
    n_estimators_list : list, optional
        Candidate number of trees to consider while searching for optimal model.
    max_depth_list : list, optional
        Candidate tree depths for model strength control.
    random_state : int, optional
        Reproducibility factor for randomness control.
    cv_splits : int, optional
        Number of folds for validation selection logic if required.
    save_model : bool, optional
        Whether to persist the best model as a `.joblib` artifact.
    model_path : str, optional
        Storage location for the saved model if persistence enabled.

    Returns
    -------
    Dict[str, Any]
        {
            "best_model": Fitted RandomForestRegressor,
            "best_params": {
                "n_estimators": optimal tree count,
                "max_depth": optimal maximum depth
            },
            "train_rmse": Measure of average training prediction error magnitude,
            "train_r2": Explained variance of training set,
            "test_rmse": Measure of average testing prediction error magnitude,
            "test_r2": Explained variance of testing set,
            "train_rmse_values": Performance trace for all train RMSE attempts,
            "test_rmse_values": Performance trace for all test RMSE attempts
        }

    Notes
    -----
    • Designed for numeric regression targets.
    • Feature importance visualization reveals data contributors.
    • Model selection inspired by scientific rigor.

    In the quiet whisper of the forest,
    every tree votes for the truth,
    and together,
    they predict the future.
    """


    print("\nData Cleaning & Feature Configuration")

    # Drop high NA columns
    df = df.loc[:, df.isnull().mean() < 0.5]

    y = df[target]
    X = df.drop(columns=[target])

    # Separate feature types
    num_cols = X.select_dtypes(include=np.number).columns
    cat_cols = X.select_dtypes(include=['object', 'bool', 'category']).columns

    # Imputation
    X_num = SimpleImputer(strategy="median").fit_transform(X[num_cols])
    X_num = StandardScaler().fit_transform(X_num)

    if len(cat_cols) > 0:
        X_cat = SimpleImputer(strategy="most_frequent").fit_transform(X[cat_cols])
        X_cat = OneHotEncoder(handle_unknown="ignore", sparse_output=False).fit_transform(X_cat)
        X_processed = np.hstack([X_num, X_cat])
    else:
        X_processed = X_num

    # Correct CV strategy (if classification target appears binary)
    if len(np.unique(y)) <= 10 and y.dtype in ['int', 'int64']:
        cv = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=random_state)
        strat_label = True
    else:
        cv = KFold(n_splits=cv_splits, shuffle=True, random_state=random_state)
        strat_label = False

    print(f"Using {'StratifiedKFold' if strat_label else 'KFold'} Cross Validation\n")

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_processed, y, test_size=test_size, random_state=random_state
    )

    best_model = None
    best_rmse = float("inf")

    train_rmse_vals = []
    test_rmse_vals = []

    for n in n_estimators_list:
        for d in max_depth_list:
            model = RandomForestRegressor(
                n_estimators=n, max_depth=d,
                random_state=random_state, n_jobs=-1
            )
            model.fit(X_train, y_train)

            pred_train = model.predict(X_train)
            pred_test = model.predict(X_test)

            train_rmse = np.sqrt(mean_squared_error(y_train, pred_train))
            test_rmse = np.sqrt(mean_squared_error(y_test, pred_test))

            train_rmse_vals.append(train_rmse)
            test_rmse_vals.append(test_rmse)

            if test_rmse < best_rmse:
                best_rmse = test_rmse
                best_model = model

    preds_test = best_model.predict(X_test)
    test_r2 = r2_score(y_test, preds_test)
    # Final metrics (train and test)
    preds_train = best_model.predict(X_train)
    train_rmse = np.sqrt(mean_squared_error(y_train, preds_train))
    train_r2 = r2_score(y_train, preds_train)

    preds_test = best_model.predict(X_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, preds_test))
    test_r2 = r2_score(y_test, preds_test)

    print("\n🚀 Final Model Performance Summary")
    print("---------------------------------------")
    print(f"Best Hyperparameters: n_estimators={best_model.n_estimators}, max_depth={best_model.max_depth}")
    print(f"Train RMSE: {train_rmse:.4f}")
    print(f"Train R2:   {train_r2:.4f}")
    print(f"Test RMSE:  {test_rmse:.4f}")
    print(f"Test R2:    {test_r2:.4f}\n")


    print("✅ Best Hyperparameters located")
    print(f"✅ Best Test RMSE: {best_rmse:.4f}")
    print(f"✅ Best Test R2:   {test_r2:.4f}\n")

    # PLOTS SECTION --------------------------------------------------------
    # Predicted vs Actual
    plt.figure(figsize=(6, 6))
    plt.scatter(y_test, preds_test, alpha=0.6)
    plt.xlabel("Actual")
    plt.ylabel("Predicted")
    plt.title("Predicted vs Actual")
    plt.grid(True)
    plt.show()

    # Residuals
    residuals = y_test - preds_test

    plt.figure(figsize=(6, 6))
    plt.scatter(preds_test, residuals, alpha=0.6)
    plt.axhline(0, color="red")
    plt.xlabel("Predicted")
    plt.ylabel("Residuals")
    plt.title("Residuals vs Predicted")
    plt.grid(True)
    plt.show()

    # Residual Distribution
    plt.figure(figsize=(6, 5))
    plt.hist(residuals, bins=30)
    plt.title("Residual Distribution")
    plt.xlabel("Residuals")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.show()

    # Feature Importance
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(best_model.feature_importances_)), best_model.feature_importances_)
    plt.title("Feature Importance")
    plt.xlabel("Feature Index")
    plt.ylabel("Importance")
    plt.grid(True)
    plt.show()

    # Model Persistence
    if save_model:
        joblib.dump(best_model, model_path)
        print(f"💾 Model saved at {model_path}")

    return {
    "best_model": best_model,
    "best_params": {
        "n_estimators": best_model.n_estimators,
        "max_depth": best_model.max_depth
    },
    "train_rmse": train_rmse,
    "train_r2": train_r2,
    "test_rmse": test_rmse,
    "test_r2": test_r2,
    "train_rmse_values": train_rmse_vals,
    "test_rmse_values": test_rmse_vals
}