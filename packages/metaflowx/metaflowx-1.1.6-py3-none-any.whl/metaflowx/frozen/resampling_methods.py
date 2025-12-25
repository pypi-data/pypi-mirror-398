def resampling_methods():
    """
    Returns a simple and exam-ready explanation of resampling techniques used to 
    handle imbalanced classification: Oversampling, Undersampling, SMOTE, and 
    Data Augmentation.
    """

    summary = """
Resampling Techniques for Imbalanced Data

1. What is Resampling?
   Resampling means modifying the training dataset so that both classes have
   a more balanced number of samples. Instead of accepting the natural imbalance,
   we change the dataset itself to help the model learn minority-class patterns.

---------------------------------------------------------------------

2. Oversampling (Increasing Minority Class Samples)
   - We increase the number of samples of the minority class.
   - Simple method: randomly duplicate existing minority points.
   - Advantage: keeps all original data; improves recall.
   - Disadvantage: may cause overfitting because the model sees many copies 
     of the same minority examples.

   When to Use:
   - When dataset is small.
   - When losing data is not acceptable.
   - When minority class is extremely rare.

---------------------------------------------------------------------

3. Undersampling (Reducing Majority Class Samples)
   - We remove samples from the majority class so that both classes become balanced.
   - Advantage: training becomes faster; no data duplication.
   - Disadvantage: important information from the majority class may be lost.

   When to Use:
   - When dataset is very large.
   - When majority class is huge and redundant.
   - When we want faster training.

---------------------------------------------------------------------

4. SMOTE (Synthetic Minority Oversampling Technique)
   - A smart oversampling method.
   - Instead of duplicating points, SMOTE creates new synthetic minority samples.
   - How it works:
        * Takes a minority sample
        * Finds its nearest minority neighbors
        * Creates new points between them using interpolation
   - Advantage: reduces overfitting by adding realistic new samples.
   - Disadvantage: may create noisy or overlapping points if data is messy.

   When to Use:
   - When minority class is too small.
   - When simple oversampling causes overfitting.
   - When the data space is continuous (numeric features).

---------------------------------------------------------------------

5. Data Augmentation (Adding Artificial Variation)
   - Used heavily in images, audio, and text.
   - New synthetic samples are created by slightly modifying existing ones.
   - Examples:
        * Image: rotate, crop, flip, color shift.
        * Audio: pitch shift, noise addition.
        * Text: synonym replacement.
   - Benefit:
        * Model learns more variations → better generalization.
   - This increases the size of the minority class in a natural way.

   Key Insight:
   - Augmentation makes new minority samples that feel real, not duplicates.

---------------------------------------------------------------------

Summary:
- Oversampling: increase minority samples (duplicates).
- Undersampling: reduce majority samples.
- SMOTE: generate synthetic minority samples using interpolation.
- Data Augmentation: create new varied samples (commonly used in images/audio/text).

These resampling techniques improve performance on minority classes and help reduce
the bias of the model toward the majority class.
    """

    return summary
