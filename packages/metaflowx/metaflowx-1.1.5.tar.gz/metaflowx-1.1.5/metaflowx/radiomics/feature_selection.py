import os
import numpy as np
import pandas as pd
from tqdm import tqdm

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
# ELASTIC NET FEATURE SELECTION
# ============================================================

def elastic_net_feature_selection(
    csv_path: str,
    label_col: str,
    top_k: int = 30,
    random_state: int = 42
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
        random_state=random_state
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
# FORWARD FEATURE SELECTION
# ============================================================

def forward_feature_selection(
    X: pd.DataFrame,
    y: pd.Series,
    candidate_features: list,
    n_features: int = 20,
    random_state: int = 42
) -> list:

    selected_features = []
    remaining_features = candidate_features.copy()

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=random_state
    )

    for step in range(n_features):
        best_feature = None
        best_score = -np.inf

        for feature in remaining_features:
            trial_features = selected_features + [feature]
            fold_scores = []

            for tr_idx, val_idx in cv.split(X, y):
                X_tr = X.iloc[tr_idx][trial_features]
                X_val = X.iloc[val_idx][trial_features]
                y_tr = y.iloc[tr_idx]
                y_val = y.iloc[val_idx]

                model = RandomForestClassifier(
                    n_estimators=300,
                    max_depth=None,
                    class_weight="balanced",
                    random_state=random_state,
                    n_jobs=-1
                )

                model.fit(X_tr, y_tr)
                prob = model.predict_proba(X_val)[:, 1]
                fold_scores.append(roc_auc_score(y_val, prob))

            mean_score = np.mean(fold_scores)

            if mean_score > best_score:
                best_score = mean_score
                best_feature = feature

        selected_features.append(best_feature)
        remaining_features.remove(best_feature)

    return selected_features


# ============================================================
# FULL PIPELINE: ELASTIC NET → FORWARD SELECTION → RF
# ============================================================

def feature_selection(
    train_csv_path: str,
    test_csv_path: str,
    label_col: str,
    output_dir: str,
    enet_top_k: int = 30,
    final_top_k: int = 20,
    random_state: int = 42
) -> pd.DataFrame:

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(train_csv_path))[0]

    # ----------------------------
    # Step 1: Elastic Net
    # ----------------------------
    enet_df = elastic_net_feature_selection(
        csv_path=train_csv_path,
        label_col=label_col,
        top_k=enet_top_k,
        random_state=random_state
    )

    enet_path = os.path.join(
        output_dir, f"{base_name}_elasticnet_features.csv"
    )
    enet_df.to_csv(enet_path, index=False)

    candidate_features = enet_df["feature"].tolist()

    # ----------------------------
    # Step 2: Load data
    # ----------------------------
    train_df = pd.read_csv(train_csv_path).select_dtypes(include=[np.number])
    test_df  = pd.read_csv(test_csv_path).select_dtypes(include=[np.number])

    # ----------------------------
    # Step 3: Forward Feature Selection
    # ----------------------------
    selected_features = forward_feature_selection(
        X=train_df[candidate_features],
        y=train_df[label_col],
        candidate_features=candidate_features,
        n_features=final_top_k,
        random_state=random_state
    )

    X_train = train_df[selected_features]
    y_train = train_df[label_col]

    X_test = test_df[selected_features]
    y_test = test_df[label_col]

    # ----------------------------
    # Step 4: Random Forest tuning
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
        random_state=random_state
    )

    best_auc = -np.inf
    best_model = None
    best_params = None

    for params in ParameterGrid(param_grid):
        rf = RandomForestClassifier(
            **params,
            class_weight="balanced",
            random_state=random_state
        )

        fold_aucs = []

        for tr_idx, val_idx in cv.split(X_train, y_train):
            rf.fit(X_train.iloc[tr_idx], y_train.iloc[tr_idx])
            prob = rf.predict_proba(X_train.iloc[val_idx])[:, 1]
            fold_aucs.append(
                roc_auc_score(y_train.iloc[val_idx], prob)
            )

        mean_auc = np.mean(fold_aucs)

        if mean_auc > best_auc:
            best_auc = mean_auc
            best_params = params
            best_model = RandomForestClassifier(
                **params,
                class_weight="balanced",
                random_state=random_state
            ).fit(X_train, y_train)

    # ----------------------------
    # Step 5: Final evaluation
    # ----------------------------
    train_pred = best_model.predict(X_train)
    train_prob = best_model.predict_proba(X_train)[:, 1]

    test_pred = best_model.predict(X_test)
    test_prob = best_model.predict_proba(X_test)[:, 1]

    perf_df = pd.DataFrame([{
        "train_accuracy": accuracy_score(y_train, train_pred),
        "train_auc": roc_auc_score(y_train, train_prob),
        "validation_auc": best_auc,
        "test_accuracy": accuracy_score(y_test, test_pred),
        "test_precision": precision_score(y_test, test_pred),
        "test_recall": recall_score(y_test, test_pred),
        "test_auc": roc_auc_score(y_test, test_prob),
        "best_params": str(best_params)
    }])

    # ----------------------------
    # Step 6: Save outputs
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