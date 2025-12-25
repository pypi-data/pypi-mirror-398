def challenges_in_ml():
    """
    Returns a clear, exam-ready summary of the major challenges faced
    when building Machine Learning models, rewritten from the user's notes.
    """

    summary = """
Challenges of Machine Learning

1. Lack of Labeled Training Data:
   - ML models need large quantities of good-quality labeled data.
   - Labeling requires domain experts and is expensive, slow, and sometimes impossible.
   - Without enough labeled data, accuracy drops sharply.

2. Non-Representative Training Data:
   - Training data and real-world test data may follow different distributions.
   - Example: training self-driving models on clean daytime images but testing them on
     rainy nighttime images.
   - The model fails because it never learned the true variety of situations.

3. Poor Quality Data:
   - Missing values, noise, outliers, duplicates, inconsistencies, and errors.
   - This leads to incorrect patterns and unstable predictions.

4. Irrelevant Features & Difficult Feature Engineering:
   - Choosing the right features requires strong domain knowledge.
   - Irrelevant or weak features reduce model accuracy.
   - Good feature engineering is hard because:
       * It needs expertise.
       * It often requires trial-and-error.
       * The best features are not always obvious.
   - Deep learning reduces feature engineering but introduces other issues.

5. Overfitting the Training Data:
   - The model memorizes fine details and noise in the training set.
   - Performs extremely well on training data but poorly on unseen test data.
   - Learns noise instead of true patterns.

6. Underfitting the Training Data:
   - The model is too simple to capture the underlying pattern.
   - Performs poorly on both training and test data.
   - Happens when the model lacks complexity or features are weak.

7. Difficulty in Visualization & Model Understanding:
   - Models learn step-by-step over epochs, but internal transformations are hard to visualize.
   - It becomes difficult to understand what the model is learning at each stage.

8. Lack of Explainability (Black-Box Models):
   - Neural networks can automatically extract features but are extremely hard to interpret.
   - We don’t always know *why* a neural network made a certain prediction.
   - This is why Explainable AI (XAI) is needed — to make deep models understandable.

9. High-Resolution vs Low-Resolution Data Issues:
   - If a model is trained on clean, high-quality images but tested on low-resolution,
     noisy images, it will fail.
   - Remedy: collect more varied and diverse data across conditions.

10. Remedies for Most Problems:
    - Collect more data.
    - Collect more *varied* data (different lighting, angles, noises).
    - Improve preprocessing and feature engineering.
    - Use regularization, cross-validation, and data augmentation.
    - Monitor performance using training/test curves to avoid over/underfitting.

    """

    return summary
