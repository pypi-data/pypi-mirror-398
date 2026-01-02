import asyncio
import logging
import os
import json
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from orca.common import setup_logging, get_logger
from ..domain import ChatMessage
from ..adapters import LambdaAdapter
from ..core import OrcaHandler
from ..infrastructure.dev_stream_client import DevStreamClient

# Optional dependencies for Lambda environment
try:
    from fastapi import FastAPI
    from mangum import Mangum
    import boto3
    HAS_LAMBDA_DEPS = True
except ImportError:
    HAS_LAMBDA_DEPS = False

def create_hybrid_handler(
    process_message_func: Callable,
    app_title: str = "Orca Hybrid Agent",
    dev_mode: bool = False,
    level: int = logging.INFO
):
    """
    Creates a robust Hybrid Lambda Handler (FastAPI + Adapter).
    
    Delegates event routing and SQS offloading to the centralized LambdaAdapter.
    """
    setup_logging(level=level)
    logger = get_logger("orca.lambda")

    if not HAS_LAMBDA_DEPS:
        logger.warning("Lambda dependencies (fastapi, mangum) are missing. HTTP mode will fail.")

    # Initialize Orca components
    orca_handler = OrcaHandler(dev_mode=dev_mode)
    adapter = LambdaAdapter()

    @adapter.message_handler
    async def handle_message(data: ChatMessage):
        """Processes messages via SQS or Direct Adapter trigger."""
        return await process_message_func(data)

    @adapter.cron_handler
    async def handle_cron(event):
        """Processes scheduled tasks."""
        logger.info("[CRON] Executing scheduled logic...")
        return {"status": "success"}

    # Initialize FastAPI
    app = FastAPI(title=app_title)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "mode": "hybrid", "dev_mode": dev_mode}

    @app.post("/api/v1/send_message")
    async def api_send_message(data: ChatMessage):
        """
        HTTP Endpoint: Offloads to SQS if configured, else processes synchronously.
        """
        queue_url = os.environ.get("SQS_QUEUE_URL")
        if queue_url:
            return adapter.offload_to_sqs(data, queue_url)

        logger.info("SQS not configured, processing message synchronously...")
        await process_message_func(data)
        return {"status": "processed", "response_uuid": data.response_uuid}

    # Initialize Mangum
    mangum_handler = Mangum(app, lifespan="off") if HAS_LAMBDA_DEPS else None

    def universal_handler(event: Dict[str, Any], context: Any):
        """
        Routes events using the centralized LambdaAdapter detection logic.
        """
        source = adapter.detect_event_source(event)
        
        if source in ["sqs", "cron"]:
            return adapter.handle(event, context)
        
        if source == "http":
            if mangum_handler:
                return mangum_handler(event, context)
            logger.error("HTTP event received but Mangum/FastAPI dependencies are missing.")
            return {"statusCode": 500, "body": "Dependency Error"}

        logger.warning(f"Unknown event source: {source}")
        return {"statusCode": 404, "body": "Not Found"}

    return universal_handler

def create_mock_event(
    type: str = "http",
    message: str = "Hello",
    **kwargs
) -> Dict[str, Any]:
    """Helper to create mock Lambda events for testing."""
    body = {
        "message": message,
        "response_uuid": str(uuid.uuid4()),
        "message_uuid": str(uuid.uuid4()),
        "thread_id": kwargs.get("thread_id", "test-thread"),
        "model": kwargs.get("model", "gpt-4"),
        "conversation_id": kwargs.get("conversation_id", 1),
        "variables": kwargs.get("variables", []),
        "channel": kwargs.get("channel", "test-channel"),
        "url": kwargs.get("url", "")
    }

    if type == "http":
        return {
            "version": "2.0",
            "routeKey": "POST /api/v1/send_message",
            "rawPath": "/api/v1/send_message",
            "headers": {"content-type": "application/json"},
            "requestContext": {
                "http": {
                    "method": "POST",
                    "path": "/api/v1/send_message",
                    "sourceIp": "127.0.0.1",
                    "userAgent": "OrcaSimulator/1.0"
                },
                "requestId": str(uuid.uuid4()),
                "timeEpoch": int(datetime.now().timestamp() * 1000)
            },
            "body": json.dumps(body),
            "isBase64Encoded": False
        }
    
    if type == "sqs":
        return {
            "Records": [{
                "eventSource": "aws:sqs",
                "body": json.dumps(body)
            }]
        }
    
    if type == "cron":
        return {"source": "aws.events", "detail-type": "Scheduled Event"}
    
    return {}

def simulate_lambda_handler(handler: Callable, message: str = "Test message"):
    """Runs a full sequence of tests on a hybrid handler."""
    logger = get_logger("orca.test")
    logger.info(f"🧪 Starting simulation for message: '{message}'")
    
    # Pre-initialize dev stream queue to avoid [QUEUE-WARN]
    try:
        DevStreamClient.get_or_create_queue("test-channel")
    except:
        pass

    # 1. Test HTTP
    logger.info("--- Phase 1: HTTP ---")
    http_event = create_mock_event("http", message)
    res_http = handler(http_event, None)
    logger.info(f"HTTP Response: {res_http}")

    # 2. Test SQS
    logger.info("\n--- Phase 2: SQS ---")
    sqs_event = create_mock_event("sqs", f"Async: {message}")
    res_sqs = handler(sqs_event, None)
    logger.info(f"SQS Response: {res_sqs}")

    # 3. Test Cron
    logger.info("\n--- Phase 3: Cron ---")
    cron_event = create_mock_event("cron")
    res_cron = handler(cron_event, None)
    logger.info(f"Cron Response: {res_cron}")
    
    logger.info("\n✨ Simulation finished successfully.")
