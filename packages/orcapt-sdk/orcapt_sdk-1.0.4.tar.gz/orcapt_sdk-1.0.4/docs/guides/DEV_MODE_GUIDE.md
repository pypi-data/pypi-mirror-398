# Orca Dev Mode Guide

## Overview

Orca now supports **Dev Mode** for local development without requiring Centrifugo. This makes it easier to develop and test AI agents locally.

**🎯 KEY POINT**: Your application code (OpenAI calls, streaming logic) **stays exactly the same** in both dev and production modes. Just change one flag!

## What is Dev Mode?

In production, Orca uses **Centrifugo** for real-time WebSocket streaming to the frontend. In dev mode, Orca uses:
- **In-memory storage** for streaming data
- **SSE (Server-Sent Events)** for real-time updates
- **Simple HTTP polling** as an alternative
- **Console output** for immediate visibility

## How to Enable Dev Mode

### Option 1: Direct Parameter (Recommended)

```python
from orca import OrcaHandler

# Enable dev mode
orca = OrcaHandler(dev_mode=True)
```

### Option 2: Environment Variable

```bash
export ORCA_DEV_MODE=true
python main.py
```

```python
from orca import OrcaHandler

# Will automatically detect ORCA_DEV_MODE env var
orca = OrcaHandler()
```

### Option 3: Command Line Argument

```python
import sys
import os

# Check for --dev flag
dev_mode = '--dev' in sys.argv

# Set environment variable
if dev_mode:
    os.environ['ORCA_DEV_MODE'] = 'true'

from orca import OrcaHandler

orca = OrcaHandler()
```

Then run:
```bash
python main.py --dev
```

## How It Works

### Production Mode (Centrifugo)
```
AI Agent (Background Task) → Centrifugo Server → WebSocket → Frontend
```

### Dev Mode (SSE)
```
AI Agent (Background Thread) → DevStreamClient (Async Queue) → SSE → Frontend
                  ↓
            Console Output
```

**Key Technical Details:**
- **Dev Mode**: Your `process_message()` runs in a background thread (not asyncio task) to avoid blocking the event loop, allowing SSE to flush chunks immediately
- **Production**: Runs as async background task with Centrifugo handling delivery
- **Your code**: Identical in both modes - just call `orca.stream_chunk(data, content)` and the package handles the rest!

## Available Endpoints in Dev Mode

### 1. SSE Stream Endpoint
```
GET /api/v1/stream/{channel}
```

**Frontend Usage (JavaScript):**
```javascript
const eventSource = new EventSource('http://localhost:5001/api/v1/stream/your-channel-id');

eventSource.addEventListener('message', (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.event) {
        case 'connected':
            console.log('Connected to stream');
            break;
        case 'delta':
            console.log('Chunk:', data.content);
            break;
        case 'complete':
            console.log('Complete response:', data.content);
            eventSource.close();
            break;
        case 'error':
            console.error('Error:', data.content);
            eventSource.close();
            break;
    }
});
```

### 2. Polling Endpoint (Alternative)
```
GET /api/v1/poll/{channel}
```

**Frontend Usage (JavaScript):**
```javascript
async function pollStream(channel) {
    const response = await fetch(`http://localhost:5001/api/v1/poll/${channel}`);
    const data = await response.json();
    
    console.log('Current state:', data);
    // data.full_response - complete response so far
    // data.finished - whether streaming is complete
    // data.chunks_count - number of chunks received
    
    if (!data.finished) {
        setTimeout(() => pollStream(channel), 100); // Poll every 100ms
    }
}
```

## Example: Complete AI Agent

The simplest way to build and test your agent locally is using the `create_agent_app` factory combined with `dev_mode=True`.

```python
#!/usr/bin/env python3
import sys
from openai import OpenAI
from orca import create_agent_app, ChatMessage, OrcaHandler

# 1. Initialize Orca handler in dev mode
# (Or set ORCA_DEV_MODE=true in your environment)
orca = OrcaHandler(dev_mode=True)

# 2. Define your agent processing logic
async def process_message(data: ChatMessage):
    """Identical code for dev and prod!"""
    session = orca.begin(data)
    
    try:
        session.loading.start("thinking")
        
        # Example: Simple response
        session.stream(f"Dev Mode active! You said: {data.message}")
        
        session.loading.end("thinking")
        session.close()
        
    except Exception as e:
        session.error("Error", exception=e)

# 3. Create the FastAPI app
app = create_agent_app(
    process_message_func=process_message,
    app_title="Dev Agent"
)

if __name__ == "__main__":
    import uvicorn
    # In dev mode, orca-sdk provides /api/v1/stream/{channel} automatically
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Run it:**
```bash
python main.py --dev   # Dev mode (SSE)
python main.py --prod  # Production (Centrifugo)
```

**Your OpenAI code is IDENTICAL in both modes!** The orca package handles all the differences internally.

## Benefits of Dev Mode

1. ✅ **No Centrifugo Required** - Run without external dependencies
2. ✅ **Console Output** - See streaming in real-time in terminal
3. ✅ **Easy Testing** - Test streaming locally without infrastructure
4. ✅ **Same API** - Code works in both dev and production mode
5. ✅ **Simple Frontend** - Use SSE or polling instead of WebSockets
6. ✅ **No Code Changes** - Your OpenAI/AI code stays identical; only change the mode flag

## Technical Implementation

### How Dev Mode Avoids Event Loop Blocking

In dev mode, orca runs your `process_message()` in a **background thread** (not an async task):

```python
# Inside orca-pip when dev_mode=True:
bg_thread = threading.Thread(target=run_process_message, daemon=True)
bg_thread.start()

# This allows your sync OpenAI code (for chunk in stream:) to work
# without blocking the FastAPI event loop!
```

Meanwhile, the HTTP response uses an **async queue** to receive chunks:
```python
# SSE generator waits on queue:
async for event_type, content in queue:
    yield f"data: {content}\n\n"
```

**Result**: Real-time streaming works with regular sync OpenAI code!

## Console Output in Dev Mode

When dev mode is active, you'll see:
```
🔧 OrcaHandler initialized in DEV MODE (no Centrifugo)
📝 Dev stream delta added to channel-123: 15 chars
✅ Dev stream completed for channel-123
```

And the actual AI response will be printed in real-time to console.

## Production vs Dev Mode Comparison

| Feature | Production | Dev Mode |
|---------|-----------|----------|
| Streaming Protocol | Centrifugo WebSocket | SSE / Polling |
| Real-time Updates | ✅ Very Fast | ✅ Fast (100ms) |
| Console Output | ❌ No | ✅ Yes |
| External Dependencies | Centrifugo Server | None |
| Setup Complexity | Medium | Low |
| Best For | Production deployment | Local development |

## Switching Between Modes

Your code works identically in both modes:

```python
# This code works in BOTH dev and production mode
orca.stream_chunk(data, content)
orca.complete_response(data, full_response)
orca.send_error(data, error_message)
```

The only difference is initialization:
```python
# Production
orca = OrcaHandler(dev_mode=False)  # or OrcaHandler()

# Development
orca = OrcaHandler(dev_mode=True)
```

## Troubleshooting

### Issue: Streaming not working in frontend

**Solution:** Make sure your frontend is connecting to the SSE endpoint:
```javascript
const eventSource = new EventSource(`http://localhost:5001/api/v1/stream/${channelId}`);
```

### Issue: CORS errors

**Solution:** Add CORS middleware to your FastAPI app:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Not seeing console output

**Solution:** Make sure dev mode is actually enabled:
```python
print(f"Dev mode: {orca.dev_mode}")  # Should print: Dev mode: True
```

## Next Steps

1. Enable dev mode in your agent
2. Test locally without Centrifugo
3. Update frontend to use SSE endpoint
4. When ready for production, simply change `dev_mode=False`

That's it! Dev mode makes local development a breeze. 🚀

