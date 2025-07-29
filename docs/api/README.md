# Azentiq Memory Manager API Documentation

## Introduction

The Azentiq Memory Manager API provides RESTful endpoints for managing memories across different tiers (short-term, working, long-term), handling conversation context, and generating prompts with relevant memory integration.

## Documentation Sections

| Document | Description |
|----------|-------------|
| [API Endpoints Reference](endpoints.md) | Complete reference of all available API endpoints |
| [Request/Response Schemas](schemas.md) | Data models used in API requests and responses |
| [Getting Started Guide](getting_started.md) | Quick start guide with code examples |
| [Integration Guide](integration.md) | Best practices for integrating with various applications |

## Key Features

- Memory CRUD operations with tiered storage
- Session-based conversation history management
- Context key-value store for session state
- Prompt generation with automatic memory integration
- Health and monitoring endpoints

## API Design Philosophy

The Memory Manager API follows these design principles:

1. **RESTful Architecture**: Standard HTTP methods and response codes
2. **Consistent Schema**: Predictable request/response formats
3. **Session-Based**: Operations scoped to session contexts
4. **Stateless Processing**: No client state stored on the server between requests
5. **Explicit Error Handling**: Clear error messages and appropriate status codes

## Authentication & Security

Currently, the API does not require authentication. This may change in future versions.

## Base URL

By default, the API is available at: `http://localhost:8000`

## Interactive Documentation

When the API server is running, interactive Swagger documentation is available at: `http://localhost:8000/docs`
