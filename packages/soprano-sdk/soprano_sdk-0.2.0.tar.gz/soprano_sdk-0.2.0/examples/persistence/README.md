# Persistence Examples

This directory contains examples demonstrating different persistence strategies for workflow state management using MongoDB.

## ⚠️ Prerequisites

Before running these examples, install the MongoDB persistence dependencies:

```bash
# Using uv (recommended)
uv add langgraph-checkpoint-mongodb pymongo --optional persistence

# Using pip
pip install langgraph-checkpoint-mongodb pymongo

# Or if installed as library
pip install conversational-sop-framework[persistence]
```

## MongoDB Setup

### Local MongoDB

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or install MongoDB locally
# https://www.mongodb.com/docs/manual/installation/
```

### MongoDB Atlas (Cloud)

1. Create free cluster at https://www.mongodb.com/cloud/atlas
2. Get connection string: `mongodb+srv://username:password@cluster.mongodb.net`

## Overview

The workflow engine uses LangGraph's MongoDB checkpointer for persistence. The `thread_id` parameter is the key for storing and retrieving workflow state.

## Persistence Strategies

### 1. Entity-Based (`entity_based.py`)

**Pattern**: Use business entity IDs as the thread_id
**Thread ID**: `f"return_{order_id}"`
**Use Case**: One workflow per business entity (order, ticket, case)

```bash
# Process return for order ORDER-123
python entity_based.py ORDER-123

# Resume same workflow later
python entity_based.py ORDER-123

# Use MongoDB Atlas
python entity_based.py ORDER-123 mongodb+srv://user:pass@cluster.mongodb.net
```

**Pros**:
- Natural resumption using business identifier
- Easy to track workflows by entity
- Prevents duplicate workflows for same entity

**Cons**:
- Only one workflow per entity at a time
- Requires unique business identifier

---

### 2. Conversation-Based (`conversation_based.py`)

**Pattern**: Generate unique conversation IDs
**Thread ID**: `str(uuid.uuid4())`
**Use Case**: Multiple concurrent workflows, supervisor orchestration

```bash
# Start new conversation
python conversation_based.py ../greeting_workflow.yaml

# Resume conversation
python conversation_based.py ../greeting_workflow.yaml --conversation-id abc-123

# Start with pre-populated context (supervisor pattern)
python conversation_based.py ../return_workflow.yaml --order-id ORDER-456

# Use MongoDB Atlas
python conversation_based.py ../greeting_workflow.yaml --mongodb mongodb+srv://user:pass@cluster.mongodb.net
```

**Pros**:
- Supports multiple concurrent workflows per user
- Flexible for chat-based systems
- Works with external supervisors

**Cons**:
- Requires storing conversation_id
- Need mechanism to list user's conversations

---

### 3. MongoDB Demo (`mongodb_demo.py`)

**Pattern**: Basic persistence with pause/resume
**Thread ID**: Generated UUID with manual save/resume

```bash
# Start workflow (displays thread ID)
python mongodb_demo.py

# Pause mid-workflow (type "PAUSE")
# Resume later with saved thread ID
python mongodb_demo.py --thread-id <saved-id>

# Use MongoDB Atlas
python mongodb_demo.py --mongodb mongodb+srv://user:pass@cluster.mongodb.net
```

**Features**:
- Demonstrates basic save/resume flow
- Shows pause capability mid-workflow
- Simple example for learning

---

## Using Persistence in Your Code

### Basic Usage

```python
from soprano_sdk import load_workflow
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient

# Setup persistence
client = MongoClient("mongodb://localhost:27017")
checkpointer = MongoDBSaver(client=client, db_name="workflows")

# Load workflow with checkpointer
graph, engine = load_workflow("workflow.yaml", checkpointer=checkpointer)

# Execute with thread_id for state tracking
config = {"configurable": {"thread_id": "my-thread-123"}}
result = graph.invoke({}, config=config)
```

### With MongoDB Atlas

```python
from pymongo import MongoClient

# MongoDB Atlas connection
client = MongoClient("mongodb+srv://username:password@cluster.mongodb.net")
checkpointer = MongoDBSaver(client=client, db_name="workflows")

graph, engine = load_workflow("workflow.yaml", checkpointer=checkpointer)
```

### With External Context Injection

```python
# Supervisor injects context and auto-completes workflow
result = graph.invoke({
    "order_id": "ORDER-789",
    "return_reason": "damaged"
}, config={"configurable": {"thread_id": "conversation-456"}})
```

---

## Choosing a Strategy

| Strategy | Thread ID Pattern | Best For |
|----------|-------------------|----------|
| **Entity-Based** | `f"return_{order_id}"` | One workflow per business entity |
| **Conversation** | `str(uuid.uuid4())` | Multiple concurrent workflows |
| **User+Workflow** | `f"{user_id}_{workflow_type}"` | One workflow type per user |
| **Session-Based** | `session_id` | Web apps with sessions |

---

## MongoDB Collections

The checkpointer creates the following collections:

- `checkpoints` - Workflow state snapshots
- `writes` - State write operations

### Viewing Saved States

```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["workflows"]

# List all thread IDs
thread_ids = db.checkpoints.distinct("thread_id")
print("Active workflows:", thread_ids)

# Get specific workflow state
state = db.checkpoints.find_one({"thread_id": "order_123"})
print(state)
```

### Cleaning Up

```python
# Remove specific workflow
db.checkpoints.delete_many({"thread_id": "old-thread-123"})
db.writes.delete_many({"thread_id": "old-thread-123"})

# Remove all workflows older than 7 days
from datetime import datetime, timedelta
cutoff = datetime.utcnow() - timedelta(days=7)
db.checkpoints.delete_many({"created_at": {"$lt": cutoff}})
```

---

## Production Considerations

1. **Use MongoDB Atlas**: Managed service with automatic backups
2. **Add indexes**: Index `thread_id` and `created_at` fields
3. **Implement TTL**: Auto-delete old workflows with TTL indexes
4. **Monitor size**: Track database growth and usage
5. **Connection pooling**: Reuse MongoClient instances
6. **Replica sets**: Use replica sets for high availability

### Example: TTL Index

```python
# Auto-delete workflows after 30 days
db.checkpoints.create_index(
    "created_at",
    expireAfterSeconds=30*24*60*60  # 30 days in seconds
)
```

---

## MongoDB Atlas Example

```python
from soprano_sdk import load_workflow
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient

# Atlas connection with authentication
uri = "mongodb+srv://username:password@cluster.mongodb.net"
client = MongoClient(uri)

# Use specific database
checkpointer = MongoDBSaver(client=client, db_name="production_workflows")

# Load workflow
graph, engine = load_workflow("workflow.yaml", checkpointer=checkpointer)

# Execute
config = {"configurable": {"thread_id": f"user_{user_id}_{workflow_type}"}}
result = graph.invoke({}, config=config)
```

---

## Troubleshooting

### Connection Issues

```python
# Test MongoDB connection
from pymongo import MongoClient

try:
    client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
    client.server_info()
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

### Authentication Issues

```bash
# For Atlas, ensure:
# 1. IP whitelist includes your IP (or 0.0.0.0/0 for testing)
# 2. Database user has read/write permissions
# 3. Connection string includes database name
```

---

## Additional Resources

- [MongoDB Checkpointer Documentation](https://www.mongodb.com/docs/atlas/ai-integrations/langgraph/)
- [LangGraph Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [Main README](../../README.md)
