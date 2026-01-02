# Utilities Guide

Complete guide to common utilities, exceptions, decorators, and logging in Orca SDK.

## Table of Contents

- [Exceptions](#exceptions)
- [Decorators](#decorators)
- [Logging](#logging)
- [Type Guards](#type-guards)
- [Utility Functions](#utility-functions)
- [App & Lambda Factories](#app--lambda-factories)

## Exceptions

### Exception Hierarchy

Orca SDK provides a comprehensive exception hierarchy:

```
OrcaException (base)
├── ConfigurationError
├── ValidationError
├── CommunicationError
│   ├── StreamError
│   └── APIError
├── BufferError
├── SessionError
└── DeploymentError
```

### OrcaException

Base exception for all Orca errors.

```python
from orca.common.exceptions import OrcaException

try:
    # Your code
    pass
except OrcaException as e:
    print(f"Error: {e.message}")
    print(f"Code: {e.error_code}")
    print(f"Context: {e.context}")

    # Get full error dict
    error_dict = e.to_dict()
    print(error_dict)
```

**Properties:**

| Property     | Type   | Description        |
| ------------ | ------ | ------------------ |
| `message`    | `str`  | Error message      |
| `error_code` | `str`  | Error code         |
| `context`    | `Dict` | Additional context |

**Methods:**

#### `to_dict() -> Dict`

Convert exception to dictionary.

```python
error_dict = exception.to_dict()
# Returns: {'message': '...', 'error_code': '...', 'context': {...}}
```

### ConfigurationError

Configuration-related errors.

```python
from orca.common.exceptions import ConfigurationError

if not api_key:
    raise ConfigurationError(
        "API key is missing",
        error_code="MISSING_API_KEY",
        context={"env_var": "OPENAI_API_KEY"}
    )
```

### ValidationError

Input validation errors.

```python
from orca.common.exceptions import ValidationError

def validate_message(data):
    if not data.message:
        raise ValidationError(
            "Message cannot be empty",
            error_code="EMPTY_MESSAGE",
            context={"field": "message"}
        )

    if len(data.message) > 10000:
        raise ValidationError(
            "Message too long",
            error_code="MESSAGE_TOO_LONG",
            context={"length": len(data.message), "max": 10000}
        )
```

### CommunicationError

Communication-related errors (base for StreamError and APIError).

```python
from orca.common.exceptions import CommunicationError

try:
    response = api_client.post(url, data)
except Exception as e:
    raise CommunicationError(
        "Failed to communicate with API",
        error_code="API_COMM_ERROR",
        context={"url": url, "error": str(e)}
    ) from e
```

### StreamError

Streaming-specific errors.

```python
from orca.common.exceptions import StreamError

try:
    stream_client.send_delta(channel, uuid, thread_id, content)
except Exception as e:
    raise StreamError(
        "Failed to stream content",
        error_code="STREAM_FAILED",
        context={"channel": channel}
    ) from e
```

### APIError

API-specific errors.

```python
from orca.common.exceptions import APIError

if response.status_code != 200:
    raise APIError(
        "API request failed",
        error_code="API_REQUEST_FAILED",
        context={
            "status_code": response.status_code,
            "url": url,
            "response": response.text
        }
    )
```

## Decorators

### @retry

Retry failed operations with exponential backoff.

```python
from orca.common.decorators import retry

@retry(max_attempts=3, delay=1.0, backoff=2.0)
def unstable_operation():
    # This will retry up to 3 times
    response = requests.get("https://api.example.com")
    return response.json()

# Usage
try:
    data = unstable_operation()
except Exception as e:
    print(f"Failed after retries: {e}")
```

**Parameters:**

| Parameter      | Type    | Default        | Description              |
| -------------- | ------- | -------------- | ------------------------ |
| `max_attempts` | `int`   | 3              | Maximum retry attempts   |
| `delay`        | `float` | 1.0            | Initial delay in seconds |
| `backoff`      | `float` | 2.0            | Backoff multiplier       |
| `exceptions`   | `Tuple` | `(Exception,)` | Exceptions to retry      |

### @log_execution

Log function execution with timing.

```python
from orca.common.decorators import log_execution
import logging

logger = logging.getLogger(__name__)

@log_execution(logger, level=logging.INFO)
def process_data(data):
    # Execution will be logged automatically
    return data.upper()

# Output:
# INFO: Executing process_data with args: ('hello',) kwargs: {}
# INFO: process_data completed in 0.001s
```

**Parameters:**

| Parameter    | Type     | Default | Description      |
| ------------ | -------- | ------- | ---------------- |
| `logger`     | `Logger` | `None`  | Logger instance  |
| `level`      | `int`    | `INFO`  | Log level        |
| `log_args`   | `bool`   | `True`  | Log arguments    |
| `log_result` | `bool`   | `False` | Log return value |

### @measure_time

Measure and log execution time.

```python
from orca.common.decorators import measure_time

# Without label (uses function name)
@measure_time
def process_large_dataset(data):
    # Processing time will be logged
    return [item * 2 for item in data]

# Output:
# process_large_dataset took 0.234s

# With custom label
@measure_time("data_processing")
def process_large_dataset(data):
    # Processing time will be logged with custom label
    return [item * 2 for item in data]

# Output:
# data_processing took 0.234s
```

**Parameters:**

| Parameter | Type  | Default | Description              |
| --------- | ----- | ------- | ------------------------ |
| `label`   | `str` | `None`  | Custom label for logging |

If no label is provided, the function name is used automatically.

### @handle_errors

Automatic error handling with custom error handler.

```python
from orca.common.decorators import handle_errors

def error_callback(exception, func_name):
    print(f"Error in {func_name}: {exception}")
    # Send to monitoring service
    send_to_sentry(exception)

@handle_errors(callback=error_callback, reraise=True)
def risky_operation():
    # Errors will be caught and logged
    raise ValueError("Something went wrong")
```

**Parameters:**

| Parameter  | Type       | Default | Description             |
| ---------- | ---------- | ------- | ----------------------- |
| `callback` | `Callable` | `None`  | Error callback function |
| `reraise`  | `bool`     | `True`  | Re-raise after handling |
| `default`  | `Any`      | `None`  | Default return value    |

### @deprecated

Mark functions as deprecated.

```python
from orca.common.decorators import deprecated

@deprecated("Use new_function() instead")
def old_function():
    return "old"

# Usage will show warning:
# DeprecationWarning: old_function is deprecated. Use new_function() instead
```

### @validate_types

Runtime type validation.

```python
from orca.common.decorators import validate_types

@validate_types
def add_numbers(x: int, y: int) -> int:
    return x + y

# Correct usage
result = add_numbers(5, 10)  # OK

# Wrong usage
result = add_numbers("5", 10)  # Raises TypeError
```

### @cache_result

Cache function results.

```python
from orca.common.decorators import cache_result

@cache_result(ttl=3600)  # Cache for 1 hour
def expensive_computation(x):
    # This will only run once per unique x value
    import time
    time.sleep(2)
    return x * 2

# First call: takes 2 seconds
result1 = expensive_computation(5)

# Second call: instant (cached)
result2 = expensive_computation(5)
```

## Logging

### setup_logging

Configure logging for your application.

```python
from orca.common.logging_config import setup_logging
import logging

# Basic setup
setup_logging(level=logging.INFO)

# With file output
setup_logging(
    level=logging.DEBUG,
    log_file="app.log",
    max_bytes=10 * 1024 * 1024,  # 10 MB
    backup_count=5
)

# With custom format
setup_logging(
    level=logging.INFO,
    format_string="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    date_format="%Y-%m-%d %H:%M:%S"
)
```

**Parameters:**

| Parameter       | Type   | Default | Description       |
| --------------- | ------ | ------- | ----------------- |
| `level`         | `int`  | `INFO`  | Logging level     |
| `log_file`      | `str`  | `None`  | Log file path     |
| `max_bytes`     | `int`  | `10MB`  | Max file size     |
| `backup_count`  | `int`  | 5       | Number of backups |
| `format_string` | `str`  | Default | Log format        |
| `date_format`   | `str`  | ISO     | Date format       |
| `colored`       | `bool` | `True`  | Colored output    |

### get_logger

Get configured logger instance.

```python
from orca.common.logging_config import get_logger

logger = get_logger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### enable_debug_logging

Enable debug logging temporarily.

```python
from orca.common.logging_config import enable_debug_logging

# Enable debug mode
enable_debug_logging()

# Now all loggers will show debug messages
logger.debug("This will now be visible")
```

### Structured Logging

```python
from orca.common.logging_config import get_logger

logger = get_logger(__name__)

# Log with extra context
logger.info(
    "User action",
    extra={
        "user_id": 123,
        "action": "login",
        "ip": "192.168.1.1"
    }
)
```

## Type Guards

### Runtime Type Checking

```python
from orca.common.type_guards import (
    is_valid_string,
    is_valid_dict,
    is_valid_list,
    validate_type
)

# Check if value is valid string
if is_valid_string(value, min_length=1, max_length=100):
    print("Valid string")

# Check if value is valid dict
if is_valid_dict(value, required_keys=["id", "name"]):
    print("Valid dict")

# Check if value is valid list
if is_valid_list(value, item_type=str, min_length=1):
    print("Valid list")

# Validate type (raises exception on failure)
validate_type(value, expected_type=int, param_name="user_id")
```

### Available Type Guards

```python
from orca.common.type_guards import *

# String validation
is_valid_string(value, min_length=None, max_length=None, pattern=None)

# Number validation
is_valid_number(value, min_value=None, max_value=None, allow_float=True)

# Dict validation
is_valid_dict(value, required_keys=None, optional_keys=None)

# List validation
is_valid_list(value, item_type=None, min_length=None, max_length=None)

# URL validation
is_valid_url(value, require_https=False)

# Email validation
is_valid_email(value)

# UUID validation
is_valid_uuid(value)

# JSON validation
is_valid_json(value)
```

## Utility Functions

### File Utilities

```python
from orca.utils.files import (
    read_file,
    write_file,
    ensure_dir,
    get_file_size,
    get_mime_type
)

# Read file
content = read_file("data.txt")

# Write file
write_file("output.txt", "Hello, world!")

# Ensure directory exists
ensure_dir("data/output")

# Get file size
size = get_file_size("data.txt")  # In bytes

# Get MIME type
mime = get_mime_type("image.png")  # Returns: "image/png"
```

### Environment Utilities

```python
from orca.utils.environment import (
    get_env,
    get_env_bool,
    get_env_int,
    require_env
)

# Get environment variable with default
api_key = get_env("API_KEY", default="")

# Get boolean from environment
debug = get_env_bool("DEBUG", default=False)

# Get integer from environment
timeout = get_env_int("TIMEOUT", default=30)

# Require environment variable (raises if missing)
api_key = require_env("API_KEY")
```

### Response Handling

```python
from orca.utils.response_handler import (
    format_error_response,
    format_success_response,
    parse_json_response
)

# Format error
error = format_error_response(
    message="Not found",
    code=404,
    details={"resource": "user"}
)

# Format success
success = format_success_response(
    data={"user_id": 123},
    message="User created"
)

# Parse JSON response
data = parse_json_response(response_text)
```
## App & Lambda Factories

Orca SDK provides factory functions to quickly bootstrap your agent for different environments.

### create_agent_app

Creates a standard FastAPI application for your agent. Ideal for local development, Docker/Kubernetes, or simple HTTP servers.

```python
from orca import create_agent_app, ChatMessage, OrcaHandler

# 1. Define your processing logic
async def process_msg(data: ChatMessage):
    handler = OrcaHandler()
    session = handler.begin(data)
    session.stream(f"Echo: {data.message}")
    session.close()

# 2. Create the app
app = create_agent_app(
    process_message_func=process_msg,
    app_title="My Agent API"
)

# Run with: uvicorn main:app
```

### create_hybrid_handler

Creates a unified handler for AWS Lambda that supports multiple event sources (HTTP, SQS, and Cron).

```python
from orca import create_hybrid_handler, ChatMessage, OrcaHandler

# 1. Define your processing logic
async def process_msg(data: ChatMessage):
    handler = OrcaHandler()
    session = handler.begin(data)
    # ... logic ...
    session.close()

# 2. Create the Lambda handler
# Automatically handles FastAPI (HTTP), SQS, and Cron routing
handler = create_hybrid_handler(
    process_message_func=process_msg,
    app_title="My Lambda Agent"
)
```

**Key Features:**
- **Centralized Event Detection**: Routes events to the right handler automatically.
- **SQS Offloading**: If `SQS_QUEUE_URL` is set, HTTP requests are automatically queued for async processing.
- **Event Loop Fixes**: Solves common asyncio issues in Lambda environments.

## Best Practices

### 1. Use Custom Exceptions

```python
from orca.common.exceptions import OrcaException

class CustomAgentError(OrcaException):
    """Custom error for agent-specific issues."""
    pass

try:
    # Your code
    pass
except SomeError as e:
    raise CustomAgentError(
        "Agent processing failed",
        error_code="AGENT_ERROR",
        context={"details": str(e)}
    ) from e
```

### 2. Combine Decorators

```python
from orca.common.decorators import retry, log_execution, measure_time

@retry(max_attempts=3)
@log_execution(logger)
@measure_time
def call_external_api():
    # This will retry, log, and measure time
    return requests.get("https://api.example.com")
```

### 3. Structure Logging

```python
from orca.common.logging_config import setup_logging, get_logger

# Setup once at startup
setup_logging(
    level=logging.INFO,
    log_file="app.log",
    colored=True
)

# Use throughout application
logger = get_logger(__name__)

logger.info("Starting processing", extra={
    "user_id": user_id,
    "request_id": request_id
})
```

### 4. Validate Input

```python
from orca.common.type_guards import validate_type, is_valid_string
from orca.common.exceptions import ValidationError

def process_user_input(user_id: int, message: str):
    # Validate types
    validate_type(user_id, int, "user_id")
    validate_type(message, str, "message")

    # Validate content
    if not is_valid_string(message, min_length=1, max_length=1000):
        raise ValidationError(
            "Invalid message",
            error_code="INVALID_MESSAGE",
            context={"length": len(message)}
        )

    # Process...
```

## See Also

- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Developer Guide](DEVELOPER_GUIDE.md) - Development guide
- [Examples](../../examples/error_handling.py) - Error handling examples
