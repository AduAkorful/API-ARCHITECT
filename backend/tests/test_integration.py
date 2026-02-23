import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.models.service import ServiceStatus, ServiceMetadata
from app.api.v1.endpoints.services import run_generation_pipeline

@pytest.mark.asyncio
async def test_generation_pipeline_flow(mock_gemini, mock_firestore):
    # Prepare metadata
    metadata = ServiceMetadata(
        user_id="test-user-id",
        service_name="test-service",
        prompt="Create a todo list API",
        status=ServiceStatus.PENDING,
        id="test-service-id"
    )

    # Mock Firestore document ref
    mock_doc_ref = AsyncMock()
    mock_firestore.collection.return_value.document.return_value = mock_doc_ref

    # Mock generation.generate_flask_service
    with patch("app.core.generation.generate_flask_service") as mock_generate_code:
        mock_generate_code.return_value = "/tmp/test.zip"

        # Mock GCP upload and trigger
        with patch("app.core.gcp.upload_source_to_gcs", new_callable=AsyncMock) as mock_upload:
            mock_upload.return_value = "gs://bucket/test.zip"

            with patch("app.core.gcp.trigger_cloud_build", new_callable=AsyncMock) as mock_trigger:
                mock_trigger.return_value = "build-id-123"

                with patch("os.remove") as mock_remove:

                    # Run the pipeline
                    await run_generation_pipeline(metadata)

                    # Verify Gemini called
                    mock_gemini.assert_called_once_with("Create a todo list API")

                    # Verify code generation
                    mock_generate_code.assert_called_once()

                    # Verify upload
                    mock_upload.assert_called_once_with("/tmp/test.zip", "source/test-service-id/test.zip")

                    # Verify build trigger
                    mock_trigger.assert_called_once()

                    # Verify Firestore updates
                    # It updates multiple times. We check the last one or that it was called.
                    assert mock_doc_ref.set.call_count >= 1

                    # Check final state of metadata object
                    assert metadata.status == ServiceStatus.BUILDING
                    assert metadata.build_id == "build-id-123"
                    assert metadata.source_blob == "source/test-service-id/test.zip"

                    # Verify zip file removal
                    mock_remove.assert_called_once_with("/tmp/test.zip")

@pytest.mark.asyncio
async def test_generation_pipeline_failure(mock_gemini, mock_firestore):
    # Test failure scenario
    metadata = ServiceMetadata(
        user_id="test-user-id",
        service_name="test-service",
        prompt="fail me",
        status=ServiceStatus.PENDING,
        id="test-service-id"
    )

    mock_doc_ref = AsyncMock()
    mock_firestore.collection.return_value.document.return_value = mock_doc_ref

    # Make Gemini raise an exception
    mock_gemini.side_effect = Exception("Gemini failed")

    await run_generation_pipeline(metadata)

    # Verify Firestore updated with failure
    assert metadata.status == ServiceStatus.FAILED
    assert metadata.error_message == "Gemini failed"
    mock_doc_ref.set.assert_called()
