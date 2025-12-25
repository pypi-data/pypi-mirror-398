def gd_convergence():
    """
    Explains whether Gradient Descent is guaranteed to converge to the best solution,
    and how the cost function (convex or non-convex) affects convergence.
    """

    summary = """
Does Gradient Descent Always Converge to the Best Solution?

1. Not Always — It Depends on the Shape of the Cost Function.
   Gradient Descent is guaranteed to reach the global minimum ONLY if the cost function 
   is convex. A convex function has a single bowl-shaped minimum. Examples:
       - Linear Regression (MSE)
       - Logistic Regression (cross-entropy)
   For convex problems, GD will always converge to the best solution if:
       - learning rate is not too high
       - gradient is computed correctly
       - enough iterations are used

2. For Non-Convex Problems (Most Deep Learning Models):
   - The loss surface contains many local minima, flat regions, and saddle points.
   - Gradient Descent can get stuck in:
        • local minima  
        • saddle points  
        • flat plateaus  
   Therefore:
       GD is NOT guaranteed to find the global best solution.
       It only finds a local minimum near where training started.

3. Why Deep Learning Still Works?
   - Neural networks do not need the absolute best minimum.
   - Many local minima are equally good in practice.
   - Modern optimizers (Adam, RMSProp), mini-batch SGD, and noise help escape bad minima.

4. Role of Learning Rate:
   - Too high → divergence or oscillations.
   - Too low → painfully slow convergence.
   - Proper learning rate schedule improves stability.

5. Summary:
   • Convex cost → GD is guaranteed to converge to the global optimum.  
   • Non-convex cost → GD is NOT guaranteed; may converge to a local optimum.  
   • In deep learning, local optima are usually good enough.

Simple Insight:
Gradient Descent is reliable ONLY when the cost function has a single valley. When the
landscape has many hills and pits, GD may not reach the deepest one.
    """

    return summary
