import uuid
import json
import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_trace_id() -> str:
    """
    Generate a unique trace ID for linking related events.
    
    A trace ID groups all events from a single execution:
    - START event gets trace_id
    - END/ERROR event gets SAME trace_id
    - Backend uses trace_id to link them together
    
    Format: "tr_{uuid}" (readable and short)
    
    Returns:
        str: Unique trace ID
    
    Example:
        trace_id = generate_trace_id()
        # Returns: "tr_a1b2c3d4-e5f6-4a7b-8c9d-e0f1a2b3c4d5"
    """
    return f"tr_{uuid.uuid4()}"

def generate_event_id() -> str:
    """
    Generate a unique event ID for each event.
    
    Every event (START, END, ERROR) gets its own unique ID.
    
    Format: "evt_{uuid}" (readable and short)
    
    Returns:
        str: Unique event ID
    
    Example:
        event_id = generate_event_id()
        # Returns: "evt_f1e2d3c4-b5a6-4d7c-8b9a-f0e1d2c3b4a5"
    """
    return f"evt_{uuid.uuid4()}"

def generate_timestamp_ms() -> int:
    """
    Generate current timestamp in milliseconds since epoch.
    
    Used for event timing and sorting events by time.
    
    Returns:
        int: Milliseconds since epoch (January 1, 1970 UTC)
    
    Example:
        ts = generate_timestamp_ms()
        # Returns: 1703352000000
        
        # Convert back to seconds (if needed):
        ts_seconds = ts / 1000
        dt = datetime.fromtimestamp(ts_seconds)
    """
    return int(time.time() * 1000)

def format_input(*args, **kwargs) -> str:
    """
    Format function arguments as a string for event input_text.
    
    Takes function args/kwargs and produces a readable string.
    Automatically truncates to 500 chars (Event model limit).
    
    Handles:
    - Positional arguments (*args)
    - Keyword arguments (**kwargs)
    - Complex objects (dicts, lists)
    - Special types (datetime, etc.)
    
    Args:
        *args: Positional arguments from wrapped function
        **kwargs: Keyword arguments from wrapped function
    
    Returns:
        str: Formatted input string (max 500 chars)
    
    Example:
        # Simple args
        formatted = format_input("query", "analyze")
        # Returns: "args: ('query', 'analyze')"
        
        # With kwargs
        formatted = format_input("query", depth=3, max_results=10)
        # Returns: "args: ('query',), kwargs: {'depth': 3, 'max_results': 10}"
        
        # Complex object
        formatted = format_input({"data": [1, 2, 3], "nested": {"key": "value"}})
        # Returns: "args: ({'data': [1, 2, 3], 'nested': {'key': 'value'}},)"
    """
    parts = []
    
    # Format args if provided
    if args:
        try:
            args_str = _format_object(args, max_length=400)
            parts.append(f"args: {args_str}")
        except Exception as e:
            logger.warning(f"Error formatting args: {e}")
            parts.append(f"args: (unprintable)")
    
    # Format kwargs if provided
    if kwargs:
        try:
            kwargs_str = _format_object(kwargs, max_length=400)
            parts.append(f"kwargs: {kwargs_str}")
        except Exception as e:
            logger.warning(f"Error formatting kwargs: {e}")
            parts.append(f"kwargs: (unprintable)")
    
    # Combine
    formatted = ", ".join(parts)
    
    # Truncate to 500 chars
    if len(formatted) > 500:
        formatted = formatted[:497] + "..."
    
    return formatted

def format_output(result: Any) -> str:
    """
    Format function output/result as a string for event output_text.
    
    Takes the return value from wrapped function and produces readable string.
    Automatically truncates to 500 chars (Event model limit).
    
    Handles:
    - Strings (returns as-is)
    - Numbers (converts to string)
    - Complex objects (JSON serialize)
    - Special types (datetime, etc.)
    
    Args:
        result: Return value from wrapped function
    
    Returns:
        str: Formatted output string (max 500 chars)
    
    Example:
        # String result
        formatted = format_output("Found 5 papers")
        # Returns: "Found 5 papers"
        
        # Dict result
        formatted = format_output({"count": 5, "titles": ["A", "B", "C"]})
        # Returns: '{"count": 5, "titles": ["A", "B", "C"]}'
        
        # Complex result (truncated)
        long_result = {"data": list(range(1000))}
        formatted = format_output(long_result)
        # Returns: '{"data": [0, 1, 2, 3, ...' (truncated to 500 chars)
    """
    try:
        # If it's already a string, use directly
        if isinstance(result, str):
            formatted = result
        
        # If it's a number, convert to string
        elif isinstance(result, (int, float, bool)):
            formatted = str(result)
        
        # If it's a dict/list, JSON serialize
        elif isinstance(result, (dict, list)):
            formatted = json.dumps(result, default=_json_serializer, indent=None)
        
        # For other types, convert to string
        else:
            formatted = str(result)
        
        # Truncate to 500 chars
        if len(formatted) > 500:
            formatted = formatted[:497] + "..."
        
        return formatted
    
    except Exception as e:
        logger.warning(f"Error formatting output: {e}")
        return "(unprintable result)"


def format_error(error: Exception) -> tuple[str, str]:
    """
    Format exception as error message and error type.
    
    Extracts error message and exception class name from exception.
    Returns both for inclusion in ERROR events.
    
    Args:
        error: Exception that was raised
    
    Returns:
        tuple: (error_message, error_type)
            - error_message (str): Error message (max 1000 chars)
            - error_type (str): Exception class name
    
    Example:
        try:
            raise ValueError("Invalid input provided")
        except Exception as e:
            msg, typ = format_error(e)
            # msg = "Invalid input provided"
            # typ = "ValueError"
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    # Truncate message to 1000 chars
    if len(error_message) > 1000:
        error_message = error_message[:997] + "..."
    
    return error_message, error_type

# Internal helpers

def _format_object(obj: Any, max_length: int = 400) -> str:
    """
    Format a Python object to string, respecting max_length.
    
    Used internally by format_input/format_output.
    
    Args:
        obj: Object to format
        max_length: Maximum string length (default 400)
    
    Returns:
        str: Formatted object string
    """
    try:
        # Try JSON serialization first (works for dicts, lists, etc.)
        formatted = json.dumps(obj, default=_json_serializer, indent=None)
    except (TypeError, ValueError):
        # Fall back to str() for unprintable objects
        formatted = repr(obj)
    
    # Truncate if needed
    if len(formatted) > max_length:
        formatted = formatted[:max_length - 3] + "..."
    
    return formatted

def _json_serializer(obj: Any) -> str:
    """
    JSON serializer for objects not serializable by default json code.
    
    Called by json.dumps() when it encounters non-standard types.
    
    Handles:
    - datetime objects
    - bytes objects
    - UUID objects
    - Custom objects (uses __dict__ if available)
    
    Args:
        obj: Object to serialize
    
    Returns:
        str: String representation for JSON
    
    Raises:
        TypeError: If object cannot be serialized
    """
    # Handle datetime
    if isinstance(obj, datetime):
        return obj.isoformat()
    
    # Handle bytes
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    
    # Handle UUID
    if isinstance(obj, uuid.UUID):
        return str(obj)
    
    # Handle custom objects with __dict__
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    
    # Can't serialize
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def truncate_string(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Safely truncate a string to max length with suffix.
    
    Used to ensure strings fit within database/API limits.
    
    Args:
        text: String to truncate
        max_length: Maximum allowed length (default 500)
        suffix: Suffix to add when truncating (default "...")
    
    Returns:
        str: Truncated string
    
    Example:
        long_text = "x" * 1000
        truncated = truncate_string(long_text, max_length=100)
        # Returns: "xxxx...xxxx..." (100 chars total)
        
        # Custom suffix
        truncated = truncate_string(long_text, max_length=50, suffix="[TRUNCATED]")
        # Returns: "xxxxx[TRUNCATED]" (50 chars total)
    """
    if len(text) <= max_length:
        return text
    
    # Calculate space for actual content
    available = max_length - len(suffix)
    
    if available < 1:
        # Not enough space for both text and suffix
        return text[:max_length]
    
    return text[:available] + suffix


def truncate_dict(data: Dict[str, Any], max_keys: int = 10) -> Dict[str, Any]:
    """
    Safely truncate a dictionary to max number of keys.
    
    Used to limit metadata size in events.
    
    Args:
        data: Dictionary to truncate
        max_keys: Maximum number of keys to keep (default 10)
    
    Returns:
        dict: Truncated dictionary
    
    Example:
        data = {f"key_{i}": i for i in range(100)}
        truncated = truncate_dict(data, max_keys=5)
        # Returns: {"key_0": 0, "key_1": 1, ..., "key_4": 4}
    """
    if len(data) <= max_keys:
        return data
    
    # Keep first max_keys items
    truncated = dict(list(data.items())[:max_keys])
    
    return truncated

def is_valid_trace_id(trace_id: str) -> bool:
    """
    Validate that a trace ID has correct format.
    
    Args:
        trace_id: Trace ID to validate
    
    Returns:
        bool: True if valid format
    
    Example:
        is_valid_trace_id("tr_abc123")  # True
        is_valid_trace_id("invalid")    # False
    """
    if not isinstance(trace_id, str):
        return False
    
    if not trace_id.startswith("tr_"):
        return False
    
    if len(trace_id) < 10:  # "tr_" + at least 7 chars
        return False
    
    return True


def is_valid_event_id(event_id: str) -> bool:
    """
    Validate that an event ID has correct format.
    
    Args:
        event_id: Event ID to validate
    
    Returns:
        bool: True if valid format
    
    Example:
        is_valid_event_id("evt_xyz789")  # True
        is_valid_event_id("invalid")     # False
    """
    if not isinstance(event_id, str):
        return False
    
    if not event_id.startswith("evt_"):
        return False
    
    if len(event_id) < 10:  # "evt_" + at least 6 chars
        return False
    
    return True


def is_valid_timestamp_ms(timestamp_ms: int) -> bool:
    """
    Validate that a timestamp is reasonable.
    
    Args:
        timestamp_ms: Timestamp in milliseconds
    
    Returns:
        bool: True if reasonable (not in far future/past)
    
    Example:
        import time
        now = int(time.time() * 1000)
        is_valid_timestamp_ms(now)  # True
        is_valid_timestamp_ms(0)    # False (too old)
    """
    if not isinstance(timestamp_ms, int):
        return False
    
    # Must be positive
    if timestamp_ms <= 0:
        return False
    
    # Must be within reasonable range (2000 to 2100)
    # 946684800000 = Jan 1, 2000
    # 4102444800000 = Jan 1, 2100
    if timestamp_ms < 946684800000 or timestamp_ms > 4102444800000:
        return False
    
    return True

def calculate_duration_ms(start_ms: int, end_ms: int) -> int:
    """
    Calculate duration between two timestamps in milliseconds.
    
    Args:
        start_ms: Start timestamp in milliseconds
        end_ms: End timestamp in milliseconds
    
    Returns:
        int: Duration in milliseconds
    
    Example:
        start = generate_timestamp_ms()
        time.sleep(0.1)
        end = generate_timestamp_ms()
        duration = calculate_duration_ms(start, end)
        # Returns: ~100 (milliseconds)
    """
    duration = end_ms - start_ms
    
    # Ensure non-negative (clock skew handling)
    return max(0, duration)


def calculate_percentile(values: List[int], percentile: float) -> float:
    """
    Calculate percentile from a list of values.
    
    Used for metrics like p95_latency, p99_latency.
    
    Args:
        values: List of numeric values
        percentile: Percentile to calculate (0-100)
    
    Returns:
        float: Percentile value
    
    Example:
        latencies = [100, 200, 150, 300, 250]
        p95 = calculate_percentile(latencies, 95)
        # Returns: 295.0
    """
    if not values:
        return 0.0
    
    if len(values) == 1:
        return float(values)
    
    # Sort values
    sorted_values = sorted(values)
    
    # Calculate index
    index = (percentile / 100) * (len(sorted_values) - 1)
    
    # Interpolate if needed
    lower_index = int(index)
    upper_index = lower_index + 1
    
    if upper_index >= len(sorted_values):
        return float(sorted_values[-1])
    
    # Linear interpolation
    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]
    fraction = index - lower_index
    
    return lower_value + fraction * (upper_value - lower_value)


def calculate_success_rate(success_count: int, total_count: int) -> float:
    """
    Calculate success rate as percentage.
    
    Args:
        success_count: Number of successful executions
        total_count: Total number of executions
    
    Returns:
        float: Success rate (0-100)
    
    Example:
        rate = calculate_success_rate(95, 100)
        # Returns: 95.0
    """
    if total_count == 0:
        return 0.0
    
    return (success_count / total_count) * 100

def get_caller_info() -> Dict[str, str]:
    """
    Get information about the caller (for debugging/logging).
    
    Returns info about the module and function that called the observability code.
    
    Returns:
        dict: Information about caller
            - module: Module name
            - function: Function name
            - file: File path
            - line: Line number
    
    Example:
        info = get_caller_info()
        # Returns: {
        #   "module": "my_agent",
        #   "function": "research",
        #   "file": "/path/to/agent.py",
        #   "line": 42
        # }
    """
    import inspect
    
    try:
        # Get the stack frame
        frame = inspect.currentframe()
        
        # Go up the stack to find the actual caller
        # Skip: get_caller_info -> caller
        if frame and frame.f_back and frame.f_back.f_back:
            caller_frame = frame.f_back.f_back
            
            module = inspect.getmodulename(caller_frame.f_code.co_filename)
            function = caller_frame.f_code.co_name
            filename = caller_frame.f_code.co_filename
            lineno = caller_frame.f_lineno
            
            return {
                "module": module or "unknown",
                "function": function,
                "file": filename,
                "line": lineno,
            }
    except Exception as e:
        logger.warning(f"Error getting caller info: {e}")
    
    return {
        "module": "unknown",
        "function": "unknown",
        "file": "unknown",
        "line": 0,
    }

def create_test_event(
    event_type: str = "start",
    agent_name: str = "test_agent",
    **kwargs
) -> Dict[str, Any]:
    """
    Create a test event with sensible defaults.
    
    Used for unit testing event handling.
    
    Args:
        event_type: Type of event ("start", "end", "error")
        agent_name: Name of agent
        **kwargs: Additional fields to override
    
    Returns:
        dict: Event data ready for Event model
    
    Example:
        event = create_test_event(event_type="end", duration_ms=100)
        # Returns: {
        #   "event_id": "evt_...",
        #   "trace_id": "tr_...",
        #   "event_type": "end",
        #   "agent_name": "test_agent",
        #   "status": "success",
        #   "duration_ms": 100,
        #   ...
        # }
    """
    from .config import Config
    from .models import EventType, ExecutionStatus
    
    # Map event_type to EventType enum
    event_type_map = {
        "start": EventType.START,
        "end": EventType.END,
        "error": EventType.ERROR,
    }
    
    # Map to status
    status_map = {
        EventType.START: ExecutionStatus.RUNNING,
        EventType.END: ExecutionStatus.SUCCESS,
        EventType.ERROR: ExecutionStatus.ERROR,
    }
    
    et = event_type_map.get(event_type.lower(), EventType.START)
    
    # Build event data
    event_data = {
        "event_id": generate_event_id(),
        "trace_id": generate_trace_id(),
        "event_type": et,
        "agent_name": agent_name,
        "status": status_map[et],
        "timestamp_ms": generate_timestamp_ms(),
    }
    
    # Add type-specific fields
    if et == EventType.END:
        event_data["duration_ms"] = 1000
        event_data["output_text"] = "Test output"
    elif et == EventType.ERROR:
        event_data["duration_ms"] = 500
        event_data["error"] = "Test error"
        event_data["error_type"] = "ValueError"
    else:  # START
        event_data["input_text"] = "Test input"
    
    # Override with kwargs
    event_data.update(kwargs)
    
    return event_data

def count_tokens_openai(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens for OpenAI models using tiktoken
    
    Args:
        text: Text to count
        model: Model name (gpt-4, gpt-3.5-turbo, etc.)
    
    Returns:
        Number of tokens
    
    Raises:
        ImportError: If tiktoken not installed
    """
    try:
        import tiktoken
        
        # Normalize model name
        model = (model or "gpt-4").lower()
        
        # Map model names to tiktoken encoding
        if "gpt-4" in model:
            encoding_name = "cl100k_base"  # GPT-4 uses cl100k_base
        elif "gpt-3.5" in model:
            encoding_name = "cl100k_base"  # GPT-3.5 also uses cl100k_base
        else:
            encoding_name = "cl100k_base"  # Default
        
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text)
        
        return len(tokens)
    
    except ImportError:
        logger.warning("tiktoken not installed. Install with: pip install tiktoken")
        # Fallback: rough estimate (1 token ≈ 4 characters)
        return max(1, len(text) // 4)
    
    except Exception as e:
        logger.warning(f"Error counting OpenAI tokens: {e}. Using fallback.")
        return max(1, len(text) // 4)


def count_tokens_anthropic(text: str) -> int:
    """
    Count tokens for Anthropic (Claude) models
    
    Anthropic uses ~1 token per 3-4 characters
    This uses their approximation formula
    
    Args:
        text: Text to count
    
    Returns:
        Number of tokens
    """
    # Anthropic's approximation: 1 token ≈ 3.5 characters
    # More accurate than 4 for Anthropic
    tokens = max(1, len(text) // 3)
    return tokens


def count_tokens_google(text: str) -> int:
    """
    Count tokens for Google Gemini models
    
    Google uses ~1 token per 4 characters
    
    Args:
        text: Text to count
    
    Returns:
        Number of tokens
    """
    # Google's approximation: 1 token ≈ 4 characters
    tokens = max(1, len(text) // 4)
    return tokens


def count_tokens(
    text: str,
    model: str = "gpt-4",
    provider: str = "openai"
) -> int:
    """
    Count tokens based on LLM provider and model
    
    Args:
        text: Text to count
        model: Model name (e.g., "gpt-4", "claude-3-opus-20240229")
        provider: Provider (e.g., "openai", "anthropic", "google")
    
    Returns:
        Number of tokens
    
    Example:
        >>> count_tokens("Hello world", "gpt-4", "openai")
        2
        >>> count_tokens("Hello world", "claude-3-opus", "anthropic")
        5
    """
    
    provider = (provider or "openai").lower()
    model = (model or "unknown").lower()
    
    try:
        if provider == "openai" or provider is None:
            return count_tokens_openai(text, model)
        
        elif provider == "anthropic" or "claude" in model:
            return count_tokens_anthropic(text)
        
        elif provider == "google" or "gemini" in model:
            return count_tokens_google(text)
        
        else:
            # Fallback for unknown providers
            logger.warning(f"Unknown provider {provider}, using generic estimation")
            return max(1, len(text) // 4)
    
    except Exception as e:
        logger.error(f"Error counting tokens: {e}")
        return max(1, len(text) // 4)
    

def get_pricing(model: str, provider: str) -> Dict[str, float]:
    """
    Get pricing for a specific model
    
    Args:
        model: Model name (e.g., "gpt-4")
        provider: Provider (e.g., "openai")
    
    Returns:
        Dict with 'input' and 'output' keys (price per 1K tokens)
    
    Example:
        >>> get_pricing("gpt-4", "openai")
        {'input': 0.03, 'output': 0.06}
    """
    
    from .pricing import LLM_PRICING, DEFAULT_PRICING
    
    model = (model or "unknown").lower()
    provider = (provider or "openai").lower()
    
    # Get provider's pricing table
    provider_models = LLM_PRICING.get(provider, {})
    
    # Try to find matching model
    for model_key, pricing in provider_models.items():
        if model_key in model or model in model_key:
            return pricing
    
    # Log warning if not found
    logger.warning(
        f"Model {model} not found in {provider} pricing table. Using default."
    )
    
    return DEFAULT_PRICING


def calculate_llm_cost(
    model: str,
    provider: str,
    input_tokens: int,
    output_tokens: int
) -> float:
    """
    Calculate cost of LLM execution
    
    Args:
        model: Model name (e.g., "gpt-4")
        provider: Provider (e.g., "openai")
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    
    Returns:
        Cost in USD (rounded to 6 decimal places)
    
    Example:
        >>> calculate_llm_cost("gpt-4", "openai", 100, 200)
        0.015000
        
        # Breaking down:
        # Input: 100 tokens × $0.03/1K = $0.003
        # Output: 200 tokens × $0.06/1K = $0.012
        # Total: $0.015
    """
    
    try:
        # Handle None/invalid values
        input_tokens = max(0, int(input_tokens or 0))
        output_tokens = max(0, int(output_tokens or 0))
        
        # Get pricing
        pricing = get_pricing(model, provider)
        
        # Calculate costs
        input_cost = (input_tokens / 1000.0) * pricing.get("input", 0.01)
        output_cost = (output_tokens / 1000.0) * pricing.get("output", 0.01)
        
        total_cost = input_cost + output_cost
        
        # Round to 6 decimal places for precision
        return round(total_cost, 6)
    
    except Exception as e:
        logger.error(f"Error calculating cost: {e}")
        return 0.0

"""
Public API (what users import):

ID Generation:
  - generate_trace_id() → "tr_..."
  - generate_event_id() → "evt_..."
  - generate_timestamp_ms() → int

Formatting:
  - format_input(*args, **kwargs) → str
  - format_output(result) → str
  - format_error(exception) → (error_msg, error_type)

Truncation:
  - truncate_string(text, max_length) → str
  - truncate_dict(data, max_keys) → dict

Validation:
  - is_valid_trace_id(trace_id) → bool
  - is_valid_event_id(event_id) → bool
  - is_valid_timestamp_ms(timestamp_ms) → bool

Metrics:
  - calculate_duration_ms(start, end) → int
  - calculate_percentile(values, percentile) → float
  - calculate_success_rate(success, total) → float

Context:
  - get_caller_info() → dict

Testing:
  - create_test_event(**kwargs) → dict
"""