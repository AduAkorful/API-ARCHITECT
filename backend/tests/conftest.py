import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Set dummy environment variables before importing app
os.environ["GCP_PROJECT_ID"] = "test-project"
os.environ["GCP_SOURCE_BUCKET_NAME"] = "test-bucket"
os.environ["GEMINI_API_KEY"] = "test-api-key"
os.environ["GCP_REGION"] = "us-central1"
os.environ["FIRESTORE_SERVICES_COLLECTION"] = "services"

# Add the backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock Google Cloud libraries
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.firestore"] = MagicMock()
sys.modules["google.cloud.storage"] = MagicMock()
sys.modules["google.cloud.devtools"] = MagicMock()

# Mock Cloud Build
mock_cloudbuild_v1 = MagicMock()
sys.modules["google.cloud.devtools.cloudbuild_v1"] = mock_cloudbuild_v1
sys.modules["google.cloud.devtools.cloudbuild_v1.services"] = MagicMock()
sys.modules["google.cloud.devtools.cloudbuild_v1.services.cloud_build"] = MagicMock()
sys.modules["google.cloud.devtools.cloudbuild_v1.types"] = MagicMock()

# Configure Build.Status enum
mock_build_status = MagicMock()
mock_build_status.SUCCESS = 1
mock_build_status.FAILURE = 2
mock_build_status.CANCELLED = 3
mock_build_status.EXPIRED = 4
sys.modules["google.cloud.devtools.cloudbuild_v1.types"].Build.Status = mock_build_status


sys.modules["google.cloud.run_v2"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["firebase_admin"] = MagicMock()
sys.modules["firebase_admin.auth"] = MagicMock()

# Now we can import the app
from fastapi.testclient import TestClient
from main import app  # Changed from app.main to main
from app.core.auth import get_current_user
from app.state import clients
from app.core import gcp, ai

# Mock User
MOCK_USER = {
    "uid": "test-user-id",
    "email": "test@example.com",
    "name": "Test User"
}

@pytest.fixture
def mock_auth():
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    yield
    app.dependency_overrides = {}

@pytest.fixture
def client(mock_auth):
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_gcp_clients(mocker):
    """
    Mock the GCP clients used in the application.
    This fixture is automatically used for all tests.
    """
    # Mock Firestore
    mock_db = MagicMock() # db client itself is synchronous in structure (methods return other objects)

    mock_collection = MagicMock()
    mock_db.collection.return_value = mock_collection

    mock_doc_ref = AsyncMock() # Operations on doc_ref are async
    mock_collection.document.return_value = mock_doc_ref

    # Query mock (for collection().where().order_by().stream())
    mock_query = MagicMock()
    mock_collection.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    # stream() returns an async iterator
    mock_query.stream.return_value = AsyncMock() # iterating over AsyncMock works? No.

    # Patch the module-level 'db' variable in app.core.gcp
    mocker.patch("app.core.gcp.db", mock_db)

    # Mock Storage
    mock_storage = MagicMock()
    mocker.patch("app.core.gcp.storage_client", mock_storage)

    # Mock Cloud Build and Run clients in the clients dictionary
    clients["build_client"] = AsyncMock()
    clients["run_client"] = AsyncMock()

    return mock_db, mock_storage, clients["build_client"], clients["run_client"]

@pytest.fixture
def mock_firestore(mock_gcp_clients):
    return mock_gcp_clients[0]

@pytest.fixture
def mock_storage(mock_gcp_clients):
    return mock_gcp_clients[1]

@pytest.fixture
def mock_cloud_build(mock_gcp_clients):
    return mock_gcp_clients[2]

@pytest.fixture
def mock_cloud_run(mock_gcp_clients):
    return mock_gcp_clients[3]

@pytest.fixture
def mock_gemini(mocker):
    """
    Mock the Gemini API call.
    """
    mock_generate = mocker.patch("app.core.ai.generate_spec_from_prompt")
    mock_generate.return_value = {
        "service_name": "test-service",
        "endpoint": {
            "path": "/test",
            "method": "POST",
            "model_name": "TestModel",
            "schema_fields": [
                {"name": "field1", "type": "str", "required": True}
            ]
        }
    }
    return mock_generate
