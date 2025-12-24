# Cilow Python SDK

**SOTA Memory Layer for AI Agents** - Beat the competition on LongMemEval benchmarks.

[![PyPI version](https://badge.fury.io/py/cilow.svg)](https://badge.fury.io/py/cilow)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🧠 **Multi-tier Memory** - Hot/Warm/Cold storage with automatic FRR ranking
- 🔍 **Semantic Search** - HNSW-powered vector search with >95% recall
- ⏱️ **Temporal Reasoning** - Bi-temporal graph for time-aware queries
- 🤖 **Agent Integration** - ReAct agents with memory-augmented reasoning
- 📊 **90% Token Reduction** - FRR ranking minimizes context usage
- 🔐 **Production Ready** - Auth, rate limiting, OWASP LLM Top-10 security

## Installation

```bash
pip install cilow
```

## Quick Start

```python
import asyncio
from cilow import CilowClient

async def main():
    async with CilowClient(base_url="http://localhost:8080") as client:
        # Add memories
        memory_id = await client.add_memory(
            "User prefers Python over JavaScript",
            tags=["preference", "programming"]
        )

        # Semantic search
        results = await client.search_memories("programming language preference")
        for result in results:
            print(f"[{result.score:.2f}] {result.memory.content}")

        # Create an AI agent
        agent_id = await client.create_agent("assistant", agent_type="react")

        # Execute tasks with memory context
        response = await client.execute_task(
            agent_id,
            "What programming language does the user prefer?"
        )
        print(response.response)

asyncio.run(main())
```

## Synchronous API

For simple scripts without async:

```python
from cilow import add_memory_sync, search_memories_sync

# Add a memory
memory_id = add_memory_sync("I love building AI applications")

# Search memories
results = search_memories_sync("AI development")
```

## Key Concepts

### Multi-Tier Storage

Cilow automatically manages memory across three tiers:

| Tier | Latency | Use Case |
|------|---------|----------|
| **Hot** | <1ms | Frequently accessed, recent memories |
| **Warm** | 8-10ms | Semantic search via HNSW |
| **Cold** | ~100ms | Historical, compressed memories |

### FRR Ranking

Memories are ranked by **Frequency-Recency-Relevance** scoring:

```
Score = 0.3 × Frequency + 0.3 × Recency + 0.4 × Relevance
```

This ensures the most important memories are always accessible while reducing token usage by 90%.

### Temporal Reasoning

Query memories across time:

```python
# Add temporal context
await client.add_memory("Moved to NYC", metadata={"date": "2020-01-01"})
await client.add_memory("Moved to SF", metadata={"date": "2023-06-01"})

# Temporal query (handled by bi-temporal graph)
results = await client.search_memories("Where did I live in 2021?")
```

## API Reference

### CilowClient

```python
class CilowClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    )
```

### Memory Operations

| Method | Description |
|--------|-------------|
| `add_memory(content, metadata, tags)` | Add new memory |
| `get_memory(memory_id)` | Retrieve specific memory |
| `update_memory(memory_id, content, metadata, tags)` | Update memory |
| `delete_memory(memory_id)` | Delete memory |
| `search_memories(query, limit, tags, min_relevance)` | Semantic search |
| `get_memory_stats()` | Get system statistics |

### Agent Operations

| Method | Description |
|--------|-------------|
| `create_agent(name, agent_type, config)` | Create AI agent |
| `get_agent(agent_id)` | Get agent details |
| `execute_task(agent_id, task, context_limit)` | Execute task |

### Fact Extraction

```python
facts = await client.extract_facts(
    "John works at Acme Corp and loves hiking on weekends"
)
for fact in facts:
    print(f"[{fact.fact_type}] {fact.statement} ({fact.confidence:.0%})")
```

## Benchmarks

Cilow achieves **SOTA performance** on LongMemEval:

| Metric | Cilow | Emergence AI | Zep |
|--------|-------|--------------|-----|
| Turn Recall | **>87%** | 86% | 71.2% |
| Token Reduction | **90%** | - | - |
| Vector Recall | **>95%** | - | - |

## Error Handling

```python
from cilow import CilowError, NotFoundError, RateLimitError

try:
    memory = await client.get_memory("invalid-id")
except NotFoundError:
    print("Memory not found")
except RateLimitError:
    print("Rate limit exceeded, retry later")
except CilowError as e:
    print(f"API error: {e}")
```

## Configuration

Environment variables:

```bash
CILOW_API_URL=http://localhost:8080
CILOW_API_KEY=your-api-key
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- 📖 [Documentation](https://docs.cilow.ai)
- 🐛 [Issue Tracker](https://github.com/cilow-ai/cilow/issues)
- 💬 [Discord](https://discord.gg/cilow)
