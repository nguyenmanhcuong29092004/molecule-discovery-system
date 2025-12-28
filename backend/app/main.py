"""
FastAPI Application

Main application entry point for Molecule Discovery System API.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import runs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Molecule Discovery System API")
    yield
    # Shutdown
    logger.info("Shutting down Molecule Discovery System API")


# Create FastAPI app
app = FastAPI(
    title="Molecule Discovery System",
    description="AI-driven drug discovery platform for CNS diseases",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    runs.router,
    prefix="/api/v1/runs",
    tags=["runs"],
)


@app.get("/", tags=["health"])
async def root():
    """
    Root endpoint - API health check.
    """
    return {
        "message": "Molecule Discovery System API",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )