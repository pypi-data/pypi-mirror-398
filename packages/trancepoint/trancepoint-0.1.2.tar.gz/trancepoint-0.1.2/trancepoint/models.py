from pydantic import ConfigDict, BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

# ============== PRE-DEFINED ENUMS ===============

class EventType(str,Enum):
    """
    Type of Event occured

    START: Agent Execution begins
    END: Agent execution has completed successfully
    ERROR: Agent failed with exception

    """
    START = 'start'
    END = 'end'
    ERROR = 'error'

class ExecutionStatus(str,Enum):
    """
    Status of Execution

    RUNNING: currently executing
    SUCCESS: execution completed successfully
    ERROR: Failed due to some exception
    """
    RUNNING = 'running'
    SUCCESS = 'success'
    ERROR = 'error'
    TIMEOUT = 'timeout'
    
# ================ Pydantic Models ====================

class Event(BaseModel):
    """
     Represents Single event for agent execution

     An event can be one of three types:
        START: Agent execution started
        END: Agent execution ended
        ERROR: Agent execution stopped working with exception

    Multiple events with same trace_id are linked together:
        START event: marks beginning
        END/ERROR event: marks end + result

    Metadata now includes:
    - llm_model: The LLM model used (e.g., "gpt-4")
    - llm_provider: The provider (e.g., "openai")
    - tokens: Dict with input, output, total token counts
    - cost_usd: Calculated cost in USD

    Example:
        # START event with input tokens
        event = Event(
            event_id="evt_123",
            trace_id="tr_456",
            event_type="start",
            agent_name="researcher",
            status="running",
            timestamp_ms=1703352000000,
            input_text="What is AI?",
            metadata={
                "llm_model": "gpt-4",
                "llm_provider": "openai",
                "input_tokens": 6
            }
        )
        
        # END event with costs
        event = Event(
            event_id="evt_124",
            trace_id="tr_456",
            event_type="end",
            agent_name="researcher",
            status="success",
            timestamp_ms=1703352005000,
            duration_ms=5000,
            output_text="AI is...",
            metadata={
                "llm_model": "gpt-4",
                "llm_provider": "openai",
                "tokens": {
                    "input": 6,
                    "output": 500,
                    "total": 506
                },
                "cost_usd": 0.030180  # ← Cost calculated!
            }
        )
    """
    
    event_id:str = Field(
         ...,  # Required
        description="Unique ID for this event",
        examples=["evt_a1b2c3d4", "evt_xyz789"],
        min_length=5
    )

    trace_id:str = Field(
         ...,  # Required
        description="Trace ID linking related events together",
        examples=["tr_abc123", "tr_xyz789"],
        min_length=5
    )

    event_type: EventType = Field(
        ...,  # Required
        description="Type of event: start, end, or error"
    )
    
    status: ExecutionStatus = Field(
        ...,  # Required
        description="Status: running, success, or error"
    )

    agent_name: str = Field(
        ...,  # Required
        description="Name of the agent (e.g., 'researcher', 'analyzer')",
        examples=["researcher", "my_agent", "crew_1"],
        min_length=1
    )

    timestamp_ms: int = Field(
        ...,  # Required
        description="Timestamp in milliseconds since epoch",
        gt=0  # > 0 (validate: greater than 0)
    )
    
    duration_ms: Optional[int] = Field(
        default=None,
        description="Duration of execution in milliseconds",
        ge=0,  # >= 0 (for END/ERROR events only)
        examples=[1000, 3200, 5000]
    )

    input_text: Optional[str] = Field(
        default=None,
        description="Input to the agent (truncated to 500 chars)",
        max_length=500
    )
    
    output_text: Optional[str] = Field(
        default=None,
        description="Output from the agent (truncated to 500 chars)",
        max_length=500
    )

    error: Optional[str] = Field(
        default=None,
        description="Error message if execution failed",
        max_length=1000
    )
    
    error_type: Optional[str] = Field(
        default=None,
        description="Exception type (e.g., 'ValueError', 'TimeoutError')",
        examples=["ValueError", "TimeoutError", "RuntimeError"]
    )

    event_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata: LLM info, token counts, cost, etc."
    )

    model_config = ConfigDict(
        use_enum_values=True,  # Serialize enums as their values (not names)
        str_strip_whitespace=True,  # Strip whitespace from strings
    )

    @property
    def is_success(self) -> bool:
        """
        Whether this event represents successful execution.
        
        Returns:
            bool: True if status is SUCCESS
        """
        return self.status == ExecutionStatus.SUCCESS
    
    @property
    def is_error(self) -> bool:
        """
        Whether this event represents failed execution.
        
        Returns:
            bool: True if status is ERROR
        """
        return self.status == ExecutionStatus.ERROR
    
    @property
    def is_start(self) -> bool:
        """
        Whether this is a START event.
        
        Returns:
            bool: True if event_type is START
        """
        return self.event_type == EventType.START
    
    @property
    def is_end(self) -> bool:
        """
        Whether this is an END event.
        
        Returns:
            bool: True if event_type is END
        """
        return self.event_type == EventType.END
    
    @property
    def cost_usd(self) -> float:
        """Get cost from metadata if available."""
        if self.event_metadata and "cost_usd" in self.event_metadata:
            return float(self.event_metadata["cost_usd"])
        return 0.0
    
    @property
    def input_tokens(self) -> int:
        """Get input token count from metadata if available."""
        if self.event_metadata and "input_tokens" in self.event_metadata:
            return int(self.event_metadata["input_tokens"])
        return 0
    
    @property
    def output_tokens(self) -> int:
        """Get output token count from metadata if available."""
        if self.event_metadata and "tokens" in self.event_metadata:
            return int(self.event_metadata["tokens"].get("output", 0))
        return 0
    
    @property
    def total_tokens(self) -> int:
        """Get total token count from metadata if available."""
        if self.event_metadata and "tokens" in self.event_metadata:
            return int(self.event_metadata["tokens"].get("total", 0))
        return 0
    

class EventBatch(BaseModel):
    """
    Batch of events to send to backend in one HTTP request.
    
    The HTTP client buffers events and sends them as a batch for efficiency:
    - Instead of 10 separate HTTP requests, send 1 request with 10 events
    - Reduces network overhead
    - Increases throughput
    
    Example:
        # Middleware creates Event objects
        event1 = Event(...)
        event2 = Event(...)
        
        # HTTP client batches them
        batch = EventBatch(
            api_key="sk_prod_123",
            events=[event1, event2]
        )
        
        # Sends to backend as JSON:
        # POST /v1/events
        # {
        #   "api_key": "sk_prod_123",
        #   "events": [
        #     {"event_id": "evt_1", ...},
        #     {"event_id": "evt_2", ...}
        #   ]
        # }
    """
    
    api_key: str = Field(
        ...,  # Required
        description="API key for authentication",
        min_length=1
    )
    
    events: List[Event] = Field(
        ...,  # Required
        description="List of events in this batch",
        min_length=1,  # At least 1 event
        max_length=100  # At most 100 events
    )
    
    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
    )

    @property
    def event_count(self) -> int:
        """Number of events in batch"""
        return len(self.events)
    
    @property
    def success_count(self) -> int:
        """Number of successful events"""
        return sum(1 for e in self.events if e.is_success)
    
    @property
    def error_count(self) -> int:
        """Number of failed events"""
        return sum(1 for e in self.events if e.is_error)
    

class Execution(BaseModel):
    """
    Represents a complete execution (aggregated from START + END/ERROR events).
    
    This is created by the backend after receiving events:
    - START event comes in → create Execution record
    - END/ERROR event comes in → update Execution record with result
    
    Used for dashboard queries and metrics calculation.
    
    Example:
        execution = Execution(
            trace_id="tr_abc123",
            agent_name="researcher",
            status="success",
            duration_ms=3200,
            input_text="Find AI papers",
            output_text="Found 5 papers",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            cost_usd=0.02
        )
    """
    
    trace_id: str = Field(
        ...,
        description="Unique execution ID"
    )
    
    agent_name: str = Field(
        ...,
        description="Name of the agent"
    )
    
    status: ExecutionStatus = Field(
        ...,
        description="Final status: success or error"
    )
    
    duration_ms: int = Field(
        ...,
        description="Total execution time in milliseconds",
        ge=0
    )
    
    input_text: Optional[str] = Field(
        default=None,
        description="Input to agent",
        max_length=500
    )
    
    output_text: Optional[str] = Field(
        default=None,
        description="Output from agent",
        max_length=500
    )
    
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed",
        max_length=1000
    )
    
    started_at: datetime = Field(
        ...,
        description="When execution started"
    )
    
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When execution completed"
    )
    
    cost_usd: Optional[float] = Field(
        default=0.0,
        description="Estimated cost in USD",
        ge=0
    )
    
    model_config = ConfigDict(
        use_enum_values=True,
    )

class DailyCost(BaseModel):
    """
    Daily cost summary for a specific date.
    
    Used for graphing cost trends over time.
    
    Example:
        daily = DailyCost(
            date="2025-12-23",
            total_cost_usd=45.50,
            execution_count=120,
            success_count=118,
            error_count=2
        )
    """
    
    date: str = Field(
        ...,
        description="Date in YYYY-MM-DD format"
    )
    
    total_cost_usd: float = Field(
        default=0.0,
        description="Total cost for this day",
        ge=0
    )
    
    execution_count: int = Field(
        default=0,
        description="Number of executions"
    )
    
    success_count: int = Field(
        default=0,
        description="Number of successful executions"
    )
    
    error_count: int = Field(
        default=0,
        description="Number of failed executions"
    )
    
    avg_duration_ms: float = Field(
        default=0.0,
        description="Average execution duration"
    )


class CostMetrics(BaseModel):
    """
    Complete cost metrics for dashboard.
    
    Includes:
    - Total cost this month
    - Breakdown by model, agent, date
    - Trend (up/down/flat)
    
    Example:
        metrics = CostMetrics(
            total_cost=425.50,
            budget=500.0,
            by_model={
                "gpt-4": 250.00,
                "gpt-3.5": 125.00,
                "claude-2": 50.50
            },
            by_agent={
                "researcher": 200.00,
                "analyzer": 150.00,
                "writer": 75.50
            },
            daily_breakdown=[...],
            trend="up"
        )
    """
    
    total_cost: float = Field(
        ...,
        description="Total cost this period",
        ge=0
    )
    
    budget: Optional[float] = Field(
        default=None,
        description="Monthly budget (if set)",
        ge=0
    )
    
    by_model: Dict[str, float] = Field(
        default_factory=dict,
        description="Cost breakdown by model"
    )
    
    by_agent: Dict[str, float] = Field(
        default_factory=dict,
        description="Cost breakdown by agent"
    )
    
    daily_breakdown: List[DailyCost] = Field(
        default_factory=list,
        description="Daily cost summaries"
    )
    
    trend: Optional[str] = Field(
        default=None,
        description="Cost trend: 'up', 'down', or 'flat'",
        examples=["up", "down", "flat"]
    )
    
    @property
    def budget_used_percent(self) -> Optional[float]:
        """
        Percentage of budget used.
        
        Returns:
            float: 0-100, or None if no budget set
        """
        if self.budget is None or self.budget == 0:
            return None
        
        return (self.total_cost / self.budget) * 100


class PerformanceMetrics(BaseModel):
    """
    Performance metrics for dashboard.
    
    Includes:
    - Success rate
    - Average latency
    - P95 latency
    - Error breakdown
    
    Example:
        metrics = PerformanceMetrics(
            success_rate=94.2,
            avg_latency_ms=2300,
            p95_latency_ms=4100,
            execution_count=120,
            error_count=7,
            error_breakdown={
                "TimeoutError": 3,
                "ValueError": 2,
                "RuntimeError": 2
            }
        )
    """
    
    success_rate: float = Field(
        ...,
        description="Success rate as percentage (0-100)",
        ge=0,
        le=100
    )
    
    avg_latency_ms: float = Field(
        ...,
        description="Average latency in milliseconds",
        ge=0
    )
    
    p95_latency_ms: float = Field(
        ...,
        description="95th percentile latency",
        ge=0
    )
    
    p99_latency_ms: Optional[float] = Field(
        default=None,
        description="99th percentile latency",
        ge=0
    )
    
    execution_count: int = Field(
        ...,
        description="Total executions",
        ge=0
    )
    
    error_count: int = Field(
        ...,
        description="Total errors",
        ge=0
    )
    
    error_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Count by error type"
    )


# ================= API Models ==================

class ReceiveEventsRequest(BaseModel):
    """
    Request body for POST /v1/events endpoint.
    
    This is what the middleware sends to the backend.
    """
    
    events: List[Event] = Field(
        ...,
        description="List of events"
    )


class ReceiveEventsResponse(BaseModel):
    """
    Response from POST /v1/events endpoint.
    
    Tells the middleware how many events were accepted.
    """
    
    accepted: int = Field(
        ...,
        description="Number of events accepted"
    )
    
    rejected: int = Field(
        default=0,
        description="Number of events rejected"
    )
    
    message: Optional[str] = Field(
        default=None,
        description="Additional message"
    )


class MetricsResponse(BaseModel):
    """
    Response from GET /v1/metrics/* endpoints.
    """
    
    data: Dict[str, Any] = Field(
        ...,
        description="Metrics data"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When metrics were calculated"
    )
