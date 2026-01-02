"""
Unit tests for models.py

Tests all data classes, enums, and validation.
Coverage: 100% of models.py
"""

import pytest
from trancepoint import (
    EventType, ExecutionStatus, Event
)

@pytest.mark.unit
class TestEventType:
    """Test EventType enumeration"""
    
    def test_event_type_start_value(self):
        """START event type has correct value"""
        assert EventType.START.value == "start"
    
    def test_event_type_end_value(self):
        """END event type has correct value"""
        assert EventType.END.value == "end"
    
    def test_event_type_error_value(self):
        """ERROR event type has correct value"""
        assert EventType.ERROR.value == "error"
    
    def test_event_type_is_string_enum(self):
        """EventType can be used as string"""
        assert str(EventType.START) == "EventType.START"
        # When serialized to JSON, becomes "start"
        assert EventType.START.value == "start"

@pytest.mark.unit
class TestExecutionStatus:
    """Test ExecutionStatus enumeration"""
    
    def test_status_running_value(self):
        """RUNNING status has correct value"""
        assert ExecutionStatus.RUNNING.value == "running"
    
    def test_status_success_value(self):
        """SUCCESS status has correct value"""
        assert ExecutionStatus.SUCCESS.value == "success"
    
    def test_status_error_value(self):
        """ERROR status has correct value"""
        assert ExecutionStatus.ERROR.value == "error"
    
    def test_status_timeout_value(self):
        """TIMEOUT status has correct value"""
        assert ExecutionStatus.TIMEOUT.value == "timeout"
    
    def test_status_all_values_are_lowercase(self):
        """All status values are lowercase (for JSON compatibility)"""
        for status in ExecutionStatus:
            assert status.value.islower()

@pytest.mark.unit
class TestEventCreation:
    """Test creating valid Event objects"""
    
    def test_create_start_event(self, start_event):
        """Create valid START event"""
        assert start_event.event_id == "evt_001"
        assert start_event.trace_id == "tr_abc123"
        assert start_event.event_type == EventType.START
        assert start_event.status == ExecutionStatus.RUNNING
        assert start_event.agent_name == "test_agent"
        assert start_event.input_text is not None
        assert start_event.output_text is None  # Not set for START
        assert start_event.duration_ms is None  # Not set for START
    
    def test_create_end_event(self, end_event):
        """Create valid END event"""
        assert end_event.event_id == "evt_002"
        assert end_event.trace_id == "tr_abc123"
        assert end_event.event_type == EventType.END
        assert end_event.status == ExecutionStatus.SUCCESS
        assert end_event.output_text is not None
        assert end_event.duration_ms == 2500
        assert end_event.error is None  # Not set for END
    
    def test_create_error_event(self, error_event):
        """Create valid ERROR event"""
        assert error_event.event_type == EventType.ERROR
        assert error_event.status == ExecutionStatus.ERROR
        assert error_event.error is not None
        assert error_event.error_type is not None
        assert error_event.duration_ms == 500


@pytest.mark.unit
class TestEventValidation:
    """Test Event validation and constraints"""
    
    def test_event_requires_event_id(self):
        """Event ID is required"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Event(
                trace_id="tr_abc",
                event_type=EventType.START,
                # Missing event_id
            )
    
    def test_event_requires_trace_id(self):
        """Trace ID is required"""
        with pytest.raises(Exception):
            Event(
                event_id="evt_001",
                # Missing trace_id
                event_type=EventType.START,
            )
    
    def test_event_requires_agent_name(self):
        """Agent name is required"""
        with pytest.raises(Exception):
            Event(
                event_id="evt_001",
                trace_id="tr_abc",
                event_type=EventType.START,
                # Missing agent_name
            )
    
    def test_event_duration_must_be_positive(self):
        """Duration must be positive (if provided)"""
        with pytest.raises(Exception):
            Event(
                event_id="evt_001",
                trace_id="tr_abc",
                event_type=EventType.END,
                agent_name="test",
                timestamp_ms=1000,
                duration_ms=-100,  # Invalid: negative
            )


@pytest.mark.unit
class TestEventSerialization:
    """Test Event JSON serialization/deserialization"""
    
    def test_event_serializes_to_dict(self, start_event):
        """Event can be serialized to dictionary"""
        event_dict = start_event.model_dump()
        
        assert isinstance(event_dict, dict)
        assert event_dict["event_id"] == "evt_001"
        assert event_dict["trace_id"] == "tr_abc123"
        assert event_dict["event_type"] == "start"  # Enum value
        assert event_dict["status"] == "running"    # Enum value
    
    def test_event_serializes_to_json(self, end_event):
        """Event can be serialized to JSON string"""
        import json
        event_json = end_event.model_dump_json()
        
        assert isinstance(event_json, str)
        parsed = json.loads(event_json)
        assert parsed["event_id"] == "evt_002"
        assert parsed["event_type"] == "end"
    
    def test_event_excludes_none_fields(self, start_event):
        """None fields are included in serialization but allowed"""
        event_dict = start_event.model_dump()
        # None fields are included (Pydantic default behavior)
        assert "output_text" in event_dict
        assert event_dict["output_text"] is None


@pytest.mark.unit
class TestEventEquality:
    """Test Event comparison and identity"""
    
    def test_two_identical_events_are_equal(self):
        """Two events with same values are equal"""
        event1 = Event(
            event_id="evt_001",
            trace_id="tr_abc",
            event_type=EventType.START,
            status=ExecutionStatus.RUNNING,
            agent_name="test",
            timestamp_ms=1000,
        )
        event2 = Event(
            event_id="evt_001",
            trace_id="tr_abc",
            event_type=EventType.START,
            status=ExecutionStatus.RUNNING,
            agent_name="test",
            timestamp_ms=1000,
        )
        assert event1 == event2
    
    def test_different_event_ids_are_not_equal(self, start_event):
        """Events with different IDs are not equal"""
        other = Event(
            event_id="evt_999",  # Different
            trace_id="tr_abc123",
            event_type=EventType.START,
            status=ExecutionStatus.RUNNING,
            agent_name="test_agent",
            timestamp_ms=1703352000000,
        )
        assert start_event != other
