def limit_bagging():
    """
    Returns a concise, exam-ready explanation of the limitations of Bagging,
    written in a smooth and academically appropriate style.
    """
    text = """
LIMITATIONS OF BAGGING

Bagging primarily reduces variance, but it does not substantially reduce bias. 
If the individual learners f_b(x) are biased, the combined predictor 
    f_bag(x) = (1/B) * Σ f_b(x)
retains much of that bias, especially when the underlying model already underfits.

Every bootstrap sample contains roughly 63.2% unique observations. 
As a result, each tree is effectively trained on a smaller subset of the original data, 
which may be problematic when the dataset is small or when rare patterns are important.

Since all models are built independently, bagging cannot correct systematic errors. 
The ensemble simply averages predictions without focusing on points that are consistently misclassified, 
which limits its ability to capture complex structures in the data.

The computational cost increases directly with the number of bootstrap samples B. 
Training many full decision trees can become expensive for large datasets or high-dimensional problems.

Interpretability decreases substantially. 
A single tree yields clear decision rules, whereas a bagged ensemble represents an average of many trees, 
making the final model difficult to interpret.

Bagging is less effective when predictors are highly correlated. 
Strong correlations reduce the diversity between bootstrap models, thereby reducing the amount of variance 
the averaging process can eliminate.
    """
    return text
