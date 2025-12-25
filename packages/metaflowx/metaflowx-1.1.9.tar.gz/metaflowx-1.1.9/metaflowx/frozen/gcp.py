def gcp():
    """
    Returns a clear, exam-ready summary of all steps and files involved
    in deploying an ML model on Google Cloud Run.
    """

    summary = """
ML Model Deployment on Google Cloud Run — Key Points

1. What is being done?
   The process describes how to take a trained machine learning model (like the IRIS classifier),
   wrap it inside a Flask web application, package it with the required files, and deploy it as a
   serverless web service using Google Cloud Run. After deployment, the model becomes a public
   web app accessible from any device.

2. Files Needed for Deployment:
   - requirements.txt:
       Contains all Python libraries needed on the Cloud Run environment.
       Only library names are listed (Flask, scikit-learn, waitress), versions are not required.
   - main.py:
       Starts the Flask server and handles multiple user requests simultaneously.
   - deploy.py:
       Extracts data from HTML form fields, converts them into numeric features, loads the
       saved model, calls predict(), and sends back the prediction.
   - templates folder:
       Contains index.html which defines the structure/UI of the web application.
   - savedmodel.sav:
       The trained ML model saved after training on the IRIS dataset. It stores the learned
       parameters and is used by deploy.py for inference.

3. Deployment Command:
   After uploading all files to the Cloud Shell, the deployment is triggered by:
       gcloud run deploy
   This command builds a container image, uploads it, and launches it on Cloud Run.

4. Interactive Setup During Deployment:
   - Service Name:
       A meaningful name like "test-iris-deploy" should be entered.
   - API Enabling:
       Google prompts to enable required services such as:
           artifactregistry.googleapis.com
           cloudbuild.googleapis.com
           run.googleapis.com
       These must be accepted.
   - Region Selection:
       A geographic region must be chosen (e.g., option [9] asia-southeast1).
       Selecting a region close to your location decreases latency and improves speed.
   - Allow Unauthenticated Access:
       Choose "Y" so the model becomes publicly accessible without login.

5. Final Output:
   After deployment succeeds, Google Cloud Run provides a public HTTPS URL.
   This link can be opened on any browser, on any device, from any location.
   It directly loads your web application and allows users to interact with your model.

    """

    return summary
