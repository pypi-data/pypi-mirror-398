def imbalanced_classification():
    """
    Returns a detailed yet simple explanation of classification problems with 
    imbalanced data, techniques to handle imbalance, confusion matrix basics,
    and the correct evaluation metrics (Precision, Recall, F1-score).
    """

    summary = """
Imbalanced Data Classification — Complete Notes

1. What is an Imbalanced Classification Problem?
   An imbalanced dataset is when one class has many more samples than the other.
   Example: 99% non-fraud and 1% fraud.
   The model learns to always predict the majority class and still shows a high accuracy.
   This makes ACCURACY a misleading evaluation metric.

   Why Accuracy Fails:
       If 99 out of 100 samples are negative, predicting everything as "negative"
       gives 99% accuracy — but the model is useless for catching the minority class.

---------------------------------------------------------------------

2. Confusion Matrix (Binary Classification)

                     Predicted
                 Negative   Positive
Actual Neg   →     TN          FP
Actual Pos   →     FN          TP

TP = correctly predicted positives  
TN = correctly predicted negatives  
FP = predicted positive but actually negative  
FN = predicted negative but actually positive (very dangerous in imbalanced data)  

In imbalanced data, FN and FP matter far more than accuracy.

---------------------------------------------------------------------

3. Better Evaluation Metrics:

a) Precision:
       TP / (TP + FP)
   "Of all predicted positives, how many were actually positive?"

b) Recall (Sensitivity):
       TP / (TP + FN)
   "Of all actual positives, how many did we catch?"
   Recall is critical for fraud detection, disease detection, anomaly detection.

c) F1-Score:
       2 * (Precision * Recall) / (Precision + Recall)
   Balance between Precision and Recall.
   Best metric when classes are imbalanced.

---------------------------------------------------------------------

4. Techniques to Handle Imbalance:

A) Data-Level Techniques:
   a) Oversampling:
      - Random oversampling the minority class.
      - SMOTE: synthetic samples created between nearby minority points.
      - Advantage: easy to apply, small datasets benefit.
      - Disadvantage: oversampling may cause overfitting.

   b) Undersampling:
      - Remove samples from the majority class.
      - Advantage: faster training.
      - Disadvantage: risk of losing important information.

   c) Hybrid Techniques:
      - Combine undersampling + SMOTE for balanced improvement.

B) Algorithm-Level Techniques:
   a) Class Weighting:
      - Tell the model to “punish” misclassifying minority class more heavily.
      - Example: Logistic Regression, SVM, Trees support class_weight="balanced".

   b) Cost-Sensitive Learning:
      - Assign different costs to FN and FP.
      - Used in medical diagnosis, fraud detection.

C) Threshold Tuning:
   - Probability threshold is changed from 0.5 to another value
     to increase recall or increase precision depending on the need.

---------------------------------------------------------------------

5. When to Use What?

- If dataset is small → Oversampling / SMOTE.
- If dataset is huge → Undersampling or class weights.
- If cost of FN is very high → Increase Recall (lower threshold).
- If cost of FP is very high → Increase Precision.
- For balanced performance → use F1-score.

---------------------------------------------------------------------

6. Summary:
   Imbalanced data cannot be judged with accuracy.
   Confusion matrix, Precision, Recall, and F1-score give true picture.
   Techniques like SMOTE, undersampling, class weighting, and threshold tuning 
   help build reliable models for minority-class prediction.
    """

    return summary
