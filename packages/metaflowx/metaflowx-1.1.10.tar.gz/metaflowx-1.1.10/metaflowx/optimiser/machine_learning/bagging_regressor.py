import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.ensemble import BaggingRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer


def bagging_regressor(
    df,
    target,
    cat_cols=None,
    n_estimators=50,
    test_size=0.2,
    random_state=42
):
    """
    Bagging Regressor: Ensemble Learning for Robust Regression Performance

    This function performs automatic preprocessing and regression
    using a Bagging ensemble of DecisionTreeRegressor models. It
    supports both numerical and categorical features, imputes missing
    values, scales numerical variables, encodes categorical variables,
    and evaluates model performance with standard regression metrics.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataset containing features and target variable.
    target : str
        Name of the target column for regression.
    cat_cols : list, optional
        List of categorical feature column names. If None, the
        function automatically detects them. Default is None.
    n_estimators : int, optional
        Number of estimators in the bagging ensemble.
        Default is 50.
    test_size : float, optional
        Proportion of the dataset reserved for testing.
        Default is 0.2.
    random_state : int, optional
        Seed value for reproducibility. Default is 42.

    Returns
    -------
    BaggingRegressor
        Trained regression model ready for prediction.

    Notes
    -----
    • Automatically preprocesses mixed-type datasets.
    • Suitable for internal academic research and practical 
      education at SXC.
    • Provides comprehensive evaluation including MAE, MSE,
      RMSE, and R² Score.
    • Generates a prediction comparison plot for quick insight.

    Example
    -------
    >>> model = bagging_regressor(
    ...     df=data,
    ...     target="price",
    ...     cat_cols=["region", "type"],
    ...     n_estimators=30,
    ...     test_size=0.25
    ... )

    Author
    ------
    SXC_Student_Developer_Community
    """
    
    X = df.drop(columns=[target])
    y = df[target]

    # Auto-detect categorical columns if not provided
    if cat_cols is None:
        cat_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
    num_cols = [col for col in X.columns if col not in cat_cols]

    # Impute and scale numeric columns
    if len(num_cols) > 0:
        num_imputer = SimpleImputer(strategy="median")
        X_num = pd.DataFrame(num_imputer.fit_transform(X[num_cols]),
                             columns=num_cols, index=X.index)
        X_num = pd.DataFrame(StandardScaler().fit_transform(X_num),
                             columns=num_cols, index=X.index)
    else:
        X_num = pd.DataFrame(index=X.index)

    # Encode categorical columns
    if len(cat_cols) > 0:
        ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        X_cat_encoded = pd.DataFrame(
            ohe.fit_transform(X[cat_cols]),
            columns=ohe.get_feature_names_out(cat_cols),
            index=X.index
        )
    else:
        X_cat_encoded = pd.DataFrame(index=X.index)

    # Combine all preprocessed features
    X_processed = pd.concat([X_num, X_cat_encoded], axis=1)

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_processed, y, test_size=test_size, random_state=random_state
    )

    # Create model
    model = BaggingRegressor(
        estimator=DecisionTreeRegressor(random_state=random_state),
        n_estimators=n_estimators,
        random_state=random_state
    )

    # Fit and predict
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    # Performance metrics
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    print("\n Bagging Regressor Results")
    print(f"MAE:  {mae:.4f}")
    print(f"MSE:  {mse:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"R² Score: {r2:.4f}")

    # Visualization
    plt.figure(figsize=(7, 4))
    plt.scatter(y_test, y_pred, alpha=0.6)
    plt.plot([y.min(), y.max()], [y.min(), y.max()], linestyle='--')  # reference line
    plt.xlabel("Actual")
    plt.ylabel("Predicted")
    plt.title("Bagging Regressor Predictions 💙")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    return model