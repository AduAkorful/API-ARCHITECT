import asyncio
from datetime import datetime, timedelta

from google.api_core.exceptions import NotFound
from google.auth.transport.requests import Request
from google.auth.iam import Signer
from google.cloud import firestore, storage
from google.cloud.devtools import cloudbuild_v1

from app.core.config import settings
from app.models.service import ServiceMetadata
from app.state import clients

# Use async clients for Google Cloud services that support them
db = firestore.AsyncClient(project=settings.GCP_PROJECT_ID)
# Use synchronous client for storage (will be wrapped in executor when called)
storage_client = storage.Client(project=settings.GCP_PROJECT_ID)
# Note: cloudbuild_client is initialized in main.py's lifespan and accessed via clients dict


async def save_service_metadata(metadata: ServiceMetadata):
    """Saves or updates service metadata in Firestore."""
    metadata.updated_at = datetime.utcnow()
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


async def generate_signed_url(destination_blob_name: str, expires_in: int = 3600) -> str:
    """Generates a signed URL for a previously uploaded artifact."""
    loop = asyncio.get_event_loop()

    def _sign():
        bucket = storage_client.bucket(settings.GCP_SOURCE_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)

        if not blob.exists():
            raise FileNotFoundError(f"Artifact {destination_blob_name} not found in bucket.")

        expiration = timedelta(seconds=expires_in)

        try:
            return blob.generate_signed_url(expiration=expiration, version="v4")
        except Exception as original_error:
            # Attempt to generate the signed URL via the IAM Credentials API.
            signer_email = settings.GCP_SIGNER_SERVICE_ACCOUNT_EMAIL
            if not signer_email:
                raise RuntimeError(
                    "GCP_SIGNER_SERVICE_ACCOUNT_EMAIL must be configured to use IAM-based signing."
                ) from original_error

            credentials = storage_client._credentials
            if credentials is None:
                raise RuntimeError("Storage client has no credentials available for signing.") from original_error

            request = Request()
            if not credentials.valid:
                credentials.refresh(request)

            signer = Signer(request, credentials, signer_email)

            return blob.generate_signed_url(
                expiration=expiration,
                version="v4",
                service_account_email=signer_email,
                signer=signer,
            )

    return await loop.run_in_executor(None, _sign)


async def fetch_build_logs(build_id: str) -> tuple[str, str]:
    """Fetches Cloud Build logs for the given build ID and returns the log text and the filename."""
    cloudbuild_client = clients["build_client"]
    build = await cloudbuild_client.get_build(project_id=settings.GCP_PROJECT_ID, id=build_id)

    logs_bucket = build.logs_bucket
    if not logs_bucket:
        raise RuntimeError("Cloud Build did not provide a logs bucket for this build.")

    bucket_path = logs_bucket.replace("gs://", "", 1).rstrip("/")
    if "/" in bucket_path:
        bucket_name, prefix = bucket_path.split("/", 1)
    else:
        bucket_name, prefix = bucket_path, ""

    prefix = prefix.strip("/")

    def with_prefix(name: str) -> str:
        return f"{prefix}/{name}" if prefix else name

    object_candidates = [
        with_prefix(f"log-{build_id}.txt"),
        with_prefix(f"{build_id}.log"),
        with_prefix(f"{build_id}.txt"),
        with_prefix(f"builds/{build_id}.log"),
    ]
    # Remove duplicates while preserving order
    object_candidates = list(dict.fromkeys(object_candidates))

    loop = asyncio.get_event_loop()

    def _download() -> tuple[str, str]:
        bucket = storage_client.bucket(bucket_name)
        last_error: Exception | None = None
        for object_name in object_candidates:
            blob = bucket.blob(object_name)
            try:
                content = blob.download_as_text()
                filename = object_name.split("/")[-1]
                return content, filename
            except NotFound as err:
                last_error = err
                continue
        raise FileNotFoundError(
            f"Build logs not found in bucket {logs_bucket} for build {build_id}."
        ) from last_error

    return await loop.run_in_executor(None, _download)


async def trigger_cloud_build(gcs_source_uri: str, service_name: str) -> str:
    """Triggers a Cloud Build job to build and deploy the service asynchronously."""
    cloudbuild_client = clients["build_client"]
    project_id = settings.GCP_PROJECT_ID
    region = settings.GCP_REGION
    source_object = gcs_source_uri.split(f"gs://{settings.GCP_SOURCE_BUCKET_NAME}/")[-1]

    # Define build steps directly (matching cloudbuild.yaml.j2 template)
    image_name = f"{region}-docker.pkg.dev/{project_id}/api-architect-repo/{service_name}:latest"

    build = cloudbuild_v1.Build(
        source=cloudbuild_v1.Source(
            storage_source=cloudbuild_v1.StorageSource(
                bucket=settings.GCP_SOURCE_BUCKET_NAME,
                object_=source_object
            )
        ),
        steps=[
            # Step 1: Build the Docker image
            cloudbuild_v1.BuildStep(
                name="gcr.io/cloud-builders/docker",
                args=["build", "-t", image_name, "."]
            ),
            # Step 2: Push to Artifact Registry
            cloudbuild_v1.BuildStep(
                name="gcr.io/cloud-builders/docker",
                args=["push", image_name]
            ),
            # Step 3: Deploy to Cloud Run
            cloudbuild_v1.BuildStep(
                name="gcr.io/google.com/cloudsdktool/cloud-sdk",
                entrypoint="gcloud",
                args=[
                    "run", "deploy", service_name,
                    "--image", image_name,
                    "--region", region,
                    "--platform", "managed",
                    "--allow-unauthenticated",
                    "--project", project_id
                ]
            )
        ]
    )

    operation = await cloudbuild_client.create_build(project_id=project_id, build=build)
    return operation.metadata.build.id
