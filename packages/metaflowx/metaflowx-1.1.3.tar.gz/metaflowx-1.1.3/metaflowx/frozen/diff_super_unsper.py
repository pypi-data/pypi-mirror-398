def diff_super_unsper():
    """
    Returns a short-point, exam-friendly comparison of
    Supervised vs Unsupervised Learning.
    """
    text = """
DIFFERENCE BETWEEN SUPERVISED AND UNSUPERVISED LEARNING

Supervised learning uses labelled data (x_i, y_i), while unsupervised learning uses
only unlabelled observations x_i.

Supervised learning aims to learn a mapping f(x) → y; unsupervised learning aims
to discover structure or patterns within x.

Supervised methods minimise prediction error using loss functions such as MSE or
classification error; unsupervised methods optimise internal criteria such as
within-cluster distance or variance explained.

Supervised learning is predictive in nature; unsupervised learning is descriptive.

Supervised models require ground-truth labels; unsupervised models do not require
any external supervision.

Supervised techniques include regression and classification; unsupervised techniques
include clustering, PCA, and density estimation.

Supervised outputs are explicit target values; unsupervised outputs are groupings,
components, or latent patterns.

Supervised learning is typically used for forecasting and decision-making; 
unsupervised learning is used for pattern discovery, data compression, and structure detection.
"""
    return text
