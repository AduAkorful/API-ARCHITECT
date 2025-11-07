from fastapi import APIRouter, HTTPException, status, Body, Depends
from typing import Dict, Any, List
import os
import re
from app.core import gcp, generation, ai
from app.core.config import settings
from app.models.service import ServiceMetadata, ServiceStatus
from google.cloud import run_v2
from google.cloud.devtools.cloudbuild_v1.services import cloud_build
from google.cloud.devtools.cloudbuild_v1.types import Build
from app.core.auth import get_current_user
from google.api_core.exceptions import NotFound

router = APIRouter()

def sanitize_service_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r'[^a-z0-9-]', '-', name)
    name = name.strip('-')
    return name[:50]

# --- CLIENT INITIALIZATION ---
# Initialize clients once with explicit project ID to ensure correct authentication context.
build_client = cloud_build.CloudBuildAsyncClient()
run_client = run_v2.ServicesAsyncClient()
# -----------------------------

@router.post("/generate", status_code=status.HTTP_202_ACCEPTED, response_model=ServiceMetadata)
async def generate_service(prompt_body: Dict[str, str] = Body(...), user: dict = Depends(get_current_user)):
    # This function's logic is correct and remains unchanged.
    prompt = prompt_body.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    try:
        spec = ai.generate_spec_from_prompt(prompt)
        service_name = sanitize_service_name(spec.get("service_name", "unnamed-service"))
        metadata = ServiceMetadata(user_id=user['uid'], service_name=service_name, prompt=prompt, spec=spec)
        await gcp.save_service_metadata(metadata)
        gcp_config = {"project_id": settings.GCP_PROJECT_ID, "region": settings.GCP_REGION, "repository": "api-architect-repo"}
        zip_path = generation.generate_flask_service(spec, gcp_config)
        blob_name = f"source/{metadata.id}/{os.path.basename(zip_path)}"
        gcs_uri = gcp.upload_source_to_gcs(zip_path, blob_name)
        build_id = gcp.trigger_cloud_build(gcs_uri, service_name)
        metadata.build_id = build_id
        metadata.status = ServiceStatus.BUILDING
        metadata.build_log_url = f"https://console.cloud.google.com/cloud-build/builds/{build_id}?project={settings.GCP_PROJECT_ID}"
        await gcp.save_service_metadata(metadata)
        os.remove(zip_path)
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.get("/", response_model=List[ServiceMetadata])
async def list_services(user: dict = Depends(get_current_user)):
    user_id = user['uid']
    query = gcp.db.collection(settings.FIRESTORE_SERVICES_COLLECTION).where("user_id", "==", user_id).order_by("created_at", direction="DESCENDING")
    docs = query.stream()
    services = [ServiceMetadata(**doc.to_dict()) async for doc in docs]
    services_to_return = []

    for service in services:
        doc_ref = gcp.db.collection(settings.FIRESTORE_SERVICES_COLLECTION).document(service.id)
        if service.status == ServiceStatus.BUILDING and service.build_id:
            try:
                build_info = await build_client.get_build(project_id=settings.GCP_PROJECT_ID, build_id=service.build_id)
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
                continue
             except Exception as e:
                print(f"Error checking delete status for {service.id}: {e}")
        services_to_return.append(service)
    return services_to_return

@router.delete("/{service_id}", status_code=status.HTTP_200_OK)
async def delete_service(service_id: str, user: dict = Depends(get_current_user)):
    try:
        doc_ref = gcp.db.collection(settings.FIRESTORE_SERVICES_COLLECTION).document(service_id)
        doc = await doc_ref.get()
        if not doc.exists or doc.to_dict().get('user_id') != user['uid']:
            raise HTTPException(status_code=404, detail="Service not found or permission denied.")
        metadata = ServiceMetadata(**doc.to_dict())
        metadata.status = ServiceStatus.DELETING
        await doc_ref.set(metadata.model_dump())
        
        # --- MORE ROBUST PATH CONSTRUCTION ---
        service_path = run_client.service_path(settings.GCP_PROJECT_ID, settings.GCP_REGION, metadata.service_name)
        
        print(f"Initiating deletion of Cloud Run service: {service_path}")
        await run_client.delete_service(name=service_path)
        return {"message": f"Deletion initiated for service '{metadata.service_name}'."}
    except Exception as e:
        if 'doc_ref' in locals() and 'metadata' in locals():
            metadata.status = ServiceStatus.FAILED
            await doc_ref.set(metadata.model_dump())
        raise HTTPException(status_code=500, detail=f"Failed to delete service: {e}")