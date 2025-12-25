import numpy as np
import pandas as pd
import time

from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import (
    roc_auc_score,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score
)
from sklearn.feature_selection import SelectFromModel

from imblearn.over_sampling import ADASYN
from imblearn.pipeline import Pipeline as ImbPipeline

from tqdm import tqdm


def inner_outer_nested_cv(
    df,
    label_col,
    output_dir=".",
    n_outer_splits=5,
    n_inner_splits=5,
    top_k_features=20,
    random_state=42
):
    start_time = time.time()

    # -------- Split X and y --------
    X = df.drop(columns=[label_col])
    y = df[label_col].values
    X = X.select_dtypes(include=[np.number])

    outer_cv = StratifiedKFold(
        n_splits=n_outer_splits,
        shuffle=True,
        random_state=random_state
    )

    fold_results = []

    print("\nStarting Nested Cross-Validation (SVM)")
    print(f"Samples  : {X.shape[0]}")
    print(f"Features : {X.shape[1]}")
    print("-" * 60)

    outer_pbar = tqdm(
        enumerate(outer_cv.split(X, y), 1),
        total=n_outer_splits,
        desc="Outer CV",
        ncols=100
    )

    for fold, (train_idx, test_idx) in outer_pbar:

        fold_start = time.time()

        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        pipeline = ImbPipeline(steps=[
            ("scaler", StandardScaler()),

            ("feature_selection",
             SelectFromModel(
                 LogisticRegression(
                     penalty="elasticnet",
                     solver="saga",
                     max_iter=5000,
                     random_state=random_state
                 ),
                 max_features=top_k_features
             )),

            ("adasyn", ADASYN(random_state=random_state)),

            ("svm", SVC(
                kernel="rbf",
                probability=True,
                random_state=random_state
            ))
        ])

        param_grid = {
            "feature_selection__estimator__C": [0.01, 0.1, 1, 10],
            "feature_selection__estimator__l1_ratio": [0.3, 0.5, 0.7],
            "svm__C": [0.1, 1, 10],
            "svm__gamma": ["scale", 0.01, 0.1]
        }

        inner_cv = StratifiedKFold(
            n_splits=n_inner_splits,
            shuffle=True,
            random_state=random_state
        )

        grid = GridSearchCV(
            estimator=pipeline,
            param_grid=param_grid,
            scoring="roc_auc",
            cv=inner_cv,
            n_jobs=-1,
            refit=True
        )

        grid.fit(X_train, y_train)

        # -------- Predictions --------
        y_prob = grid.best_estimator_.predict_proba(X_test)[:, 1]
        y_pred = (y_prob >= 0.5).astype(int)

        # -------- Metrics --------
        auc = roc_auc_score(y_test, y_prob)
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)   # Sensitivity
        f1 = f1_score(y_test, y_pred, zero_division=0)

        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

        fold_time = (time.time() - fold_start) / 60

        fold_results.append({
            "Fold": fold,
            "AUC": auc,
            "Accuracy": acc,
            "Precision": prec,
            "Recall_Sensitivity": recall,
            "Specificity": specificity,
            "F1": f1,
            "Fold_Time_min": fold_time
        })

        outer_pbar.set_postfix({
            "Fold": fold,
            "AUC": f"{auc:.3f}"
        })

    # -------- Save per-fold results --------
    results_df = pd.DataFrame(fold_results)
    results_df.to_csv(f"{output_dir}/outer_cv_fold_metrics.csv", index=False)

    # -------- Summary --------
    summary_df = results_df.drop(columns=["Fold", "Fold_Time_min"]).agg(
        ["mean", "std"]
    ).reset_index()

    summary_df.to_csv(f"{output_dir}/outer_cv_summary_metrics.csv", index=False)

    total_time = (time.time() - start_time) / 60

    print("\n" + "=" * 60)
    print("Nested Cross-Validation Finished (SVM)")
    print(summary_df)
    print(f"Total runtime: {total_time:.2f} minutes")
    print("=" * 60)

    return results_df, summary_df