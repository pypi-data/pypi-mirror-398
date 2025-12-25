def map_reduce_lambda():
    """
    Returns a simple, clear explanation of MapReduce and Lambda Functions
    in an exam-ready format.
    """

    summary = """
MapReduce and Lambda Function — Explained

1. MapReduce — What It Is:
   MapReduce is a programming model used to process very large datasets by
   splitting the work across many machines. It has two main stages:

   a) Map Phase:
      - The input data is broken into smaller chunks.
      - A 'map' function processes each chunk independently.
      - It converts the raw data into key-value pairs.
      Example: ("word", 1) for every word in a text file.

   b) Reduce Phase:
      - All key-value pairs with the same key are grouped together.
      - The 'reduce' function combines them to produce the final output.
      Example: summing counts of each word to get total frequency.

   Why Used:
   - Handles huge data that cannot fit in one machine.
   - Highly parallel, scalable, fault-tolerant.
   - Used in big data systems like Hadoop.

   Simple Example:
      Input: ["cat dog", "cat mouse"]
      Map Output:
          cat→1, dog→1, cat→1, mouse→1
      Reduce Output:
          cat→2, dog→1, mouse→1

------------------------------------------------------------

2. Lambda Function — What It Is:
   A lambda function in Python is a small, anonymous function written in one line.
   It does not use 'def' and is used when a tiny function is needed only once.

   Syntax:
       lambda arguments: expression

   Example:
       f = lambda x: x * 2
       f(5) → 10

   Why Used:
   - Short, quick functions.
   - Often used with map(), filter(), and reduce() for clean code.

   Small Example With Map:
       data = [1, 2, 3]
       doubled = list(map(lambda x: x * 2, data))
       Result → [2, 4, 6]

Summary:
- MapReduce → big data processing model with Map + Reduce steps.
- Lambda → small anonymous function used for short operations.
    """

    return summary
