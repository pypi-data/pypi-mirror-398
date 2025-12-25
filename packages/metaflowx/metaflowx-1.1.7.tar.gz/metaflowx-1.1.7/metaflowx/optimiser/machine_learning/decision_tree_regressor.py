import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.tree import DecisionTreeRegressor, plot_tree
from sklearn.model_selection import train_test_split, GridSearchCV, KFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score
)
from sklearn.impute import SimpleImputer


def decision_tree_regressor(df, target, test_size=0.4, random_state=42):
    """
    Train and evaluate a Decision Tree Regressor with automatic preprocessing,
    pruning visualization, and performance metrics.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataset containing both features and the target variable.
    target : str
        Name of the target column for regression.
    test_size : float, optional, default=0.4
        Proportion of the dataset reserved for testing.
    random_state : int, optional, default=42
        Random seed for reproducibility.

    Workflow
    --------
    1. Separates features and target
    2. Handles missing values using median imputation
    3. One-hot encodes categorical columns automatically
    4. Scales features using StandardScaler
    5. Iterates over ccp_alpha values to:
        - Compute train and test R2 scores
        - Track node counts for pruning analysis
        - Plot alpha vs score and alpha vs nodes
    6. Performs GridSearchCV for hyperparameter tuning
    7. Trains and visualizes:
        - Full decision tree
        - Pruned decision tree

    Returns
    -------
    results : dict
        {
            "best_model": trained DecisionTreeRegressor,
            "best_params": grid.best_params_,
            "MAE": float,
            "MSE": float,
            "RMSE": float,
            "R2": float,
            "ccp_alphas": list,
            "train_scores": list,
            "test_scores": list,
            "node_counts": list
        }

    Notes
    -----
    This function includes automatic preprocessing for both numerical and 
    categorical variables and produces insightful visual diagnostics to 
    support model interpretability.
    """
    
    # Separate features and target
    X = df.drop(columns=[target])
    y = df[target]

    numeric_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()

    # Train test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Impute numeric data
    num_imputer = SimpleImputer(strategy='median')
    X_train[numeric_cols] = num_imputer.fit_transform(X_train[numeric_cols])
    X_test[numeric_cols] = num_imputer.transform(X_test[numeric_cols])

    # Encode categorical columns if present
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

    # Scaling
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Base model
    dt = DecisionTreeRegressor(random_state=random_state)

    # Cost Complexity Pruning Path
    path = dt.cost_complexity_pruning_path(X_train, y_train)
    ccp_alphas = path.ccp_alphas

    train_scores, test_scores, node_counts = [], [], []

    for alpha in ccp_alphas:
        dt_temp = DecisionTreeRegressor(random_state=random_state, ccp_alpha=alpha)
        dt_temp.fit(X_train, y_train)
        train_scores.append(dt_temp.score(X_train, y_train))
        test_scores.append(dt_temp.score(X_test, y_test))
        node_counts.append(dt_temp.tree_.node_count)

    # Plot alpha vs scores
    plt.figure(figsize=(10, 5))
    plt.plot(ccp_alphas, train_scores, marker='o', label="Train R2 Score")
    plt.plot(ccp_alphas, test_scores, marker='s', label="Test R2 Score")
    plt.xlabel("ccp_alpha")
    plt.ylabel("R2 Score")
    plt.title("Alpha vs R2 Score")
    plt.legend()
    plt.show()

    # Plot alpha vs number of nodes
    plt.figure(figsize=(10, 5))
    plt.plot(ccp_alphas, node_counts, marker='o', color='purple')
    plt.xlabel("ccp_alpha")
    plt.ylabel("Number of Nodes")
    plt.title("Alpha vs Node Count")
    plt.show()

    # Grid search for hyperparameter tuning
    param_grid = {
        # 'criterion': ['squared_error', 'friedman_mse', 'absolute_error'],
        'criterion': ['squared_error'],
        'max_depth': [None, 5],
        'min_samples_split': [2],
        'min_samples_leaf': [1, 2],
        'ccp_alpha': ccp_alphas
    }

    cv_strategy = KFold(n_splits=5, shuffle=True, random_state=random_state)

    grid = GridSearchCV(dt, param_grid, cv=cv_strategy, scoring='r2', n_jobs=-1)
    grid.fit(X_train, y_train)

    best_model = grid.best_estimator_
    y_pred = best_model.predict(X_test)

    # Evaluation metrics
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    # Full Tree
    full_tree = DecisionTreeRegressor(random_state=random_state)
    full_tree.fit(X_train, y_train)

    # Pruned Tree (Max Depth)
    pruned_tree = DecisionTreeRegressor(max_depth=3, random_state=random_state)
    pruned_tree.fit(X_train, y_train)

    # Plot full tree
    plt.figure(figsize=(18, 10))
    plt.title("Full Decision Tree")
    plot_tree(
        full_tree,
        filled=True,
        feature_names=[f"feature_{i}" for i in range(X_train.shape[1])],
        fontsize=8
    )
    plt.show()

    # Plot pruned tree
    plt.figure(figsize=(18, 10))
    plt.title("Pruned Decision Tree (max_depth=3)")
    plot_tree(
        pruned_tree,
        filled=True,
        feature_names=[f"feature_{i}" for i in range(X_train.shape[1])],
        fontsize=8
    )
    plt.show()

    print("\n Smart Pruned Decision Tree Regressor Results")
    print("----------------------------------------------")
    print(f"Best Hyperparameters: {grid.best_params_}")
    print(f"MAE:   {mae:.4f}")
    print(f"MSE:   {mse:.4f}")
    print(f"RMSE:  {rmse:.4f}")
    print(f"R2:    {r2:.4f}")

    return {
        "best_model": best_model,
        "best_params": grid.best_params_,
        "MAE": mae,
        "MSE": mse,
        "RMSE": rmse,
        "R2": r2,
        "ccp_alphas": ccp_alphas,
        "train_scores": train_scores,
        "test_scores": test_scores,
        "node_counts": node_counts
    }