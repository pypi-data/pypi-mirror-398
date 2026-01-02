# Orca SDK Examples

Comprehensive examples demonstrating all Orca SDK features.

## Quick Start Examples

### 1. `basic_usage.py` - Start Here! 🚀

Basic streaming and button usage. Perfect for beginners.

```bash
python examples/basic_usage.py
```

### 2. `advanced_usage.py` - Advanced Features

Decorators, logging, usage tracking, and more.

```bash
python examples/advanced_usage.py
```

### 3. `error_handling.py` - Error Handling

Comprehensive error handling patterns and best practices.

```bash
python examples/error_handling.py
```

## Deployment Examples

### 4. `lambda_deployment_simple.py` - Lambda Deployment ⚡

**Production-ready Lambda handler template.** Copy this as your `lambda_handler.py`!

Features:

- ✅ HTTP, SQS, and Cron event handling
- ✅ Automatic error handling
- ✅ Ready to customize with your agent logic
- ✅ Includes OpenAI examples (commented out)

Deploy:

```bash
# 1. Copy to your project
cp examples/lambda_deployment_simple.py lambda_handler.py

# 2. Customize your logic
# Edit lambda_handler.py

# 3. Build Docker image
docker build -f Dockerfile.lambda -t my-agent:latest .

# 4. Deploy with orca-cli
orca ship my-agent --image my-agent:latest --env-file .env
```

See `LAMBDA_DEPLOY_GUIDE.md` for complete deployment guide.

### 5. `lambda_usage_example.py` - Lambda Advanced Examples

Advanced Lambda examples with different patterns and use cases.

```bash
python examples/lambda_usage_example.py
```

## Feature Examples

### 7. `patterns_example.py` - Design Patterns 🏗️

Builder, Context Managers, and Middleware patterns.

```bash
python examples/patterns_example.py
```

### 8. `storage_example.py` - Storage SDK 📦

Orca Storage SDK for file management.

```bash
python examples/storage_example.py
```

## Template Files

### `Dockerfile.lambda` - Lambda Dockerfile Template

Sample Dockerfile for AWS Lambda deployment. Copy to your project root.

### `requirements-lambda.txt` - Lambda Requirements Template

Sample requirements file for Lambda. Keep dependencies minimal!

## Key Concepts

### Streaming

```python
session = handler.begin(data)
session.stream("Hello, world!")
```

### Loading Indicators

```python
from orca.config import LoadingKind
session.loading.start(LoadingKind.THINKING.value)
session.stream("Processing...")
session.loading.end(LoadingKind.THINKING.value)
```

### Buttons

```python
from orca.config import ButtonColor
session.button.link("Click", "https://example.com", color=ButtonColor.PRIMARY.value)
```

### Error Handling

```python
from orca.exceptions import OrcaException
try:
    # operations
except OrcaException as e:
    logger.error(f"Error: {e.to_dict()}")
```

### Decorators

```python
from orca.decorators import retry, log_execution

@retry(max_attempts=3)
@log_execution
def process_data():
    pass
```

### Logging

```python
from orca.logging_config import setup_logging
setup_logging(level=logging.DEBUG, log_file="app.log")
```
