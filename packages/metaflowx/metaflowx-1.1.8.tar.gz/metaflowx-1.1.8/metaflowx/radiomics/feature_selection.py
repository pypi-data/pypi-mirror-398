import os
import re
import numpy as np
import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegressionCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, ParameterGrid
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    roc_auc_score
)

# ============================================================
# SEED EXTRACTION (SINGLE SOURCE OF TRUTH)
# ============================================================

def seed_from_csv(csv_path: str, fallback: int = 42) -> int:
    """
    Extract seed from filenames like:
    seed_10_train.csv, seed-27-test.csv
    """
    match = re.search(r"seed[_\-]?(\d+)", os.path.basename(csv_path))
    return int(match.group(1)) if match else fallback


# ============================================================
# ELASTIC NET FEATURE SELECTION
# ============================================================

def elastic_net_feature_selection(
    csv_path: str,
    label_col: str,
    top_k: int,
    seed: int
) -> pd.DataFrame:

    data = pd.read_csv(csv_path).select_dtypes(include=[np.number])

    if label_col not in data.columns:
        raise ValueError(f"Label column '{label_col}' not found")

    X = data.drop(columns=[label_col]).fillna(data.mean())
    y = data[label_col]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    enet = LogisticRegressionCV(
        penalty="elasticnet",
        solver="saga",
        l1_ratios=np.linspace(0.1, 0.9, 5),
        Cs=10,
        cv=5,
        scoring="roc_auc",
        max_iter=50000,
        n_jobs=-1,
        random_state=seed
    )

    enet.fit(X_scaled, y)

    coef_df = (
        pd.DataFrame({
            "feature": X.columns,
            "importance": np.abs(enet.coef_.ravel())
        })
        .sort_values("importance", ascending=False)
        .head(top_k)
        .reset_index(drop=True)
    )

    return coef_df


# ============================================================
# FORWARD FEATURE SELECTION (RF + CV)
# ============================================================

def forward_feature_selection(
    X: pd.DataFrame,
    y: pd.Series,
    candidate_features: list,
    n_features: int,
    seed: int
) -> list:

    selected = []
    remaining = candidate_features.copy()

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=seed
    )

    for _ in range(n_features):
        best_feature = None
        best_auc = -np.inf

        for feature in remaining:
            trial_feats = selected + [feature]
            fold_aucs = []

            for tr, val in cv.split(X, y):
                model = RandomForestClassifier(
                    n_estimators=300,
                    class_weight="balanced",
                    random_state=seed,
                    n_jobs=-1
                )

                model.fit(X.iloc[tr][trial_feats], y.iloc[tr])
                prob = model.predict_proba(X.iloc[val][trial_feats])[:, 1]
                fold_aucs.append(roc_auc_score(y.iloc[val], prob))

            mean_auc = np.mean(fold_aucs)

            if mean_auc > best_auc:
                best_auc = mean_auc
                best_feature = feature

        selected.append(best_feature)
        remaining.remove(best_feature)

    return selected


# ============================================================
# FULL PIPELINE
# ============================================================

def feature_selection(
    train_csv_path: str,
    test_csv_path: str,
    label_col: str,
    output_dir: str,
    enet_top_k: int = 30,
    final_top_k: int = 20
) -> pd.DataFrame:

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(train_csv_path))[0]

    # ----------------------------
    # Seed derived from CSV
    # ----------------------------
    seed = seed_from_csv(train_csv_path)
    np.random.seed(seed)

    # ----------------------------
    # Elastic Net
    # ----------------------------
    enet_df = elastic_net_feature_selection(
        csv_path=train_csv_path,
        label_col=label_col,
        top_k=enet_top_k,
        seed=seed
    )

    enet_df.to_csv(
        os.path.join(output_dir, f"{base_name}_elasticnet_features.csv"),
        index=False
    )

    candidates = enet_df["feature"].tolist()

    # ----------------------------
    # Load data
    # ----------------------------
    train_df = pd.read_csv(train_csv_path).select_dtypes(include=[np.number])
    test_df  = pd.read_csv(test_csv_path).select_dtypes(include=[np.number])

    # ----------------------------
    # Forward Selection
    # ----------------------------
    selected_features = forward_feature_selection(
        X=train_df[candidates],
        y=train_df[label_col],
        candidate_features=candidates,
        n_features=final_top_k,
        seed=seed
    )

    X_train = train_df[selected_features]
    y_train = train_df[label_col]

    X_test = test_df[selected_features]
    y_test = test_df[label_col]

    # ----------------------------
    # Random Forest Grid Search
    # ----------------------------
    param_grid = {
        "n_estimators": [200, 300, 500],
        "max_depth": [3, 4, 5, None],
        "min_samples_leaf": [2, 4, 6],
        "min_samples_split": [2, 5, 10]
    }

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=seed
    )

    best_auc = -np.inf
    best_model = None
    best_params = None

    for params in ParameterGrid(param_grid):
        model = RandomForestClassifier(
            **params,
            class_weight="balanced",
            random_state=seed,
            n_jobs=-1
        )

        fold_aucs = []

        for tr, val in cv.split(X_train, y_train):
            model.fit(X_train.iloc[tr], y_train.iloc[tr])
            prob = model.predict_proba(X_train.iloc[val])[:, 1]
            fold_aucs.append(roc_auc_score(y_train.iloc[val], prob))

        mean_auc = np.mean(fold_aucs)

        if mean_auc > best_auc:
            best_auc = mean_auc
            best_params = params
            best_model = RandomForestClassifier(
                **params,
                class_weight="balanced",
                random_state=seed,
                n_jobs=-1
            ).fit(X_train, y_train)

    # ----------------------------
    # Final Evaluation
    # ----------------------------
    train_prob = best_model.predict_proba(X_train)[:, 1]
    test_prob  = best_model.predict_proba(X_test)[:, 1]

    perf_df = pd.DataFrame([{
        "data_seed": seed,
        "train_accuracy": accuracy_score(y_train, best_model.predict(X_train)),
        "train_auc": roc_auc_score(y_train, train_prob),
        "cv_auc": best_auc,
        "test_accuracy": accuracy_score(y_test, best_model.predict(X_test)),
        "test_precision": precision_score(y_test, best_model.predict(X_test)),
        "test_recall": recall_score(y_test, best_model.predict(X_test)),
        "test_auc": roc_auc_score(y_test, test_prob),
        "best_params": str(best_params)
    }])

    # ----------------------------
    # Save outputs
    # ----------------------------
    pd.DataFrame({"feature": selected_features}).to_csv(
        os.path.join(output_dir, f"{base_name}_rf_features.csv"),
        index=False
    )

    perf_df.to_csv(
        os.path.join(output_dir, f"{base_name}_performance.csv"),
        index=False
    )

    return perf_df