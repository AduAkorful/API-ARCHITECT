from fastapi import APIRouter, HTTPException, status, Body
from typing import Dict, Any, List
import os
import re
from app.core import gcp, generation, ai
from app.core.config import settings
from app.models.service import ServiceMetadata, ServiceStatus
from google.cloud import run_v2

router = APIRouter()

# --- HELPER FUNCTION (unchanged) ---
def sanitize_service_name(name: str) -> str:
    # ... (code is the same)
    name = name.lower()
    name = re.sub(r'[^a-z0-9-]', '-', name)
    name = name.strip('-')
    return name[:50]

# --- GENERATE ENDPOINT (unchanged) ---
@router.post("/generate", status_code=status.HTTP_202_ACCEPTED, response_model=ServiceMetadata)
async def generate_service(prompt: str = Body(..., embed=True)):
    # ... (code is the same)
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    try:
        spec = ai.generate_spec_from_prompt(prompt)
        service_name = sanitize_service_name(spec.get("service_name", "unnamed-service"))
        metadata = ServiceMetadata(
            user_id="test-user",
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

# --- GET SERVICES ENDPOINT (NOW FULLY IMPLEMENTED) ---
@router.get("/", response_model=List[ServiceMetadata])
async def list_services():
    """
    Retrieves all services for the user from Firestore.
    """
    # NOTE: In a real multi-user app, you would add a .where("user_id", "==", current_user_id)
    query = gcp.db.collection(settings.FIRESTORE_SERVICES_COLLECTION).order_by("created_at", direction="DESCENDING")
    results = [ServiceMetadata(**doc.to_dict()) async for doc in query.stream()]
    return results

# --- NEW DELETE ENDPOINT ---
@router.delete("/{service_id}", status_code=status.HTTP_200_OK)
async def delete_service(service_id: str):
    """
    Deletes a service from Cloud Run and Firestore.
    """
    try:
        # 1. Fetch the service metadata from Firestore
        doc_ref = gcp.db.collection(settings.FIRESTORE_SERVICES_COLLECTION).document(service_id)
        doc = await doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Service not found in database.")
        
        metadata = ServiceMetadata(**doc.to_dict())
        
        # 2. Update status in Firestore to DELETING
        metadata.status = ServiceStatus.DELETING
        await doc_ref.set(metadata.model_dump())

        # 3. Initialize the Cloud Run client
        run_client = run_v2.ServicesAsyncClient()
        service_path = f"projects/{settings.GCP_PROJECT_ID}/locations/{settings.GCP_REGION}/services/{metadata.service_name}"

        # 4. Trigger the deletion of the Cloud Run service
        print(f"Initiating deletion of Cloud Run service: {service_path}")
        await run_client.delete_service(name=service_path)
        
        # 5. (Optional but good practice) Delete the record from Firestore after successful deletion trigger
        # For now, we will leave it in the 'DELETING' state for visibility.
        # await doc_ref.delete()

        return {"message": f"Deletion initiated for service '{metadata.service_name}'."}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        # Revert status if deletion fails
        if 'doc_ref' in locals() and 'metadata' in locals():
            metadata.status = ServiceStatus.FAILED # Or its previous status
            await doc_ref.set(metadata.model_dump())
        raise HTTPException(status_code=500, detail=f"Failed to delete service: {e}")