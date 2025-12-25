# GenAI Telemetry

[![PyPI version](https://badge.fury.io/py/genai-telemetry.svg)](https://badge.fury.io/py/genai-telemetry)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Observability SDK for GenAI/LLM applications.**

Send telemetry data to any observability platform with a single, unified API.

## Supported Platforms

| Platform | Status | Description |
|----------|--------|-------------|
| **Splunk** | ✅ Ready | HTTP Event Collector (HEC) |
| **Elasticsearch** | ✅ Ready | Bulk API with daily indices |
| **OpenTelemetry** | ✅ Ready | OTLP HTTP (Jaeger, Tempo, etc.) |
| **Datadog** | ✅ Ready | Direct API integration |
| **Prometheus** | ✅ Ready | Push Gateway |
| **Grafana Loki** | ✅ Ready | Log aggregation |
| **AWS CloudWatch** | ✅ Ready | CloudWatch Logs |
| **Console** | ✅ Ready | Colored terminal output |
| **File** | ✅ Ready | JSONL with rotation |

## Installation

```bash
# Core package (no dependencies)
pip install genai-telemetry

# With optional dependencies
pip install genai-telemetry[opentelemetry]  # For OTLP
pip install genai-telemetry[aws]            # For CloudWatch
pip install genai-telemetry[all]            # All optional deps
```

## Quick Start

### Splunk

```python
from genai_telemetry import setup_telemetry, trace_llm

setup_telemetry(
    workflow_name="my-chatbot",
    exporter="splunk",
    splunk_url="https://splunk.company.com:8088",
    splunk_token="your-hec-token"
)

@trace_llm(model_name="gpt-4o", model_provider="openai")
def chat(message):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": message}]
    )
    return response.choices[0].message.content

# Telemetry is automatic!
answer = chat("What is the capital of France?")
```

### Elasticsearch

```python
from genai_telemetry import setup_telemetry, trace_llm

setup_telemetry(
    workflow_name="my-chatbot",
    exporter="elasticsearch",
    es_hosts=["http://localhost:9200"],
    es_index="genai-traces"
)

@trace_llm(model_name="gpt-4o", model_provider="openai")
def chat(message):
    # Your LLM code here
    pass
```

### OpenTelemetry (Jaeger, Tempo, Datadog Agent, etc.)

```python
from genai_telemetry import setup_telemetry, trace_llm

setup_telemetry(
    workflow_name="my-chatbot",
    exporter="otlp",
    otlp_endpoint="http://localhost:4318"
)

@trace_llm(model_name="claude-3", model_provider="anthropic")
def chat(message):
    # Your LLM code here
    pass
```

### Datadog

```python
from genai_telemetry import setup_telemetry, trace_llm

setup_telemetry(
    workflow_name="my-chatbot",
    exporter="datadog",
    datadog_api_key="your-api-key",
    datadog_site="datadoghq.com"
)

@trace_llm(model_name="gpt-4o", model_provider="openai")
def chat(message):
    # Your LLM code here
    pass
```

### Prometheus

```python
from genai_telemetry import setup_telemetry, trace_llm

setup_telemetry(
    workflow_name="my-chatbot",
    exporter="prometheus",
    prometheus_gateway="http://localhost:9091"
)

@trace_llm(model_name="gpt-4o", model_provider="openai")
def chat(message):
    # Your LLM code here
    pass
```

### Grafana Loki

```python
from genai_telemetry import setup_telemetry, trace_llm

setup_telemetry(
    workflow_name="my-chatbot",
    exporter="loki",
    loki_url="http://localhost:3100"
)

@trace_llm(model_name="gpt-4o", model_provider="openai")
def chat(message):
    # Your LLM code here
    pass
```

### AWS CloudWatch

```python
from genai_telemetry import setup_telemetry, trace_llm

setup_telemetry(
    workflow_name="my-chatbot",
    exporter="cloudwatch",
    cloudwatch_log_group="/genai/my-chatbot",
    cloudwatch_region="us-east-1"
)

@trace_llm(model_name="gpt-4o", model_provider="openai")
def chat(message):
    # Your LLM code here
    pass
```

### Multiple Exporters

Send to multiple platforms simultaneously:

```python
from genai_telemetry import setup_telemetry, trace_llm

setup_telemetry(
    workflow_name="my-chatbot",
    exporter=[
        {"type": "splunk", "url": "https://splunk:8088", "token": "xxx"},
        {"type": "elasticsearch", "hosts": ["http://localhost:9200"]},
        {"type": "console"}
    ]
)

@trace_llm(model_name="gpt-4o", model_provider="openai")
def chat(message):
    # Traces go to Splunk, Elasticsearch, AND console!
    pass
```

### Console (for debugging)

```python
from genai_telemetry import setup_telemetry, trace_llm

setup_telemetry(
    workflow_name="my-chatbot",
    exporter="console"
)

@trace_llm(model_name="gpt-4o", model_provider="openai")
def chat(message):
    pass

chat("Hello!")
# Output: [LLM         ] chat                           |   1234.5ms | OK    | gpt-4o | 57 tokens
```

## Available Decorators

| Decorator | Span Type | Use Case |
|-----------|-----------|----------|
| `@trace_llm` | LLM | OpenAI, Anthropic, etc. |
| `@trace_embedding` | EMBEDDING | Embedding generation |
| `@trace_retrieval` | RETRIEVER | Vector DB queries |
| `@trace_tool` | TOOL | Function/tool calls |
| `@trace_chain` | CHAIN | Pipelines/workflows |
| `@trace_agent` | AGENT | Agent execution |

## RAG Pipeline Example

```python
from genai_telemetry import (
    setup_telemetry,
    trace_llm,
    trace_embedding,
    trace_retrieval,
    trace_chain
)
from openai import OpenAI

setup_telemetry(
    workflow_name="rag-app",
    exporter="elasticsearch",
    es_hosts=["http://localhost:9200"]
)

client = OpenAI()

@trace_embedding(model="text-embedding-3-small")
def embed_query(text):
    response = client.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding

@trace_retrieval(vector_store="pinecone", embedding_model="text-embedding-3-small")
def search_docs(query_embedding):
    # Your vector search here
    return pinecone_index.query(vector=query_embedding, top_k=5)

@trace_llm(model_name="gpt-4o", model_provider="openai")
def generate_answer(context, question):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"Context: {context}"},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content

@trace_chain(name="rag-pipeline")
def rag_query(question):
    embedding = embed_query(question)
    docs = search_docs(embedding)
    context = "\n".join([d.text for d in docs])
    answer = generate_answer(context, question)
    return answer

# All spans are traced!
result = rag_query("What is machine learning?")
```

## Telemetry Data Schema

Each span contains:

```json
{
    "trace_id": "abc123...",
    "span_id": "xyz789...",
    "parent_span_id": "...",
    "span_type": "LLM",
    "name": "chat",
    "workflow_name": "my-chatbot",
    "timestamp": "2025-12-17T10:30:00Z",
    "duration_ms": 1234.5,
    "status": "OK",
    "is_error": 0,
    "model_name": "gpt-4o",
    "model_provider": "openai",
    "input_tokens": 15,
    "output_tokens": 42
}
```

## Configuration Options

### Common Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `workflow_name` | str | required | Your application name |
| `exporter` | str/list | "console" | Exporter type or list |
| `console` | bool | False | Also print to console |
| `batch_size` | int | 1 | Spans per batch |
| `flush_interval` | float | 5.0 | Seconds between flushes |
| `verify_ssl` | bool | False | Verify SSL certificates |

### Splunk Options

| Option | Type | Default |
|--------|------|---------|
| `splunk_url` | str | required |
| `splunk_token` | str | required |
| `splunk_index` | str | "genai_traces" |

### Elasticsearch Options

| Option | Type | Default |
|--------|------|---------|
| `es_hosts` | list | ["http://localhost:9200"] |
| `es_index` | str | "genai-traces" |
| `es_api_key` | str | None |
| `es_username` | str | None |
| `es_password` | str | None |

### OpenTelemetry Options

| Option | Type | Default |
|--------|------|---------|
| `otlp_endpoint` | str | "http://localhost:4318" |
| `otlp_headers` | dict | None |

### Datadog Options

| Option | Type | Default |
|--------|------|---------|
| `datadog_api_key` | str | required |
| `datadog_site` | str | "datadoghq.com" |

## Performance

- **Zero dependencies** for core functionality
- **< 3ms overhead** per span
- **Thread-safe** for concurrent use
- **Async-friendly** batching
- **Automatic retry** on failures

## Why genai-telemetry?

| Feature | genai-telemetry | Others |
|---------|-----------------|--------|
| Multi-platform | ✅ 9 platforms | ❌ Usually 1 |
| Zero dependencies | ✅ Core only | ❌ Heavy deps |
| LLM-specific metrics | ✅ Tokens, costs | ❌ Generic |
| Simple decorators | ✅ One line | ❌ Complex |
| Auto token extraction | ✅ OpenAI, etc. | ❌ Manual |

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## Author

**Kamal Singh Bisht**
- IEEE Senior Member
- [GitHub](https://github.com/rootiq-ai)
- [LinkedIn](https://www.linkedin.com/in/kmluvce)
