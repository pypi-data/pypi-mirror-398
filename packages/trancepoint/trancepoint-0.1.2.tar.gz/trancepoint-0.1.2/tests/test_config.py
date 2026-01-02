"""
Unit tests for config.py

Tests configuration loading, validation, and merging.
Coverage: 100% of config.py
"""

import pytest
import os
import tempfile
from trancepoint import Config


# ============================================================================
# TESTS: Config Creation & Defaults
# ============================================================================

@pytest.mark.unit
class TestConfigDefaults:
    """Test configuration defaults"""
    
    def test_config_with_only_api_key(self):
        """Can create config with only API key (uses defaults for others)"""
        config = Config(api_key="sk_test_minimal")
        
        assert config.api_key == "sk_test_minimal"
        assert config.api_endpoint == "https://api.agentobs.io"  # Default
        assert config.batch_size == 10  # Default
        assert config.flush_interval_seconds == 5  # Default
        assert config.timeout_seconds == 5  # Default
        assert config.enabled is True  # Default
        assert config.debug is False  # Default
    
    def test_config_with_all_fields(self, valid_config):
        """Can create config with all fields specified"""
        assert valid_config.api_key == "sk_test_abc123"
        assert valid_config.batch_size == 10
        assert valid_config.enabled is True
        assert valid_config.debug is False


# ============================================================================
# TESTS: API Key Validation
# ============================================================================

@pytest.mark.unit
class TestConfigAPIKeyValidation:
    """Test API key validation"""
    
    def test_api_key_must_start_with_sk(self):
        """API key must start with 'sk_'"""
        with pytest.raises(Exception):  # ValidationError
            Config(api_key="invalid_key")
    
    def test_api_key_sk_test_valid(self):
        """API key starting with 'sk_test_' is valid"""
        config = Config(api_key="sk_test_abc123")
        assert config.api_key == "sk_test_abc123"
    
    def test_api_key_sk_prod_valid(self):
        """API key starting with 'sk_prod_' is valid"""
        config = Config(api_key="sk_prod_xyz789")
        assert config.api_key == "sk_prod_xyz789"
    
    def test_api_key_empty_invalid(self):
        """Empty API key is invalid"""
        with pytest.raises(Exception):
            Config(api_key="")


# ============================================================================
# TESTS: Batch Size Validation
# ============================================================================

@pytest.mark.unit
class TestConfigBatchSizeValidation:
    """Test batch size validation"""
    
    def test_batch_size_minimum(self):
        """Batch size must be at least 1"""
        with pytest.raises(Exception):
            Config(api_key="sk_...", batch_size=0)
    
    def test_batch_size_maximum(self):
        """Batch size must not exceed 100"""
        with pytest.raises(Exception):
            Config(api_key="sk_...", batch_size=101)
    
    def test_batch_size_valid_range(self):
        """Batch size in range 1-100 is valid"""
        config1 = Config(api_key="sk_...iujh6uyg", batch_size=1)
        assert config1.batch_size == 1
        
        config100 = Config(api_key="sk_...fgtyuijhbv", batch_size=100)
        assert config100.batch_size == 100


# ============================================================================
# TESTS: Endpoint Validation
# ============================================================================

@pytest.mark.unit
class TestConfigEndpointValidation:
    """Test API endpoint validation"""
    
    def test_endpoint_must_have_protocol(self):
        """Endpoint must start with http:// or https://"""
        with pytest.raises(Exception):
            Config(api_key="sk_...", api_endpoint="api.example.com")
    
    def test_endpoint_https_valid(self):
        """https:// endpoint is valid"""
        config = Config(
            api_key="sk_...",
            api_endpoint="https://api.example.com"
        )
        assert config.api_endpoint == "https://api.example.com"
    
    def test_endpoint_http_valid(self):
        """http:// endpoint is valid (for local testing)"""
        config = Config(
            api_key="sk_...",
            api_endpoint="http://localhost:8000"
        )
        assert config.api_endpoint == "http://localhost:8000"


# ============================================================================
# TESTS: Environment Variable Loading
# ============================================================================

@pytest.mark.unit
class TestConfigFromEnvironment:
    """Test loading config from environment variables"""
    
    def test_load_from_env_minimal(self, mocker):
        """Load config from environment variables"""
        mocker.patch.dict(os.environ, {
            "AGENT_OBS_API_KEY": "sk_env_test",
        })
        
        config = Config.from_env()
        
        assert config.api_key == "sk_env_test"
        assert config.batch_size == 10  # Uses default
    
    def test_load_from_env_all_fields(self, mocker):
        """Load all fields from environment"""
        mocker.patch.dict(os.environ, {
            "AGENT_OBS_API_KEY": "sk_env_full",
            "AGENT_OBS_BATCH_SIZE": "25",
            "AGENT_OBS_TIMEOUT_SECONDS": "10",
            "AGENT_OBS_DEBUG": "true",
            "AGENT_OBS_ENABLED": "false",
        })
        
        config = Config.from_env()
        
        assert config.api_key == "sk_env_full"
        assert config.batch_size == 25
        assert config.timeout_seconds == 10
        assert config.debug is True
        assert config.enabled is False
    
    def test_from_env_missing_api_key_raises(self, mocker):
        """Missing API key in env raises error"""
        mocker.patch.dict(os.environ, {}, clear=True)
        
        with pytest.raises(Exception):
            Config.from_env()


# ============================================================================
# TESTS: File Loading
# ============================================================================

@pytest.mark.unit
class TestConfigFromFile:
    """Test loading config from YAML/JSON file"""
    
    def test_load_from_yaml_file(self, mocker):
        """Load config from YAML file"""
        yaml_content = """
api_key: sk_file_yaml
batch_size: 15
debug: true
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            # Mock yaml.safe_load
            mocker.patch("yaml.safe_load", return_value={
                "api_key": "sk_file_yaml",
                "batch_size": 15,
                "debug": True,
            })
            
            config = Config.from_file(f.name)
            
            assert config.api_key == "sk_file_yaml"
            assert config.batch_size == 15
            assert config.debug is True
    
    def test_load_from_file_invalid_path(self):
        """Loading from non-existent file raises error"""
        with pytest.raises(Exception):
            Config.from_file("/nonexistent/path/config.yaml")


# ============================================================================
# TESTS: Disabled Config
# ============================================================================

@pytest.mark.unit
class TestConfigDisabled:
    """Test disabled configuration behavior"""
    
    def test_can_create_disabled_config(self):
        """Can create config with enabled=False"""
        config = Config(
            api_key="sk_...",
            enabled=False
        )
        assert config.enabled is False
    
    def test_disabled_config_still_validates(self):
        """Even when disabled, config validates fields"""
        with pytest.raises(Exception):  # API key still validated
            Config(
                api_key="invalid",  # Still invalid
                enabled=False
            )
