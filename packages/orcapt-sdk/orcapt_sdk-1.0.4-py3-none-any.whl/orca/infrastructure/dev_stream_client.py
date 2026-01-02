"""
Dev Stream Client
=================

Handles streaming for local development without Centrifugo.
Uses in-memory storage and async queues for real-time updates.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from threading import Lock
from collections import defaultdict
import json
from ..domain.interfaces import IStreamClient

logger = logging.getLogger(__name__)


class DevStreamClient(IStreamClient):
    """
    Development streaming client that stores messages in memory and uses async queues.
    """
    
    # Class-level storage for streaming data (shared across instances)
    _streams: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        'chunks': [],
        'full_response': '',
        'finished': False,
        'error': None,
        'queue': None  # Will hold asyncio.Queue for real-time streaming
    })
    _lock = Lock()
    
    def __init__(self):
        """Initialize the dev stream client."""
        logger.info("🔧 Dev Stream Client initialized (no Centrifugo)")
    
    def update_config(self, url: str, token: str) -> None:
        """
        Update client configuration (no-op for dev client).
        
        Args:
            url: Config URL (ignored in dev mode)
            token: Config token (ignored in dev mode)
        """
        logger.debug("Dev mode: update_config called but ignored")
    
    @classmethod
    def get_stream(cls, channel: str) -> Dict[str, Any]:
        """
        Get the current stream state for a channel.
        
        Args:
            channel: Channel name
            
        Returns:
            Dict containing chunks, full_response, finished status, and error
        """
        with cls._lock:
            return dict(cls._streams[channel])
    
    @classmethod
    def get_or_create_queue(cls, channel: str) -> asyncio.Queue:
        """
        Get or create an async queue for a channel.
        
        Args:
            channel: Channel name
            
        Returns:
            asyncio.Queue for the channel
        """
        with cls._lock:
            stream = cls._streams[channel]
            if stream['queue'] is None:
                stream['queue'] = asyncio.Queue()
                logger.info(f"🟠 [QUEUE-CREATE] Created new queue for channel: {channel}")
            else:
                logger.info(f"🟠 [QUEUE-EXIST] Queue already exists for channel: {channel}")
            return stream['queue']
    
    @classmethod
    def clear_stream(cls, channel: str):
        """
        Clear a stream's data but keep the queue reference.
        
        Args:
            channel: Channel name
        """
        with cls._lock:
            if channel in cls._streams:
                stream = cls._streams[channel]
                
                # Clear the data but KEEP the queue
                queue_ref = stream.get('queue')
                
                # Empty the queue if it exists
                if queue_ref is not None:
                    while not queue_ref.empty():
                        try:
                            queue_ref.get_nowait()
                        except asyncio.QueueEmpty:
                            break
                
                # Reset the stream data but keep the same queue object
                stream['chunks'] = []
                stream['full_response'] = ''
                stream['finished'] = False
                stream['error'] = None
                stream['queue'] = queue_ref  # Keep the same queue reference!
                
                logger.info(f"🟠 [CLEAR] Cleared stream data for channel {channel}, kept queue: {id(queue_ref)}")
    
    def send(self, channel: str, data: Dict[str, Any]):
        """
        Store data for a channel and push to async queue (dev mode).
        
        Args:
            channel: Channel name
            data: Data to store
        """
        try:
            with self._lock:
                stream = self._streams[channel]
                
                # Handle delta (streaming chunk)
                if 'delta' in data and data.get('delta'):
                    stream['chunks'].append(data['delta'])
                    stream['full_response'] += data['delta']
                    logger.info(f"🟠 [7-QUEUE] Delta added to chunks. Total chunks: {len(stream['chunks'])}")
                    
                    # Push to queue for real-time streaming
                    if stream['queue'] is not None:
                        try:
                            logger.info(f"🟠 [8-QUEUE] Pushing to queue: '{data['delta']}' ({len(data['delta'])} chars)")
                            # Use put_nowait for synchronous context
                            stream['queue'].put_nowait(('delta', data['delta']))
                            logger.info(f"🟠 [9-QUEUE] Successfully pushed to queue! Queue size: {stream['queue'].qsize()}")
                        except asyncio.QueueFull:
                            logger.error(f"🟠 [QUEUE-ERROR] Queue is full!")
                        except Exception as e:
                            logger.error(f"🟠 [QUEUE-ERROR] Failed to push to queue: {e}", exc_info=True)
                    else:
                        logger.error(f"🟠 [QUEUE-WARN] Queue is None for channel {channel}! Cannot push chunk.")
                
                # Handle completion
                if data.get('finished'):
                    stream['finished'] = True
                    if 'full_response' in data:
                        stream['full_response'] = data['full_response']
                    logger.info(f"✅ Dev stream completed for {channel}")
                    
                    # Push completion to queue
                    if stream['queue'] is not None:
                        try:
                            stream['queue'].put_nowait(('complete', stream['full_response']))
                        except:
                            pass
                
                # Handle error
                if data.get('error'):
                    stream['error'] = data.get('content', 'An error occurred')
                    stream['finished'] = True
                    logger.error(f"❌ Dev stream error for {channel}: {stream['error']}")
                    
                    # Push error to queue
                    if stream['queue'] is not None:
                        try:
                            stream['queue'].put_nowait(('error', stream['error']))
                        except:
                            pass
                
                # Store the complete message data
                stream['last_message'] = data
                
        except Exception as e:
            logger.error(f"Error in dev stream send to {channel}: {e}")
    
    def send_delta(self, channel: str, uuid: str, thread_id: str, delta: str):
        """
        Send a streaming delta message (dev mode).
        
        Args:
            channel: Channel name
            uuid: Response UUID
            thread_id: Thread ID
            delta: Text delta to send
        """
        logger.info(f"🟡 [5-DEVCLIENT] send_delta() called with '{delta}' ({len(delta)} chars)")
        
        data = {
            'delta': delta,
            'finished': False,
            'uuid': uuid,
            'thread_id': thread_id
        }
        self.send(channel, data)
        
        logger.info(f"🟡 [6-DEVCLIENT] After send(), checking queue status...")
        
        # Also log to console for immediate visibility in dev
        print(delta, end='', flush=True)
    
    def send_completion(self, channel: str, uuid: str, thread_id: str, full_response: str):
        """
        Send a completion signal (dev mode).
        
        Args:
            channel: Channel name
            uuid: Response UUID
            thread_id: Thread ID
            full_response: Complete response text
        """
        data = {
            'finished': True,
            'uuid': uuid,
            'thread_id': thread_id,
            'full_response': full_response
        }
        self.send(channel, data)
        print()  # New line after completion in console
    
    def send_error(self, channel: str, uuid: str, thread_id: str, error_message: str):
        """
        Send an error notification (dev mode).
        
        Args:
            channel: Channel name
            uuid: Response UUID
            thread_id: Thread ID
            error_message: Error message
        """
        data = {
            'error': True,
            'content': error_message,
            'finished': True,
            'uuid': uuid,
            'thread_id': thread_id,
            'status': 'FAILED',
            'role': 'developer'
        }
        self.send(channel, data)

