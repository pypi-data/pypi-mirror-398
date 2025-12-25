import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.model_selection import train_test_split, GridSearchCV, KFold, StratifiedKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_curve, auc, confusion_matrix, ConfusionMatrixDisplay,
    classification_report
)
from sklearn.impute import SimpleImputer

def decision_tree_classifier(df, target, test_size=0.4, random_state=42, cv_type="stratified"):
    """
    Decision Tree Classifier with Automatic Preprocessing, Pruning, and Model Selection

    This function builds a Decision Tree classifier with advanced preprocessing
    and evaluation capabilities. It handles both numerical and categorical data,
    performs imputation, scaling, one-hot encoding, stratified or standard CV splitting,
    applies pruning techniques, performs hyperparameter tuning using GridSearchCV,
    and generates performance diagnostics including ROC curves, accuracy plots, 
    and confusion matrices.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataset including both feature variables and the target column.
    target : str
        Name of the target column for classification tasks.
    test_size : float, optional
        Fraction of the dataset set aside for testing. Default is 0.4.
    random_state : int, optional
        Seed used for reproducibility. Default is 42.
    cv_type : str, optional
        Either "stratified" for classification-sensitive splits or "kfold".
        Default is "stratified".

    Returns
    -------
    dict
        A dictionary containing:
        • best_model : Optimized DecisionTreeClassifier instance  
        • best_params : Best hyperparameters obtained from GridSearchCV  
        • accuracy : Final classification accuracy  
        • precision : Weighted precision score  
        • recall : Weighted recall score  
        • f1 : Weighted F1 score  
        • auc : Area under the ROC curve  
        • confusion_matrix : Final confusion matrix  
        • ccp_alphas : Complexity pruning values tested  
        • train_acc : Training accuracy for pruning evaluation  
        • test_acc : Testing accuracy for pruning evaluation  
        • node_counts : Node counts across pruning configurations  

    Notes
    -----
    • Automatically manages datasets with mixed feature types.  
    • Evaluates over a range of pruning strengths (ccp_alpha).  
    • Supports cost complexity pruning and detailed tree visualization.  
    • Intended for internal academic use and educational deployment at SXC.  

    Example
    -------
    >>> results = decision_tree_classifier(
    ...     df=data,
    ...     target="class",
    ...     test_size=0.3,
    ...     random_state=7,
    ...     cv_type="stratified"
    ... )
    >>> results["accuracy"]

    Author
    ------
    SXC_Student_Developer_Community
    """
    
    # Separate features and target
    X = df.drop(columns=[target])
    y = df[target]

    numeric_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()

    # Train test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state,
        stratify=y if cv_type == "stratified" else None
    )

    # Impute numeric
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
    dt = DecisionTreeClassifier(random_state=random_state)

    # Cost Complexity Pruning Path
    path = dt.cost_complexity_pruning_path(X_train, y_train)
    ccp_alphas = path.ccp_alphas

    train_acc, test_acc, node_counts = [], [], []

    for alpha in ccp_alphas:
        dt_temp = DecisionTreeClassifier(random_state=random_state, ccp_alpha=alpha)
        dt_temp.fit(X_train, y_train)
        train_acc.append(dt_temp.score(X_train, y_train))
        test_acc.append(dt_temp.score(X_test, y_test))
        node_counts.append(dt_temp.tree_.node_count)

    # Plot 1: alpha vs accuracy (train & test)
    plt.figure(figsize=(10, 5))
    plt.plot(ccp_alphas, train_acc, marker='o', label="Train Accuracy")
    plt.plot(ccp_alphas, test_acc, marker='s', label="Test Accuracy")
    plt.xlabel("ccp_alpha")
    plt.ylabel("Accuracy")
    plt.title("Alpha vs Accuracy")
    plt.legend()
    plt.show()

    # Plot 2: alpha vs node count
    plt.figure(figsize=(10, 5))
    plt.plot(ccp_alphas, node_counts, marker='o', color='purple')
    plt.xlabel("ccp_alpha")
    plt.ylabel("Number of Nodes")
    plt.title("Alpha vs Node Count")
    plt.show()

    # Grid search for best model
    param_grid = {
        'criterion': ['gini', 'entropy'],
        'max_depth': [None, 5, 10, 20],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 5],
        'ccp_alpha': ccp_alphas
    }

    if cv_type == "stratified":
        cv_strategy = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    else:
        cv_strategy = KFold(n_splits=5, shuffle=True, random_state=random_state)

    grid = GridSearchCV(dt, param_grid, cv=cv_strategy, scoring='f1', n_jobs=-1)
    grid.fit(X_train, y_train)

    best_model = grid.best_estimator_
    y_pred = best_model.predict(X_test)
    y_proba = best_model.predict_proba(X_test)[:, 1]

    # Final metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    ConfusionMatrixDisplay(cm).plot(cmap='Greens')
    plt.title("Decision Tree Confusion Matrix")
    plt.show()

    # ROC curve
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    roc_auc = auc(fpr, tpr)
    plt.figure()
    plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.4f}")
    plt.plot([0, 1], [0, 1], linestyle='--')
    plt.title("ROC Curve")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.legend()
    plt.show()

   # Full Tree (No pruning)
    full_tree = DecisionTreeClassifier(random_state=42)
    full_tree.fit(X_train, y_train)

    # Pruned Tree (Using Max Depth)
    pruned_tree = DecisionTreeClassifier(max_depth=3, random_state=42)
    pruned_tree.fit(X_train, y_train)

    # Plot Full Tree
    plt.figure(figsize=(18, 10))
    plt.title("Full Decision Tree")
    plot_tree(
    full_tree,
    filled=True,
    feature_names=[f"feature_{i}" for i in range(X_train.shape[1])],
    class_names=[str(cls) for cls in np.unique(y)],
    fontsize=8
    )
    plt.show()

    # Plot Pruned Tree
    plt.figure(figsize=(18, 10))
    plt.title("Pruned Decision Tree (max_depth=3)")
    plot_tree(
        pruned_tree,
        filled=True,
        feature_names=[f"feature_{i}" for i in range(X_train.shape[1])],
        class_names=[str(cls) for cls in np.unique(y)],
        fontsize=8
    )
    plt.show()

    print("\n Smart Pruned Decision Tree Results")
    print("-------------------------------------------")
    print(f"Best Hyperparameters: {grid.best_params_}")
    print(f"Accuracy:   {accuracy:.4f}")
    print(f"Precision:  {precision:.4f}")
    print(f"Recall:     {recall:.4f}")
    print(f"F1 Score:   {f1:.4f}")

    return {
        "best_model": best_model,
        "best_params": grid.best_params_,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "auc": roc_auc,
        "confusion_matrix": cm,
        "ccp_alphas": ccp_alphas,
        "train_acc": train_acc,
        "test_acc": test_acc,
        "node_counts": node_counts
    }