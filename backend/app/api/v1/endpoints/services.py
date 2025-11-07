from fastapi import APIRouter, HTTPException, status, Body, Depends
from typing import Dict, Any, List
import os
import re
from app.core import gcp, generation, ai
from app.core.config import settings
from app.models.service import ServiceMetadata, ServiceStatus
from google.cloud import run_v2
from app.core.auth import get_current_user # <-- IMPORT THE AUTH FUNCTION

router = APIRouter()

def sanitize_service_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r'[^a-z0-9-]', '-', name)
    name = name.strip('-')
    return name[:50]

@router.post("/generate", status_code=status.HTTP_202_ACCEPTED, response_model=ServiceMetadata)
async def generate_service(prompt_body: Dict[str, str] = Body(...), user: dict = Depends(get_current_user)):
    prompt = prompt_body.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    
    try:
        spec = ai.generate_spec_from_prompt(prompt)
        service_name = sanitize_service_name(spec.get("service_name", "unnamed-service"))
        
        metadata = ServiceMetadata(
            user_id=user['uid'], # Use the real user ID from the token
            service_name=service_name,
            prompt=prompt,
            spec=spec
        )
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

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Error processing AI response: {ve}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.get("/", response_model=List[ServiceMetadata])
async def list_services(user: dict = Depends(get_current_user)):
    """
    Retrieves all services for the authenticated user from Firestore.
    """
    query = gcp.db.collection(settings.FIRESTORE_SERVICES_COLLECTION).where("user_id", "==", user['uid']).order_by("created_at", direction="DESCENDING")
    results = [ServiceMetadata(**doc.to_dict()) async for doc in query.stream()]
    return results

@router.delete("/{service_id}", status_code=status.HTTP_200_OK)
async def delete_service(service_id: str, user: dict = Depends(get_current_user)):
    """
    Deletes a service from Cloud Run and Firestore, checking for ownership.
    """
    try:
        doc_ref = gcp.db.collection(settings.FIRESTORE_SERVICES_COLLECTION).document(service_id)
        doc = await doc_ref.get()

        if not doc.exists or doc.to_dict().get('user_id') != user['uid']:
            raise HTTPException(status_code=404, detail="Service not found or permission denied.")
        
        metadata = ServiceMetadata(**doc.to_dict())
        
        metadata.status = ServiceStatus.DELETING
        await doc_ref.set(metadata.model_dump())

        run_client = run_v2.ServicesAsyncClient()
        service_path = f"projects/{settings.GCP_PROJECT_ID}/locations/{settings.GCP_REGION}/services/{metadata.service_name}"

        print(f"Initiating deletion of Cloud Run service: {service_path}")
        await run_client.delete_service(name=service_path)
        
        # We will leave the record in Firestore with "DELETING" status for history.
        
        return {"message": f"Deletion initiated for service '{metadata.service_name}'."}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        if 'doc_ref' in locals() and 'metadata' in locals():
            metadata.status = ServiceStatus.FAILED
            await doc_ref.set(metadata.model_dump())
        raise HTTPException(status_code=500, detail=f"Failed to delete service: {e}")