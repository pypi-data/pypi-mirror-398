"""
Unit tests for wrapper.py

Tests function wrapping, event creation, and error handling.
Coverage: 100% of wrapper.py
"""

import pytest
from unittest.mock import Mock, patch
from trancepoint import (
    wrap_agent_function,
    ExecutionScope,
)


# ============================================================================
# TESTS: Basic Function Wrapping
# ============================================================================

@pytest.mark.unit
class TestWrapAgentFunction:
    """Test wrap_agent_function"""
    
    def test_wrap_simple_function(self, valid_config):
        """Wrap a simple function"""
        def my_agent(x):
            return x * 2
        
        wrapped = wrap_agent_function(my_agent, valid_config, "test_agent")
        
        # Should still work
        result = wrapped(5)
        assert result == 10
    
    def test_wrapped_function_preserves_behavior(self, valid_config):
        """Wrapped function has identical behavior"""
        def my_agent(a, b, c=3):
            return a + b + c
        
        wrapped = wrap_agent_function(my_agent, valid_config)
        
        assert wrapped(1, 2) == 6
        assert wrapped(1, 2, c=5) == 8
    
    def test_wrapped_function_with_kwargs(self, valid_config):
        """Wrapped function handles kwargs"""
        def my_agent(x, multiplier=2):
            return x * multiplier
        
        wrapped = wrap_agent_function(my_agent, valid_config)
        
        assert wrapped(5) == 10
        assert wrapped(5, multiplier=3) == 15
    
    def test_wrapped_function_with_args_and_kwargs(self, valid_config):
        """Wrapped function handles both args and kwargs"""
        def my_agent(a, b, *args, **kwargs):
            return sum([a, b, *args])
        
        wrapped = wrap_agent_function(my_agent, valid_config)
        
        assert wrapped(1, 2) == 3
        assert wrapped(1, 2, 3, 4) == 10

    def test_wrapped_function_preserves_name(self, valid_config):
        """Wrapped function preserves original function name"""
        def my_agent(x):
            """Agent docstring"""
            return x

        wrapped = wrap_agent_function(my_agent, valid_config)

        assert wrapped.__name__ == "my_agent"
        assert "Agent docstring" in wrapped.__doc__


# ============================================================================
# TESTS: Event Generation During Wrap
# ============================================================================

@pytest.mark.unit
class TestWrapperEventGeneration:
    """Test event generation during wrapping"""
    
    def test_wrapper_creates_start_event(self, valid_config):
        """Wrapper creates START event"""
        def my_agent(x):
            return x
        
        # Create a mock HTTP client with send_event
        mock_client = Mock()
        mock_client.send_event = Mock(return_value=True)
        mock_client.flush = Mock(return_value=True)

        # Pass the mock client directly
        wrapped = wrap_agent_function(
            my_agent, 
            valid_config, 
            "test_agent",
            http_client=mock_client
        )

        result = wrapped(42)
        assert result == 42

        # Verify send_event was called
        assert mock_client.send_event.called

        calls = mock_client.send_event.call_args_list
        assert len(calls) >= 1

        print(calls[0].args[0])

        # First call should be START event
        start_event = calls[0].args[0]
        assert start_event.event_type == "start"
        assert start_event.agent_name == "test_agent"
    
    def test_wrapper_creates_end_event(self, valid_config):
        """Wrapper creates END event"""
        def my_agent(x):
            return x * 2

        mock_client = Mock()
        mock_client.send_event = Mock(return_value=True)
        mock_client.flush = Mock(return_value=True)

        wrapped = wrap_agent_function(
            my_agent, 
            valid_config, 
            "test_agent",
            http_client=mock_client
        )

        result = wrapped(5)
        assert result == 10

        # We expect at least START and END events
        calls = mock_client.send_event.call_args_list
        assert len(calls) >= 2

        # Last call should be END event
        end_event = calls[-1].args[0]
        assert end_event.event_type == "end"
        assert end_event.status == "success"

        # Duration should be populated
        assert end_event.duration_ms is not None
        assert end_event.duration_ms >= 0

        # Output should be populated
        assert end_event.output_text is not None

    def test_wrapper_creates_error_event_on_exception(self, valid_config):
        """Wrapper creates ERROR event on exception"""
        def my_agent(x):
            raise ValueError("Bad input")

        mock_client = Mock()
        mock_client.send_event = Mock(return_value=True)
        mock_client.flush = Mock(return_value=True)

        wrapped = wrap_agent_function(
            my_agent, 
            valid_config, 
            "test_agent",
            http_client=mock_client
        )

        with pytest.raises(ValueError):
            wrapped(42)

        # ERROR event should be created
        calls = mock_client.send_event.call_args_list
        assert len(calls) >= 2  # START + ERROR at minimum

        error_event = calls[-1].args[0]
        assert error_event.event_type == "error"
        assert error_event.status == "error"
        assert "Bad input" in (error_event.error or "")

    def test_wrapper_respects_enabled_flag(self, valid_config):
        """Wrapper respects config.enabled flag"""
        def my_agent(x):
            return x * 2

        mock_client = Mock()
        mock_client.send_event = Mock(return_value=True)
        mock_client.flush = Mock(return_value=True)

        # Disable the config
        disabled_config = valid_config.__class__(
            api_key=valid_config.api_key,
            api_endpoint=valid_config.api_endpoint,
            enabled=False
        )

        wrapped = wrap_agent_function(
            my_agent,
            disabled_config,
            "test_agent",
            http_client=mock_client
        )

        result = wrapped(5)
        assert result == 10

        # send_event should NOT be called if disabled
        assert not mock_client.send_event.called


# ============================================================================
# TESTS: Error Propagation
# ============================================================================

@pytest.mark.unit
class TestWrapperErrorPropagation:
    """Test error propagation in wrapper"""
    
    def test_wrapper_propagates_exceptions(self, valid_config):
        """Exceptions are propagated (not suppressed)"""
        def my_agent(x):
            raise RuntimeError("Agent failed")

        mock_client = Mock()
        mock_client.send_event = Mock(return_value=True)
        mock_client.flush = Mock(return_value=True)

        wrapped = wrap_agent_function(
            my_agent,
            valid_config,
            http_client=mock_client
        )

        with pytest.raises(RuntimeError) as exc_info:
            wrapped(42)

        assert "Agent failed" in str(exc_info.value)

    def test_wrapper_handles_various_exception_types(self, valid_config):
        """Wrapper handles different exception types"""
        exceptions = [
            ValueError("value error"),
            TypeError("type error"),
            KeyError("key error"),
            RuntimeError("runtime error"),
        ]

        mock_client = Mock()
        mock_client.send_event = Mock(return_value=True)
        mock_client.flush = Mock(return_value=True)

        for exc in exceptions:
            def my_agent(x):
                raise exc

            wrapped = wrap_agent_function(
                my_agent,
                valid_config,
                http_client=mock_client
            )

            with pytest.raises(type(exc)):
                wrapped(42)

    def test_wrapper_calls_flush_on_error(self, valid_config):
        """Wrapper calls flush after error"""
        def my_agent(x):
            raise ValueError("error")

        mock_client = Mock()
        mock_client.send_event = Mock(return_value=True)
        mock_client.flush = Mock(return_value=True)

        wrapped = wrap_agent_function(
            my_agent,
            valid_config,
            http_client=mock_client
        )

        with pytest.raises(ValueError):
            wrapped(42)

        # Flush should be called
        assert mock_client.flush.called

    def test_wrapper_calls_flush_on_success(self, valid_config):
        """Wrapper calls flush after success"""
        def my_agent(x):
            return x * 2

        mock_client = Mock()
        mock_client.send_event = Mock(return_value=True)
        mock_client.flush = Mock(return_value=True)

        wrapped = wrap_agent_function(
            my_agent,
            valid_config,
            http_client=mock_client
        )

        result = wrapped(5)
        assert result == 10

        # Flush should be called
        assert mock_client.flush.called

# ============================================================================
# TESTS: ExecutionScope
# ============================================================================


@pytest.mark.unit
class TestExecutionScope:
    """Test ExecutionScope context manager"""

    def test_execution_scope_basic(self, valid_config):
        """ExecutionScope enters and exits successfully"""
        with ExecutionScope(valid_config, "test_scope") as scope:
            assert scope.agent_name == "test_scope"
            assert scope.trace_id is not None

    def test_execution_scope_log_step(self, valid_config):
        """ExecutionScope logs steps"""
        with ExecutionScope(valid_config, "test_scope") as scope:
            # Should not raise
            scope.log_step("step1", {"data": "value"})
            scope.log_step("step2")

    def test_execution_scope_exit_handler(self, valid_config):
        """ExecutionScope handles exit properly"""
        try:
            with ExecutionScope(valid_config, "test_scope"):
                pass  # Exit normally
        except Exception:
            pytest.fail("ExecutionScope should not raise on normal exit")


# ============================================================================
# TESTS: Type Validation
# ============================================================================


@pytest.mark.unit
class TestWrapperTypeValidation:
    """Test type validation in wrapper"""

    def test_wrapper_rejects_non_callable(self, valid_config):
        """Wrapper rejects non-callable objects"""
        with pytest.raises(TypeError):
            wrap_agent_function("not_callable", valid_config)

    def test_wrapper_rejects_invalid_config(self):
        """Wrapper rejects invalid config"""
        def my_agent(x):
            return x

        with pytest.raises(TypeError):
            wrap_agent_function(my_agent, "not_a_config")

    def test_wrapper_accepts_none_agent_name(self, valid_config):
        """Wrapper accepts None as agent_name (uses function name)"""
        def my_agent(x):
            return x

        wrapped = wrap_agent_function(my_agent, valid_config, agent_name=None)
        assert wrapped(5) == 5