# Orca Agent Lambda Shipping Guide

This document is written for external agent developers who have:

- The **`orca` PyPI package** (`pip install orca`)
- Access to the hosted **`orca-cli`** and platform APIs
- Their agent code (using `OrcaHandler`)

Nothing in this guide depends on any internal repositories or starter kits. Follow the steps below to deploy your agent to AWS Lambda with Function URL + SQS trigger.

---

## 1. Prerequisites

| Tool / Access                              | Why it’s needed                               |
| ------------------------------------------ | --------------------------------------------- |
| Docker 24+ with BuildKit enabled           | Build the Lambda container image              |
| AWS account + IAM user/role                | Push to ECR and create Lambda/SQS resources   |
| AWS CLI v2 (`aws --version`)               | Login to ECR, test SQS, inspect Lambda        |
| `orca-cli ≥ 1.12.0`                       | Runs `orca ship` which talks to platform API |
| `orca` PyPI package (`pip install orca`) | Provides `ChatMessage`, `OrcaHandler`, etc.  |
| `jq` (optional)                            | Formatting JSON for curl/SQS tests            |
| Text editor + git                          | Modify starter kit and track your changes     |

> **AWS Permissions:** The IAM principal used by `orca ship` must have `ecr:*`, `lambda:*`, `sqs:*`, `iam:PassRole`, and CloudWatch Logs access. Your platform admin can scope this via IAM policies.

---

## 2. Project Structure

Your project needs these files for Lambda deployment:

```
my-agent/
├── lambda_handler.py       # Main entry point (see §3)
├── requirements-lambda.txt # Dependencies
├── Dockerfile.lambda       # Container definition
└── .env.lambda            # Environment variables (never commit!)
```

That's it! No starter kit or complex structure needed.

---

## 3. Create Lambda Handler

Create `lambda_handler.py` in your project root. Using `LambdaAdapter` from the orca SDK makes this incredibly simple:

```python
from orca import OrcaHandler, LambdaAdapter, ChatMessage

# Initialize handler
handler = OrcaHandler(dev_mode=False)

# Initialize adapter (automatically handles HTTP, SQS, and cron events!)
adapter = LambdaAdapter()


@adapter.message_handler
async def process_message(data: ChatMessage):
    """
    Your agent logic - exactly the same as local development!
    """
    session = handler.begin(data)

    try:
        session.loading.start("thinking")

        # Your agent logic here (OpenAI, LangChain, custom tools, etc.)
        response = await your_agent_logic(data.message)

        session.loading.end("thinking")
        session.stream(response)
        session.close()

    except Exception as e:
        session.error("An error occurred", exception=e)


@adapter.cron_handler
async def scheduled_task(event):
    """
    Optional: scheduled maintenance tasks
    """
    print("[CRON] Running scheduled task...")
    # Your scheduled logic here


# Lambda entry point
def handler(event, context):
    """
    That's it! LambdaAdapter handles everything:
    - HTTP requests (Function URL)
    - SQS events (async processing)
    - EventBridge (cron jobs)
    - Event loop management
    - Automatic queuing if SQS_QUEUE_URL exists
    """
    return adapter.handle(event, context)
```

**What LambdaAdapter does for you:**

✅ **Automatic event detection** - HTTP, SQS, or cron  
✅ **SQS queuing** - If `SQS_QUEUE_URL` exists, HTTP requests are queued automatically  
✅ **Direct processing** - If no queue, processes immediately  
✅ **Event loop management** - Fixes Python 3.11+ asyncio issues  
✅ **Error handling** - Proper logging and error responses

**No need to:**

- ❌ Write SQS parsing logic
- ❌ Handle HTTP request/response manually
- ❌ Manage event loops
- ❌ Write separate handlers for different event sources

---

## 4. Create Dockerfile

Save as `Dockerfile.lambda` at the project root:

```dockerfile
FROM public.ecr.aws/lambda/python:3.11

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements-lambda.txt .
RUN pip install --no-cache-dir -r requirements-lambda.txt

COPY lambda_handler.py .
COPY . .
# This copies all your agent code and assets

CMD ["lambda_handler.handler"]
```

**requirements-lambda.txt:**

```txt
# Core
orca>=2.0.0
boto3>=1.34.0

# Your providers
openai>=1.0.0
# anthropic>=0.7.0
# langchain>=0.1.0

# Optional: only if you need FastAPI endpoints
# fastapi>=0.104.0
# mangum>=0.17.0
```

Tips:

- Keep dependencies minimal for faster cold starts
- `LambdaAdapter` doesn't require FastAPI or Mangum (unless you need custom HTTP endpoints)
- If you need system deps (e.g., `psycopg[binary]`), add `RUN yum install -y postgresql15 && yum clean all`
- For extra assets (prompts, tools), add `COPY prompts ./prompts`

---

## 5. Build Docker Image

```bash
# Build locally
docker build -f Dockerfile.lambda -t my-agent:latest .
```

**Note:** You don't need to push to ECR manually! `orca ship` will handle the ECR push automatically.

---

## 6. Prepare Environment Variables

Create `.env.lambda` (never commit) with everything your agent needs:

```
OPENAI_API_KEY=sk-...
DB_URL=postgresql+psycopg://user:pass@host:5432/db
STREAM_URL=https://centrifugo.your-org.com
STREAM_TOKEN=ST_xxx
LOG_LEVEL=info
```

The Orca CLI will also inject:

- `SQS_QUEUE_URL` (auto-created per function)
- Any flags you pass via repeated `--env KEY=value`

---

## 7. Deploy with `orca ship`

```bash
# Login to orca-cli
orca login --api-url https://platform.orca.ai --token <personal-access-token>

# Deploy (orca-cli handles EVERYTHING!)
orca ship my-agent \
  --image my-agent:latest \
  --memory 2048 \
  --timeout 300 \
  --env-file ./.env.lambda
```

**What `orca ship` does automatically:**

1. ✅ **Pushes image to ECR** - No manual ECR login/push needed
2. ✅ **Creates/updates Lambda function** - Using your image
3. ✅ **Creates SQS queue** - Named `my-agent-queue`, URL set to `SQS_QUEUE_URL`
4. ✅ **Configures SQS trigger** - Lambda auto-invoked on messages
5. ✅ **Creates Function URL** - Public HTTPS endpoint (CORS enabled)
6. ✅ **Sets environment variables** - From `.env.lambda` + `--env` flags
7. ✅ **Configures IAM roles** - All necessary permissions

**Output:**

```
✅ Image pushed to ECR
✅ Lambda function: my-agent (created/updated)
✅ SQS queue: my-agent-queue
✅ Function URL: https://abc123.lambda-url.us-east-1.on.aws/
✅ Environment variables: 12 variables set

Deploy complete! 🚀
```

You can re-run `orca ship` any time to update code or environment variables.

---

## 8. Test Deployment

**Test HTTP invocation:**

```bash
curl -XPOST https://<function-url>/ \
  -H "content-type: application/json" \
  -d '{
    "message": "Hello from Lambda!",
    "response_uuid": "test-123",
    "stream_url": "https://centrifugo.your-org.com",
    "stream_token": "your-token"
  }'
```

**Expected response (if SQS queue exists):**

```json
{
  "status": "queued",
  "response_uuid": "test-123"
}
```

**Expected response (no SQS queue):**

```json
{
  "status": "ok",
  "response_uuid": "test-123"
}
```

**View logs:**

```bash
orca lambda logs my-agent --tail

# Or use AWS CLI
aws logs tail /aws/lambda/my-agent --follow
```

**Expected log output:**

```
==================================================
[LAMBDA] Event source: HTTP (Function URL/API Gateway)
==================================================
[HTTP] Processing request...
[HTTP] Queued successfully ✓

# Then when SQS processes:
==================================================
[LAMBDA] Event source: SQS
==================================================
[SQS] Processing 1 message(s)
[SQS] Processing message 1/1: test-123
[SQS] Message 1 completed ✓
```

---

## 9. Environment Variable Reference

| Variable                         | Required?    | Source                   | Purpose                        |
| -------------------------------- | ------------ | ------------------------ | ------------------------------ |
| `OPENAI_API_KEY` / provider keys | ✅           | `.env.lambda` or `--env` | Model access                   |
| `STREAM_URL`, `STREAM_TOKEN`     | ✅           | payload + fallback env   | Centrifugo/Websocket streaming |
| `DB_URL`, `REDIS_URL`, etc.      | ✅ (if used) | `.env.lambda`            | Backing services               |
| `SQS_QUEUE_URL`                  | Auto         | Set by platform          | Decides async vs direct mode   |
| `LOG_LEVEL`, feature flags       | Optional     | `.env.lambda`            | Tuning and debugging           |

The handler prints every key (value masked) on cold start so you can confirm they are present.

---

## 10. Troubleshooting

| Symptom                             | Root cause                                        | Fix                                                                                                |
| ----------------------------------- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `TLS handshake timeout` during push | Slow network / ECR region mismatch                | Re-run `orca ship` (retries enabled) or push from an EC2 builder in the same region               |
| `Runtime.ExitError` right away      | Wrong base image or missing handler               | Use `public.ecr.aws/lambda/python:3.11` and `CMD ["lambda_handler.handler"]`                       |
| Function URL returns 403            | Permission missing                                | Re-run `orca ship`; it re-applies `lambda:InvokeFunctionUrl` policy                               |
| Env vars missing                    | Incorrect `--env` syntax or missing `.env.lambda` | Use `KEY=value` pairs; CLI prints final map—double-check before confirming                         |
| Centrifugo points to internal URL   | `stream_url` in payload was `null`                | Ensure the invoking service sends `stream_url`/`stream_token`; fallback env can be set             |
| SQS never triggers                  | Event source mapping disabled                     | `orca ship` recreates it; or run `aws lambda list-event-source-mappings --function-name my-agent` |

Need more help? Collect the latest CloudWatch log stream and open a ticket with the Function name + timestamp.

---

## 11. Deployment Checklist

- [ ] `lambda_handler.py` created with `LambdaAdapter`
- [ ] `@adapter.message_handler` decorator wraps your agent logic
- [ ] `requirements-lambda.txt` includes `orca>=2.0.0` and your providers
- [ ] `Dockerfile.lambda` builds successfully locally
- [ ] `.env.lambda` created with all required variables (never commit!)
- [ ] Docker image built: `docker build -f Dockerfile.lambda -t my-agent:latest .`
- [ ] `orca ship my-agent --image my-agent:latest --env-file .env.lambda` executed
- [ ] Function URL received from `orca ship` output
- [ ] Test HTTP request works: `curl -XPOST <function-url> ...`
- [ ] Check logs: `orca lambda logs my-agent --tail`
- [ ] Verify SQS processing in logs: `[SQS] Processing ... Message completed ✓`

Once all boxes are checked, your agent is production-ready on AWS Lambda! 🚀

---

## 12. Complete Example

Here's a complete, production-ready `lambda_handler.py` using `LambdaAdapter`:

```python
"""
Lambda Handler - Production-Ready Example
==========================================

Simplest possible Lambda handler using OrcaAdapter.
Handles HTTP, SQS, and cron events automatically.
"""

from orca import OrcaHandler, LambdaAdapter, ChatMessage
import os

# Initialize Orca handler
handler = OrcaHandler(dev_mode=False)

# Initialize adapter (handles ALL event types!)
adapter = LambdaAdapter()


@adapter.message_handler
async def process_message(data: ChatMessage):
    """
    Your agent logic - same as local development!
    Replace this with your actual agent implementation.
    """
    session = handler.begin(data)

    try:
        session.loading.start("thinking")

        # ==========================================
        # YOUR AGENT LOGIC HERE
        # ==========================================

        # Example: Simple echo
        response = f"You said: {data.message}"

        # Example with OpenAI:
        # from openai import OpenAI
        # client = OpenAI()
        # response = client.chat.completions.create(
        #     model="gpt-4",
        #     messages=[{"role": "user", "content": data.message}]
        # )
        # response_text = response.choices[0].message.content

        session.loading.end("thinking")

        # Stream response
        session.stream(response)

        # Optional: Add buttons
        session.button.link("Learn More", "https://example.com")

        # Close session
        session.close()

    except Exception as e:
        # Automatic error handling and user notification
        session.error("An error occurred while processing your request", exception=e)
        raise


@adapter.cron_handler
async def scheduled_task(event):
    """
    Optional: Handle scheduled/cron events
    """
    print("[CRON] Running maintenance task...")

    # Example: Database cleanup, report generation, etc.
    # your_maintenance_logic()

    print("[CRON] Task completed!")


# Lambda entry point
def handler(event, context):
    """
    Main entry point - LambdaAdapter does ALL the work!

    Automatically handles:
    - HTTP requests (Function URL)
    - SQS events (async processing)
    - EventBridge (cron jobs)
    """
    return adapter.handle(event, context)


# Optional: Print configuration on cold start
print(f"[INIT] Lambda function ready!")
print(f"[INIT] SQS queue: {os.environ.get('SQS_QUEUE_URL', 'Not configured (direct mode)')}")
```

**That's it!** No need for:

- ❌ Manual SQS parsing
- ❌ Manual HTTP handling
- ❌ Separate handler files
- ❌ Event loop management
- ❌ FastAPI/Mangum (unless you need custom endpoints)

The `LambdaAdapter` handles everything automatically! 🚀

Happy shipping! 🚀
