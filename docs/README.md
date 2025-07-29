# Azentiq Memory Manager Documentation

## Overview

This documentation covers the Azentiq Memory Manager system, with a focus on the FastAPI service layer that exposes core functionality via REST APIs.

## Table of Contents

- [API Documentation](api/README.md)
  - [Endpoints Reference](api/endpoints.md)
  - [Request/Response Schemas](api/schemas.md)
  - [Authentication & Security](api/security.md)
  - [Error Handling](api/errors.md)
  
- [Sequence Diagrams](diagrams/README.md)
  - [Memory CRUD Operations](diagrams/memory_crud.md)
  - [Session & Context Management](diagrams/session_context.md)
  - [Conversation Management](diagrams/conversation.md)
  
- [Integration Guide](api/integration.md)
  - [Getting Started](api/getting_started.md)
  - [Common Use Cases](api/use_cases.md)

## Project Structure

```
azentiq_memory_manager/
├── core/                   # Core memory management functionality
├── services/               # API service implementation
│   ├── api/                # FastAPI application and routers
│   │   ├── routers/        # API endpoint definitions
│   │   └── main.py         # FastAPI app initialization
│   ├── dependencies/       # FastAPI dependencies
│   ├── schemas/            # Pydantic models for request/response validation
│   └── run_api.py          # API server entry point
└── storage/                # Storage implementations
    ├── redis_store.py      # Redis-based memory store
    └── vector_store.py     # Vector database integration
```

## Getting Started

See the [Getting Started](api/getting_started.md) guide for information on how to set up and interact with the Memory Manager API.
