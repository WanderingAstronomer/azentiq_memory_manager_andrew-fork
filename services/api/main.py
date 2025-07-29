from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
from typing import Dict, Any

# Import the pythonpath helper (first add services to path)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pythonpath_helper import add_project_root_to_path

# Add project root to path
project_root = add_project_root_to_path()
print(f"Added project root in main.py: {project_root}")
print(f"Current sys.path: {sys.path}")
print(f"Current directory: {os.getcwd()}")

# Import routers
from services.api.routers import (
    memories, 
    sessions, 
    context,
    system
)

# Import dependencies
from services.dependencies.memory_manager import get_memory_manager

# Create FastAPI app
app = FastAPI(
    title="Azentiq Memory Manager API",
    description="API for managing memory operations across different tiers",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(memories.router, prefix="/memories", tags=["memories"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(context.router, prefix="/context", tags=["context"])
app.include_router(system.router, tags=["system"])

@app.get("/", tags=["root"])
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "Azentiq Memory Manager API",
        "version": "0.1.0",
        "description": "API for managing memory operations across different tiers"
    }

@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/version", tags=["system"])
async def version():
    """Get API version information."""
    return {
        "version": "0.1.0",
        "build": os.environ.get("BUILD_ID", "development")
    }

if __name__ == "__main__":
    uvicorn.run("services.api.main:app", host="0.0.0.0", port=8000, reload=True)
