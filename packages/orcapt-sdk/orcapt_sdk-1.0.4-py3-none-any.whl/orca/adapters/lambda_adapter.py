import os
import json
import asyncio
import logging
from typing import Any, Dict, Callable, Optional, Awaitable, Union
from functools import wraps

from orca.domain.models import ChatMessage
from orca.common import get_logger, setup_logging

logger = get_logger("orca.lambda")

class LambdaAdapter:
    """
    Lambda Adapter
    ==============
    
    A utility class to easily run Orca agents on AWS Lambda.
    This adapter handles the differences between standard Docker environments and Lambda.
    
    It manages various complexities including:
    - HTTP Routing (Function URL, API Gateway, ALB)
    - SQS Event processing (Asynchronous message processing)
    - EventBridge (Cron/Scheduled tasks)
    - Event loop management (especially for Python 3.11+)

    Example:
        >>> from orca import LambdaAdapter, OrcaHandler, ChatMessage
        >>> 
        >>> handler = OrcaHandler()
        >>> adapter = LambdaAdapter()
        >>> 
        >>> @adapter.message_handler
        >>> async def process_message(data: ChatMessage):
        ...     session = handler.begin(data)
        ...     session.stream("Hello from Lambda!")
        ...     session.close()
        >>> 
        >>> # Inside your Lambda handler:
        >>> def lambda_handler(event, context):
        ...     return adapter.handle(event, context)
    """
    
    def __init__(self, enable_sqs: bool = True, enable_cron: bool = True):
        """
        Initialize the adapter.
        
        Args:
            enable_sqs: Whether to enable the SQS event handler.
            enable_cron: Whether to enable the Cron/Scheduled event handler.
        """
        self.enable_sqs = enable_sqs
        self.enable_cron = enable_cron
        self._message_handler: Optional[Callable[[ChatMessage], Awaitable[Any]]] = None
        self._cron_handler: Optional[Callable[[Dict], Awaitable[Any]]] = None
        
        # Ensure a stable event loop exists for the Lambda environment
        self._ensure_event_loop()
    
    def _ensure_event_loop(self):
        """Helper to ensure an event loop exists (required for Python 3.11+ in Lambda)."""
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
    
    def message_handler(self, func: Callable[[ChatMessage], Awaitable[Any]]) -> Callable:
        """
        Decorator for the main message processing function.
        
        Example:
            >>> @adapter.message_handler
            >>> async def process_message(data: ChatMessage):
            ...     # Your agent logic goes here
            ...     pass
        """
        @wraps(func)
        async def wrapper(data: ChatMessage):
            return await func(data)
        self._message_handler = wrapper
        return wrapper
    
    def cron_handler(self, func: Callable[[Dict], Awaitable[Any]]) -> Callable:
        """
        Decorator for cron or scheduled tasks.
        
        Example:
            >>> @adapter.cron_handler
            >>> async def scheduled_task(event: Dict):
            ...     # Your scheduled task logic goes here
            ...     pass
        """
        @wraps(func)
        async def wrapper(event: Dict):
            return await func(event)
        self._cron_handler = wrapper
        return wrapper

    def detect_event_source(self, event: Dict[str, Any]) -> str:
        """
        Identifies the source of the Lambda event.
        
        Returns:
            One of: "sqs", "cron", "http", or "unknown"
        """
        if "Records" in event and any(r.get("eventSource") == "aws:sqs" for r in event.get("Records", [])):
            return "sqs"
        if event.get("source") == "aws.events":
            return "cron"
        if "requestContext" in event or "httpMethod" in event:
            return "http"
        return "unknown"

    def offload_to_sqs(self, data: ChatMessage, queue_url: str) -> Dict[str, Any]:
        """
        Publishes a ChatMessage to an SQS queue for asynchronous processing.
        
        Args:
            data: The message to be offloaded.
            queue_url: The AWS SQS Queue URL.
            
        Returns:
            A status dictionary indicating success or failure.
        """
        try:
            import boto3
            sqs = boto3.client("sqs")
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=data.model_dump_json()
            )
            logger.info(f"Message offloaded to SQS: {queue_url}")
            return {"status": "queued", "response_uuid": data.response_uuid}
        except Exception as e:
            logger.exception(f"Failed to offload to SQS: {e}")
            raise

    def handle(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        The main Lambda entry point method.
        
        Automatically detects the event source and routes to the appropriate internal handler:
        - HTTP (API Gateway / Function URL)
        - SQS
        - Cron (EventBridge)
        
        Args:
            event: The Lambda event object.
            context: The Lambda context object.
            
        Returns:
            A dictionary response compatible with Lambda API expectations.
        """
        source = self.detect_event_source(event)
        logger.info(f"Lambda event received from source: {source}")

        if source == "sqs" and self.enable_sqs:
            return self._run_async(self._handle_sqs(event))
        
        if source == "cron" and self.enable_cron:
            return self._run_async(self._handle_cron(event))
        
        if source == "http":
            return self._run_async(self._handle_http(event))

        logger.warning(f"Unhandled or disabled event source: {source}")
        return {"statusCode": 404, "body": "Not Found"}

    def _run_async(self, coro: Awaitable[Any]) -> Any:
        """Helper to run a coroutine in the synchronous Lambda process."""
        return asyncio.run(coro)

    async def _handle_sqs(self, event: Dict) -> Dict[str, Any]:
        """Handles events originating from SQS."""
        logger.info("[SQS] Processing messages...")
        
        if not self._message_handler:
            logger.error("No message handler registered for SQS processing.")
            return {"statusCode": 500, "body": "Misconfigured"}

        records = event.get("Records", [])
        logger.info(f"[SQS] Found {len(records)} message(s)")
        
        for i, record in enumerate(records, 1):
            try:
                body = json.loads(record["body"])
                data = ChatMessage(**body)
                logger.info(f"[SQS] Processing message {i}/{len(records)}: {data.response_uuid}")
                
                await self._message_handler(data)
                logger.info(f"[SQS] Message {i} completed ✓")
            except Exception as e:
                logger.exception(f"[SQS] Message {i} failed: {e}")
        
        return {"statusCode": 200}

    async def _handle_cron(self, event: Dict) -> Dict[str, Any]:
        """Handles events originating from EventBridge (Cron)."""
        logger.info("[CRON] Running scheduled task...")
        
        if not self._cron_handler:
            logger.info("[CRON] No cron handler registered.")
            return {"statusCode": 200}
        
        try:
            await self._cron_handler(event)
            logger.info("[CRON] Task completed successfully ✓")
            return {"statusCode": 200}
        except Exception as e:
            logger.exception(f"[CRON] Error: {e}")
            return {"statusCode": 500}

    async def _handle_http(self, event: Dict) -> Dict[str, Any]:
        """
        Handles direct HTTP requests (Function URL or API Gateway).
        Typically used in simple deployments or as a fallback for offloading.
        """
        logger.info("[HTTP] Processing request...")
        
        try:
            body_str = event.get("body", "{}")
            body = json.loads(body_str) if isinstance(body_str, str) else body_str
            data = ChatMessage(**body)

            # Check if we should offload to SQS for async processing
            queue_url = os.environ.get("SQS_QUEUE_URL")
            if queue_url and self.enable_sqs:
                logger.info("[HTTP] Offloading to SQS...")
                result = self.offload_to_sqs(data, queue_url)
                logger.info("[HTTP] Offloaded successfully ✓")
                return {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps(result)
                }

            # Direct sync processing
            if self._message_handler:
                logger.info("[HTTP] Processing directly (sync/await)...")
                await self._message_handler(data)
                logger.info("[HTTP] Completed successfully ✓")
                return {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "status": "ok",
                        "response_uuid": data.response_uuid
                    })
                }
            
            logger.error("[HTTP] No message handler registered for direct processing")
            return {
                "statusCode": 500, 
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "No handler registered"})
            }

        except Exception as e:
            logger.exception(f"[HTTP] Error: {e}")
            return {
                "statusCode": 500, 
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": str(e)})
            }

def create_lambda_handler(
    message_handler: Callable[[ChatMessage], Awaitable[Any]],
    cron_handler: Optional[Callable[[Dict], Awaitable[Any]]] = None,
    enable_sqs: bool = True,
    enable_cron: bool = True
) -> Callable:
    """
    Helper function to create a standard Lambda handler from simple async functions.
    
    Example:
        >>> async def process_message(data: ChatMessage):
        ...     # Your logic
        ...     pass
        >>> 
        >>> # create_lambda_handler returns a standard handler(event, context)
        >>> handler = create_lambda_handler(process_message)
    """
    adapter = LambdaAdapter(enable_sqs=enable_sqs, enable_cron=enable_cron)
    adapter._message_handler = message_handler
    if cron_handler:
        adapter._cron_handler = cron_handler
    
    return adapter.handle

__all__ = ['LambdaAdapter', 'create_lambda_handler']

