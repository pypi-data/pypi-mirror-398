# Jarvis SDK v0 - Product Requirements Document

## Overview

A minimal Python SDK that lets users define inference endpoints using a decorated class pattern and run them locally as APIs.

---

## Problem Statement

Developers building ML inference services need to write boilerplate code for:

- Setting up web servers
- Handling request/response serialization
- Managing model lifecycle (loading once, reusing across requests)

Jarvis SDK provides a simple decorator-based pattern that handles all of this automatically.

---

## Goals

1. **Simple API** - One decorator, one class, one method
2. **Type-safe** - Pydantic models for input/output validation
3. **Developer-friendly** - IDE autocomplete, typo detection, auto-generated docs
4. **Minimal** - No GPU, no cloud, just local CPU execution

---

## Non-Goals (for v0)

- GPU support
- Cloud deployment to Jarvis Labs
- Authentication
- Multiple routes per endpoint
- Billing/metering

---

## User Experience

### Defining an Endpoint

```python
# app.py
import jarvis
from pydantic import BaseModel

class Input(BaseModel):
    name: str

class Output(BaseModel):
    message: str

@jarvis.endpoint(name="greeter")
class Greeter:
    def setup(self):
        self.prefix = "Hello"

    def run(self, input: Input) -> Output:
        return Output(message=f"{self.prefix}, {input.name}!")
```

### Running Locally

```bash
jarvis dev app.py
```

Output:

```
Serving greeter at http://localhost:8000
Docs at http://localhost:8000/docs
```

### Testing

```bash
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"name": "Vishnu"}'
```

Response:

```json
{"message": "Hello, Vishnu!"}
```

---

## API Specification

### `@jarvis.endpoint()`

Decorator that marks a class as a Jarvis endpoint.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | `str` | Yes | - | Name of the endpoint |

### Class Requirements

| Method | Required | Description |
|--------|----------|-------------|
| `setup(self)` | No | Called once when server starts. Use for loading models, initializing resources. |
| `run(self, input) -> output` | Yes | Handles incoming requests. Must have type hints for input and output. |

### Input/Output

- Input must be a Pydantic `BaseModel`
- Output must be a Pydantic `BaseModel`
- Type hints are required on the `run()` method

---

## CLI Specification

### `jarvis dev <file>`

Runs the endpoint locally for development.

| Option | Default | Description |
|--------|---------|-------------|
| `--port` | `8000` | Port to serve on |

---

## Auto-Generated Features

| Feature | Description |
|---------|-------------|
| OpenAPI docs | Available at `/docs` |
| Request validation | Invalid input returns 422 with details |
| JSON serialization | Automatic based on Pydantic models |

---

## Error Handling

| Error | Behavior |
|-------|----------|
| Missing `run()` method | Error at startup: "Endpoint class must define a run() method" |
| Missing type hints on `run()` | Error at startup: "run() must have type hints for input and output" |
| Invalid input JSON | 422 response with validation errors |
| Exception in `run()` | 500 response with error message |
| Exception in `setup()` | Server fails to start with error message |

---

## Example: ML Inference

```python
import jarvis
from pydantic import BaseModel

class SentimentInput(BaseModel):
    text: str

class SentimentOutput(BaseModel):
    label: str
    score: float

@jarvis.endpoint(name="sentiment")
class SentimentAnalyzer:
    def setup(self):
        from transformers import pipeline
        self.pipe = pipeline("sentiment-analysis")

    def run(self, input: SentimentInput) -> SentimentOutput:
        result = self.pipe(input.text)[0]
        return SentimentOutput(
            label=result["label"],
            score=result["score"]
        )
```

---

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Web framework | FastAPI | Auto-generates OpenAPI, handles validation |
| Validation | Pydantic | Standard, good IDE support |
| Config style | Decorator params | Typo detection, autocomplete |
| Class inheritance | Not required | Simpler, less magic |
| Routes | Single `run()` method | Simplicity for v0 |

---

## Success Criteria

1. User can define an endpoint in <10 lines of code
2. `jarvis dev` starts a working server in <2 seconds
3. Typos in decorator params raise immediate errors
4. IDE autocomplete works for all decorator parameters
5. OpenAPI docs are auto-generated and accurate

---

## Future Considerations (v1+)

- `@jarvis.route()` for multiple paths per endpoint
- `gpu` parameter for GPU selection
- `requirements` parameter for dependencies
- `jarvis deploy` for cloud deployment to Jarvis Labs
- Authentication and API keys
- Billing hooks
- Keep-alive and concurrency settings
