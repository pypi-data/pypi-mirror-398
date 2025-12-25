# Artanis Python SDK

Artanis SDK for AI application observability - understand failures, build evaluation sets, and act on user feedback.

## Installation

```bash
pip install artanis-ai
```

## Quick Start

```python
from artanis import Artanis

# Initialize client
artanis = Artanis(api_key="sk_...")

# Create a trace
trace = artanis.trace("answer-question")
trace.input(question="What is AI?", model="gpt-4")
trace.output("AI stands for Artificial Intelligence")

# Record feedback
artanis.feedback(trace.id, rating="positive")
```

## Configuration

### API Key

Provide your API key either explicitly or via environment variable:

```python
# Explicit
artanis = Artanis(api_key="sk_...")

# Environment variable
export ARTANIS_API_KEY="sk_..."
artanis = Artanis()
```

### Options

```python
artanis = Artanis(
    api_key="sk_...",              # Required (or ARTANIS_API_KEY env var)
    base_url="https://app.artanis.ai",  # Optional: custom API endpoint
    enabled=True,                  # Optional: enable/disable tracing
    debug=False,                   # Optional: enable debug logging
    on_error=lambda e: print(e)    # Optional: error callback
)
```

### Environment Variables

| Variable           | Default                  | Description            |
| ------------------ | ------------------------ | ---------------------- |
| `ARTANIS_API_KEY`  | Required                 | Your API key           |
| `ARTANIS_BASE_URL` | `https://app.artanis.ai` | API endpoint           |
| `ARTANIS_ENABLED`  | `true`                   | Enable/disable tracing |
| `ARTANIS_DEBUG`    | `false`                  | Enable debug logging   |

## Usage

### Basic Tracing

```python
trace = artanis.trace("operation-name")
trace.input(question="...", context="...")
# ... perform operation ...
trace.output(result)
```

### With Metadata

```python
trace = artanis.trace(
    "answer-question",
    metadata={
        "user_id": "user-123",
        "session_id": "session-456"
    }
)
```

### Capturing State for Replay

```python
trace = artanis.trace("rag-query")

# Capture document state
trace.state("documents", [{"id": "doc1", "score": 0.95}])

# Capture configuration
trace.state("config", {"model": "gpt-4", "temperature": 0.7})

# Record inputs and output
trace.input(query="...", prompt="...")
trace.output(response)
```

### Error Handling

```python
trace = artanis.trace("risky-operation")
trace.input(data=input_data)

try:
    result = process(input_data)
    trace.output(result)
except Exception as e:
    trace.error(str(e))
    raise
```

### Context Manager

```python
with artanis.trace("operation") as trace:
    trace.input(data=...)
    result = perform_operation()
    trace.output(result)
# Automatically sends trace on exit
```

### Method Chaining

```python
artanis.trace("operation")\
    .input(question="What is AI?")\
    .state("config", {"model": "gpt-4"})\
    .output("AI stands for Artificial Intelligence")
```

### Feedback

```python
# Binary feedback
artanis.feedback(trace.id, rating="positive")
artanis.feedback(trace.id, rating="negative")

# Numeric rating (0.0-1.0)
artanis.feedback(trace.id, rating=0.85)

# With comment
artanis.feedback(
    trace.id,
    rating="negative",
    comment="The answer was incorrect"
)

# With correction
artanis.feedback(
    trace.id,
    rating="negative",
    correction={"answer": "The correct answer is..."}
)
```

## Complete Example: RAG Pipeline

```python
from artanis import Artanis

artanis = Artanis()

def answer_question(question: str, user_id: str):
    # Create trace with metadata
    trace = artanis.trace(
        "rag-answer",
        metadata={"user_id": user_id}
    )

    # Capture document corpus state
    corpus = load_documents()
    trace.state("corpus", [doc.id for doc in corpus])

    # Retrieve relevant chunks
    chunks = retriever.search(question)
    trace.state("chunks", [
        {"id": c.id, "score": c.score}
        for c in chunks
    ])

    # Generate response
    prompt = build_prompt(question, chunks)
    trace.input(
        question=question,
        prompt=prompt,
        model="gpt-4"
    )

    response = llm.generate(prompt)
    trace.output(response)

    return response, trace.id

# Later, collect feedback
answer, trace_id = answer_question("What is AI?", "user-123")
print(answer)

# User provides feedback
artanis.feedback(trace_id, rating="positive")
```

## Testing

Disable tracing in tests:

```python
# Option 1: Environment variable
export ARTANIS_ENABLED=false

# Option 2: Explicit configuration
artanis = Artanis(enabled=False)
```

## Performance

- **P50 overhead**: < 0.05ms per operation
- **P99 overhead**: < 0.5ms per operation
- All network operations are non-blocking (fire-and-forget)
- No retries or queueing to prevent memory leaks

## Error Handling Philosophy

The SDK never throws exceptions. All errors are handled silently to ensure observability never breaks production:

- Invalid API key → traces dropped, error logged (if debug)
- Network failure → traces dropped silently
- Payload too large → trace dropped, error logged

Use the `on_error` callback to monitor SDK errors:

```python
def handle_error(error: Exception):
    logger.warning(f"Artanis error: {error}")

artanis = Artanis(on_error=handle_error)
```

## Development

### Setup

```bash
cd python
pip install -e ".[dev]"
```

Note: Package name is `artanis-ai` on PyPI, but import name is still `artanis`.

### Run Tests

```bash
pytest
pytest --cov=artanis  # With coverage
```

### Format Code

```bash
black artanis tests
ruff check artanis tests
```

### Type Checking

```bash
mypy artanis
```

## Support

- Documentation: https://docs.artanis.ai
- GitHub: https://github.com/artanis-ai/sdk
- Email: team@artanis.ai

## License

MIT License - see LICENSE file for details.
