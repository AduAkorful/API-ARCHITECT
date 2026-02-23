import pytest
from fastapi import status
from unittest.mock import MagicMock, AsyncMock
from app.models.service import ServiceStatus, ServiceMetadata
from datetime import datetime

def test_generate_service(client, mock_gemini, mock_firestore):
    response = client.post(
        "/api/v1/services/generate",
        json={"prompt": "Create a todo list API"}
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert data["service_name"].startswith("service-")
    assert data["status"] == ServiceStatus.PENDING
    assert data["prompt"] == "Create a todo list API"

    # Verify Firestore was called to save metadata
    # Access the AsyncMock returned by document()
    mock_doc_ref = mock_firestore.collection.return_value.document.return_value
    # It might be called multiple times due to background tasks
    assert mock_doc_ref.set.call_count >= 1

def test_generate_service_empty_prompt(client):
    response = client.post(
        "/api/v1/services/generate",
        json={"prompt": ""}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_list_services(client, mock_firestore, mock_cloud_build, mock_cloud_run):
    # Mock Firestore stream
    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = {
        "id": "test-id",
        "user_id": "test-user-id",
        "service_name": "test-service",
        "prompt": "test prompt",
        "status": ServiceStatus.BUILDING,
        "build_id": "build-123",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    # Setup async generator for stream()
    async def async_stream():
        yield mock_doc

    mock_firestore.collection.return_value.where.return_value.order_by.return_value.stream = MagicMock(return_value=async_stream())

    # Mock Cloud Build response
    mock_build = MagicMock()
    mock_build.status = 1  # SUCCESS
    # Make get_build awaitable
    mock_cloud_build.get_build.return_value = mock_build

    # Mock Cloud Run response
    mock_service = MagicMock()
    mock_service.uri = "https://test-service-url"
    mock_cloud_run.get_service.return_value = mock_service

    response = client.get("/api/v1/services/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == ServiceStatus.DEPLOYED
    assert data[0]["deployed_url"] == "https://test-service-url"

def test_get_service_logs(client, mock_firestore, mock_storage):
    # Mock Firestore document
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "id": "test-id",
        "user_id": "test-user-id",
        "service_name": "test-service",
        "prompt": "test prompt",
        "build_id": "build-123",
        "status": ServiceStatus.DEPLOYED
    }
    mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc

    # Mock Cloud Build and Storage for logs (fetch_build_logs logic)
    with pytest.MonkeyPatch.context() as m:
        mock_fetch_logs = AsyncMock(return_value=("log content", "log.txt"))
        m.setattr("app.core.gcp.fetch_build_logs", mock_fetch_logs)

        response = client.get("/api/v1/services/test-id/logs")
        assert response.status_code == status.HTTP_200_OK
        assert response.text == "log content"
        assert response.headers["content-disposition"] == 'attachment; filename="log.txt"'

def test_get_service_artifact(client, mock_firestore):
    # Mock Firestore document
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "id": "test-id",
        "user_id": "test-user-id",
        "service_name": "test-service",
        "prompt": "test prompt",
        "source_blob": "source/test.zip"
    }
    mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc

    with pytest.MonkeyPatch.context() as m:
        mock_signed_url = AsyncMock(return_value="https://signed.url/test.zip")
        m.setattr("app.core.gcp.generate_signed_url", mock_signed_url)

        response = client.get("/api/v1/services/test-id/artifact")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"download_url": "https://signed.url/test.zip"}

def test_delete_service(client, mock_firestore, mock_cloud_run):
    # Mock Firestore document
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "id": "test-id",
        "user_id": "test-user-id",
        "service_name": "test-service",
        "prompt": "test prompt"
    }
    mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc

    response = client.delete("/api/v1/services/test-id")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify Cloud Run deletion was called
    mock_cloud_run.delete_service.assert_called_once()

    # Verify Firestore deletion was called
    mock_firestore.collection.return_value.document.return_value.delete.assert_called_once()
