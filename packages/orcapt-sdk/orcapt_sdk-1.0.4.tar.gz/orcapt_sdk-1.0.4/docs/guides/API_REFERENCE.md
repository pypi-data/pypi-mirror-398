# API Reference

Complete API reference for Orca SDK domain models and interfaces.

## Table of Contents

- [Domain Models](#domain-models)
- [Core Classes](#core-classes)
- [Factories](#factories)
- [Interfaces](#interfaces)
- [Configuration](#configuration)

## Domain Models

### ChatMessage

Primary data model for chat interactions.

```python
from orca import ChatMessage

message = ChatMessage(
    message="Hello, world!",
    response_uuid="uuid-123",
    thread_id="thread-456",
    model="gpt-4",
    conversation_id=789,
    message_uuid="msg-uuid",
    channel="general",
    variables=[],
    stream_url="https://stream.example.com",
    stream_token="token-xyz",
    url="https://api.example.com"
)
```

**Fields:**

| Field             | Type             | Required | Description                |
| ----------------- | ---------------- | -------- | -------------------------- |
| `message`         | `str`            | Yes      | User message content       |
| `response_uuid`   | `str`            | Yes      | Unique response identifier |
| `thread_id`       | `str`            | Yes      | Thread identifier          |
| `model`           | `str`            | Yes      | AI model identifier        |
| `conversation_id` | `int`            | Yes      | Conversation ID            |
| `message_uuid`    | `str`            | Yes      | Message unique ID          |
| `channel`         | `str`            | Yes      | Communication channel      |
| `variables`       | `List[Variable]` | Yes      | Context variables          |
| `stream_url`      | `str`            | Yes      | Streaming endpoint URL     |
| `stream_token`    | `str`            | Yes      | Streaming auth token       |
| `url`             | `str`            | Yes      | Backend API URL            |
| `headers`         | `Dict`           | No       | Optional HTTP headers      |

### Variable

Context variable for agent execution.

```python
from orca import Variable

var = Variable(
    key="user_name",
    value="John Doe",
    type="string"
)
```

**Fields:**

| Field   | Type  | Required | Description        |
| ------- | ----- | -------- | ------------------ |
| `key`   | `str` | Yes      | Variable name/key  |
| `value` | `Any` | Yes      | Variable value     |
| `type`  | `str` | No       | Variable type hint |

### Memory

Long-term memory storage for agents.

```python
from orca import Memory

memory = Memory(
    key="user_preference",
    value={"theme": "dark", "language": "en"},
    timestamp=1234567890,
    metadata={"source": "settings"}
)
```

**Fields:**

| Field       | Type   | Required | Description           |
| ----------- | ------ | -------- | --------------------- |
| `key`       | `str`  | Yes      | Memory key/identifier |
| `value`     | `Any`  | Yes      | Stored value          |
| `timestamp` | `int`  | No       | Creation timestamp    |
| `metadata`  | `Dict` | No       | Additional metadata   |

## Core Classes

### OrcaHandler

Main handler for Orca communication.

```python
from orca import OrcaHandler

handler = OrcaHandler(
    dev_mode=False,
    stream_client=None,
    api_client=None,
    buffer_manager=None,
    button_renderer=None,
    loading_marker_provider=None,
    usage_tracker=None,
    tracing_service=None,
    error_handler=None,
    response_builder=None
)
```

**Parameters:**

| Parameter                 | Type                     | Default | Description             |
| ------------------------- | ------------------------ | ------- | ----------------------- |
| `dev_mode`                | `bool`                   | `None`  | Development mode flag   |
| `stream_client`           | `IStreamClient`          | `None`  | Custom stream client    |
| `api_client`              | `IAPIClient`             | `None`  | Custom API client       |
| `buffer_manager`          | `IBufferManager`         | `None`  | Custom buffer manager   |
| `button_renderer`         | `IButtonRenderer`        | `None`  | Custom button renderer  |
| `loading_marker_provider` | `ILoadingMarkerProvider` | `None`  | Custom loading provider |
| `usage_tracker`           | `IUsageTracker`          | `None`  | Custom usage tracker    |
| `tracing_service`         | `ITracingService`        | `None`  | Custom tracing service  |
| `error_handler`           | `IErrorHandler`          | `None`  | Custom error handler    |
| `response_builder`        | `IResponseBuilder`       | `None`  | Custom response builder |

**Methods:**

#### `begin(data: Any) -> Session`

Start a streaming session.

```python
session = handler.begin(data)
```

#### `stream(data: Any, content: str) -> None`

Stream content to client.

```python
handler.stream(data, "Hello!")
```

#### `close(data: Any, usage_info=None, file_url=None) -> str`

Close session and finalize response.

```python
full_response = handler.close(data, usage_info=usage_info)
```

#### `send_error(data: Any, error_message: str, trace=None, exception=None) -> None`

Send error to client.

```python
handler.send_error(data, "An error occurred", exception=e)
```

### Session

Session interface for agent interactions.

```python
# Get session from handler
session = handler.begin(data)
```

**Properties:**

| Property   | Type                 | Description                  |
| ---------- | -------------------- | ---------------------------- |
| `loading`  | `LoadingOperations`  | Loading indicator operations |
| `image`    | `ImageOperations`    | Image passing operations     |
| `video`    | `VideoOperations`    | Video operations             |
| `location` | `LocationOperations` | Location operations          |
| `card`     | `CardListOperations` | Card list operations         |
| `audio`    | `AudioOperations`    | Audio operations             |
| `tracing`  | `TracingOperations`  | Tracing operations           |
| `usage`    | `UsageOperations`    | Usage tracking operations    |
| `button`   | `ButtonHelper`       | Button management            |

**Methods:**

#### `stream(content: str) -> None`

Stream content to user.

```python
session.stream("Hello, world!")
```

#### `close(usage_info=None, file_url=None) -> str`

Close session.

```python
session.close()
```

#### `error(error_message: str, exception=None, trace=None) -> None`

Send error message.

```python
session.error("An error occurred", exception=e)
```

### LoadingOperations

Loading indicator management.

```python
# Access via session
session.loading.start("thinking")
session.loading.end("thinking")
```

**Methods:**

#### `start(kind: str = "thinking") -> None`

Start loading indicator.

```python
session.loading.start("thinking")
session.loading.start("searching")
session.loading.start("coding")
```

#### `end(kind: str = "thinking") -> None`

Stop loading indicator.

```python
session.loading.end("thinking")
```

### ImageOperations

Image passing to frontend.

```python
session.image.send("https://example.com/image.jpg")
```

**Methods:**

#### `send(url: str) -> None`

Pass image URL to frontend.

```python
session.image.send("https://cdn.example.com/result.png")
```

#### `pass_image(url: str) -> None`

Alias for `send()`.

```python
session.image.pass_image("https://cdn.example.com/result.png")
```

### VideoOperations

Video playback operations.

```python
session.video.send("https://example.com/video.mp4")
session.video.youtube("https://www.youtube.com/watch?v=...")
```

**Methods:**

#### `send(url: str) -> None`

Send video URL for playback.

```python
session.video.send("https://example.com/video.mp4")
```

#### `youtube(url: str) -> None`

Send YouTube video URL for embedded playback.

```python
session.video.youtube("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
```

### LocationOperations

Location and map operations.

```python
session.location.send("35.6892, 51.3890")
session.location.send_coordinates(35.6892, 51.3890)
```

**Methods:**

#### `send(coordinates: str) -> None`

Send location coordinates as string.

```python
session.location.send("35.6892, 51.3890")
```

#### `send_coordinates(lat: float, lng: float) -> None`

Send location using latitude and longitude.

```python
session.location.send_coordinates(35.6892, 51.3890)
```

### CardListOperations

Card list display operations.

```python
cards = [
    {"photo": "https://example.com/img.jpg", "header": "Title", "text": "Content"}
]
session.card.send(cards)
```

**Methods:**

#### `send(cards: List[Dict[str, Any]]) -> None`

Send card list for display.

```python
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

### AudioOperations

Audio playback operations.

```python
tracks = [{"url": "https://example.com/audio.mp3", "label": "Track 1"}]
session.audio.send(tracks)
session.audio.send_single("https://example.com/audio.mp3", label="Track")
```

**Methods:**

#### `send(tracks: List[Dict[str, str]]) -> None`

Send audio tracks for playback.

```python
tracks = [
    {"url": "https://example.com/audio1.mp3", "label": "Track 1", "type": "audio/mpeg"},
    {"url": "https://example.com/audio2.mp3", "label": "Track 2"}
]
session.audio.send(tracks)
```

#### `send_single(url: str, label: str = None, mime_type: str = None) -> None`

Send single audio track.

```python
session.audio.send_single(
    "https://example.com/audio.mp3",
    label="My Track",
    mime_type="audio/mpeg"
)
```

### TracingOperations

Progressive tracing for transparency.

```python
session.tracing.begin("Processing", visibility="all")
session.tracing.append("Step 1...")
session.tracing.end("Complete")
```

**Methods:**

#### `begin(message: str, visibility: str = "all") -> None`

Start tracing block.

```python
session.tracing.begin("Analyzing input", visibility="all")
```

#### `append(message: str) -> None`

Append to tracing.

```python
session.tracing.append("Step 1: Parsing data")
```

#### `end(message: str = None) -> None`

End tracing block.

```python
session.tracing.end("Analysis complete")
```

### UsageOperations

Track token usage and costs.

```python
session.usage.track(
    tokens=1500,
    token_type="gpt4",
    cost="0.03",
    label="OpenAI GPT-4"
)
```

**Methods:**

#### `track(tokens: int, token_type: str, cost: str = None, label: str = None) -> None`

Track usage.

```python
session.usage.track(
    tokens=1500,
    token_type="gpt4",
    cost="0.03",
    label="OpenAI GPT-4"
)
```

### ButtonHelper

Button management for interactive UI.

```python
# Link button
session.button.link("Visit", "https://example.com")

# Action button
session.button.action("Regenerate", "regenerate")
```

**Methods:**

#### `link(label: str, url: str, row: int = 1, color: str = None) -> None`

Add link button.

```python
session.button.link("Learn More", "https://docs.example.com")
session.button.link("GitHub", "https://github.com/repo", color="primary")
```

#### `action(label: str, action_id: str, row: int = 1, color: str = None) -> None`

Add action button.

```python
session.button.action("Regenerate", "regenerate")
session.button.action("Delete", "delete", color="danger")
```

## Factories

Higher-level functions to quickly bootstrap AI agents.

### create_agent_app

Creates a standard FastAPI application with Orca endpoints.

```python
from orca import create_agent_app

app = create_agent_app(
    process_message_func=my_logic,
    app_title="My Agent API",
    app_version="1.0.0",
    dev_mode=False
)
```

**Parameters:**

| Parameter              | Type       | Default      | Description                     |
| ---------------------- | ---------- | ------------ | ------------------------------- |
| `process_message_func` | `Callable` | **Required** | Async function to handle msg    |
| `app_title`            | `str`      | `Orca Agent` | FastAPI app title               |
| `app_version`          | `str`      | `1.0.0`      | FastAPI app version             |
| `dev_mode`             | `bool`     | `False`      | Development mode flag           |

---

### create_hybrid_handler

Creates a unified handler for AWS Lambda environment.

```python
from orca import create_hybrid_handler

handler = create_hybrid_handler(
    process_message_func=my_logic,
    app_title="My Lambda Agent",
    dev_mode=False
)
```

**Parameters:**

| Parameter              | Type       | Default | Description                  |
| ---------------------- | ---------- | ------- | ---------------------------- |
| `process_message_func` | `Callable` | **Required** | Async function to handle msg |
| `app_title`            | `str`      | `Orca Hybrid Agent` | App title (for HTTP mode) |
| `dev_mode`             | `bool`     | `False` | Development mode flag        |

---

## Interfaces

### IStreamClient

Stream client interface.

```python
from orca.domain.interfaces import IStreamClient

class CustomStreamClient(IStreamClient):
    def update_config(self, stream_url: str, stream_token: str):
        pass

    def send_delta(self, channel: str, uuid: str, thread_id: str, delta: str):
        pass

    def send_completion(self, channel: str, uuid: str, thread_id: str, full_response: str):
        pass

    def send_error(self, channel: str, uuid: str, thread_id: str, error_message: str):
        pass
```

### IAPIClient

API client interface.

```python
from orca.domain.interfaces import IAPIClient

class CustomAPIClient(IAPIClient):
    def get(self, url: str, params=None, headers=None):
        pass

    def post(self, url: str, data=None, headers=None):
        pass
```

## Configuration

### LoadingKind

Loading indicator types.

```python
from orca.config import LoadingKind

LoadingKind.THINKING      # "thinking"
LoadingKind.SEARCHING     # "searching"
LoadingKind.CODING        # "coding"
LoadingKind.ANALYZING     # "analyzing"
LoadingKind.GENERATING    # "generating"
LoadingKind.CUSTOM        # "custom"
```

### ButtonColor

Button colors.

```python
from orca.config import ButtonColor

ButtonColor.PRIMARY       # "primary"
ButtonColor.SECONDARY     # "secondary"
ButtonColor.SUCCESS       # "success"
ButtonColor.DANGER        # "danger"
ButtonColor.WARNING       # "warning"
ButtonColor.INFO          # "info"
ButtonColor.LIGHT         # "light"
ButtonColor.DARK          # "dark"
```

### TokenType

Token types for tracking.

```python
from orca.config import TokenType

TokenType.GPT4            # "gpt4"
TokenType.GPT35           # "gpt35"
TokenType.CLAUDE          # "claude"
TokenType.CUSTOM          # "custom"
```

## See Also

- [Quick Reference](QUICK_REFERENCE.md) - Quick examples
- [Developer Guide](DEVELOPER_GUIDE.md) - Complete guide
- [Patterns Guide](PATTERNS_GUIDE.md) - Design patterns
