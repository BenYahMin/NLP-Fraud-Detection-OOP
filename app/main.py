from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles #
from fastapi.responses import FileResponse
import os
from app.config import settings
from app.api.v1.router import router as api_router #
from app.services.model_service import model_service
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing NLP Fraud Engine services...")
    model_service.load_model()
    yield
    logger.info("Shutting down NLP Fraud Engine services...")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Hybrid rule-based and transformer-driven fraud detection API",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api/v1") #

# Mount static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_dashboard():
        return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model_service.is_ready(),
        "environment": settings.ENVIRONMENT
    }