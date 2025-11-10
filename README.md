# API Architect

Generate and deploy production-ready microservices from natural language prompts. This project combines a FastAPI backend, a React frontend, Google Cloud Platform services, and Google Gemini to transform a prompt into a Flask service deployed on Cloud Run with CI/CD, logging, and downloadable source artifacts.

---

## Key Features
- **Prompt-to-API generation** – Gemini produces a structured spec that drives automated code scaffolding via Jinja templates.
- **One-click deployments** – Cloud Build builds the generated service, pushes the image to Artifact Registry, and deploys to Cloud Run.
- **Living status dashboard** – React + React Query poll Firestore to surface build progress, live URLs, artifacts, and logs.
- **Secure by default** – Firebase Authentication (Google Sign-In) issues ID tokens that the backend verifies before serving requests.
- **Downloadable outputs** – Every deployment exposes the generated source bundle and Cloud Build logs for review.

---

## Repository Layout

```
backend/            FastAPI service orchestrating AI -> code -> deploy pipeline
  app/              Core application modules (AI, GCP, auth, generation, routes)
  templates/        Flask microservice templates rendered from Gemini specs
  cloudbuild.yaml   Cloud Build definition for deploying the backend itself
  Dockerfile        Container image for backend runtime on Cloud Run
frontend/           React + Vite single-page application (dashboard + auth)
  src/              Components, pages, hooks, and API client
```

---

## Prerequisites

- Python 3.12
- Node.js 20+ (recommended) and npm
- Google Cloud project with:
  - Cloud Run, Cloud Build, Artifact Registry, Firestore (Native mode), and Cloud Storage enabled
  - A bucket for generated source uploads (e.g., `api-architect-source-code`)
  - An Artifact Registry repository (e.g., `api-architect-repo`)
  - Service account(s) with permissions for Cloud Build, Cloud Run, Artifact Registry, Firestore, and Storage
- Firebase project configured for Google Sign-In
- Gemini API access and key (`GEMINI_API_KEY`)

For local development against Google Cloud, install the gcloud CLI and authenticate with `gcloud auth application-default login` or provide a service account key via `GOOGLE_APPLICATION_CREDENTIALS`.

---

## Backend Configuration (`backend/.env`)

Create a `.env` file inside `backend/` with:

```
GCP_PROJECT_ID=your-gcp-project-id
GCP_REGION=us-central1
GCP_SOURCE_BUCKET_NAME=api-architect-source-code
FIRESTORE_SERVICES_COLLECTION=services
GEMINI_API_KEY=your-gemini-api-key
GCP_SIGNER_SERVICE_ACCOUNT_EMAIL=service-account-for-signed-urls@project.iam.gserviceaccount.com
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
API_V1_STR=/api/v1
```

Notes:
- `GCP_SIGNER_SERVICE_ACCOUNT_EMAIL` is optional locally but required in Cloud Run when Storage credentials cannot sign URLs directly. Grant it the `roles/iam.serviceAccountTokenCreator` role on the base runtime service account.
- Ensure Firestore is in Native mode and initialized in the target project.

---

## Frontend Configuration (`frontend/.env.local`)

Inside `frontend/`, create `.env.local`:

```
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_FIREBASE_API_KEY=firebase-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-app.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=firebase-messaging-sender-id
VITE_FIREBASE_APP_ID=1:...
VITE_FIREBASE_MEASUREMENT_ID=G-...
```

`VITE_API_BASE_URL` should point to the backend’s `/api/v1` prefix. When deployed to Cloud Run, update it to the public HTTPS base URL.

---

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/api-architect.git
   cd api-architect
   ```

2. **Set up Google Cloud credentials**
   - Option A: `gcloud auth application-default login`
   - Option B: Set `GOOGLE_APPLICATION_CREDENTIALS` to a JSON key for an authorized service account.

3. **Provision Firebase Authentication**
   - Enable Google Sign-In for your Firebase project.
   - Whitelist local origin(s) and your Cloud Run domain in Firebase console > Authentication > Settings.

---

## Running the Backend Locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # PowerShell on Windows
pip install --upgrade pip
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Tips:
- The backend assumes Firestore, Storage, Cloud Build, and Cloud Run APIs are reachable using Application Default Credentials.
- For background tasks to succeed locally, your credentials must have permission to create builds, upload to the source bucket, and manage Cloud Run services.
- Health check is available at `http://localhost:8000/`.

---

## Running the Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

By default, Vite serves the SPA at `http://localhost:5173`. Sign in with Google; upon authentication, the app will call the backend using the ID token from Firebase.

---

## How the System Works

1. **Prompt submission**
   - User logs in via Firebase and submits a natural-language prompt from the dashboard.
2. **Gemini spec generation**
   - Backend sends the prompt to Gemini (`models/gemini-pro-latest`), receives a strict JSON schema containing service metadata, endpoint definition, and Pydantic-friendly fields.
3. **Service scaffolding**
   - Jinja templates render a Flask microservice (routes, models, Dockerfile, Cloud Build config), zipped for deployment.
4. **Artifact upload**
   - Zip is uploaded to the configured Cloud Storage bucket; Firestore metadata stores the blob path.
5. **Cloud Build pipeline**
   - An asynchronous Cloud Build job builds the Docker image, pushes to Artifact Registry, and deploys a Cloud Run service with public ingress.
6. **Status reconciliation**
   - Firestore record updates to `BUILDING`, then `DEPLOYED` (with Cloud Run URL) or `FAILED`. The frontend polls and reflects progress.
7. **Post-deployment**
   - Users can fetch Cloud Build logs or download the generated source archive through signed URLs.

---

## Deployment with Cloud Build

The backend deployment is described in `backend/cloudbuild.yaml`. To deploy:

```bash
cd backend
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_SERVICE_NAME=api-architect-core,_GCP_REGION=us-central1,_REPOSITORY=api-architect-repo,_GCP_SOURCE_BUCKET_NAME=api-architect-source-code
```

Before running the build:
- Create the Artifact Registry repository and source bucket referenced above.
- Store required secrets (`gemini-api-key`, `gcp-signer-service-account-email`) in Google Secret Manager.
- Ensure the Cloud Build service account has IAM roles for Cloud Run Admin, Service Account User, Artifact Registry Writer, Secret Manager Accessor, and Storage Object Admin (for bucket uploads).

The generated services reuse a templated Cloud Build pipeline that assumes the same bucket and repository; no manual edits are necessary for standard deployments.

---

## Testing & Linting

- **Frontend**
  - `npm run lint` – ESLint with TypeScript and React hooks rules.
  - `npm run test` – Vitest + Testing Library in a jsdom environment.
- **Backend**
  - No test suite included yet; consider adding pytest-based integration tests with Firestore emulator.

---

## Troubleshooting

- **Firebase token errors** – Confirm the backend has access to verify ID tokens; locally you may need to initialize Firebase Admin with explicit credentials if Application Default Credentials are unavailable.
- **Permission denied (Cloud Build/Run)** – Check IAM roles on your service accounts and ensure `gcloud auth application-default login` was executed with the right project.
- **Signed URL generation failures** – Provide `GCP_SIGNER_SERVICE_ACCOUNT_EMAIL` for a service account with `roles/iam.serviceAccountTokenCreator`; add `roles/storage.objectViewer` for bucket access.
- **Firestore emulator vs production** – The backend currently targets the project’s live Firestore instance. For local-only workflows, configure emulator environment variables before importing Firestore.

---

## Next Steps

- Harden generated services with custom business logic hooks.
- Extend the frontend to support multi-endpoint specs or version history.
- Implement automated tests for the backend pipeline using Google Cloud emulators.

Happy building! Let me know if you need deployment diagrams, scripted Terraform, or emulator configs added.

