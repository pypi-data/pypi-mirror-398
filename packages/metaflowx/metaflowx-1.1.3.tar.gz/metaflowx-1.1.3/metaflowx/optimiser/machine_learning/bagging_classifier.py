import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.impute import SimpleImputer
from sklearn.ensemble import BaggingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier


def bagging_classifier(data, target, method="decision_tree",
                           cat_cols=None,
                           n_estimators=50, test_size=0.2,
                           random_state=42, plot_feature_importance=True):
    """
    The Bagging Ensemble Maestro:
    An educational yet powerful classifier that harmonizes multiple models
    to outperform a lonely learner. Handles categorical chaos, numerical nuance, 
    missing mysteries, and scales data like a gentleman.

    Description:
        This function automatically preprocesses the dataset by imputing missing values,
        encoding categorical variables, scaling numerical features, and then trains a 
        BaggingClassifier ensemble. The base model can be chosen from a variety of 
        popular algorithms. Evaluation metrics, including classification report, 
        confusion matrix, and cross-validation accuracy, are printed with flair.
        Optionally, if supported by the model, the top feature importances are visualized.

    Parameters:
        data (pd.DataFrame):
            A pandas DataFrame containing both features and target.
        target (str):
            The name of the target column for classification.
        method (str, optional):
            Base estimator type to be bagged. Choose from:
            "decision_tree", "logistic", "svm", "knn", "random_forest".
            Default is "decision_tree".
        cat_cols (list, optional):
            List of categorical feature column names. If None, automatically detected.
        n_estimators (int, optional):
            Number of estimators (models) inside the bagging ensemble. Default is 50.
        test_size (float, optional):
            Proportion of the dataset reserved for testing. Default is 0.2.
        random_state (int, optional):
            Seed for reproducibility. Default is 42.
        plot_feature_importance (bool, optional):
            Whether to display top feature importance plot. Default True.

    Returns:
        BaggingClassifier:
            The trained ensemble model, ready to make predictions that would impress
            even the strictest professors at SXC.

    Example:
        >>> model = bagging_classifier(
        ...     data=df,
        ...     target="purchased",
        ...     method="decision_tree",
        ...     cat_cols=["gender"],
        ...     n_estimators=20,
        ...     test_size=0.3
        ... )

    Author:
        SXC_Student_developer_Community

    """

    # --- Step 1: Split features and target ---
    X = data.drop(columns=[target])
    y = data[target]

    # --- Step 2: Identify categorical and numeric columns ---
    if cat_cols is None:
        cat_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
    num_cols = [col for col in X.columns if col not in cat_cols]

    if len(cat_cols) == 0:
        print("ℹ No categorical columns detected. Proceeding with numeric-only features.")
    else:
        print(f"Categorical columns: {cat_cols}")
    print(f"Numerical columns: {num_cols}")

    # --- Step 3: Handle missing values ---
    num_imputer = SimpleImputer(strategy='mean')
    X_num = pd.DataFrame(num_imputer.fit_transform(X[num_cols]),
                         columns=num_cols, index=X.index) if num_cols else pd.DataFrame(index=X.index)

    if len(cat_cols) > 0:
        cat_imputer = SimpleImputer(strategy='most_frequent')
        X_cat = pd.DataFrame(cat_imputer.fit_transform(X[cat_cols]),
                             columns=cat_cols, index=X.index)
    else:
        X_cat = pd.DataFrame(index=X.index)

    # --- Step 4: One-hot encode categorical data ---
    if not X_cat.empty:
        ohe = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
        X_cat_encoded = pd.DataFrame(ohe.fit_transform(X_cat),
                                     columns=ohe.get_feature_names_out(cat_cols),
                                     index=X.index)
    else:
        X_cat_encoded = pd.DataFrame(index=X.index)

    # --- Step 5: Standardize numeric data ---
    if not X_num.empty:
        scaler = StandardScaler()
        X_num_scaled = pd.DataFrame(scaler.fit_transform(X_num),
                                    columns=num_cols, index=X.index)
    else:
        X_num_scaled = pd.DataFrame(index=X.index)

    # --- Step 6: Combine all processed features ---
    X_processed = pd.concat([X_num_scaled, X_cat_encoded], axis=1)

    # --- Step 7: Train/test split ---
    X_train, X_test, y_train, y_test = train_test_split(
        X_processed, y, test_size=test_size, random_state=random_state)

    # --- Step 8: Choose base model ---
    if method.lower() == "decision_tree":
        base = DecisionTreeClassifier(random_state=random_state)
    elif method.lower() == "logistic":
        base = LogisticRegression(max_iter=2000)
    elif method.lower() == "svm":
        base = SVC(probability=True)
    elif method.lower() == "knn":
        base = KNeighborsClassifier()
    elif method.lower() == "random_forest":
        base = RandomForestClassifier(random_state=random_state)
    else:
        raise ValueError("Choose from: decision_tree, logistic, svm, knn, random_forest")

    # --- Step 9: Bagging ensemble ---
    bagger = BaggingClassifier(
        estimator=base,
        n_estimators=n_estimators,
        random_state=random_state
    )

    # --- Step 10: Train and evaluate ---
    bagger.fit(X_train, y_train)
    y_pred = bagger.predict(X_test)

    print(f"\n=== Bagging Model: {method.upper()} ===")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    cv_scores = cross_val_score(bagger, X_processed, y, cv=5)
    print(f"\nCV Accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # --- Step 11: Feature importance plot ---
    if plot_feature_importance:
        try:
            importances = np.mean([
                est.feature_importances_ for est in bagger.estimators_
                if hasattr(est, "feature_importances_")
            ], axis=0)

            feature_names = X_processed.columns
            sorted_idx = np.argsort(importances)[::-1][:15]

            plt.figure(figsize=(10, 5))
            plt.bar(range(len(sorted_idx)), importances[sorted_idx])
            plt.xticks(range(len(sorted_idx)),
                       np.array(feature_names)[sorted_idx],
                       rotation=45, ha="right")
            plt.title("Top Feature Importances")
            plt.tight_layout()
            plt.show()

        except Exception:
            print("\n⚠ Feature importance not available for this method.")

    return bagger

# Example usage: ( If gender is categorical, pass it explicitly: )
# model = bagging_classification(data=df, target="purchased", method="decision_tree", cat_cols=["gender"], n_estimators=20, test_size=0.3, plot_feature_importance=True)

# Example usage: ( Multiple Categorical Variables )
# cat_columns = ["gender", "city", "education_level"]
# model = bagging_classification(data=df, target="target_col", method="random_forest", cat_cols=cat_columns, n_estimators=50, test_size=0.2)
