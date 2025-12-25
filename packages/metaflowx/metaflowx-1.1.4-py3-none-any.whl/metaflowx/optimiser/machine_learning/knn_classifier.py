import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, KFold
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)


def knn_classifier(df, target, test_size=0.3, random_state=42, cv=5, n_jobs=-1):
    """
    Perform a complete K-Nearest Neighbors (KNN) classification workflow with
    train-test split before preprocessing to avoid data leakage, followed by model
    tuning, evaluation, and visualization.

    This function automatically handles missing values, categorical encoding,
    numeric scaling, hyperparameter optimization using Grid Search CV, and
    evaluation through classification metrics and a confusion matrix plot.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataset containing both features and target variable.
    target : str
        Name of the target column to be predicted.
    test_size : float, optional, default=0.3
        Proportion of data reserved for testing after splitting.
    random_state : int, optional, default=42
        Random seed used for reproducibility in splitting and model behavior.
    cv : int, optional, default=5
        Number of cross-validation folds used during hyperparameter tuning.
    n_jobs : int, optional, default=-1
        Number of parallel CPU jobs used during grid search. -1 utilizes all cores.

    Workflow
    --------
    1. Split data into train-test subsets before preprocessing
    2. Impute missing values in numerical and categorical features
    3. Encode categorical features using OneHotEncoder with unknown handling
    4. Scale feature space using StandardScaler (fit on train only)
    5. Tune KNN hyperparameters using GridSearchCV and accuracy scoring
    6. Evaluate best model on the test set
    7. Plot annotated confusion matrix and print classification report

    Returns
    -------
    dict
        A comprehensive dictionary containing:
        - "best_model" : sklearn.neighbors.KNeighborsClassifier
            Final tuned classifier instance.
        - "grid_search" : sklearn.model_selection.GridSearchCV
            Grid search object including cross-validation details.
        - "num_imputer" : sklearn.impute.SimpleImputer or None
            Fitted imputer for numerical features.
        - "cat_imputer" : sklearn.impute.SimpleImputer or None
            Fitted imputer for categorical features.
        - "onehot_encoder" : sklearn.preprocessing.OneHotEncoder or None
            Encoder fitted on training categorical data.
        - "scaler" : sklearn.preprocessing.StandardScaler or None
            Scaler fitted on processed training data.
        - "X_train_processed_shape" : tuple
            Shape of preprocessed training feature matrix.
        - "X_test_processed_shape" : tuple
            Shape of preprocessed test feature matrix.
        - "y_test" : numpy.ndarray
            True class labels for test data.
        - "y_pred" : numpy.ndarray
            Predicted class labels for test data.
        - "accuracy" : float
            Overall accuracy on the test set.
        - "precision" : float
            Weighted precision score.
        - "recall" : float
            Weighted recall score.
        - "f1" : float
            Weighted F1 score.
        - "confusion_matrix" : numpy.ndarray
            Matrix summarizing classification performance.

    Notes
    -----
    - Stratified splitting is applied only if the target contains more than one class.
    - Pipeline implementation is not used to provide visibility into each preprocessing step.
    - Performance and optimality highly depend on balanced datasets and sensible metric selection.

    Example
    -------
    >>> results = knn_classifier(df, target="label")
    >>> print("Accuracy:", results["accuracy"])
    >>> model = results["best_model"]
    """

    # 1) Separate X and y
    X = df.drop(columns=[target]).copy()
    y = df[target].copy()

    # 2) Train/test split early to avoid leakage
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y if len(np.unique(y)) > 1 else None
    )

    # 3) Identify numeric and categorical columns
    numeric_cols = X.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = X.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

    # 4) Impute numeric and categorical (fit on train only)
    num_imputer = None
    if numeric_cols:
        num_imputer = SimpleImputer(strategy='median')
        X_train_num = pd.DataFrame(
            num_imputer.fit_transform(X_train[numeric_cols]),
            columns=numeric_cols,
            index=X_train.index
        )
        X_test_num = pd.DataFrame(
            num_imputer.transform(X_test[numeric_cols]),
            columns=numeric_cols,
            index=X_test.index
        )
    else:
        X_train_num = pd.DataFrame(index=X_train.index)
        X_test_num = pd.DataFrame(index=X_test.index)

    cat_imputer = None
    if categorical_cols:
        # For categorical, fill missing with a constant (most_frequent sometimes preferable; here constant is safe)
        cat_imputer = SimpleImputer(strategy='most_frequent')
        X_train_cat = pd.DataFrame(
            cat_imputer.fit_transform(X_train[categorical_cols]),
            columns=categorical_cols,
            index=X_train.index
        )
        X_test_cat = pd.DataFrame(
            cat_imputer.transform(X_test[categorical_cols]),
            columns=categorical_cols,
            index=X_test.index
        )
    else:
        X_train_cat = pd.DataFrame(index=X_train.index)
        X_test_cat = pd.DataFrame(index=X_test.index)

    # 5) Encode categorical features with OneHotEncoder (fit on train only)
    encoder = None
    X_train_cat_enc = pd.DataFrame(index=X_train.index)
    X_test_cat_enc = pd.DataFrame(index=X_test.index)
    if not X_train_cat.empty:
        encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        enc_train_arr = encoder.fit_transform(X_train_cat)
        enc_test_arr = encoder.transform(X_test_cat)  # unknown categories handled
        enc_feature_names = encoder.get_feature_names_out(categorical_cols)

        X_train_cat_enc = pd.DataFrame(enc_train_arr, columns=enc_feature_names, index=X_train.index)
        X_test_cat_enc  = pd.DataFrame(enc_test_arr, columns=enc_feature_names, index=X_test.index)

    # 6) Concatenate numeric and encoded categorical parts
    X_train_proc = pd.concat([X_train_num.reset_index(drop=True), X_train_cat_enc.reset_index(drop=True)], axis=1)
    X_test_proc  = pd.concat([X_test_num.reset_index(drop=True),  X_test_cat_enc.reset_index(drop=True)], axis=1)

    # 7) Scale numeric features (fit on train only). If there are no numeric features, scaler will be None.
    scaler = None
    if not X_train_proc.empty:
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train_proc)
        X_test_scaled = scaler.transform(X_test_proc)
    else:
        # defensive fallback: create zero-shape arrays
        X_train_scaled = np.empty((X_train_proc.shape[0], 0))
        X_test_scaled  = np.empty((X_test_proc.shape[0], 0))

    # 8) Ensure targets are aligned as arrays
    y_train_arr = np.array(y_train)
    y_test_arr  = np.array(y_test)

    # 9) Hyperparameter tuning (GridSearch on the processed arrays)
    knn = KNeighborsClassifier()
    param_grid = {
        'n_neighbors': [3, 5, 7, 9, 11],
        'weights': ['uniform', 'distance'],
        'metric': ['minkowski', 'euclidean', 'manhattan']
    }
    cv_strategy = KFold(n_splits=cv, shuffle=True, random_state=random_state)
    grid = GridSearchCV(knn, param_grid, cv=cv_strategy, scoring='accuracy', n_jobs=n_jobs)
    grid.fit(X_train_scaled, y_train_arr)

    best_model = grid.best_estimator_

    # 10) Fit best model on the whole training processed data (already done by grid; but re-fit for clarity)
    best_model.fit(X_train_scaled, y_train_arr)

    # 11) Predictions and metrics
    y_pred = best_model.predict(X_test_scaled)

    accuracy = accuracy_score(y_test_arr, y_pred)
    precision = precision_score(y_test_arr, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y_test_arr, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test_arr, y_pred, average='weighted', zero_division=0)

    # 12) Confusion matrix plot (matplotlib; annotated)
    cm = confusion_matrix(y_test_arr, y_pred)
    classes = [str(c) for c in np.unique(y)]
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation='nearest', cmap='Blues')
    ax.figure.colorbar(im, ax=ax)
    ax.set(
        xticks=np.arange(cm.shape[1]),
        yticks=np.arange(cm.shape[0]),
        xticklabels=classes, yticklabels=classes,
        ylabel='True label',
        xlabel='Predicted label',
        title='KNN Confusion Matrix'
    )

    # annotate cells
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], 'd'),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    plt.tight_layout()
    plt.show()

    # 13) Print classification report
    print("Classification Report:")
    print(classification_report(y_test_arr, y_pred, zero_division=0))

    # 14) Return objects and metrics so caller can reuse encoders/scaler/model
    return {
        "best_model": best_model,
        "grid_search": grid,
        "num_imputer": num_imputer,
        "cat_imputer": cat_imputer,
        "onehot_encoder": encoder,
        "scaler": scaler,
        "X_train_processed_shape": X_train_scaled.shape,
        "X_test_processed_shape": X_test_scaled.shape,
        "y_test": y_test_arr,
        "y_pred": y_pred,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "confusion_matrix": cm
    }