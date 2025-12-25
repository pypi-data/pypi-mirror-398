# Memorer Python SDK

The official Python SDK for [Memorer](https://memorer.ai) - Intelligent Memory for AI Agents.

[![PyPI](https://img.shields.io/pypi/v/memorer)](https://pypi.org/project/memorer/)
[![Python](https://img.shields.io/pypi/pyversions/memorer)](https://pypi.org/project/memorer/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

## Installation

```bash
pip install memorer
```

## Quick Start

```python
from memorer import Memorer

# Initialize the client
client = Memorer(api_key="your-api-key")

# Ingest documents
client.knowledge.ingest([
    "AI agents need memory to maintain context across interactions.",
    "Memory enables agents to learn from past experiences.",
])

# Query with multi-hop reasoning
result = client.knowledge.query("Why do AI agents need memory?")
print(result.answer)
print(f"Confidence: {result.confidence}")
print(f"Latency: {result.latency_ms}ms")

# View reasoning chains
for chain in result.reasoning_chains:
    print(f"Reasoning path (confidence: {chain.total_confidence}):")
    for step in chain.steps:
        print(f"  {step.source_content} -> {step.target_content}")
```

## Features

- **Knowledge Graph Operations** - Query, ingest, and manage your knowledge graph
- **Multi-hop Reasoning** - Get answers with full reasoning chains and citations
- **Memory Management** - List, filter, and manage memories (direct and derived)
- **Chat with Streaming** - Real-time streaming responses with SSE
- **Async Support** - Full async/await support with `AsyncMemorer`
- **Type Safety** - Full type hints with Pydantic models

## Usage Examples

### Knowledge Operations

```python
from memorer import Memorer, Document

client = Memorer(api_key="your-api-key")

# Ingest with metadata
client.knowledge.ingest([
    Document(content="Neural networks are computational models.", metadata={"source": "textbook"}),
    "Deep learning uses multiple neural network layers.",
])

# Query with options
result = client.knowledge.query(
    "How are neural networks related to deep learning?",
    max_hops=3,
    confidence_threshold=0.8,
)

# Get graph statistics
stats = client.knowledge.stats()
print(f"Entities: {stats.total_entities}")
print(f"Relationships: {stats.total_relationships}")
```

### Entity Management

```python
# List entities
entities = client.entities.list(limit=50, type="fact")
for entity in entities.entities:
    print(f"{entity.type}: {entity.content}")

# Get specific entity
entity = client.entities.get("entity-uuid")

# Update entity
updated = client.entities.update(
    "entity-uuid",
    content="Updated content",
    importance=0.9,
)

# Get relationships
rels = client.entities.relationships("entity-uuid")
print(f"Outgoing: {len(rels.outgoing)}")
print(f"Incoming: {len(rels.incoming)}")

# Bulk delete
result = client.entities.bulk_delete(["uuid-1", "uuid-2"])
print(f"Deleted: {result.deleted}")
```

### Memory Management

```python
# List all memories
memories = client.memories.list(limit=20)

# List direct memories (user-stated facts)
direct = client.memories.list_direct()

# List derived memories (AI-synthesized)
derived = client.memories.list_derived()
for memory in derived.memories:
    print(f"Derived: {memory.content}")
    print(f"From: {memory.derived_from_contents}")

# Get memory statistics
stats = client.memories.stats()
print(f"Total: {stats.total_memories}")
print(f"Direct: {stats.direct_memories}")
print(f"Derived: {stats.derived_memories}")
```

### Chat with Streaming

```python
# Non-streaming
response = client.chat.send_message("Hello! What do you know about me?")
print(response.content)
print(f"Confidence: {response.confidence}")

# Streaming with iteration
for event in client.chat.send_message("Tell me about AI memory.", stream=True):
    if event.type == "token":
        print(event.content, end="", flush=True)
    elif event.type == "metadata":
        print(f"\n\nConfidence: {event.confidence}")

# Streaming with callbacks
client.chat.send_message(
    "Explain neural networks.",
    stream=True,
    on_token=lambda t: print(t, end="", flush=True),
    on_metadata=lambda m: print(f"\nLatency: {m.latency_ms}ms"),
    on_done=lambda: print("\nDone!"),
)

# Manage conversations
conv = client.chat.create_conversation(title="My Chat")
response = client.chat.send_message("Hello!", conversation_id=conv.id)

# List conversations
conversations = client.chat.list_conversations(limit=10)

# Get conversation with history
detail = client.chat.get_conversation(conv.id)
for msg in detail.messages:
    print(f"{msg.role}: {msg.content}")
```

### Async Usage

```python
import asyncio
from memorer import AsyncMemorer

async def main():
    async with AsyncMemorer(api_key="your-api-key") as client:
        # Async query
        result = await client.knowledge.query("What is AI?")
        print(result.answer)

        # Async streaming
        async for event in await client.chat.send_message("Hello!", stream=True):
            if event.type == "token":
                print(event.content, end="")

asyncio.run(main())
```

### Organization Context

```python
# Set organization context for all requests
client = Memorer(
    api_key="your-api-key",
    organization_id="org-uuid",
    project_id="project-uuid",
)

# All requests now include organization/project headers
result = client.knowledge.query("...")
```

## Error Handling

```python
from memorer import (
    Memorer,
    NotFoundError,
    ValidationError,
    RateLimitError,
    AuthenticationError,
)

client = Memorer(api_key="your-api-key")

try:
    entity = client.entities.get("non-existent-id")
except NotFoundError as e:
    print(f"Entity not found: {e.detail}")
except ValidationError as e:
    print(f"Invalid request: {e.detail}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except AuthenticationError as e:
    print(f"Auth failed: {e.detail}")
```

## Configuration

### Environment Variables

```bash
export MEMORER_API_KEY="your-api-key"
export MEMORER_BASE_URL="https://api.memorer.ai"  # optional
```

```python
# Client will use environment variables
client = Memorer()
```

### Client Options

```python
client = Memorer(
    api_key="your-api-key",
    base_url="https://api.memorer.ai",  # API base URL
    organization_id="org-uuid",          # Default organization
    project_id="project-uuid",           # Default project
    timeout=30.0,                        # Request timeout (seconds)
    max_retries=3,                       # Max retry attempts
)
```

## API Reference

### Client Classes

- `Memorer` - Synchronous client
- `AsyncMemorer` - Asynchronous client

### Resources

- `client.knowledge` - Knowledge graph operations (query, ingest, stats)
- `client.entities` - Entity CRUD operations
- `client.memories` - Memory management
- `client.chat` - Conversations and messaging

### Types

See [types.py](memorer/types.py) for all request/response models.

## License

Apache 2.0 License - see [LICENSE](LICENSE) for details.

## Links

- [Documentation](https://docs.memorer.ai)
- [API Reference](https://docs.memorer.ai/api)
- [GitHub](https://github.com/memorer/memorer)
- [Discord](https://discord.gg/memorer)
