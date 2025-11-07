# backend/app/state.py

from typing import Dict, Any
from google.cloud.devtools.cloudbuild_v1.services import cloud_build
from google.cloud import run_v2

# This simple dictionary will hold our shared client instances.
# They will be populated during the application's startup.
clients: Dict[str, Any] = {}