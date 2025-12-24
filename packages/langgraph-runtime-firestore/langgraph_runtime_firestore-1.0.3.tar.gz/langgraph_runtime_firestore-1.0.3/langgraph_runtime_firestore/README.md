# LangGraph Runtime - Firestore Edition

This package provides a Firestore-based runtime implementation for LangGraph API, enabling persistent storage of threads, runs, assistants, and state in Google Cloud Firestore.

## Installation

```bash
pip install -e ".[dev]"
```

## Configuration

### Environment Variables

Set these environment variables before starting the LangGraph API server:

```bash
# Firestore Configuration
FIRESTORE_PROJECT_ID=your-gcp-project-id
FIRESTORE_CREDENTIALS_PATH=/path/to/firebase-credentials.json

# LangGraph Runtime
LANGGRAPH_RUNTIME_EDITION=firestore

# Redis (required for LangGraph API)
REDIS_URI=redis://localhost:6379

# Database URI (for compatibility)
DATABASE_URI=firestore://your-project-id
```

### Firebase Credentials

1. Create a Firebase project in Google Cloud Console
2. Generate a service account key:
   - Go to "Project Settings" > "Service Accounts"
   - Click "Generate New Private Key"
   - Save the JSON file securely
3. Set `FIRESTORE_CREDENTIALS_PATH` to point to this file

## Architecture

### Document Structure

The Firestore implementation uses the following document structure:

```
/assistants/{assistant_id}
  - assistant_id (string)
  - graph_id (string)
  - name (string)
  - description (string)
  - config (map)
  - context (map)
  - metadata (map)
  - created_at (timestamp)
  - updated_at (timestamp)

/threads/{thread_id}
  - thread_id (string, UUID)
  - metadata (map)
  - status (string: idle, running, paused)
  - created_at (timestamp)
  - updated_at (timestamp)
  - ttl (optional, integer)

/runs/{run_id}
  - run_id (string, UUID)
  - thread_id (string, UUID)
  - assistant_id (string, UUID)
  - metadata (map)
  - status (string)
  - created_at (timestamp)
  - updated_at (timestamp)

/crons/{cron_id}
  - cron_id (string)
  - schedule (string)
  - graph_id (string)
  - metadata (map)
  - created_at (timestamp)
```

### User-Hierarchical Structure (Future)

To support hierarchical document storage by user:

```
/users/{user_id}/threads/{thread_id}
/users/{user_id}/runs/{run_id}
/users/{user_id}/assistants/{assistant_id}
```

Set `user_id` from `config["configurable"]["user_id"]` in your ops methods.

## Core Modules

### database.py
Manages Firestore connection, initialization, and lifecycle. Implements:
- `connect()` - Create Firestore connection context
- `start_pool()` - Initialize connection and collections
- `stop_pool()` - Clean up resources
- `healthcheck()` - Verify Firestore connectivity

### ops.py
Implements CRUD operations for all LangGraph entities:
- `Assistants` - Search, create, update assistants
- `Threads` - CRUD operations for threads
- `Threads.State` - State management and history
- `Threads.Stream` - Real-time event streaming
- `Runs` - Run execution management (TODO)
- `Crons` - Scheduled task management (TODO)

### checkpoint.py
Handles graph state persistence:
- `FirestoreCheckpointer` - Checkpoint saver using Firestore
- In-memory storage with Firestore persistence layer

### store.py
Key-value store for LangGraph context:
- `FirestoreBackedStore` - Extends InMemoryStore with Firestore backing
- TTL and cleanup management

### retry.py
Implements retry logic for transient failures:
- `retry_db` decorator for automatic retry on failures
- Exponential backoff strategy

### lifespan.py
Application lifecycle management:
- Startup: Initialize Firestore connection, collect graphs
- Shutdown: Clean up resources, close connections

## Usage

### Starting the Server

```bash
# Set environment variables
export FIRESTORE_PROJECT_ID=your-project-id
export FIRESTORE_CREDENTIALS_PATH=/path/to/credentials.json
export LANGGRAPH_RUNTIME_EDITION=firestore
export REDIS_URI=redis://localhost:6379
export DATABASE_URI=firestore://your-project-id

# Start the server
langgraph run
```

### Creating Threads via API

```python
import requests

response = requests.post(
    "http://localhost:2024/threads",
    json={
        "metadata": {"user_id": "user123", "project": "my-project"}
    }
)
thread = response.json()
print(f"Created thread: {thread['thread_id']}")
```

### User-Specific Storage

To store threads per user, extract `user_id` from config:

```python
# In ops.py Threads.put():
user_id = config.get("configurable", {}).get("user_id")
if user_id:
    # Store at /users/{user_id}/threads/{thread_id}
    thread_ref = conn.db.collection("users").document(user_id).collection("threads").document(thread_id)
else:
    # Store at /threads/{thread_id}
    thread_ref = conn.db.collection("threads").document(thread_id)
```

## Implementation Status

### Completed ✅
- Core Firestore connectivity
- Database initialization and lifecycle
- Thread CRUD operations (get, put, delete, patch, search, copy)
- Checkpoint integration
- Retry logic with exponential backoff
- Store integration
- Metrics collection

### In Progress 🔄
- State management (State.get, State.post, State.list)
- Real-time thread streaming
- Full Run operations
- Cron job management

### TODO 📋
- Composite Firestore indexes for efficient queries
- TTL document deletion via Cloud Functions
- Performance optimization for bulk operations
- Backup and restore functionality
- Cross-user query isolation and filtering
- Batch state updates

## Performance Considerations

1. **Indexes**: Create composite indexes in Firestore for queries filtering by multiple fields
2. **Document Size**: Keep individual documents under 1MB (typical threads/runs are < 100KB)
3. **Query Limits**: Pagination is required for large result sets (limit + offset)
4. **Real-time Updates**: Consider Cloud Pub/Sub for high-volume event streaming
5. **Caching**: Layer Redis caching for frequently accessed threads

## Testing

```bash
# Run tests
pytest tests/ -v

# Run with Firestore emulator
gcloud firestore emulators start
FIRESTORE_EMULATOR_HOST=localhost:8080 pytest tests/ -v
```

## Troubleshooting

### Firebase Admin SDK Not Found
```bash
pip install firebase-admin>=6.0.0
```

### Connection Timeouts
- Verify Firestore project ID and credentials path
- Check IAM permissions for the service account
- Ensure Firestore database is created in Google Cloud Console

### Firestore Quota Exceeded
- Monitor write/read usage in Cloud Console
- Implement caching for frequently read items
- Consider upgrading billing plan

## Future Enhancements

1. **Hierarchical User Data**: Implement `/users/{user_id}/threads/{thread_id}` structure
2. **Realtime Streaming**: Use Cloud Pub/Sub for event distribution
3. **Advanced Querying**: Full-text search, vector similarity for embeddings
4. **Compression**: Compress large state blobs for storage efficiency
5. **Multi-tenancy**: Per-tenant collections with security rules
6. **Analytics**: Built-in analytics collection and reporting
