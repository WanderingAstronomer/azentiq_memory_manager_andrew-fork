# Azentiq Memory Manager Sequence Diagrams

This directory contains sequence diagrams that illustrate the interaction flows between the client, API layer, Memory Manager, and storage system for various operations.

## Available Diagrams

| Diagram | Description |
|---------|-------------|
| [Memory CRUD Operations](memory_crud.md) | Create, Read, Update, and Delete memory operations |
| [Conversation Management](conversation.md) | Adding conversation turns, retrieving history, and generating prompts |
| [Session & Context Management](session_context.md) | Setting context, retrieving session context, and storing context values |

## Diagram Format

All sequence diagrams are written using the Mermaid markdown syntax, which can be rendered by:

1. GitHub markdown (natively supported)
2. VS Code with the Mermaid extension
3. Online Mermaid editors (e.g., https://mermaid-js.github.io/mermaid-live-editor/)
4. Documentation tools like Docusaurus or MkDocs

## Diagram Components

The sequence diagrams generally show interactions between:

- **Client**: External application making API requests
- **FastAPI Endpoint**: The REST API endpoint handling the request
- **Memory Manager**: The core functionality that implements memory operations
- **Redis Store**: The storage backend where memories are persisted

## Key Flows

### Memory Storage Flow

```
Client → API → Memory Manager → Redis Store
```

### Memory Retrieval Flow

```
Client → API → Memory Manager → Redis Store → Memory Manager → API → Client
```

### Error Handling Flow

```
Client → API → Memory Manager → Redis Store (Error) → Memory Manager (Error) → API (Error Response) → Client
```
