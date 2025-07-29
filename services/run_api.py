#!/usr/bin/env python
"""
Entry point script to start the Azentiq Memory Manager API service.
"""
import uvicorn
import os
import argparse
import sys

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
print(f"Python path in run_api.py: {sys.path}")
print(f"Current working directory: {os.getcwd()}")

# Import the pythonpath helper
from services.pythonpath_helper import add_project_root_to_path

# Add project root to path
root_dir = add_project_root_to_path()

def main():
    """Run the FastAPI application."""
    parser = argparse.ArgumentParser(description="Start the Memory Manager API service")
    
    parser.add_argument(
        "--host", 
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="Port to bind the server to (default: 8000)"
    )
    
    parser.add_argument(
        "--reload", 
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--redis-url",
        default="redis://localhost:6379/0",
        help="Redis URL for the memory store (default: redis://localhost:6379/0)"
    )
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ["REDIS_URL"] = args.redis_url
    
    print(f"Starting Memory Manager API on {args.host}:{args.port}")
    print(f"Redis URL: {args.redis_url}")
    print(f"Auto-reload: {'Enabled' if args.reload else 'Disabled'}")
    
    uvicorn.run(
        "services.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main()
