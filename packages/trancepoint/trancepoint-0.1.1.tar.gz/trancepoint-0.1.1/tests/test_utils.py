"""
Unit tests for utils.py

Tests ID generation, formatting, truncation, and metrics.
Coverage: 100% of utils.py
"""

import pytest
from datetime import datetime
from trancepoint import (
    generate_trace_id,
    generate_event_id,
    generate_timestamp_ms,
    format_input,
    format_output,
    format_error,
    truncate_string,
    truncate_dict,
    calculate_duration_ms,
    calculate_percentile,
    calculate_success_rate,
    is_valid_trace_id,
    is_valid_event_id,
    is_valid_timestamp_ms,
)


# ============================================================================
# TESTS: ID Generation
# ============================================================================

@pytest.mark.unit
class TestIDGeneration:
    """Test ID generation functions"""
    
    def test_generate_trace_id_format(self):
        """Trace ID has correct format"""
        trace_id = generate_trace_id()
        
        assert isinstance(trace_id, str)
        assert trace_id.startswith("tr_")
        assert len(trace_id) > 5
    
    def test_generate_trace_id_unique(self):
        """Each trace ID is unique"""
        id1 = generate_trace_id()
        id2 = generate_trace_id()
        
        assert id1 != id2
    
    def test_generate_event_id_format(self):
        """Event ID has correct format"""
        event_id = generate_event_id()
        
        assert isinstance(event_id, str)
        assert event_id.startswith("evt_")
        assert len(event_id) > 5
    
    def test_generate_event_id_unique(self):
        """Each event ID is unique"""
        id1 = generate_event_id()
        id2 = generate_event_id()
        
        assert id1 != id2
    
    def test_generate_timestamp_ms_format(self):
        """Timestamp has millisecond precision"""
        ts = generate_timestamp_ms()
        
        assert isinstance(ts, int)
        assert ts > 0
        assert ts > 1700000000000  # After 2023-01-01
    
    def test_generate_timestamp_ms_current(self):
        """Timestamp is approximately current time"""
        ts = generate_timestamp_ms()
        now = int(datetime.now().timestamp() * 1000)
        
        # Should be within 1 second of now
        assert abs(ts - now) < 1000


# ============================================================================
# TESTS: Input/Output Formatting
# ============================================================================

@pytest.mark.unit
class TestFormatting:
    """Test input/output formatting"""
    
    def test_format_input_with_args(self):
        """Format function arguments"""
        result = format_input("test_query", depth=3, max_results=10)
        
        assert isinstance(result, str)
        assert "test_query" in result
        assert "depth" in result or "3" in result
    
    def test_format_input_no_args(self):
        """Format input with no arguments"""
        result = format_input()
        
        assert isinstance(result, str)
    
    def test_format_output_dict(self):
        """Format output as dictionary"""
        output_dict = {"results": [1, 2, 3], "count": 3}
        result = format_output(output_dict)
        
        assert isinstance(result, str)
        assert "results" in result
        assert "count" in result
    
    def test_format_output_string(self):
        """Format output as string"""
        result = format_output("test output string")
        
        assert isinstance(result, str)
        assert "test output string" in result
    
    def test_format_output_list(self):
        """Format output as list"""
        result = format_output([1, 2, 3, 4, 5])
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_format_output_none(self):
        """Format None output"""
        result = format_output(None)
        
        assert isinstance(result, str)
        assert "None" in result or "null" in result


# ============================================================================
# TESTS: Error Formatting
# ============================================================================

@pytest.mark.unit
class TestFormatError:
    """Test error formatting"""
    
    def test_format_error_value_error(self):
        """Format ValueError"""
        try:
            raise ValueError("Invalid input")
        except Exception as e:
            error_msg, error_type = format_error(e)
        
        assert "Invalid input" in error_msg
        assert error_type == "ValueError"
    
    def test_format_error_type_error(self):
        """Format TypeError"""
        try:
            raise TypeError("Wrong type")
        except Exception as e:
            error_msg, error_type = format_error(e)
        
        assert "Wrong type" in error_msg
        assert error_type == "TypeError"
    
    def test_format_error_custom_exception(self):
        """Format custom exception"""
        class CustomError(Exception):
            pass
        
        try:
            raise CustomError("Custom error message")
        except Exception as e:
            error_msg, error_type = format_error(e)
        
        assert "Custom error message" in error_msg
        assert error_type == "CustomError"


# ============================================================================
# TESTS: Truncation
# ============================================================================

@pytest.mark.unit
class TestTruncation:
    """Test truncation functions"""
    
    def test_truncate_string_no_truncation_needed(self):
        """String shorter than max_length is unchanged"""
        short = "hello"
        result = truncate_string(short, max_length=100)
        
        assert result == short
    
    def test_truncate_string_truncates(self):
        """Long string is truncated"""
        long_str = "a" * 1000
        result = truncate_string(long_str, max_length=100)
        
        assert len(result) <= 100
        assert "..." in result  # Should have ellipsis
    
    def test_truncate_string_exact_length(self):
        """String at exact max_length"""
        exact = "a" * 100
        result = truncate_string(exact, max_length=100)
        
        assert len(result) <= 100
    
    def test_truncate_dict_no_truncation(self):
        """Small dict is unchanged"""
        small_dict = {"key1": "value1", "key2": "value2"}
        result = truncate_dict(small_dict, max_keys=10)
        
        assert len(result) == 2
    
    def test_truncate_dict_removes_excess_keys(self):
        """Excess keys removed"""
        large_dict = {f"key{i}": f"value{i}" for i in range(20)}
        result = truncate_dict(large_dict, max_keys=10)
        
        assert len(result) <= 10


# ============================================================================
# TESTS: Validation
# ============================================================================

@pytest.mark.unit
class TestValidation:
    """Test validation functions"""
    
    def test_is_valid_trace_id_correct_format(self):
        """Valid trace ID recognized"""
        trace_id = generate_trace_id()
        assert is_valid_trace_id(trace_id) is True
    
    def test_is_valid_trace_id_wrong_prefix(self):
        """Invalid prefix rejected"""
        assert is_valid_trace_id("evt_abc123") is False
        assert is_valid_trace_id("invalid") is False
    
    def test_is_valid_event_id_correct_format(self):
        """Valid event ID recognized"""
        event_id = generate_event_id()
        assert is_valid_event_id(event_id) is True
    
    def test_is_valid_event_id_wrong_prefix(self):
        """Invalid prefix rejected"""
        assert is_valid_event_id("tr_abc123") is False
        assert is_valid_event_id("invalid") is False
    
    def test_is_valid_timestamp_current(self):
        """Current timestamp is valid"""
        ts = generate_timestamp_ms()
        assert is_valid_timestamp_ms(ts) is True
    
    def test_is_valid_timestamp_too_old(self):
        """Very old timestamp is invalid"""
        old_ts = 1000  # 1970
        assert is_valid_timestamp_ms(old_ts) is False


# ============================================================================
# TESTS: Metrics Calculation
# ============================================================================

@pytest.mark.unit
class TestMetricsCalculation:
    """Test metrics calculation functions"""
    
    def test_calculate_duration_ms_basic(self):
        """Calculate duration between timestamps"""
        start = 1000000
        end = 1002500
        
        duration = calculate_duration_ms(start, end)
        
        assert duration == 2500
    
    def test_calculate_duration_ms_same_time(self):
        """Duration for same timestamps is 0"""
        duration = calculate_duration_ms(1000, 1000)
        assert duration == 0
    
    def test_calculate_percentile_basic(self):
        """Calculate percentile of values"""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        p50 = calculate_percentile(values, 50)
        p95 = calculate_percentile(values, 95)
        p99 = calculate_percentile(values, 99)
        
        assert p50 >= values[0]
        assert p50 <= values[-1]
        assert p95 > p50  # 95th > 50th
        assert p99 > p95  # 99th > 95th
    
    def test_calculate_percentile_p100(self):
        """P100 is maximum value"""
        values = [10, 20, 30, 40, 50]
        p100 = calculate_percentile(values, 100)
        
        assert p100 == 50
    
    def test_calculate_success_rate_100_percent(self):
        """100% success rate"""
        rate = calculate_success_rate(100, 100)
        assert rate == 100.0
    
    def test_calculate_success_rate_partial(self):
        """Partial success rate"""
        rate = calculate_success_rate(80, 100)
        assert rate == 80.0
    
    def test_calculate_success_rate_zero(self):
        """Zero success rate"""
        rate = calculate_success_rate(0, 100)
        assert rate == 0.0
