def limit_tree():
    """
    Returns a detailed, exam-ready explanation of the limitations of Decision Trees,
    including conceptual weaknesses and mathematical intuition.
    """
    text = """
LIMITATIONS OF DECISION TREES

Decision Trees suffer from high variance. 
A tree is extremely sensitive to small fluctuations in the training data. 
If the dataset D is replaced by a slightly perturbed version D', the sequence of chosen split points 
argmin_s I(t | s) can change, producing an entirely different tree. 
This instability comes from the greedy nature of minimizing impurity I(t) at each node 
independently rather than solving a global optimization.

Trees tend to overfit without pruning. 
If the tree is allowed to grow until every terminal node becomes pure 
(i.e., impurity I(t) = 0 for classification or minimal MSE for regression), 
the model begins to memorize noise. 
Formally, the empirical risk R_emp(f_tree) becomes very small, 
but the expected risk R_exp(f_tree) increases because the hypothesis space of all possible trees 
is extremely large.

The splitting procedure is locally greedy. 
At each node t, the algorithm selects a feature x_j and threshold s by minimizing
    ΔI(t, s) = I(t) - (n_L/n) I(t_L) - (n_R/n) I(t_R).
This process does not reconsider previous splits, which means the tree may miss 
the globally optimal structure if an early split was suboptimal.

Decision boundaries are piecewise constant. 
For classification, the prediction function f(x) is constant within each leaf region R_m:
    f(x) = c_m   for x ∈ R_m.
These rectangular partitions cannot capture smooth or highly non-linear boundaries efficiently. 
For regression, the tree approximates a function as a step function, which leads to poor 
performance when the true function is continuous or curved.

Decision Trees are biased toward features with many possible split points. 
For a continuous feature, the algorithm evaluates many thresholds s, increasing the chance 
of finding an impurity reduction that occurs by random fluctuation. 
Thus, features with more potential splits appear artificially more important.

Trees do not extrapolate. 
In regression, if the training outputs lie in the interval [y_min, y_max], 
every leaf prediction is simply the mean of its region. 
Therefore, f_tree(x) cannot produce values outside this range, 
making trees unsuitable for extrapolation tasks.

In high-dimensional settings, the number of possible splits grows rapidly. 
The search over all features and thresholds becomes computationally expensive, 
and the risk of overfitting increases because the algorithm can accidentally find 
a split that aligns with noise rather than true structure.

Class imbalance harms split quality. 
When one class dominates, entropy and Gini impurity become small even without meaningful separation. 
In a node where class proportions are (p_majority, p_minority), 
the Gini impurity = 1 - p_majority^2 - p_minority^2 may remain low, 
discouraging the tree from exploring minority patterns.

Small datasets make splits unreliable. 
When n is small, the impurity reduction ΔI(t, s) becomes statistically unstable, 
as slight sampling variation drastically changes the estimated class probabilities p_k(t).
This leads to unstable structures and erratic performance.
    """
    return text