from google.cloud import firestore, storage
from google.cloud.devtools import cloudbuild_v1
from app.core.config import settings
from app.models.service import ServiceMetadata
from app.state import clients
import asyncio

# Use async clients for Google Cloud services that support them
db = firestore.AsyncClient(project=settings.GCP_PROJECT_ID)
# Use synchronous client for storage (will be wrapped in executor when called)
storage_client = storage.Client(project=settings.GCP_PROJECT_ID)
# Note: cloudbuild_client is initialized in main.py's lifespan and accessed via clients dict

async def save_service_metadata(metadata: ServiceMetadata):
    """Saves or updates service metadata in Firestore."""
    # This function is already correct.
    doc_ref = db.collection(settings.FIRESTORE_SERVICES_COLLECTION).document(metadata.id)
    await doc_ref.set(metadata.model_dump())

async def upload_source_to_gcs(source_zip_path: str, destination_blob_name: str) -> str:
    """Uploads the zipped source code to Google Cloud Storage asynchronously."""
    # Run the synchronous storage operation in a thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    
    def _upload():
        bucket = storage_client.bucket(settings.GCP_SOURCE_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_zip_path)
        return f"gs://{settings.GCP_SOURCE_BUCKET_NAME}/{destination_blob_name}"
    
    return await loop.run_in_executor(None, _upload)

async def trigger_cloud_build(gcs_source_uri: str, service_name: str) -> str:
    """Triggers a Cloud Build job to build and deploy the service asynchronously."""
    cloudbuild_client = clients["build_client"]
    project_id = settings.GCP_PROJECT_ID
    
    # Create build request with source from GCS
    build_request = {
        "project_id": project_id,
        "build": {
            "source": {
                "storage_source": {
                    "bucket": settings.GCP_SOURCE_BUCKET_NAME,
                    "object_": gcs_source_uri.split(f"gs://{settings.GCP_SOURCE_BUCKET_NAME}/")[-1]
                }
            }
        }
    }
    
    # Cloud Build will automatically find and use the cloudbuild.yaml in the source
    operation = await cloudbuild_client.create_build(**build_request)
    return operation.metadata.build.id