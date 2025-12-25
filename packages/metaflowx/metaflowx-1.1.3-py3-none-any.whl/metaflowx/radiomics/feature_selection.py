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

# ELASTIC NET FEATURE SELECTION

def elastic_net_feature_selection(
    csv_path: str,
    label_col: str,
    top_k: int = 30,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Runs Elastic Net Logistic Regression and returns top-k features
    ranked by absolute coefficient magnitude.
    """
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


# ELASTIC NET + RANDOM FOREST PIPELINE
def feature_selection(
    train_csv_path: str,
    test_csv_path: str,
    label_col: str,
    output_dir: str,
    enet_top_k: int = 30,
    final_top_k: int = 20,
    random_state: int = 42
) -> pd.DataFrame:
    """
    1. Elastic Net feature selection
    2. Random Forest hyperparameter tuning with CV
    3. Final evaluation on test set
    """

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(train_csv_path))[0]

    # Step 1: Elastic Net
    enet_df = elastic_net_feature_selection(
        csv_path=train_csv_path,
        label_col=label_col,
        top_k=enet_top_k,
        random_state=random_state
    )

    enet_feature_path = os.path.join(
        output_dir, f"{base_name}_elasticnet_features.csv"
    )
    enet_df.to_csv(enet_feature_path, index=False)

    selected_features = enet_df["feature"].head(final_top_k).tolist()

    # Step 2: Load train / test
    train_df = pd.read_csv(train_csv_path).select_dtypes(include=[np.number])
    test_df  = pd.read_csv(test_csv_path).select_dtypes(include=[np.number])

    X_train = train_df[selected_features]
    y_train = train_df[label_col]

    X_test = test_df[selected_features]
    y_test = test_df[label_col]


    # Step 3: Random Forest CV
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

    grid = list(ParameterGrid(param_grid))
    best_auc = -np.inf
    best_model = None
    best_params = None

    pbar = tqdm(
        total=len(grid) * cv.get_n_splits(),
        desc=f"RF tuning ({base_name})"
    )

    for params in grid:
        rf = RandomForestClassifier(
            **params,
            class_weight="balanced",
            random_state=random_state
        )

        fold_aucs = []

        for tr_idx, val_idx in cv.split(X_train, y_train):
            rf.fit(X_train.iloc[tr_idx], y_train.iloc[tr_idx])
            val_prob = rf.predict_proba(X_train.iloc[val_idx])[:, 1]
            fold_aucs.append(
                roc_auc_score(y_train.iloc[val_idx], val_prob)
            )
            pbar.update(1)

        mean_auc = np.mean(fold_aucs)

        if mean_auc > best_auc:
            best_auc = mean_auc
            best_params = params
            best_model = RandomForestClassifier(
                **params,
                class_weight="balanced",
                random_state=random_state
            ).fit(X_train, y_train)

    pbar.close()

    # Step 4: Final Metrics
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

    # Step 5: Save outputs
    rf_feature_path = os.path.join(
        output_dir, f"{base_name}_rf_features.csv"
    )
    perf_path = os.path.join(
        output_dir, f"{base_name}_performance.csv"
    )

    pd.DataFrame({"feature": selected_features}).to_csv(
        rf_feature_path, index=False
    )
    perf_df.to_csv(perf_path, index=False)

    return perf_df
