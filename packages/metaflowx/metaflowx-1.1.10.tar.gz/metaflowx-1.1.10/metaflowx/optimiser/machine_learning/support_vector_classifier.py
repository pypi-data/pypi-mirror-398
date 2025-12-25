import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, GridSearchCV, KFold, StratifiedKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_curve, auc, confusion_matrix, ConfusionMatrixDisplay,
    classification_report
)
from sklearn.impute import SimpleImputer

def support_vector_classifier(
    df,
    target,
    test_size=0.4,
    random_state=42,
    cv_type="stratified"
):
    """
    A refined and adaptable Support Vector Machine classification workflow designed
    to handle both numeric and categorical features gracefully, avoid data leakage,
    and provide strong performance interpretability.

    This function performs:
    • Feature separation, imputation, one-hot encoding, and feature scaling
    • Intelligent CV strategy: StratifiedKFold for class-balanced training
    • Hyperparameter tuning using GridSearchCV across kernels, C, and gamma
    • Comprehensive model evaluation metrics and visual diagnostics

    Parameters
    ----------
    df : pandas.DataFrame
        Complete dataset containing both features and the classification label.
    target : str
        Name of the target column in the DataFrame representing class labels.
    test_size : float, optional (default=0.4)
        Fraction of the dataset allocated to the testing set.
    random_state : int, optional (default=42)
        Seed for reproducibility of training, splits, and SVC behavior.
    cv_type : str, optional (default="stratified")
        Cross-validation strategy. Acceptable values:
        "stratified"  Preserves class distribution across folds.
        "kfold"       Standard KFold without class balancing.

    Returns
    -------
    dict
        {
            "best_model": Trained SVC classifier,
            "best_params": Optimal hyperparameters discovered via GridSearchCV,
            "accuracy": Overall proportion of correct predictions,
            "precision": Positive predictive value,
            "recall": Class sensitivity or hit-rate,
            "f1": Harmonic mean of precision and recall,
            "auc": Area under the ROC curve measuring discriminative power,
            "confusion_matrix": Final computed confusion matrix
        }

    Notes
    -----
    • Suitable for binary or multiclass classification tasks.
    • Visualization includes confusion matrix + ROC curve for binary outcomes.
    • Predictive behavior interpretable via detailed classification report.

    The SVM stands firm like a warrior with a sharpened margin,
    dividing worlds with mathematical elegance,
    ensuring every prediction is a calculated victory.
    """
    
    # Separate features and target
    X = df.drop(columns=[target])
    y = df[target]

    numeric_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()

    # Split early to avoid leakage
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y if cv_type=="stratified" else None
    )

    # Impute numeric
    num_imputer = SimpleImputer(strategy='mean')
    X_train[numeric_cols] = num_imputer.fit_transform(X_train[numeric_cols])
    X_test[numeric_cols] = num_imputer.transform(X_test[numeric_cols])

    # --------------------------------------------
    # Encode categoricals ( If Needed )
    # --------------------------------------------
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

    # Model and params
    svc = SVC(probability=True)
    param_grid = {
        'C': [0.1, 1],
        'kernel': ['linear', 'rbf', 'poly'],
        'gamma': ['scale', 'auto']
    }

    # Choose Cross Validation Strategy
    if cv_type == "stratified":
        cv_strategy = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    else:
        cv_strategy = KFold(n_splits=5, shuffle=True, random_state=random_state)

    # Grid search
    grid = GridSearchCV(svc, param_grid, cv=cv_strategy, scoring='f1', n_jobs=-1)
    grid.fit(X_train, y_train)

    best_model = grid.best_estimator_
    y_pred = best_model.predict(X_test)
    y_proba = best_model.predict_proba(X_test)[:, 1]

    # Performance metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    ConfusionMatrixDisplay(cm).plot(cmap='Blues')
    plt.title("Confusion Matrix")
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

    # Summary
    print("\n Superior SVC Performance Summary")
    print("-------------------------------------------")
    print(f"CV Type: {cv_type}")
    print(f"Best Hyperparameters: {grid.best_params_}")
    print(f"Accuracy:   {accuracy:.4f}")
    print(f"Precision:  {precision:.4f}")
    print(f"Recall:     {recall:.4f}")
    print(f"F1 Score:   {f1:.4f}")
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred))

    return {
        "best_model": best_model,
        "best_params": grid.best_params_,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "auc": roc_auc,
        "confusion_matrix": cm
    }