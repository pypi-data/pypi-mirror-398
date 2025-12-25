import warnings
warnings.filterwarnings('ignore')

from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split, GridSearchCV, learning_curve, validation_curve, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, precision_recall_curve,
    confusion_matrix, ConfusionMatrixDisplay, PrecisionRecallDisplay,
    matthews_corrcoef, log_loss,mean_squared_error
)
from sklearn.calibration import CalibrationDisplay


def random_forest_classifier(
    df: pd.DataFrame,
    target: str,
    test_size: float = 0.2,
    param_grid: Optional[Dict[str, List[Any]]] = None,
    random_state: int = 42,
    cv_folds: int = 5,
    save_artifacts: bool = False,
    artifact_prefix: str = "rfc_artifact"
) -> Dict[str, Any]:
    """
    A refined Random Forest classification pipeline that transforms your raw dataset
    into smart predictions, charming visuals, and a well-behaved model that knows
    how to perform.

    The function handles:
    • Intelligent preprocessing of numerical and categorical variables
    • Model tuning through Grid Search with cross-validation
    • Comprehensive evaluation metrics including AUC, MCC, F1, and specificity
    • Visual diagnostics like ROC, PR, learning curves, and calibration plots
    • Optional artifact saving for production-style deployment

    Parameters
    ----------
    df : pandas.DataFrame
        Your complete dataset containing predictors and target.
    target : str
        Column name representing the dependent binary class label.
    test_size : float, optional (default=0.2)
        Proportion of data reserved for testing model performance.
    param_grid : dict, optional
        Hyperparameter search space for GridSearchCV.
        If None, a balanced default grid of forest depths and tree counts is applied.
    random_state : int, optional
        Controls randomization for reproducibility.
    cv_folds : int, optional
        Number of folds for StratifiedKFold cross-validation.
    save_artifacts : bool, optional
        Whether to save preprocessing and model objects as `.joblib` files.
    artifact_prefix : str, optional
        Prefix for saved artifact file names, if enabled.

    Returns
    -------
    Dict[str, Any]
        {
            "best_model": Fitted RandomForestClassifier,
            "best_params": Optimal parameter set discovered,
            "train_accuracy": Accuracy on the training set,
            "test_accuracy": Accuracy on the testing set,
            "precision": Positive predictive value,
            "recall_sensitivity": True positive recovery rate,
            "specificity": Ability to avoid false alarms,
            "f1": Harmonic score balancing precision and recall,
            "mcc": Matthews Correlation Coefficient for true model balance,
            "auc": Area Under ROC Curve,
            "test_logloss": Probability quality measure,
            "train_mse": Mean square deviations on training predictions,
            "test_mse": Mean square deviations on testing predictions,
            "train_r2": Informative R² estimate on training,
            "test_r2": Informative R² estimate on testing,
            "cv_results_df": Detailed cross-validation metrics,
            "artifacts": Dictionary of preprocessors and fitted model
        }

    Notes
    -----
    • Designed for binary classification.
    • Evaluations follow scientific rigor.
    • Visual storytelling included by default.

    Like a forest that grows wiser with every split,
    this model learns patterns no human eye can witness,
    and delivers predictions with class.
    """


    # ---------------------------
    # Default parameter grid
    # ---------------------------
    if param_grid is None:
        param_grid = {
            "n_estimators": [50, 100, 200],
            "max_depth": [None, 5, 10],
            "min_samples_split": [2, 5]
        }

    # ---------------------------
    # Basic cleaning & split
    # ---------------------------
    df = df.copy()
    df = df.loc[:, df.isnull().mean() < 0.5]  # drop columns with >50% NA

    X = df.drop(columns=[target])
    y = df[target]

    # train/test split (stratified for binary)
    X_train_df, X_test_df, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # ---------------------------
    # Explicit preprocessing (fit on TRAIN, apply to TEST)
    # ---------------------------
    # numeric / categorical split (explicit)
    num_cols = X_train_df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = X_train_df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

    # Numeric imputer + scaler
    num_imputer = SimpleImputer(strategy="median")
    X_train_num = num_imputer.fit_transform(X_train_df[num_cols])
    scaler = StandardScaler()
    X_train_num = scaler.fit_transform(X_train_num)

    # Categorical imputer + encoder
    if len(cat_cols) > 0:
        cat_imputer = SimpleImputer(strategy="most_frequent")
        X_train_cat_imputed = cat_imputer.fit_transform(X_train_df[cat_cols])
        encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
        X_train_cat = encoder.fit_transform(X_train_cat_imputed)
        X_train_proc = np.hstack([X_train_num, X_train_cat])
    else:
        cat_imputer = None
        encoder = None
        X_train_proc = X_train_num

    # Transform test set using fitted transformers
    X_test_num = num_imputer.transform(X_test_df[num_cols])
    X_test_num = scaler.transform(X_test_num)
    if len(cat_cols) > 0:
        X_test_cat = encoder.transform(cat_imputer.transform(X_test_df[cat_cols]))
        X_test_proc = np.hstack([X_test_num, X_test_cat])
    else:
        X_test_proc = X_test_num

    # ---------------------------
    # Grid search (explicit estimator only)
    # ---------------------------
    rf = RandomForestClassifier(random_state=random_state, class_weight="balanced")
    # GridSearchCV expects parameter names for estimator directly since we pass arrays (no pipeline)
    gs = GridSearchCV(
        rf,
        param_grid=param_grid,
        scoring="f1",
        cv=StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state),
        return_train_score=True,
        n_jobs=-1
    )
    gs.fit(X_train_proc, y_train)

    best_model = gs.best_estimator_
    cv_results_df = pd.DataFrame(gs.cv_results_)

    # ---------------------------
    # Best model evaluation
    # ---------------------------
    y_train_pred = best_model.predict(X_train_proc)
    y_test_pred = best_model.predict(X_test_proc)
    y_test_proba = best_model.predict_proba(X_test_proc)[:, 1]

    # Core metrics
    train_acc = accuracy_score(y_train, y_train_pred)
    test_acc = accuracy_score(y_test, y_test_pred)
    precision = precision_score(y_test, y_test_pred, zero_division=0)
    recall = recall_score(y_test, y_test_pred, zero_division=0)   # sensitivity
    f1 = f1_score(y_test, y_test_pred, zero_division=0)
    mcc = matthews_corrcoef(y_test, y_test_pred)

    # Specificity = TN / (TN + FP)
    tn, fp, fn, tp = confusion_matrix(y_test, y_test_pred).ravel()
    specificity = tn / (tn + fp) if (tn + fp) > 0 else np.nan

    # Additional continuous-style diagnostics (allowed for classification but interpret carefully)
    train_mse = mean_squared_error(y_train, y_train_pred)
    test_mse = mean_squared_error(y_test, y_test_pred)
    # For "R^2" on binary labels, this is not standard; compute for information only
    train_r2 = 1 - (np.sum((y_train - y_train_pred) ** 2) / np.sum((y_train - np.mean(y_train)) ** 2))
    test_r2 = 1 - (np.sum((y_test - y_test_pred) ** 2) / np.sum((y_test - np.mean(y_test)) ** 2))

    # AUC
    auc_score = roc_auc_score(y_test, y_test_proba)

    # Log-loss for probability quality
    test_logloss = log_loss(y_test, y_test_proba)

    # ---------------------------
    # Print summary
    # ---------------------------
    print("\n=== Best Model Summary ===")
    print("Best params:", gs.best_params_)
    print(f"Train Accuracy: {train_acc:.4f} | Test Accuracy: {test_acc:.4f}")
    print(f"Precision: {precision:.4f} | Recall (Sensitivity): {recall:.4f} | Specificity: {specificity:.4f}")
    print(f"F1: {f1:.4f} | MCC: {mcc:.4f} | AUC: {auc_score:.4f} | LogLoss: {test_logloss:.4f}")
    print(f"Train MSE: {train_mse:.4f} | Test MSE: {test_mse:.4f}")
    print(f"Train R2: {train_r2:.4f} | Test R2: {test_r2:.4f}")

    # ---------------------------
    # Plots
    # ---------------------------
    # 1) Confusion matrix (raw counts)
    plt.figure(figsize=(5,4))
    ConfusionMatrixDisplay.from_predictions(y_test, y_test_pred, cmap="Blues")
    plt.title("Confusion Matrix (counts)")
    plt.show()

    # 2) ROC with AUC displayed on plot
    fpr, tpr, _ = roc_curve(y_test, y_test_proba)
    plt.figure(figsize=(6,5))
    plt.plot(fpr, tpr, lw=2, label=f"AUC = {auc_score:.4f}")
    plt.plot([0,1], [0,1], linestyle='--', color='grey')
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend(loc="lower right")
    # place AUC on plot as text (upper left)
    plt.text(0.6, 0.05, f"AUC = {auc_score:.4f}", bbox=dict(facecolor='white', alpha=0.7))
    plt.grid(True)
    plt.show()

    # 3) Precision-Recall curve (with average precision)
    prec_vals, recall_vals, _ = precision_recall_curve(y_test, y_test_proba)
    # average precision (area under PR)
    # sklearn's precision_recall_curve does not return AP; compute via trapezoid if needed
    ap_score = np.trapz(prec_vals[::-1], recall_vals[::-1])  # approximate AP
    plt.figure(figsize=(6,5))
    plt.plot(recall_vals, prec_vals, lw=2)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(f"Precision-Recall Curve (AP ≈ {ap_score:.4f})")
    plt.grid(True)
    plt.show()

    # 4) Calibration plot
    plt.figure(figsize=(6,5))
    disp = CalibrationDisplay.from_predictions(y_test, y_test_proba, n_bins=10)
    plt.title("Calibration Curve")
    plt.show()

    # 5) Learning curve (accuracy) using sklearn.learning_curve on best_model
    # Use StratifiedKFold to keep class balance in folds
    train_sizes, train_scores, val_scores = learning_curve(
        best_model, np.vstack([X_train_proc, X_test_proc]) if False else X_train_proc, y_train,
        cv=StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state),
        scoring='accuracy',
        n_jobs=-1,
        train_sizes=np.linspace(0.1, 1.0, 5)
    )
    train_scores_mean = train_scores.mean(axis=1)
    val_scores_mean = val_scores.mean(axis=1)
    plt.figure(figsize=(6,5))
    plt.plot(train_sizes, train_scores_mean, 'o-', label='Train accuracy')
    plt.plot(train_sizes, val_scores_mean, 'o-', label='CV accuracy')
    plt.xlabel("Training examples")
    plt.ylabel("Accuracy")
    plt.title("Learning Curve (accuracy)")
    plt.legend()
    plt.grid(True)
    plt.show()

    # 6) Validation curves for n_estimators and max_depth (train & CV accuracy)
    # validation_curve accepts estimator and raw arrays
    def plot_validation_curve(estimator, X_arr, y_arr, param_name, param_range, title):
        train_scores_v, val_scores_v = validation_curve(
            estimator, X_arr, y_arr, param_name=param_name, param_range=param_range,
            cv=StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state),
            scoring='accuracy', n_jobs=-1
        )
        train_mean = train_scores_v.mean(axis=1)
        val_mean = val_scores_v.mean(axis=1)
        plt.figure(figsize=(6,5))
        plt.plot(param_range, train_mean, marker='o', label='Train accuracy')
        plt.plot(param_range, val_mean, marker='o', label='CV accuracy')
        plt.xlabel(param_name)
        plt.ylabel("Accuracy")
        plt.title(title)
        plt.legend()
        plt.grid(True)
        plt.show()

    # If param values include None, skip None for plotting (validation_curve can't accept None)
    n_est_plot_vals = [v for v in param_grid.get("n_estimators", []) if v is not None]
    if len(n_est_plot_vals) >= 2:
        plot_validation_curve(RandomForestClassifier(random_state=random_state, class_weight="balanced"),
                              X_train_proc, y_train, param_name="n_estimators",
                              param_range=n_est_plot_vals, title="Validation Curve: n_estimators")

    max_depth_vals = [v for v in param_grid.get("max_depth", []) if v is not None]
    if len(max_depth_vals) >= 2:
        plot_validation_curve(RandomForestClassifier(random_state=random_state, class_weight="balanced"),
                              X_train_proc, y_train, param_name="max_depth",
                              param_range=max_depth_vals, title="Validation Curve: max_depth")

    # ---------------------------
    # Save artifacts (optional)
    # ---------------------------
    artifacts = {
        "num_cols": num_cols,
        "cat_cols": cat_cols,
        "num_imputer": num_imputer,
        "scaler": scaler,
        "cat_imputer": cat_imputer,
        "encoder": encoder,
        "best_model": best_model,
        "cv_results": cv_results_df
    }

    if save_artifacts:
        joblib.dump(artifacts, f"{artifact_prefix}_artifacts.joblib")
        print(f"Saved artifacts to {artifact_prefix}_artifacts.joblib")

    # ---------------------------
    # Return structure
    # ---------------------------
    summary = {
        "best_model": best_model,
        "best_params": gs.best_params_,
        "train_accuracy": train_acc,
        "test_accuracy": test_acc,
        "precision": precision,
        "recall_sensitivity": recall,
        "specificity": specificity,
        "f1": f1,
        "mcc": mcc,
        "auc": auc_score,
        "test_logloss": test_logloss,
        "train_mse": train_mse,
        "test_mse": test_mse,
        "train_r2": train_r2,
        "test_r2": test_r2,
        "cv_results_df": cv_results_df,
        "artifacts": artifacts
    }

    return summary