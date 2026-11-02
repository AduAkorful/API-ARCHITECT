output "artifact_registry_repo" {
  value = google_artifact_registry_repository.repo.name
  description = "The name of the Artifact Registry repository"
}

output "source_code_bucket" {
  value = google_storage_bucket.source_code_bucket.name
  description = "The name of the Cloud Storage bucket for source code"
}

output "builder_service_account" {
  value = google_service_account.builder_sa.email
  description = "The email of the Cloud Build Service Account"
}

output "signer_service_account" {
  value = google_service_account.signer_sa.email
  description = "The email of the Signer Service Account"
}
