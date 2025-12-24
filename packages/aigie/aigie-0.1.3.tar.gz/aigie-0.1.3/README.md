# Aigie SDK

Production-grade Python SDK for integrating Aigie monitoring into your AI agent workflows.

## ✨ Features

- 🚀 **Event Buffering**: 10-100x performance improvement with batch uploads
- 🎯 **Decorator Support**: 50%+ less boilerplate code
- ⚙️ **Flexible Configuration**: Config class with sensible defaults
- 🔄 **Automatic Retries**: Exponential backoff with configurable policies
- 🔗 **LangChain Integration**: Seamless callback handler
- 📊 **Production Ready**: Handles network failures, race conditions, and more

## Quick Start

### Installation

```bash
pip install aigie
```

### Basic Usage

#### Option 1: Context Manager (Traditional)
```python
from aigie import Aigie

aigie = Aigie()
await aigie.initialize()

async with aigie.trace("My Workflow") as trace:
    async with trace.span("operation", type="llm") as span:
        result = await do_work()
        span.set_output({"result": result})
```

#### Option 2: Decorator (Recommended - 50% less code!)
```python
from aigie import Aigie

aigie = Aigie()
await aigie.initialize()

@aigie.trace(name="my_workflow")
async def my_workflow():
    @aigie.span(name="operation", type="llm")
    async def operation():
        return await do_work()
    return await operation()
```

#### Option 3: With Configuration
```python
from aigie import Aigie, Config

config = Config(
    api_url="https://api.aigie.com",
    api_key="your-key",
    batch_size=100,  # Buffer 100 events before sending
    flush_interval=5.0  # Or flush every 5 seconds
)
aigie = Aigie(config=config)
await aigie.initialize()
```

## Configuration

### Environment Variables
```bash
export AIGIE_API_URL=http://your-aigie-instance:8000/api
export AIGIE_API_KEY=your-api-key-here
export AIGIE_BATCH_SIZE=100
export AIGIE_FLUSH_INTERVAL=5.0
```

### Config Object
```python
from aigie import Config

config = Config(
    api_url="https://api.aigie.com",
    api_key="your-key",
    batch_size=100,
    flush_interval=5.0,
    enable_buffering=True,  # Default: True
    max_retries=3
)
```

## Performance

### Before (No Buffering)
- 1000 spans = 1000+ API calls
- ~30 seconds total time
- High network overhead

### After (With Buffering)
- 1000 spans = 2-10 API calls
- ~0.5 seconds total time
- **99%+ reduction in API calls**

## Advanced Features

### OpenTelemetry Integration

Works with any OpenTelemetry-compatible tool (Datadog, New Relic, Jaeger, etc.):

```python
from aigie import Aigie
from aigie.opentelemetry import setup_opentelemetry

aigie = Aigie()
await aigie.initialize()

# One-line setup
setup_opentelemetry(aigie, service_name="my-service")

# Now all OTel spans automatically go to Aigie!
from opentelemetry import trace
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("operation"):
    # Automatically traced
    pass
```

### Synchronous API

For non-async codebases:

```python
from aigie import AigieSync

aigie = AigieSync()
aigie.initialize()  # Blocking

with aigie.trace("workflow") as trace:
    with trace.span("operation") as span:
        result = do_work()  # Sync code
        span.set_output({"result": result})
```

## Installation

### Basic
```bash
pip install aigie
```

### With OpenTelemetry
```bash
pip install aigie[opentelemetry]
```

### With LangChain
```bash
pip install aigie[langchain]
```

### All Features
```bash
pip install aigie[all]
```

## Advanced Features (Phase 3)

### W3C Trace Context Propagation

Distributed tracing across microservices:

```python
# Extract from incoming request
context = aigie.extract_trace_context(request.headers)

async with aigie.trace("workflow") as trace:
    trace.set_trace_context(context)
    
    # Propagate to downstream service
    headers = trace.get_trace_headers()
    response = await httpx.get("https://api.example.com", headers=headers)
```

### Prompt Management

Create, version, and track prompts:

```python
# Create prompt
prompt = await aigie.prompts.create(
    name="customer_support",
    template="You are a helpful assistant. Customer: {customer_name}",
    version="1.0"
)

# Use in trace
async with aigie.trace("support") as trace:
    trace.set_prompt(prompt)
    rendered = prompt.render(customer_name="John")
    response = await llm.ainvoke(rendered)
```

### Evaluation Hooks

Automatic quality monitoring:

```python
from aigie import EvaluationHook, ScoreType

hook = EvaluationHook(
    name="accuracy",
    evaluator=accuracy_evaluator,
    score_type=ScoreType.ACCURACY
)

async with aigie.trace("workflow") as trace:
    trace.add_evaluation_hook(hook)
    result = await do_work()
    await trace.run_evaluations(expected, result)
```

### Streaming Support

Real-time span updates:

```python
async with aigie.trace("workflow") as trace:
    async with trace.span("llm_call", stream=True) as span:
        async for chunk in llm.astream("Hello"):
            span.append_output(chunk)  # Update in real-time
            yield chunk
```

## Documentation

- [SDK Improvement Analysis](./SDK_IMPROVEMENT_ANALYSIS.md) - Comprehensive analysis
- [Examples](./EXAMPLES_IMPROVED.md) - Before/after code examples
- [Comparison Table](./COMPARISON_TABLE.md) - Feature comparison with market leaders
- [Phase 2 Features](./PHASE2_FEATURES.md) - OpenTelemetry, Sync API, Type Hints
- [Phase 3 Features](./PHASE3_FEATURES.md) - W3C Context, Prompts, Evaluations, Streaming


