from fastapi import APIRouter, Depends
import os
from typing import Dict, Any

router = APIRouter()


@router.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/version", tags=["system"])
async def version():
    """Get API version information."""
    return {
        "version": "0.1.0",
        "build": os.environ.get("BUILD_ID", "development"),
        "name": "Azentiq Memory Manager API"
    }
