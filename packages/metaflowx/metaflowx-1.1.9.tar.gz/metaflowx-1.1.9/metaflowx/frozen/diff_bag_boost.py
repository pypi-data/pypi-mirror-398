def diff_bag_boost():
    """
    Returns an exam-style, short-point, comprehensive comparison
    between Bagging and Boosting algorithms.
    """
    text = """
DIFFERENCE BETWEEN BAGGING AND BOOSTING

Bagging combines predictions of the same type of model, whereas boosting combines
weak learners that sequentially refine one another.

Bagging primarily reduces variance; boosting primarily reduces bias.

In bagging, each model receives equal weight in the final prediction. 
In boosting, models are assigned weights based on their individual performance.

Bagging builds each model independently. 
Boosting builds each new model in response to the errors of the previous models.

Bagging uses row sampling with replacement to generate multiple training subsets.
Boosting uses the entire dataset but increases the weight of misclassified or
poorly predicted observations in later rounds.

Bagging helps reduce overfitting by stabilising high-variance models.
Boosting helps reduce bias by making weak learners progressively more accurate.

Bagging is recommended when the base model is unstable (high variance). 
Boosting is recommended when the base model is simple and biased.

Bagging trains all base learners in parallel. 
Boosting trains base learners sequentially.

Bagging uses simple averaging or majority vote for final predictions. 
Boosting uses a weighted sum of weak learners.

Bagging is relatively robust to noise, since averaging reduces fluctuations. 
Boosting is more sensitive to noise and mislabeled points because it increases
their influence over iterations.

Example: Random Forest is a classic bagging method. 
Example: AdaBoost and Gradient Boosting are standard boosting techniques.
"""
    return text
