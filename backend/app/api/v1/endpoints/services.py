from fastapi import APIRouter, HTTPException, status, Body, Depends, BackgroundTasks
from typing import Dict, List
import os
import re
import asyncio
from app.core import gcp, generation, ai
from app.core.config import settings
from app.models.service import ServiceMetadata, ServiceStatus
from app.state import clients
from google.cloud.devtools.cloudbuild_v1.types import Build
from app.core.auth import get_current_user
from google.api_core.exceptions import NotFound

router = APIRouter()

async def run_generation_pipeline(metadata: ServiceMetadata):
    """
    This background task runs the full service generation and deployment pipeline.
    """
    doc_ref = gcp.db.collection(settings.FIRESTORE_SERVICES_COLLECTION).document(metadata.id)
    try:
        # 1. Generate the spec from the AI
        spec = ai.generate_spec_from_prompt(metadata.prompt)
        metadata.spec = spec
        
        # Ensure service_name is updated from spec if it changed
        service_name = sanitize_service_name(spec.get("service_name", metadata.service_name))
        metadata.service_name = service_name
        
        # 2. Generate the Flask service source code
        gcp_config = {
            "project_id": settings.GCP_PROJECT_ID, 
            "region": settings.GCP_REGION, 
            "repository": "api-architect-repo"
        }
        zip_path = generation.generate_flask_service(spec, gcp_config)
        
        # 3. Upload to GCS
        blob_name = f"source/{metadata.id}/{os.path.basename(zip_path)}"
        gcs_uri = await gcp.upload_source_to_gcs(zip_path, blob_name)
        
        # 4. Trigger Cloud Build
        build_id = await gcp.trigger_cloud_build(gcs_uri, service_name)
        metadata.build_id = build_id
        metadata.status = ServiceStatus.BUILDING
        metadata.build_log_url = f"https://console.cloud.google.com/cloud-build/builds/{build_id}?project={settings.GCP_PROJECT_ID}"
        
        await doc_ref.set(metadata.model_dump())
        os.remove(zip_path)

    except Exception as e:
        print(f"Error in generation pipeline for service {metadata.id}: {e}")
        metadata.status = ServiceStatus.FAILED
        metadata.error_message = str(e)
        await doc_ref.set(metadata.model_dump())


def sanitize_service_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r'[^a-z0-9-]', '-', name)
    name = name.strip('-')
    return name[:50]

@router.post("/generate", status_code=status.HTTP_202_ACCEPTED, response_model=ServiceMetadata)
async def generate_service(
    background_tasks: BackgroundTasks,
    prompt_body: Dict[str, str] = Body(...), 
    user: dict = Depends(get_current_user)
):
    prompt = prompt_body.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    
    # Immediately create and save metadata with PENDING status
    # Use a temporary name that will be updated by the pipeline
    temp_service_name = sanitize_service_name(f"service-{os.urandom(4).hex()}")
    metadata = ServiceMetadata(
        user_id=user['uid'], 
        service_name=temp_service_name, 
        prompt=prompt, 
        status=ServiceStatus.PENDING
    )
    await gcp.save_service_metadata(metadata)
    
    # Delegate the long-running process to a background task
    background_tasks.add_task(run_generation_pipeline, metadata)
    
    # Return immediately
    return metadata

@router.get("/", response_model=List[ServiceMetadata])
async def list_services(user: dict = Depends(get_current_user)):
    user_id = user['uid']
    query = gcp.db.collection(settings.FIRESTORE_SERVICES_COLLECTION).where("user_id", "==", user_id).order_by("created_at", direction="DESCENDING")
    docs = query.stream()
    services = [ServiceMetadata(**doc.to_dict()) async for doc in docs]
    
    async def reconcile_status(service: ServiceMetadata):
        build_client = clients["build_client"]
        run_client = clients["run_client"]
        doc_ref = gcp.db.collection(settings.FIRESTORE_SERVICES_COLLECTION).document(service.id)
        
        if service.status == ServiceStatus.BUILDING and service.build_id:
            try:
                # --- THE FINAL, CORRECTED FIX ---
                # The argument is 'id', not 'build_id'
                build_info = await build_client.get_build(project_id=settings.GCP_PROJECT_ID, id=service.build_id)
                
                if build_info.status == Build.Status.SUCCESS:
                    service.status = ServiceStatus.DEPLOYED
                    service_path = run_client.service_path(settings.GCP_PROJECT_ID, settings.GCP_REGION, service.service_name)
                    run_service = await run_client.get_service(name=service_path)
                    service.deployed_url = run_service.uri
                    await doc_ref.set(service.model_dump())
                elif build_info.status in [Build.Status.FAILURE, Build.Status.CANCELLED, Build.Status.EXPIRED]:
                    service.status = ServiceStatus.FAILED
                    await doc_ref.set(service.model_dump())
            except Exception as e:
                print(f"Error checking build status for {service.id}: {e}")
        
        elif service.status == ServiceStatus.DELETING:
             try:
                service_path = run_client.service_path(settings.GCP_PROJECT_ID, settings.GCP_REGION, service.service_name)
                await run_client.get_service(name=service_path)
             except NotFound:
                await doc_ref.delete()
                return None
             except Exception as e:
                print(f"Error checking delete status for {service.id}: {e}")

        return service

    tasks = [reconcile_status(s) for s in services]
    reconciled_results = await asyncio.gather(*tasks)
    services_to_return = [s for s in reconciled_results if s is not None]
    return services_to_return

@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(service_id: str, user: dict = Depends(get_current_user)):
    """
    Deletes a service. This operation is idempotent.
    It will succeed even if the underlying Cloud Run service has already been deleted.
    """
    try:
        doc_ref = gcp.db.collection(settings.FIRESTORE_SERVICES_COLLECTION).document(service_id)
        doc = await doc_ref.get()

        if not doc.exists:
            # The metadata is already gone. Return success.
            return

        if doc.to_dict().get('user_id') != user['uid']:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

        metadata = ServiceMetadata(**doc.to_dict())
        
        # Attempt to delete the service from Google Cloud Run
        if metadata.service_name:
            run_client = clients["run_client"]
            service_path = run_client.service_path(settings.GCP_PROJECT_ID, settings.GCP_REGION, metadata.service_name)
            
            try:
                await run_client.delete_service(name=service_path)
            except NotFound:
                # This is the desired state, so we can ignore this error.
                print(f"Cloud Run service '{metadata.service_name}' not found. It may have been deleted manually.")
                pass
        
        # Finally, delete the service metadata from Firestore
        await doc_ref.delete()

    except HTTPException:
        # Re-raise user-facing errors (e.g., 403)
        raise
    except Exception as e:
        # For any other unexpected error, return a generic 500
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")