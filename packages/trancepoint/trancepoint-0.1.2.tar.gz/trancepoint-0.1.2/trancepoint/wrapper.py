# agent_observability/wrapper.py
"""
Core wrapper implementation.

Handles:
1. Event creation (START, END, ERROR)
2. Token counting for LLMs
3. Cost calculation
4. Event transmission to backend
"""

import functools
import logging
from typing import Callable, Any, Optional, TypeVar
from datetime import datetime

from trancepoint.config import Config
from trancepoint.http_client import SyncEventClient
from trancepoint.models import Event, EventType, ExecutionStatus
from trancepoint.utils import (
    generate_trace_id,
    generate_event_id,
    generate_timestamp_ms,
    format_input,
    format_output,
    format_error,
    calculate_duration_ms,
    count_tokens,         
    calculate_llm_cost,      
)

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def wrap_agent_function(
    agent_function: F,
    config: Config,
    agent_name: Optional[str] = None,
    llm_model: Optional[str] = None,  # ← NEW: LLM model name
    llm_provider: str = "openai",     # ← NEW: LLM provider
    http_client: Optional[SyncEventClient] = None,
) -> F:
    """
    Wrap an agent function to automatically track execution WITH TOKEN COUNTING.
    
    This wrapper:
    1. Creates a START event when function is called
    2. Counts input tokens using the specified LLM model
    3. Tracks execution time
    4. Counts output tokens
    5. Calculates cost based on LLM pricing
    6. Creates END/ERROR event with cost metadata
    7. Sends all events to the observability backend
    
    The wrapper is transparent - function signature and behavior unchanged.
    
    Args:
        agent_function: The agent function to wrap
        config: Config with API credentials
        agent_name: Name for this agent (defaults to function name)
        llm_model: LLM model name (e.g., "gpt-4", "claude-3-opus")
        llm_provider: LLM provider (default "openai")
        http_client: Optional HTTP client for event sending (for testing)
    
    Returns:
        Callable: Wrapped function with same signature
    
    Raises:
        ValueError: If config is invalid
        TypeError: If agent_func is not callable
    
    Example:
        from agent_observability.config import Config
        from agent_observability.wrapper import wrap_agent_function
        
        config = Config.from_env()
        
        def my_agent(query: str, depth: int = 3):
            return f"Results for {query}"
        
        tracked_agent = wrap_agent_function(
            my_agent,
            config,
            agent_name="research_agent",
            llm_model="gpt-4",           # ← Token counting enabled!
            llm_provider="openai"
        )
        
        result = tracked_agent(query="AI trends", depth=5)
        # ↓ Automatically:
        # 1. Counts input tokens: ~6 tokens
        # 2. Executes agent
        # 3. Counts output tokens: ~200 tokens
        # 4. Cost: (6/1000 * $0.03) + (200/1000 * $0.06) = $0.00018 + $0.012 = $0.01218
        # 5. Sends to backend with cost metadata
    """
    
    if not isinstance(config, Config):
        raise TypeError(f'config must be Config, got {type(config)}')
    
    if not callable(agent_function):
        raise TypeError(f'agent_func must be callable, got {type(agent_function)}')
    
    final_agent_name = agent_name or agent_function.__name__ or "unknown_agent"
    final_llm_model = llm_model or "unknown"
    final_llm_provider = llm_provider or "openai"
    
    client = http_client or SyncEventClient(config)
    
    @functools.wraps(agent_function)
    def wrapper(*args, **kwargs) -> Any:
        """
        Wrapper that tracks agent execution WITH TOKEN COUNTING.
        
        This function is called instead of the original agent_function.
        It handles event creation, token counting, cost calculation, and transmission.
        """
        
        # ════════════════════════════════════════════════════════════════
        # PHASE 1: Initialize tracking IDs, LLM info, and timestamps
        # ════════════════════════════════════════════════════════════════
        
        trace_id = generate_trace_id()
        event_id_start = generate_event_id()
        start_time_ms = generate_timestamp_ms()
        
        logger.debug(
            f"[{trace_id}] Starting agent: {final_agent_name} "
            f"(LLM: {final_llm_provider}/{final_llm_model})"
        )
        
        # ════════════════════════════════════════════════════════════════
        # PHASE 2: Format input and COUNT INPUT TOKENS
        # ════════════════════════════════════════════════════════════════
        
        try:
            input_text = format_input(args, kwargs)
        except Exception as e:
            logger.warning(f"[{trace_id}] Error formatting input: {e}")
            input_text = "(error formatting input)"
        
        # COUNT INPUT TOKENS ← NEW!
        try:
            input_tokens = count_tokens(
                input_text,
                final_llm_model,
                final_llm_provider
            )
            logger.debug(f"[{trace_id}] Input tokens: {input_tokens}")
        except Exception as e:
            logger.warning(f"[{trace_id}] Error counting input tokens: {e}")
            input_tokens = 0
        
        # ════════════════════════════════════════════════════════════════
        # PHASE 3: Create and send START event
        # ════════════════════════════════════════════════════════════════
        
        start_event = Event(
            event_id=event_id_start,
            trace_id=trace_id,
            event_type=EventType.START,
            agent_name=final_agent_name,
            status=ExecutionStatus.RUNNING,
            timestamp_ms=start_time_ms,
            input_text=input_text,
            metadata={
                "llm_model": final_llm_model,
                "llm_provider": final_llm_provider,
                "input_tokens": input_tokens,  # ← NEW: Include in metadata
            }
        )
        
        try:
            if config.enabled:
                client.send_event(start_event)
                logger.debug(f"[{trace_id}] Sent START event")
        except Exception as e:
            logger.error(f"[{trace_id}] Error sending START event: {e}")
        
        # ════════════════════════════════════════════════════════════════
        # PHASE 4: Execute agent function
        # ════════════════════════════════════════════════════════════════
        
        result = None
        error_occurred = False
        error_message = ""
        error_type = ""
        
        try:
            logger.debug(f"[{trace_id}] Executing agent function")
            result = agent_function(*args, **kwargs)
            logger.debug(f"[{trace_id}] Agent executed successfully")
        
        except Exception as e:
            error_occurred = True
            error_message, error_type = format_error(e)
            logger.warning(
                f"[{trace_id}] Agent raised {error_type}: {error_message}"
            )
        
        # ════════════════════════════════════════════════════════════════
        # PHASE 5: Handle errors OR success
        # ════════════════════════════════════════════════════════════════
        
        end_time_ms = generate_timestamp_ms()
        duration_ms = calculate_duration_ms(start_time_ms, end_time_ms)
        
        if error_occurred:
            # ════════════════════════════════════════════════════════════
            # ERROR: Send ERROR event and re-raise
            # ════════════════════════════════════════════════════════════
            
            error_event = Event(
                event_id=generate_event_id(),
                trace_id=trace_id,
                event_type=EventType.ERROR,
                agent_name=final_agent_name,
                status=ExecutionStatus.ERROR,
                timestamp_ms=end_time_ms,
                duration_ms=duration_ms,
                error=error_message,
                error_type=error_type,
                metadata={
                    "llm_model": final_llm_model,
                    "llm_provider": final_llm_provider,
                    "input_tokens": input_tokens,
                }
            )
            
            try:
                if config.enabled:
                    client.send_event(error_event)
                    logger.debug(f"[{trace_id}] Sent ERROR event")
            except Exception as send_error:
                logger.error(f"[{trace_id}] Error sending ERROR event: {send_error}")
            
            # Flush to ensure ERROR event is sent before raising
            try:
                if config.enabled:
                    client.flush()
            except Exception as flush_error:
                logger.error(f"[{trace_id}] Error flushing: {flush_error}")
            
            # Re-raise the original exception
            raise
        
        else:
            # ════════════════════════════════════════════════════════════
            # SUCCESS: Format output, count tokens, calculate cost
            # ════════════════════════════════════════════════════════════
            
            try:
                output_text = format_output(result)
            except Exception as e:
                logger.warning(f"[{trace_id}] Error formatting output: {e}")
                output_text = "(error formatting output)"
            
            # COUNT OUTPUT TOKENS ← NEW!
            try:
                output_tokens = count_tokens(
                    output_text,
                    final_llm_model,
                    final_llm_provider
                )
                logger.debug(f"[{trace_id}] Output tokens: {output_tokens}")
            except Exception as e:
                logger.warning(f"[{trace_id}] Error counting output tokens: {e}")
                output_tokens = 0
            
            # Calculate total tokens and COST ← NEW!
            total_tokens = input_tokens + output_tokens
            
            try:
                cost_usd = calculate_llm_cost(
                    model=final_llm_model,
                    provider=final_llm_provider,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens
                )
                logger.debug(
                    f"[{trace_id}] Cost calculated: ${cost_usd:.6f} "
                    f"({input_tokens} input + {output_tokens} output tokens)"
                )
            except Exception as e:
                logger.warning(f"[{trace_id}] Error calculating cost: {e}")
                cost_usd = 0.0
            
            # Create and send END event WITH COST ← NEW!
            end_event = Event(
                event_id=generate_event_id(),
                trace_id=trace_id,
                event_type=EventType.END,
                agent_name=final_agent_name,
                status=ExecutionStatus.SUCCESS,
                timestamp_ms=end_time_ms,
                duration_ms=duration_ms,
                output_text=output_text,
                metadata={
                    "llm_model": final_llm_model,
                    "llm_provider": final_llm_provider,
                    "tokens": {
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": total_tokens,
                    },
                    "cost_usd": cost_usd,  # ← NEW: Cost included!
                }
            )
            
            try:
                if config.enabled:
                    client.send_event(end_event)
                    logger.debug(
                        f"[{trace_id}] Sent END event "
                        f"(cost: ${cost_usd:.6f}, tokens: {total_tokens}, "
                        f"duration: {duration_ms}ms)"
                    )
            except Exception as e:
                logger.error(f"[{trace_id}] Error sending END event: {e}")
            
            # Flush buffered events
            try:
                if config.enabled:
                    client.flush()
            except Exception as e:
                logger.error(f"[{trace_id}] Error flushing: {e}")
            
            logger.info(
                f"[{trace_id}] Agent completed: "
                f"duration={duration_ms}ms, "
                f"tokens={total_tokens}, "
                f"cost=${cost_usd:.6f}"
            )
            
            return result
    
    return wrapper
