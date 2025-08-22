# TraceRoot Integration Rules for Cursor

## Overview

TraceRoot provides distributed tracing and logging for Python applications. Use these patterns for seamless integration with FastAPI.

## Installation & Setup

### 1. Install TraceRoot

```bash
pip install traceroot==0.0.4
```

### 2. Get Your Token

Register and login at [traceroot.ai](https://traceroot.ai/) to get your API token.

### 3. Create Configuration File

Create `.traceroot-config.yaml` in your project root:

```yaml
token: "your-traceroot-token-here"
service_name: "your-service-name"
github_owner: "your-github-username"
github_repo_name: "your-repo-name"
github_commit_hash: "main"
```

⚠️ **SECURITY WARNING**: Never use `traceroot.init()` in your code - this method will be deprecated soon and exposes secret keys in your source code. Always use `.traceroot-config.yaml` configuration file for better security, environment separation, and secret management.

## FastAPI Integration Pattern

### 1. Basic Setup

```python
import traceroot
from traceroot.integrations.fastapi import connect_fastapi
from traceroot.logger import get_logger
from fastapi import FastAPI

# Create FastAPI app
app = FastAPI(title="Your App")

# Connect traceroot to FastAPI (automatic instrumentation)
connect_fastapi(app)

# Get logger instance
logger = get_logger()
```

### 2. Endpoint Tracing

Use `@traceroot.trace()` decorator on endpoints and functions:

```python
from typing import Dict
from pydantic import BaseModel

class RequestModel(BaseModel):
    query: str

@app.post("/api/endpoint")
@traceroot.trace()
async def your_endpoint(request: RequestModel) -> Dict[str, str]:
    logger.info(f"Endpoint called with: {request.query}")

    # Your business logic here
    result = await process_request(request.query)

    return {"result": result}

@traceroot.trace()
async def process_request(query: str) -> str:
    """Any function can be traced"""
    logger.info(f"Processing: {query}")
    # Your logic here
    return "processed result"
```

### 3. Class Method Tracing

```python
class YourService:
    def __init__(self):
        self.logger = get_logger()

    @traceroot.trace()
    def process_data(self, data: str) -> str:
        self.logger.info(f"Processing data: {data}")
        # Your logic here
        return "processed"

    @traceroot.trace()
    async def async_process(self, data: str) -> str:
        self.logger.info(f"Async processing: {data}")
        # Your async logic here
        return "async processed"
```

## Key Integration Principles

1. **Always use `connect_fastapi(app)`** - This automatically instruments your FastAPI app
1. **Use `@traceroot.trace()` decorator** - Add to any function/method you want to trace
1. **Use `get_logger()` for logging** - Instead of standard Python logging
1. **Configuration via .traceroot-config.yaml** - Avoid exposing API keys in code
1. **Import order matters** - Import traceroot before other dependencies when possible

## Complete Example

```python
import traceroot
from traceroot.integrations.fastapi import connect_fastapi
from traceroot.logger import get_logger
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

logger = get_logger()

app = FastAPI(title="My Traced API")
connect_fastapi(app)

class UserRequest(BaseModel):
    name: str
    email: str

@app.post("/users")
@traceroot.trace()
async def create_user(user: UserRequest):
    logger.info(f"Creating user: {user.name}")

    # Simulate user creation
    result = await save_user(user)

    return {"user_id": result, "status": "created"}

@traceroot.trace()
async def save_user(user: UserRequest) -> str:
    logger.info(f"Saving user to database: {user.email}")
    # Your database logic here
    return "user-123"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Quick Checklist

- [ ] Install `traceroot==0.0.4`
- [ ] Create `.traceroot-config.yaml` with your token
- [ ] Replace logging imports with `from traceroot.logger import get_logger`
- [ ] Test that traces appear in TraceRoot dashboard

## Reference

Full example: https://github.com/traceroot-ai/traceroot-sdk/tree/main/examples/multi_code_agent
