def threshold_precision_recall():
    """
    Returns a clear and exam-ready explanation of the relationships among
    classification threshold, precision, and recall.
    """

    summary = """
Relationship Among Threshold, Precision, and Recall

1. What is a Classification Threshold?
   Most classifiers (like Logistic Regression, Neural Networks, Random Forests) output 
   a probability, e.g., P(class = 1). The threshold decides at what probability we call 
   something "positive". Default is 0.5, but it can be moved up or down.

   Predict Positive if P >= threshold  
   Predict Negative if P < threshold  

-------------------------------------------------------------------

2. Effect of Threshold on Precision and Recall:

A) Lowering the Threshold (e.g., from 0.5 → 0.3)
   - The model calls more samples "positive".
   - True Positives (TP) increase.
   - False Positives (FP) also increase.

   Result:
      Precision ↓ (because more wrong positives)
      Recall ↑ (because we catch more actual positives)

   Summary:
      Lower threshold → high recall, low precision

-------------------------------------------------------------------

B) Increasing the Threshold (e.g., 0.5 → 0.8)
   - The model becomes stricter.
   - It predicts positive only when very confident.
   - TP decreases.
   - FP decreases sharply.

   Result:
      Precision ↑ (fewer wrong positives)
      Recall ↓ (misses many real positives)

   Summary:
      Higher threshold → high precision, low recall

-------------------------------------------------------------------

3. Why Precision and Recall Move Opposite?
   - Precision cares about quality of positive predictions.
   - Recall cares about quantity of positive predictions.
   - When you try to increase one, the other naturally suffers.

   Example:
      If you label almost everything positive → high recall, low precision  
      If you label very few things positive → high precision, low recall  

This “see-saw” effect comes directly from how many positives the threshold allows.

-------------------------------------------------------------------

4. Choosing the Right Threshold Depends on the Problem:

- If missing a positive is dangerous → increase recall by lowering threshold  
  (fraud detection, cancer detection, safety alerts)

- If false alarms are costly → increase precision by raising threshold  
  (spam filtering, expensive medical tests, police alerts)

-------------------------------------------------------------------

5. F1-Score Balances Both:
   F1 is the harmonic mean of Precision and Recall.
   It is used when both matter equally.

-------------------------------------------------------------------

Summary:
- Threshold controls how strict the classifier is.  
- Lower threshold → more positives → Recall ↑ Precision ↓  
- Higher threshold → fewer positives → Precision ↑ Recall ↓  
- Precision and recall are always linked through the threshold, and improving one 
  usually lowers the other.
    """

    return summary
