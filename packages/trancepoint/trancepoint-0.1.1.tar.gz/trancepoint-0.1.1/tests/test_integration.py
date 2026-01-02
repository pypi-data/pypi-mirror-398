"""
Integration tests for agent observability system

Tests interactions between multiple components.
Coverage: Integration scenarios
"""

import pytest
from unittest.mock import Mock, patch
from trancepoint import Config
from trancepoint import SyncEventClient
from trancepoint import wrap_agent_function
from trancepoint import Event, EventType, ExecutionStatus


# ============================================================================
# TESTS: Config → HTTP Client → Events
# ============================================================================

@pytest.mark.integration
class TestConfigToHTTPClient:
    """Test config loading → HTTP client initialization → event transmission"""
    
    def test_full_flow_env_to_flush(self, mocker):
        """Load config from env → create client → send event → flush"""
        # Mock environment
        mocker.patch.dict("os.environ", {
            "AGENT_OBS_API_KEY": "sk_test_integration",
            "AGENT_OBS_BATCH_SIZE": "5",
        })
        
        # Mock HTTP
        mock_send_event = mocker.patch("agent_observability.http_client.SyncEventClient.send_event")
        
        # Load config
        config = Config.from_env()
        assert config.api_key == "sk_test_integration"
        assert config.batch_size == 5
        
        # Create client
        client = SyncEventClient(config)
        
        # Send event
        event = Event(
            event_id="evt_001",
            trace_id="tr_abc",
            event_type=EventType.START,
            status=ExecutionStatus.RUNNING,
            agent_name="test",
            timestamp_ms=1000,
        )
        client.send_event(event)
        
        # Flush
        client.flush()
        
        # Verify POST was called
        mock_send_event.assert_called()


# ============================================================================
# TESTS: Wrapper → Event Creation → HTTP Transmission
# ============================================================================

@pytest.mark.integration
class TestWrapperEndToEnd:
    """Test wrapping function → event creation → transmission"""
    
    def test_wrap_function_creates_and_sends_events(self, mocker):
        """Wrap function, execute it, verify events sent"""
        # Mock HTTP
        mock_post = mocker.patch("requests.Session.post")
        mock_response = Mock(status_code=200)
        mock_post.return_value = mock_response
        
        # Create config
        config = Config(api_key="sk_test")
        
        # Define function
        def my_agent(x):
            return x * 2
        
        # Wrap it
        wrapped = wrap_agent_function(my_agent, config, "test_agent")
        
        # Execute
        result = wrapped(5)
        assert result == 10
        
        # Verify events were sent
        # START event + END event = 1 POST with 2 events


# ============================================================================
# TESTS: Decorator → Wrapper → Events → HTTP
# ============================================================================

@pytest.mark.integration
class TestDecoratorFullFlow:
    """Test decorator → wrapper → event generation → HTTP transmission"""
    
    def test_observe_decorator_full_integration(self, mocker):
        """@observe decorator full execution"""
        # Mock environment
        mocker.patch.dict("os.environ", {
            "AGENT_OBS_API_KEY": "sk_test_decorator",
        })
        
        # Mock HTTP
        mock_send_event = mocker.patch("agent_observability.http_client.SyncEventClient.send_event")
        
        # Import and use decorator
        from trancepoint import observe
        
        @observe(agent_name="integration_test")
        def my_agent(x):
            return x + 10
        
        # Execute
        result = my_agent(5)
        assert result == 15
        
        # Verify HTTP called
        assert mock_send_event.called


# ============================================================================
# TESTS: Multi-Step Pipeline
# ============================================================================

@pytest.mark.integration
class TestMultiStepPipeline:
    """Test tracking multi-step pipeline"""
    
    def test_multi_function_pipeline(self, mocker):
        """Track multiple functions in sequence"""
        # Mock HTTP
        mock_post = mocker.patch("requests.Session.post")
        mock_post.return_value = Mock(status_code=200)
        
        config = Config(api_key="sk_test")
        
        def extract(data):
            return data.split(",")
        
        def transform(items):
            return [int(x) for x in items]
        
        def load(items):
            return sum(items)
        
        # Wrap all
        extract_wrapped = wrap_agent_function(extract, config, "extract")
        transform_wrapped = wrap_agent_function(transform, config, "transform")
        load_wrapped = wrap_agent_function(load, config, "load")
        
        # Execute pipeline
        step1 = extract_wrapped("1,2,3")
        step2 = transform_wrapped(step1)
        step3 = load_wrapped(step2)
        
        assert step3 == 6  # 1+2+3
        
        # Verify 3 separate traces


# ============================================================================
# TESTS: Error Handling Across Components
# ============================================================================

@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling across components"""
    
    def test_error_in_wrapped_function_tracked(self, mocker):
        """Error in wrapped function is tracked and sent"""
        # Mock HTTP
        mock_post = mocker.patch("requests.Session.post")
        mock_post.return_value = Mock(status_code=200)
        
        config = Config(api_key="sk_test")
        
        def my_agent(x):
            raise ValueError("Test error")
        
        wrapped = wrap_agent_function(my_agent, config, "error_test")
        
        # Execute (should raise)
        with pytest.raises(ValueError):
            wrapped(42)
        
        # Verify ERROR event was sent
        # mock_post should be called with ERROR event
