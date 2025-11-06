from google.cloud import firestore, storage
from google.cloud.devtools import cloudbuild_v1
from app.core.config import settings
from app.models.service import ServiceMetadata
from datetime import datetime

db = firestore.AsyncClient(project=settings.GCP_PROJECT_ID)
storage_client = storage.Client(project=settings.GCP_PROJECT_ID)
cloudbuild_client = cloudbuild_v1.CloudBuildClient()

async def save_service_metadata(metadata: ServiceMetadata):
    """Saves or updates service metadata in Firestore."""
    doc_ref = db.collection(settings.FIRESTORE_SERVICES_COLLECTION).document(metadata.id)
    # Use the modern .model_dump() for Pydantic v2
    await doc_ref.set(metadata.model_dump())

def upload_source_to_gcs(source_zip_path: str, destination_blob_name: str) -> str:
    bucket = storage_client.bucket(settings.GCP_SOURCE_BUCKET_NAME)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_zip_path)
    return f"gs://{settings.GCP_SOURCE_BUCKET_NAME}/{destination_blob_name}"

def trigger_cloud_build(gcs_source_uri: str, service_name: str) -> str:
    project_id = settings.GCP_PROJECT_ID
    build = cloudbuild_v1.Build()
    source_object = gcs_source_uri.split(f"gs://{settings.GCP_SOURCE_BUCKET_NAME}/")[-1]
    build.source = {"storage_source": {"bucket": settings.GCP_SOURCE_BUCKET_NAME, "object_": source_object}}
    build.steps = [{"name": "gcr.io/cloud-builders/gcloud", "args": ["builds", "submit", "--config", "cloudbuild.yaml", "."]}]
    build.options = {"logging": cloudbuild_v1.BuildOptions.LoggingMode.CLOUD_LOGGING_ONLY}
    operation = cloudbuild_client.create_build(project_id=project_id, build=build)
    return operation.metadata.build.id