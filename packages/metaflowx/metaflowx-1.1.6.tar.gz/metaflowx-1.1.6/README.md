# **metaflowx**
A modular, enterprise-grade machine-learning library engineered to streamline data workflows, accelerate model development, and operationalize end-to-end analytics pipelines. The framework is purpose-built to enable research-grade experimentation while maintaining production-level governance, reproducibility, and scale-out capability.

---

## **Overview**
`metaflowx` is positioned as a full-stack machine-learning toolkit designed to deliver high operational efficiency across the entire data lifecycle. The package consolidates industry-standard modeling utilities, modern preprocessing pipelines, advanced decomposition operators, robust ensemble systems, and battle-tested evaluation modules.  
The architecture is aligned for extensibility, maintainability, and high-performance execution, empowering both academic research and industrial ML deployments.

The solution leverages a structured module layout inspired by modern ML ecosystems, accelerating onboarding and cross-functional collaboration. Its broad coverage allows teams to build, benchmark, and operationalize ML assets with minimized technical debt and maximum throughput.

> **Note:** This README intentionally excludes detailed documentation for the `optimiser` folder functions, as requested.

---

## **Key Value Proposition**
- **End-to-end workflow acceleration**—curated building blocks covering datasets, feature engineering, model selection, and post-training evaluation.
- **Scalable and modular architecture**—clean separation of responsibilities, reusable primitives, and enterprise-friendly structure.
- **High test coverage**—extensive test suites ensure deterministic execution and strong governance across ML releases.
- **Research-ready and production-aligned**—balances academic flexibility with corporate-grade engineering rigor.
- **Dataset-first philosophy**—built-in access to canonical datasets enables rapid prototyping and standardized benchmarking.

---

## **Project Structure**

### **Datasets Module (`datasets/`)**
A comprehensive library of dataset loaders, parsers, readers, and test datasets.

#### Capabilities
- Native support for canonical datasets including Iris, Breast Cancer, Wine, California Housing, LFW, 20 Newsgroups, RCV1, KDDCup99, and Species Distributions.
- Local data ingestion layer with CSV/ARFF/SVMLight support.
- Internal OpenML readers to streamline API-free reproducibility for experimentation.
- Optimized SVMLight parsers underpinned by Cython for throughput and reliability.

#### Subcomponents
- `data/`: prepackaged datasets (CSV, GZ archives).
- `descr/`: structured documentation describing metadata and schema for each dataset.
- `images/`: bundled sample images for vision workflows.
- `tests/`: dataset-level validation ensuring schema consistency and deterministic outcomes.
- `_svmlight_format_fast.pyx`: Cython-accelerated parsing engine for large-scale ingestion.

The dataset hub enables fast onboarding, standardized evaluation cycles, and simulation of production-scale ingestion patterns.

---

### **Decomposition Module (`decomposition/`)**
A full suite of dimensionality-reduction and matrix-factorization utilities engineered for speed and analytical clarity.

#### Operators Include:
- PCA, Incremental PCA, Kernel PCA  
- FastICA  
- Factor Analysis  
- Sparse PCA  
- Truncated SVD  
- Non-Negative Matrix Factorization (NMF)  
- Online LDA (Latent Dirichlet Allocation)  
- Dictionary Learning  
- Coordinate Descent NMF (Cython-accelerated)

#### Performance Considerations
- High-throughput Cython kernels (`_cdnmf_fast.pyx`, `_online_lda_fast.pyx`)
- Numerical stability enhancements for large datasets
- Memory-efficient incremental methods suitable for streaming workloads

Ideal for feature extraction, representation learning, signal separation, and topic modeling across structured and unstructured datasets.

---

### **Ensemble Module (`ensemble/`)**
A complete ensemble-learning suite instrumented for operational robustness and model governance.

#### Supported Frameworks:
- Random Forests  
- Extra Trees  
- Bagging  
- Boosting (Gradient Boosting, Histogram-Based Gradient Boosting)  
- Stacking  
- Voting  
- Isolation Forest for anomaly detection  

#### Engineering Highlights:
- Cython-optimized histogram-based boosting stack (`_hist_gradient_boosting/`)
- Bitset-based performance enhancements for categorical splits
- Monotonic constraint support for regulated industries (finance, healthcare)
- Predictive pipeline fully aligned with high-volume production workloads

The ensemble stack ensures consistent, scalable model performance even in high-cardinality environments.

---

### **Feature Selection Module (`feature_selection/`)**
A research-grade toolkit for filter, wrapper, and embedded feature-selection strategies.

#### Tooling Includes:
- Variance Thresholding  
- Univariate Statistical Tests  
- Mutual Information  
- RFE / RFECV  
- Sequential Feature Selectors  
- Model-based selectors  
- Cython-driven mutual information estimators  

Built for teams optimizing feature pipelines, reducing computational overhead, and enhancing interpretability.

---

### **Frozen Models Module (`frozen/`)**
A controlled environment for immutable model artefacts used in audit-compliant ML pipelines.

This module supports freezing model states to enforce reproducibility during validation or regulatory review.

---

### **Linear Models (`linear_model/`)**
An industrial-strength suite of regression and classification algorithms.

#### Coverage:
- Ridge, Lasso, ElasticNet  
- Logistic Regression  
- Bayesian Regression  
- SGD-based solvers  
- Huber Regression  
- Quantile Regression  
- Coordinate Descent engines  
- Passive-Aggressive models  
- Least Angle Regression (LARS)  
- RANSAC Robust Regression  
- Theil–Sen Estimator  

Cython integrations (`_cd_fast.pyx`, `_sag_fast.pyx.tp`, `_sgd_fast.pyx.tp`) provide scale-up capability for enterprise workloads.

---

### **Model Selection (`model_selection/`)**
A holistic module for model tuning, split strategies, and performance validation.

#### Functional Areas:
- Train/Validation/Test split orchestration  
- K-Fold, Stratified K-Fold, Shuffle Splits  
- Grid Search, Random Search, Successive Halving  
- Classification threshold optimization  
- Visualization utilities for diagnostic analysis (`_plot.py`)  
- Enhanced validation logic with deterministic behaviors  

The module is designed for repeatable experimentation and strong audit trails.

---

### **Neural Network Module (`neural_network/`)**
A lightweight neural network stack built around core feedforward architectures.

Included:
- MLP classifiers and regressors  
- RBM (Restricted Boltzmann Machine)  
- Stochastic optimization utilities  
- Gradient-based solvers tuned for controlled training regimes

Positioned as a research accelerator rather than a deep learning framework.

---

### **Preprocessing (`preprocessing/`)**
A scalable data-preprocessing library that minimizes friction in ETL and feature engineering pipelines.

#### Assets Include:
- Label Encoding, One-Hot Encoding, Ordinal Encoding  
- Target Encoding (with Cython-accelerated fast path)  
- Polynomial Feature Expansion  
- Binning and Discretization  
- Scalable sparse matrix transformations  
- Function transformers for custom data logic  

This module anchors the data engineering pipeline, enabling clean, repeatable transformations.

---

### **Support Vector Machines (`svm/`)**
A feature-rich SVM implementation built on top of optimized C++ backends.

- LibSVM and LibLinear integrations  
- Sparse SVM routines  
- Cython bridges for accelerated inference  
- Deterministic linear SVM solvers  
- C++ template architecture for compute-efficient training  

This subsystem enables enterprise teams to deploy classical ML with predictable performance and full reproducibility.

---

## **Tests**
The repository includes an extensive automated testing framework across all modules, ensuring:
- Regression safety
- Deterministic output behavior
- Conformance to expected data and model interfaces
- Compliance with enterprise release processes

CI-friendly test structure enables frictionless integration into DevOps pipelines.

---

## **Installation**
Standard installation via pip:

```bash
pip install metaflowx