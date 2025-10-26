import os
import logging
from google.cloud import storage
from pathlib import Path

def upload_to_gcs(local_path: str, bucket_name: str, destination_blob: str):
    """
    Uploads a file to Google Cloud Storage bucket.

    Args:
        local_path (str): Local file path to upload.
        bucket_name (str): GCS bucket name (e.g. 'citeconnect-raw-pdfs').
        destination_blob (str): Path in the bucket (e.g. 'healthcare/AI_in_healthcare.parquet').
    """
    try:
        if not os.path.exists(local_path):
            logging.error(f"❌ Local file not found: {local_path}")
            return False

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob)

        blob.upload_from_filename(local_path)
        logging.info(f"✅ Uploaded to GCS: gs://{bucket_name}/{destination_blob}")
        return True

    except Exception as e:
        logging.error(f"⚠️ Failed to upload {local_path} to GCS: {e}")
        return False
