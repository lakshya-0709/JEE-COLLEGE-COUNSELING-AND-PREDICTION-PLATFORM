"""
FastAPI Main Application — JEE College Counseling Platform
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import CORS_ORIGINS
from app.database import data_store
from app.services.prediction import prediction_service
from app.routes import predict, trends, compare, colleges


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — load data and ML model on startup."""
    print("\n" + "=" * 50)
    print("  Starting JEE Counseling Platform API")
    print("=" * 50)

    # Load cutoff data
    data_store.load()

    # Load ML model
    prediction_service.load_model()

    print("\nAPI is ready!\n")
    yield
    print("\nShutting down...")


# Create FastAPI app
app = FastAPI(
    title="JEE College Counseling & Prediction Platform",
    description="AI-powered college prediction using JoSAA cutoff data",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(predict.router, prefix="/api")
app.include_router(trends.router, prefix="/api")
app.include_router(compare.router, prefix="/api")
app.include_router(colleges.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "records": len(data_store.cutoffs),
        "model_loaded": prediction_service._loaded,
        "mysql_enabled": data_store.use_mysql,
        "mysql_status": data_store.mysql_status,
    }
