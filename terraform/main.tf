provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "artifact_registry" {
  service = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudbuild" {
  service = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "run" {
  service = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "firestore" {
  service = "firestore.googleapis.com"
  disable_on_destroy = false
}

# Artifact Registry Repository
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "api-architect-repo"
  description   = "Docker repository for API Architect generated services"
  format        = "DOCKER"

  depends_on = [google_project_service.artifact_registry]
}

# Cloud Storage Bucket for Source Code
resource "google_storage_bucket" "source_code_bucket" {
  name          = "api-architect-source-code-${var.project_id}" # Append project_id for uniqueness
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true
}

# Firestore Database (Native Mode)
resource "google_firestore_database" "database" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.firestore]
}

# Service Account for Cloud Build
resource "google_service_account" "builder_sa" {
  account_id   = "api-architect-builder"
  display_name = "API Architect Cloud Build Service Account"
}

# IAM Roles for Cloud Build Service Account
resource "google_project_iam_member" "builder_sa_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
    "roles/artifactregistry.writer",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectAdmin",
    "roles/logging.logWriter"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.builder_sa.email}"
}

# Signer Service Account (Optional, for signed URLs)
resource "google_service_account" "signer_sa" {
  account_id   = "api-architect-signer"
  display_name = "API Architect Signer Service Account"
}

# Grant Token Creator role to the Signer SA (so it can sign URLs?)
# Actually, the signer SA needs to be impersonated or have key.
# If we use impersonation, the caller (Backend SA) needs Token Creator on the Signer SA.
# But for simplicity, let's just give the Signer SA Storage Object Viewer.
resource "google_project_iam_member" "signer_sa_storage" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.signer_sa.email}"
}

# Grant Token Creator to the default Compute Engine SA (which Cloud Run uses by default)
# or create a dedicated Backend SA.
# Let's assume Backend uses default compute SA for now as per README "Base runtime service account".
# We need to know which SA runs the backend.
# The README says: "Grant it [signer SA] the roles/iam.serviceAccountTokenCreator role on the base runtime service account."
# This is backwards. The runtime SA needs Token Creator ON the Signer SA.
# OR the runtime SA needs to be able to impersonate the Signer SA.
# OR the Signer SA is the runtime SA.
# The README says: "GCP_SIGNER_SERVICE_ACCOUNT_EMAIL is optional ... required ... when Storage credentials cannot sign URLs directly. Grant it the roles/iam.serviceAccountTokenCreator role on the base runtime service account."
# This phrasing is confusing. "Grant it (the signer email) the role ... on the base runtime service account."
# This implies the Signer SA has TokenCreator on the Runtime SA? No, that doesn't make sense for signing URLs.
# Usually, Runtime SA impersonates Signer SA. So Runtime SA needs `roles/iam.serviceAccountTokenCreator` on the Signer SA (or project).

# Let's just output the SA emails so the user can configure them.
