"""
Lambda Adapter
==============

Adapter برای اجرای راحت Orca agents روی AWS Lambda.
این adapter تفاوت‌های بین Docker معمولی و Lambda رو handle میکنه.
"""

import os
import json
import asyncio
from typing import Any, Dict, Callable, Optional, Awaitable
from functools import wraps

from orca.domain.models import ChatMessage


class LambdaAdapter:
    """
    Adapter برای Lambda deployment.
    
    این کلاس همه پیچیدگی‌های Lambda رو handle میکنه:
    - Function URL requests
    - SQS events
    - EventBridge (cron)
    - Event loop management
    
    Example:
        >>> from orca import LambdaAdapter, OrcaHandler
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
        >>> # در Lambda:
        >>> def lambda_handler(event, context):
        ...     return adapter.handle(event, context)
    """
    
    def __init__(self, enable_sqs: bool = True, enable_cron: bool = True):
        """
        Initialize adapter.
        
        Args:
            enable_sqs: فعال‌سازی SQS handler
            enable_cron: فعال‌سازی cron handler
        """
        self.enable_sqs = enable_sqs
        self.enable_cron = enable_cron
        self._message_handler: Optional[Callable[[ChatMessage], Awaitable[Any]]] = None
        self._cron_handler: Optional[Callable[[Dict], Awaitable[Any]]] = None
        
        # Fix event loop برای Lambda
        self._ensure_event_loop()
    
    def _ensure_event_loop(self):
        """اطمینان از وجود event loop (برای Python 3.11+)."""
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
    
    def message_handler(self, func: Callable[[ChatMessage], Awaitable[Any]]) -> Callable:
        """
        Decorator برای message handler.
        
        Example:
            >>> @adapter.message_handler
            >>> async def process_message(data: ChatMessage):
            ...     # Your agent logic here
            ...     pass
        """
        @wraps(func)
        async def wrapper(data: ChatMessage):
            return await func(data)
        
        self._message_handler = wrapper
        return wrapper
    
    def cron_handler(self, func: Callable[[Dict], Awaitable[Any]]) -> Callable:
        """
        Decorator برای cron/scheduled handler.
        
        Example:
            >>> @adapter.cron_handler
            >>> async def scheduled_task(event: Dict):
            ...     # Your scheduled task logic
            ...     pass
        """
        @wraps(func)
        async def wrapper(event: Dict):
            return await func(event)
        
        self._cron_handler = wrapper
        return wrapper
    
    def handle(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Main Lambda handler.
        
        این متد automatically تشخیص میده event از کجا اومده:
        - HTTP (Function URL)
        - SQS
        - EventBridge (cron)
        
        Args:
            event: Lambda event
            context: Lambda context
            
        Returns:
            Response dict
        """
        print("=" * 50, flush=True)
        print(f"[LAMBDA] Event source: {self._detect_source(event)}", flush=True)
        print("=" * 50, flush=True)
        
        # SQS Event
        if self.enable_sqs and 'Records' in event and len(event['Records']) > 0:
            if event['Records'][0].get('eventSource') == 'aws:sqs':
                return self._handle_sqs(event)
        
        # EventBridge (Cron)
        if self.enable_cron and event.get('source') == 'aws.events':
            return self._handle_cron(event)
        
        # HTTP (Function URL or API Gateway)
        return self._handle_http(event)
    
    def _detect_source(self, event: Dict) -> str:
        """تشخیص منبع event."""
        if 'Records' in event:
            return "SQS"
        if event.get('source') == 'aws.events':
            return "EventBridge (Cron)"
        if 'requestContext' in event or 'httpMethod' in event:
            return "HTTP (Function URL/API Gateway)"
        return "Unknown"
    
    def _handle_sqs(self, event: Dict) -> Dict[str, Any]:
        """Handle SQS events."""
        print("[SQS] Processing messages...", flush=True)
        
        if not self._message_handler:
            print("[SQS] No message handler registered!", flush=True)
            return {"statusCode": 500, "body": "No message handler"}
        
        records = event.get('Records', [])
        print(f"[SQS] Found {len(records)} message(s)", flush=True)
        
        for i, record in enumerate(records, 1):
            try:
                body = json.loads(record['body'])
                data = ChatMessage(**body)
                
                print(f"[SQS] Processing message {i}/{len(records)}: {data.response_uuid}", flush=True)
                
                # Run async handler
                asyncio.run(self._message_handler(data))
                
                print(f"[SQS] Message {i} completed ✓", flush=True)
                
            except Exception as e:
                print(f"[SQS] Message {i} failed: {e}", flush=True)
        
        return {"statusCode": 200}
    
    def _handle_http(self, event: Dict) -> Dict[str, Any]:
        """Handle HTTP events (Function URL or API Gateway)."""
        print("[HTTP] Processing request...", flush=True)
        
        try:
            # Parse body
            body = event.get('body', '{}')
            if isinstance(body, str):
                body = json.loads(body)
            
            # Check if should queue to SQS
            queue_url = os.environ.get('SQS_QUEUE_URL')
            
            if queue_url and self.enable_sqs:
                # Queue to SQS (async mode)
                print("[HTTP] Queueing to SQS...", flush=True)
                
                try:
                    import boto3
                    data = ChatMessage(**body)
                    sqs = boto3.client('sqs')
                    sqs.send_message(
                        QueueUrl=queue_url,
                        MessageBody=data.model_dump_json()
                    )
                    print("[HTTP] Queued successfully ✓", flush=True)
                    
                    return {
                        "statusCode": 200,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({
                            "status": "queued",
                            "response_uuid": data.response_uuid
                        })
                    }
                except Exception as e:
                    print(f"[HTTP] Queue failed: {e}", flush=True)
                    # Fall through to direct processing
            
            # Direct processing (sync mode)
            if not self._message_handler:
                return {
                    "statusCode": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "No message handler registered"})
                }
            
            print("[HTTP] Processing directly (await)...", flush=True)
            data = ChatMessage(**body)
            asyncio.run(self._message_handler(data))
            
            print("[HTTP] Completed ✓", flush=True)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "status": "ok",
                    "response_uuid": data.response_uuid
                })
            }
            
        except Exception as e:
            print(f"[HTTP] Error: {e}", flush=True)
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": str(e)})
            }
    
    def _handle_cron(self, event: Dict) -> Dict[str, Any]:
        """Handle EventBridge (cron) events."""
        print("[CRON] Running scheduled task...", flush=True)
        
        if self._cron_handler:
            try:
                asyncio.run(self._cron_handler(event))
                print("[CRON] Completed ✓", flush=True)
            except Exception as e:
                print(f"[CRON] Error: {e}", flush=True)
                return {"statusCode": 500}
        else:
            print("[CRON] No cron handler registered", flush=True)
        
        return {"statusCode": 200}


def create_lambda_handler(
    message_handler: Callable[[ChatMessage], Awaitable[Any]],
    cron_handler: Optional[Callable[[Dict], Awaitable[Any]]] = None,
    enable_sqs: bool = True,
    enable_cron: bool = True
) -> Callable:
    """
    Helper برای ساخت Lambda handler.
    
    Example:
        >>> async def process_message(data: ChatMessage):
        ...     # Your logic
        ...     pass
        >>> 
        >>> handler = create_lambda_handler(process_message)
        >>> 
        >>> # در Lambda:
        >>> def lambda_handler(event, context):
        ...     return handler(event, context)
    
    Args:
        message_handler: تابع async برای پردازش پیام‌ها
        cron_handler: تابع async برای scheduled tasks (optional)
        enable_sqs: فعال‌سازی SQS
        enable_cron: فعال‌سازی cron
        
    Returns:
        Lambda handler function
    """
    adapter = LambdaAdapter(enable_sqs=enable_sqs, enable_cron=enable_cron)
    adapter._message_handler = message_handler
    if cron_handler:
        adapter._cron_handler = cron_handler
    
    return adapter.handle


__all__ = ['LambdaAdapter', 'create_lambda_handler']

