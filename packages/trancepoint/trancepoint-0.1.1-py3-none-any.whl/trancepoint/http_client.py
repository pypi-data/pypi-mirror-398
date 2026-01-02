import httpx
import asyncio
import logging
import time
from typing import Optional, List
from datetime import datetime

from trancepoint.models import Event, EventBatch
from trancepoint.config import Config

logger = logging.getLogger(__name__)

# ============== ASYNC HTTP CLIENT =================

class EventClient:
    """
    Asynchronous HTTP client for sending events to backend.

    Features:
    - Non-blocking: uses async/await
    - Batching: Groups events, sends in batches
    - Auto-flush: Sends events periodically (every 5 seconds)
    - Resilient: Retries failed requests
    - Buffer: Stores events in memory until sent

    Usage (async context):
        async with EventClient(config) as client:
            await client.send_event(event)
            await client.flush()
    """

    def __init__(self,config:Config):
        """
        Initialize the client event

        Args:
            config: Configuration object with:
                - api_key: Authentication key
                - api_endpoint: Backend URL
                - batch_size: Max events per batch (default: 10)
                - flush_interval_seconds: Max wait before sending (default: 5)
                - timeout_seconds: HTTP request timeout (default: 5)
                - debug: Enable debug logging

        Example:
            config = Config(
                api_key="sk_prod_123",
                api_endpoint="https://api.agentobs.io",
                batch_size=10,
                flush_interval_seconds=5,
                debug=False
            )
            client = EventClient(config)
        """
        self.config = config
        self.client: Optional[httpx.AsyncClient] = None

        # buffer: stores events until sent
        self.event_buffer:List[Event] = []

        # Flushes events periodically
        self.background_task: Optional[asyncio.Task] = None

        if config.debug:
            logger.setLevel(logging.DEBUG)

    # Context Manager Protocol
    async def __aenter__(self):
        """
        Enter async context manager.

        Creates HTTP client and starts background flush loop.

        Usage:
            async with EventClient(config) as client:
                await client.send_event(event)
        
        Returns:
            self
        """
        # Creating HTTP client 
        self.client = httpx.AsyncClient(
            timeout=self.config.timeout_seconds,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "agent-observability/0.1.0"
            }
        )

        # Start background flush task
        self.background_task = asyncio.create_task(self._flush_loop())

        if self.config.debug:
            logger.debug("EventClient started")

        return self
    
    async def __aexit__(self,exc_type,exc_val,exc_tb):
        """
        Exit async context manager.

        Flushes remaining events, cancels background task, and closes HTTP client.
        Ensures no events are lost when exiting.
        """
        try:
            # Flush any remaining events
            await self.flush()

            if self.config.debug:
                logger.debug("Final flush completed")
            
        except Exception as e:
            logger.error(f"Error during final flush: {e}")

        try:
            # Cancel background task
            if self.background_task and not self.background_task.done():
                self.background_task.cancel()
                
                # Wait for cancellation to complete
                try:
                    await self.background_task
                except asyncio.CancelledError:
                    pass
            
            # Close HTTP client
            if self.client:
                await self.client.aclose()
            
            if self.config.debug:
                logger.debug("EventClient closed")
        
        except Exception as e:
            logger.error(f"Error closing EventClient: {e}")

    async def send_event(self,event:Event) -> bool:
        """
        Send a single event.
        
        Process:
        1. Add event to buffer
        2. Check if buffer is full
        3. If full, flush immediately
        4. Otherwise, wait for background flush (5 seconds)
        
        Args:
            event: Event object to send
        
        Returns:
            bool: True if event queued successfully, False if error
        
        Example:
            event = Event(
                event_id="evt_123",
                trace_id="tr_456",
                event_type=EventType.START,
                agent_name="researcher",
                status=ExecutionStatus.RUNNING,
                timestamp_ms=int(time.time() * 1000)
            )
            success = await client.send_event(event)
            if not success:
                logger.error("Failed to queue event")
        """

        # Skip if disabled
        if not self.config.enabled:
            return True
        
        try:
            # Add to buffer
            self.event_buffer.append(event)
            
            if self.config.debug:
                logger.debug(
                    f"Event buffered: {event.event_id} "
                    f"(buffer size: {len(self.event_buffer)}/{self.config.batch_size})"
                )
            
            # Check if buffer is full
            if len(self.event_buffer) >= self.config.batch_size:
                if self.config.debug:
                    logger.debug(
                        f"Buffer full ({self.config.batch_size} events). "
                        f"Flushing now..."
                    )
                
                # Send immediately (don't wait for 5-second timeout)
                return await self.flush()
            
            # Otherwise, background task will flush later
            return True
        
        except Exception as e:
            logger.error(f"Error queueing event: {e}")
            return False
        
    async def flush(self) -> bool:
        """
        Send all buffered events to backend.
        
        Process:
        1. Copy buffer to local list (so new events can be queued)
        2. Clear buffer
        3. Send batch to backend
        4. If successful, return True
        5. If failed, re-add to buffer for retry
        
        Returns:
            bool: True if successful, False if failed
        
        Example:
            success = await client.flush()
            if not success:
                logger.warning("Events will be retried")
        """
        
        # Not buffering if buffer is empty
        if not self.event_buffer or not self.config.enabled:
            return True
        
        # Make a copy of events to send
        events_to_send = self.event_buffer.copy()

        # Clear buffer immediately (allows new events to be queued)
        self.event_buffer.clear()

        if self.config.debug:
            logger.debug(
                f"Flushing {len(events_to_send)} events to "
                f"{self.config.api_endpoint}/v1/events"
            )
        try:
            # Create batch
            batch = EventBatch(
                api_key=self.config.api_key,
                events=events_to_send
            )
            
            # Convert to JSON dict
            batch_data = batch.model_dump(
                by_alias=False,
                mode="json"
            )
            
            # Send to backend
            response = await self.client.post(
                f"{self.config.api_endpoint}/v1/events",
                json=batch_data,
                headers={
                    "X-API-Key": self.config.api_key,
                    "X-Event-Count": str(len(events_to_send))
                }
            )
            
            # Check response
            if response.status_code == 200:
                if self.config.debug:
                    logger.debug(
                        f"✓ Successfully sent {len(events_to_send)} events"
                    )
                return True
            
            else:
                logger.error(
                    f"Failed to send events: "
                    f"Status {response.status_code}, "
                    f"Body: {response.text[:200]}"
                )
                
                # Re-add failed events to buffer for retry
                self.event_buffer.extend(events_to_send)
                return False
        
        except httpx.TimeoutException:
            logger.error(
                f"Timeout sending events "
                f"(exceeded {self.config.timeout_seconds}s). "
                f"Will retry."
            )
            # Re-add for retry
            self.event_buffer.extend(events_to_send)
            return False
        
        except httpx.NetworkError as e:
            logger.error(f"Network error sending events: {e}. Will retry.")
            # Re-add for retry
            self.event_buffer.extend(events_to_send)
            return False
        
        except Exception as e:
            logger.error(
                f"Unexpected error sending events: {e}. Will retry."
            )
            # Re-add for retry
            self.event_buffer.extend(events_to_send)
            return False
        
    async def _flush_loop(self):
        """
        Background task: periodically flush events.
        
        Runs forever, waking up every N seconds to flush:
        - Checks if there are buffered events
        - Sends them to backend
        - Continues running until cancelled
        
        This ensures:
        - Events don't get stuck in buffer too long
        - Batching still works (waits up to 5 seconds for more events)
        - Network isn't flooded (only 1 request every 5 seconds minimum)
        
        Note:
        - This runs in background and doesn't block user code
        - Will be cancelled when EventClient exits
        """

        while True:
            try:
                # Wait before flushing
                await asyncio.sleep(self.config.flush_interval_seconds)
                
                # Flush any buffered events
                await self.flush()
            
            except asyncio.CancelledError:
                # Task was cancelled (shutdown or context manager exit)
                if self.config.debug:
                    logger.debug("Flush loop cancelled")
                break
            
            except Exception as e:
                logger.error(f"Error in flush loop: {e}")
                # Continue even if error (don't let background task die)


class SyncEventClient:
    """
    Synchronous wrapper around async EventClient.
    
    Why we need this:
    - User's agent code is synchronous (not async/await)
    - We can't block the user's code
    - Solution: Run async client in background
    
    Usage:
        client = SyncEventClient(config)
        event = Event(...)
        client.send_event(event)  # Returns immediately!
        client.flush()             # Ensure all sent
        client.close()             # Cleanup
    
    Example:
        from agent_observability.http_client import SyncEventClient
        from agent_observability.models import Event, Config
        
        config = Config(api_key="sk_prod_123")
        client = SyncEventClient(config)
        
        # Send event (returns immediately)
        event = Event(...)
        client.send_event(event)
        
        # Later, when done
        client.flush()
        client.close()
    """

    def __init__(self, config: Config):
        """
        Initialize sync client.
        
        Creates internal async client but doesn't start it yet.
        Async client is created on first use.
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        # Async client (created on first use)
        self._async_client: Optional[EventClient] = None
        
        # Event loop (created if needed)
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def send_event(self, event: Event) -> bool:
        """
        Send event synchronously (non-blocking).
        
        Process:
        1. Initialize async client if needed
        2. Queue event in async client (doesn't block)
        3. Return immediately to user
        
        The actual HTTP request happens in background.
        
        Args:
            event: Event to send
        
        Returns:
            bool: True if queued, False if error
        
        Example:
            client = SyncEventClient(config)
            event = Event(...)
            success = client.send_event(event)
            
            if success:
                print("Event queued for sending")
            else:
                print("Error queueing event")
        """
        
        if not self.config.enabled:
            return True
        
        try:
            # Initialize async client if needed
            if not self._async_client:
                self._initialize_async_client()
            
            # Get or create event loop
            try:
                # If already in async context, use existing loop
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # Not in async context, use the stored loop
                if self._loop is None:
                    try:
                        self._loop = asyncio.get_event_loop()
                        # Check if loop is closed
                        if self._loop.is_closed():
                            self._loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(self._loop)
                    except RuntimeError:
                        self._loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(self._loop)
                
                loop = self._loop
            
            # Queue event (fire-and-forget)
            # This creates a task but doesn't wait for it
            asyncio.create_task(
                self._async_client.send_event(event)
            )
            
            if self.config.debug:
                logger.debug(f"Event queued for sending: {event.event_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error queueing event: {e}")
            return False
    
    def flush(self) -> bool:
        """
        Synchronously flush all buffered events.
        
        Waits for all events to be sent before returning.
        Use this before exiting the program.
        
        Returns:
            bool: True if successful, False if failed
        
        Example:
            client.send_event(event1)
            client.send_event(event2)
            client.send_event(event3)
            
            # Wait for all 3 to be sent
            success = client.flush()
            
            if not success:
                print("Some events failed to send")
        """
        
        if not self._async_client:
            return True
        
        try:
            # Get event loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = self._loop or asyncio.get_event_loop()
            
            # Run async flush on the loop
            return loop.run_until_complete(self._async_client.flush())
        
        except Exception as e:
            logger.error(f"Error flushing events: {e}")
            return False
    
    
    def close(self):
        """
        Cleanup: close HTTP client and event loop.
        
        Call this when shutting down the application to ensure:
        - All remaining events are flushed
        - HTTP client is properly closed
        - Event loop is closed
        
        Example:
            client = SyncEventClient(config)
            try:
                # ... use client ...
                tracked = wrap_agent(agent.invoke, client=client)
                result = tracked(...)
            finally:
                client.close()  # Always cleanup!
        """
        try:
            if self._async_client:
                # Flush remaining events
                self.flush()
        
        except Exception as e:
            logger.error(f"Error during final flush: {e}")
        
        try:
            if self._loop and not self._loop.is_closed():
                self._loop.close()
        except Exception as e:
            logger.error(f"Error closing event loop: {e}")
    
    
    def _initialize_async_client(self):
        """
        Initialize the async client.
        
        Called lazily on first use of send_event().
        """
        if self._async_client is None:
            self._async_client = EventClient(self.config)
            
            if self.config.debug:
                logger.debug("Async client initialized")