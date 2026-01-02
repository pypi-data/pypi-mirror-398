# Quick Reference

Fast API reference for Orca SDK with common usage patterns.

## 📦 Installation

```bash
pip install orcapt-sdk
```

## 🚀 Quick Start

```python
from orca import OrcaHandler

# Development mode (in-memory streaming)
handler = OrcaHandler(dev_mode=True)

# Production mode (Centrifugo streaming)
handler = OrcaHandler(dev_mode=False)
```

## 💬 Basic Usage

### Simplified Agent (Recommended)

The easiest way to build a production-ready agent API:

```python
from orca import create_agent_app, ChatMessage, OrcaHandler

async def process_msg(data: ChatMessage):
    handler = OrcaHandler()
    session = handler.begin(data)
    session.stream(f"Echo: {data.message}")
    session.close()

app = create_agent_app(process_msg)
# Run with: uvicorn main:app
```

### Manual Message Flow

### With Loading Indicators

```python
session = handler.begin(data)

# Start loading
session.loading.start("thinking")

# Process...
response = process_with_ai(data.message)

# Stop loading
session.loading.end("thinking")

# Stream result
session.stream(response)
session.close()
```

### With Buttons

```python
session = handler.begin(data)
session.stream("Here are your options:")

# Link button
session.button.link("Documentation", "https://docs.example.com")

# Action button
session.button.action("Regenerate", "regenerate")

session.close()
```

### With Error Handling

```python
session = handler.begin(data)

try:
    session.loading.start("thinking")
    result = risky_operation()
    session.loading.end("thinking")
    session.stream(result)
    session.close()
except Exception as e:
    session.error("An error occurred", exception=e)
```

## 📚 Core Classes

### OrcaHandler

Main handler for all Orca operations.

```python
handler = OrcaHandler(
    dev_mode=True,           # Enable dev mode
    stream_client=None,      # Custom stream client
    api_client=None,         # Custom API client
    buffer_manager=None,     # Custom buffer
    button_renderer=None,    # Custom button renderer
)
```

**Methods:**

- `begin(data)` - Start a new session
- `stream(data, content)` - Stream content directly
- `close(data, usage_info, file_url)` - Close session
- `send_error(data, error_message, trace, exception)` - Send error

### Session

User session interface returned by `handler.begin(data)`.

**Properties:**

- `loading` - Loading indicator operations
- `image` - Image passing operations
- `video` - Video operations
- `location` - Location operations
- `card` - Card list operations
- `audio` - Audio operations
- `tracing` - Tracing operations
- `usage` - Usage tracking operations
- `button` - Button management

**Methods:**

- `stream(content)` - Stream content
- `close(usage_info, file_url)` - Close session
- `error(error_message, exception, trace)` - Send error

## 🎨 Advanced Features

### Loading Indicators

```python
# Built-in types
session.loading.start("thinking")   # 🤔 Thinking
session.loading.start("searching")  # 🔍 Searching
session.loading.start("coding")     # 💻 Coding
session.loading.start("analyzing")  # 📊 Analyzing

# Stop loading
session.loading.end("thinking")
```

### Image Passing

```python
# Pass image URL to frontend
session.image.image("https://example.com/image.jpg")
```

### Video Operations

```python
# Send video URL
session.video.send("https://example.com/video.mp4")

# Send YouTube video
session.video.youtube("https://www.youtube.com/watch?v=...")
```

### Location Operations

```python
# Send location as string
session.location.send("35.6892, 51.3890")

# Send location with coordinates
session.location.send_coordinates(35.6892, 51.3890)
```

### Card List Operations

```python
# Send card list
cards = [
    {
        "photo": "https://example.com/card1.jpg",
        "header": "Card Title",
        "subheader": "Subtitle",
        "text": "Description"
    }
]
session.card.send(cards)
```

### Audio Operations

```python
# Send multiple audio tracks
tracks = [
    {"url": "https://example.com/audio1.mp3", "label": "Track 1"},
    {"url": "https://example.com/audio2.mp3", "label": "Track 2"}
]
session.audio.send(tracks)

# Send single audio track
session.audio.send_single("https://example.com/audio.mp3", label="My Track")
```

### Tracing

```python
# Start tracing block
session.tracing.begin("Processing input", visibility="all")

# Add trace messages
session.tracing.append("Step 1: Parsing data")
session.tracing.append("Step 2: Validating")

# End tracing
session.tracing.end("Processing complete")
```

### Usage Tracking

```python
# Track token usage
session.usage.track(
    tokens=1500,
    token_type="gpt4",
    cost="0.03",
    label="OpenAI GPT-4"
)
```

### Button Management

```python
# Link button (opens URL)
session.button.link(
    label="Visit Website",
    url="https://example.com",
    row=1,
    color="primary"
)

# Action button (triggers action)
session.button.action(
    label="Regenerate",
    action_id="regenerate",
    row=1,
    color="secondary"
)
```

## 🛠️ Utilities

### Variables

```python
from orca import get_variable_value, Variables

# Get single variable
api_key = get_variable_value(data.variables, "api_key")

# Use helper class
vars = Variables(data.variables)
api_key = vars.get("api_key")
db_url = vars.get("db_url", default="localhost")
```

### Memory Helper

```python
from orca import MemoryHelper

memory = MemoryHelper()

# Store data
memory.set("user_preference", {"theme": "dark"})

# Retrieve data
pref = memory.get("user_preference")

# Check existence
if memory.has("user_preference"):
    print("Found!")
```

### Environment

```python
from orca import get_openai_api_key

# Get OpenAI API key from variables or env
api_key = get_openai_api_key(data.variables)
```

### Response Builder

```python
from orca import create_success_response

# Create success response
response = create_success_response(
    data={"result": "success"},
    message="Operation completed"
)
```

## 🔧 Advanced Patterns

### Builder Pattern

```python
from orca.patterns import OrcaBuilder, SessionBuilder

# Build handler with fluent interface
handler = (OrcaBuilder()
    .with_dev_mode(True)
    .with_buffer_manager(custom_buffer)
    .build())

# Build session workflow (all operations are queued)
builder = SessionBuilder(handler).start_session(data)
builder.add_stream("Hello")
builder.add_image("https://example.com/image.jpg")
builder.add_button("Click", "https://example.com")
builder.execute()  # Execute all queued operations
result = builder.complete()  # Execute remaining + close session
```

### Context Manager

```python
from orca.patterns import SessionContext

# Automatic session management
with SessionContext(handler, data) as session:
    session.stream("Processing...")
    # Session automatically closes on exit
```

### Middleware

```python
from orca.patterns import MiddlewareChain, LoggingMiddleware

# Create middleware chain
chain = MiddlewareChain()
from orca.patterns import MiddlewareManager

manager = MiddlewareManager()
manager.use(LoggingMiddleware())

# Execute with middleware
def process(data):
    session = handler.begin(data)
    session.stream("Hello")
    session.close()

manager.execute(process, data)
```

## 🚀 Lambda Deployment

### Unified Lambda (Recommended)

```python
from orca import create_hybrid_handler, ChatMessage, OrcaHandler

async def process_message(data: ChatMessage):
    handler = OrcaHandler()
    session = handler.begin(data)
    session.stream("Response from Lambda!")
    session.close()

# Handles HTTP, SQS, and Cron automatically
handler = create_hybrid_handler(process_message)
```

### Manual Lambda Adapter

## 📦 Storage SDK

### Basic Storage Operations

```python
from orca import OrcaStorage

storage = OrcaStorage(
    workspace="my-workspace",
    token="api-token",
    base_url="https://api.example.com/storage"
)

# Create bucket
storage.create_bucket("my-bucket", visibility="private")

# Upload file
file = storage.upload_file("my-bucket", "local/file.jpg")

# Download
storage.download_file("my-bucket", "file.jpg", "dest/file.jpg")

# List files
files = storage.list_files("my-bucket")
```

## 🔗 Common Patterns

### Complete Agent Flow

```python
from orca import OrcaHandler, get_openai_api_key
from openai import OpenAI

handler = OrcaHandler(dev_mode=True)

def process_message(data):
    session = handler.begin(data)

    try:
        # Start loading
        session.loading.start("thinking")

        # Get API key
        api_key = get_openai_api_key(data.variables)

        # Call OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": data.message}]
        )

        # Track usage
        usage = response.usage
        session.usage.track(
            tokens=usage.total_tokens,
            token_type="gpt4",
            cost="0.03"
        )

        # Stop loading
        session.loading.end("thinking")

        # Stream response
        result = response.choices[0].message.content
        session.stream(result)

        # Add actions
        session.button.action("Regenerate", "regenerate")

        # Close
        return session.close()

    except Exception as e:
        session.error("Failed to process", exception=e)
        return None
```

### With Tracing

```python
def process_with_tracing(data):
    session = handler.begin(data)

    try:
        # Trace: Analysis
        session.tracing.begin("Analyzing input", visibility="all")
        analysis = analyze(data.message)
        session.tracing.append(f"Found {len(analysis)} entities")
        session.tracing.end()

        # Trace: Processing
        session.tracing.begin("Processing", visibility="all")
        session.loading.start("thinking")
        result = process(analysis)
        session.loading.end("thinking")
        session.tracing.end("Complete")

        # Stream result
        session.stream(result)
        session.close()

    except Exception as e:
        session.error("Error", exception=e)
```

## 🔍 Debugging

### Enable Debug Logging

```python
from orca.common import setup_logging, enable_debug_logging
import logging

# Setup logging
setup_logging(level=logging.DEBUG, log_file="app.log")

# Or enable debug mode
enable_debug_logging()
```

### Development Mode

```python
# Dev mode uses in-memory streaming (no Centrifugo needed)
handler = OrcaHandler(dev_mode=True)

# Test your agent locally
session = handler.begin(test_data)
session.stream("Testing...")
response = session.close()
print(f"Full response: {response}")
```

## 📋 Cheat Sheet

| Task               | Code                                                          |
| ------------------ | ------------------------------------------------------------- |
| Initialize handler | `handler = OrcaHandler(dev_mode=True)`                        |
| Start session      | `session = handler.begin(data)`                               |
| Stream text        | `session.stream("Hello")`                                     |
| Close session      | `session.close()`                                             |
| Send error         | `session.error("Error", exception=e)`                         |
| Start loading      | `session.loading.start("thinking")`                           |
| Stop loading       | `session.loading.end("thinking")`                             |
| Add button         | `session.button.link("Click", "url")`                         |
| Track usage        | `session.usage.track(tokens=100, token_type="gpt4")`          |
| Pass image         | `session.image.image("https://example.com/img.jpg")`          |
| Send video         | `session.video.send("https://example.com/video.mp4")`         |
| Send YouTube       | `session.video.youtube("https://youtube.com/watch?v=...")`    |
| Send location      | `session.location.send("35.6892, 51.3890")`                   |
| Send cards         | `session.card.send([{"header": "Title", "text": "Content"}])` |
| Send audio         | `session.audio.send([{"url": "...", "label": "Track"}])`      |
| Trace              | `session.tracing.begin("Step", visibility="all")`             |

## 🔗 See Also

- [Developer Guide](DEVELOPER_GUIDE.md) - Complete development guide
- [API Reference](API_REFERENCE.md) - Detailed API documentation
- [Lambda Deploy Guide](LAMBDA_DEPLOY_GUIDE.md) - AWS Lambda deployment
- [Patterns Guide](PATTERNS_GUIDE.md) - Design patterns
- [Examples](../../examples/) - Working code examples

---

**Pro Tip:** Start with `basic_usage.py` example and gradually add features as needed!
