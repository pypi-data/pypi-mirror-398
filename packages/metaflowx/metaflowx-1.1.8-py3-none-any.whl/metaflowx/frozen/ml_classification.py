def ml_classification():
    """
    Returns a crisp, exam-ready explanation of all major types of
    Machine Learning systems based on supervision, output type,
    modeling approach, and learning style.
    """

    summary = """
Types of Machine Learning Systems

1. Based on Human Supervision:
   a) Supervised Learning:
      - Data comes with input–output pairs (labels).
      - Tasks: regression, binary classification, multi-class classification,
        multi-output regression, multi-output classification.
   
   b) Unsupervised Learning:
      - Only input data is available; no labels.
      - System discovers patterns (clustering, dimensionality reduction, density estimation).

   c) Semi-Supervised Learning:
      - Combination of labeled and large amounts of unlabeled data.
      - The algorithm leverages unlabeled data to improve accuracy.
      - Example: models trained on a small set of labeled images + huge unlabeled image pool.

   d) Reinforcement Learning:
      - An agent learns by performing actions in an environment and receiving rewards.
      - Goal: maximize cumulative reward.
      - Examples: robots, self-driving cars, game-playing agents.

------------------------------------------------------------

2. Based on Type of Output:
   - Single Output Regression: predicts one continuous value.
   - Multi-Output Regression: predicts multiple continuous values simultaneously.
   - Binary Classification: two classes (0/1).
   - Multi-Class Classification: more than two classes.
   - Multi-Label Classification: each example can belong to multiple classes.

------------------------------------------------------------

3. Based on Whether the System Builds a Model:
   a) Instance-Based Learning:
      - No explicit model.
      - Simply compares new data points to stored training examples.
      - Example: K-Nearest Neighbors (KNN).
   
   b) Model-Based Learning:
      - Learns parameters/patterns from data and builds a generalizable model.
      - Example: Linear Regression, Decision Trees, Neural Networks.

------------------------------------------------------------

4. Based on Learning Mode (Incremental or Not):
   a) Batch Learning (Offline Learning):
      - Model is trained once on historical data.
      - After deployment, it does NOT update automatically.
      - To retrain the model, you must retrain offline and redeploy.

   b) Online Learning (Incremental Learning):
      - Model updates continuously as new data arrives.
      - Suitable for real-time systems, streaming data, and quickly changing environments.
      - Model improves “on the fly.”

     Difference Summary:
        Batch = train once, deploy, no auto-updates.
        Online = updates continuously during deployment.

------------------------------------------------------------

Summary:
Machine Learning systems differ based on:
- Whether they have labels (supervised, unsupervised, semi-supervised, RL)
- What they output (regression, classification)
- How they learn (instance-based vs model-based)
- Whether they learn incrementally (online vs batch)
    """

    return summary
