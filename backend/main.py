from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.v1.router import api_router
from app.core.config import settings
from app.state import clients # Import the clients dictionary
from google.cloud.devtools.cloudbuild_v1.services import cloud_build
from google.cloud import run_v2

# This is the lifespan event handler.
# Code before the 'yield' runs on startup.
# Code after the 'yield' runs on shutdown.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup, initialize the async clients and store them in the shared state
    print("Application startup: Initializing Google Cloud clients...")
    clients["build_client"] = cloud_build.CloudBuildAsyncClient()
    clients["run_client"] = run_v2.ServicesAsyncClient()
    print("Google Cloud clients initialized successfully.")
    yield
    # On shutdown, clients will be closed automatically.
    print("Application shutdown: Closing clients.")


# Pass the lifespan manager to the FastAPI app
app = FastAPI(
    title="API Architect Core",
    description="Backend service to generate and deploy microservices.",
    version="0.1.0",
    lifespan=lifespan
)

if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip() for origin in settings.CORS_ORIGINS.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok"}

app.include_router(api_router, prefix=settings.API_V1_STR)