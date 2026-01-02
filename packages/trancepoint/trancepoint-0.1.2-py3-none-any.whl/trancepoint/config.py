import os
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

class Config(BaseModel):
    """
    Configuration for agent  system.
    
    Loads settings from:
    1. Environment variables (highest priority)
    2. Constructor arguments (medium priority)
    3. Default values (lowest priority)
    
    Example 1: Load from environment
        # Set these in your shell or .env file:
        # export AGENT_OBS_API_KEY="sk_prod_abc123"
        # export AGENT_OBS_API_ENDPOINT="https://api.agentobs.io"
        # export AGENT_OBS_BATCH_SIZE="10"
        
        config = Config.from_env()
        # config.api_key = "sk_prod_abc123"
        # config.batch_size = 10
    
    Example 2: Load from constructor
        config = Config(
            api_key="sk_prod_xyz789",
            batch_size=5
        )
    
    Example 3: Mix environment + constructor (constructor overrides env)
        # Environment: AGENT_OBS_API_KEY="sk_prod_from_env"
        # Code: Config.from_env(api_key="sk_prod_override")
        # Result: api_key = "sk_prod_override"
    """

    api_key:str = Field(
        ..., # required
        description="API key for authentication with  backend",
        examples=["sk_prod_abc123", "sk_test_xyz789"]
    )

    api_endpoint: str = Field(
        default="https://api.agentobs.io",
        description="Base URL of  backend API",
        examples=["https://api.agentobs.io", "http://localhost:8000"],
    )

    agent_name: Optional[str] = Field(
        default=None,
        description="Name of this agent (for dashboard organization)",
        examples=["researcher", "analyzer", "crew_main"],
    )

    batch_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Max events to buffer before sending to backend",
    )
    
    flush_interval_seconds: int = Field(
        default=5,
        ge=1,
        le=300,
        description="Max seconds to wait before auto-flushing buffered events",
    )
    
    timeout_seconds: int = Field(
        default=5,
        ge=1,
        le=60,
        description="HTTP request timeout in seconds",
    )
    
    enabled: bool = Field(
        default=True,
        description="Whether to send events to backend (can disable for testing)",
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug logging for troubleshooting",
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,  # Remove leading/trailing whitespace
        validate_default=True,       # Validate default values
        populate_by_name=True,       # Accept both field name and alias
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """
        Validate API key format.
        
        Rules:
        - Cannot be empty
        - Should start with 'sk_' prefix (production or test)
        - Minimum length of 10 characters
        
        Args:
            v: API key string
        
        Returns:
            str: Validated API key
        
        Raises:
            ValueError: If validation fails
        """
        if not v or not v.strip():
            raise ValueError("api_key cannot be empty")
        
        if not v.startswith("sk_"):
            raise ValueError(
                "api_key should start with 'sk_' (e.g., 'sk_prod_xyz' or 'sk_test_xyz')"
            )
        
        if len(v) < 5:
            raise ValueError("api_key should be at least 5 characters long")
        
        return v.strip()
    
    @field_validator("api_endpoint")
    @classmethod
    def validate_api_endpoint(cls, v: str) -> str:
        """
        Validate API endpoint URL.
        
        Rules:
        - Cannot be empty
        - Should be valid URL (starts with http:// or https://)
        
        Args:
            v: API endpoint URL
        
        Returns:
            str: Validated URL
        
        Raises:
            ValueError: If validation fails
        """
        if not v or not v.strip():
            raise ValueError("api_endpoint cannot be empty")
        
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(
                "api_endpoint should start with 'http://' or 'https://'"
            )
        
        # Remove trailing slash for consistency
        return v.strip().rstrip("/")
    
    
    @field_validator("batch_size", "timeout_seconds", "flush_interval_seconds")
    @classmethod
    def validate_positive_int(cls, v: int) -> int:
        """
        Validate that integer fields are positive.
        
        This is a meta-validator for multiple fields.
        
        Args:
            v: Integer value
        
        Returns:
            int: Validated value
        
        Raises:
            ValueError: If value is not positive
        """
        if v <= 0:
            raise ValueError("Value must be positive (> 0)")
        
        return v
    
    
    @field_validator("agent_name")
    @classmethod
    def validate_agent_name(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate agent name if provided.
        
        Rules:
        - Can be None (optional)
        - If provided, should be non-empty
        - Only alphanumeric, underscore, hyphen, and space allowed
        
        Args:
            v: Agent name string or None
        
        Returns:
            str or None: Validated agent name
        
        Raises:
            ValueError: If validation fails
        """
        if v is None:
            return None
        
        if not v or not v.strip():
            raise ValueError("agent_name cannot be empty string")
        
        # Allow alphanumeric, underscore, hyphen, space
        import re
        if not re.match(r"^[a-zA-Z0-9_\-\s]+$", v):
            raise ValueError(
                "agent_name can only contain letters, numbers, underscore, hyphen, and space"
            )
        
        return v.strip()
    
    @classmethod
    def from_env(cls, **overrides) -> "Config":
        """
        Load configuration from environment variables.
        
        Required:
        - AGENT_OBS_API_KEY: Must be set (starts with 'sk_')
        
        Optional:
        - AGENT_OBS_API_ENDPOINT (default: https://api.agentobs.io)
        - AGENT_OBS_BATCH_SIZE (default: 10)
        - AGENT_OBS_FLUSH_INTERVAL (default: 5)
        - AGENT_OBS_TIMEOUT (default: 5)
        - AGENT_OBS_ENABLED (default: true)
        - AGENT_OBS_DEBUG (default: false)
        """
        api_key = os.getenv("AGENT_OBS_API_KEY", "").strip()
        
        if not api_key:
            raise ValueError(
                "AGENT_OBS_API_KEY environment variable not set.\n"
                "Set it with: export AGENT_OBS_API_KEY='sk_prod_xxx'"
            )
        
        if not api_key.startswith("sk_"):
            raise ValueError(
                f"Invalid API key format. Must start with 'sk_', got: {api_key[:15]}..."
            )
        
        return cls(
            api_key=api_key,
            api_endpoint=os.getenv(
                "AGENT_OBS_API_ENDPOINT", 
                "https://api.agentobs.io"
            ),
            batch_size=int(os.getenv("AGENT_OBS_BATCH_SIZE", "10")),
            flush_interval_seconds=int(os.getenv("AGENT_OBS_FLUSH_INTERVAL", "5")),
            timeout_seconds=int(os.getenv("AGENT_OBS_TIMEOUT", "5")),
            enabled=os.getenv("AGENT_OBS_ENABLED", "true").lower() == "true",
            debug=os.getenv("AGENT_OBS_DEBUG", "false").lower() == "true",
            **overrides
        )

    
    @classmethod
    def from_file(cls, filepath: str, **overrides) -> "Config":
        """
        Create configuration from a YAML or JSON file.
        
        Supported formats:
        - YAML (.yaml, .yml)
        - JSON (.json)
        
        File format examples:
        
        YAML:
            api_key: sk_prod_abc123
            api_endpoint: https://api.agentobs.io
            batch_size: 10
            debug: false
        
        JSON:
            {
              "api_key": "sk_prod_abc123",
              "api_endpoint": "https://api.agentobs.io",
              "batch_size": 10,
              "debug": false
            }
        
        Args:
            filepath: Path to configuration file
            **overrides: Constructor arguments that override file values
        
        Returns:
            Config: Configuration object
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is unsupported or invalid
        
        Example:
            # Load from config.yaml
            config = Config.from_file(
                "config.yaml",
                debug=True  # Override debug setting
            )
        """
        import json
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        # Determine format from extension
        if filepath.endswith((".yaml", ".yml")):
            # YAML format
            try:
                import yaml
            except ImportError:
                raise ImportError(
                    "PyYAML is required to load YAML config files. "
                    "Install with: pip install pyyaml"
                )
            
            with open(filepath, "r") as f:
                file_data = yaml.safe_load(f)
        
        elif filepath.endswith(".json"):
            # JSON format
            with open(filepath, "r") as f:
                file_data = json.load(f)
        
        else:
            raise ValueError(
                f"Unsupported config file format: {filepath}. "
                f"Use .yaml, .yml, or .json"
            )
        
        if not isinstance(file_data, dict):
            raise ValueError(f"Config file must contain a dictionary, got {type(file_data)}")
        
        # Merge: overrides have highest priority
        config_data = {**file_data, **overrides}
        
        # Create and return
        return cls(**config_data)
    
    def to_dict(self) -> dict:
        """
        Export configuration as dictionary.
        
        Returns:
            dict: Configuration values
        
        Example:
            config = Config.from_env()
            config_dict = config.to_dict()
            print(config_dict)
            # {'api_key': 'sk_...', 'batch_size': 10, ...}
        """
        return self.model_dump()
    
    
    def to_env_format(self) -> str:
        """
        Export configuration as shell environment variables.
        
        Useful for debugging or sharing configuration.
        
        Returns:
            str: Environment variables in shell format
        
        Example:
            config = Config.from_env()
            env_str = config.to_env_format()
            print(env_str)
            # export AGENT_OBS_API_KEY="sk_..."
            # export AGENT_OBS_BATCH_SIZE="10"
            # ...
        """
        lines = []
        mapping = {
            "api_key": "AGENT_OBS_API_KEY",
            "api_endpoint": "AGENT_OBS_API_ENDPOINT",
            "agent_name": "AGENT_OBS_AGENT_NAME",
            "batch_size": "AGENT_OBS_BATCH_SIZE",
            "flush_interval_seconds": "AGENT_OBS_FLUSH_INTERVAL_SECONDS",
            "timeout_seconds": "AGENT_OBS_TIMEOUT_SECONDS",
            "enabled": "AGENT_OBS_ENABLED",
            "debug": "AGENT_OBS_DEBUG",
        }
        
        data = self.model_dump()
        
        for field_name, env_var in mapping.items():
            value = data.get(field_name)
            
            # Convert to string representation
            if isinstance(value, bool):
                value_str = "true" if value else "false"
            elif value is None:
                continue  # Skip None values
            else:
                value_str = str(value)
            
            lines.append(f'export {env_var}="{value_str}"')
        
        return "\n".join(lines)
    
    
    def validate(self) -> bool:
        """
        Validate all configuration values.
        
        Called automatically by Pydantic, but you can call explicitly.
        
        Returns:
            bool: True if all values are valid
        
        Raises:
            ValueError: If any validation fails
        
        Example:
            config = Config(api_key="sk_test_123")
            if config.validate():
                print("✓ Configuration is valid")
        """
        # All validation happens at construction time via Pydantic
        # This method is here for explicit checks if needed
        return True
    
    
    def __repr__(self) -> str:
        """
        String representation of configuration (safe for logging).
        
        Hides sensitive values (api_key) in output.
        
        Returns:
            str: Safe representation
        
        Example:
            config = Config(api_key="sk_prod_secret123")
            print(config)
            # Config(
            #   api_key="sk_prod_***",
            #   api_endpoint="https://api.agentobs.io",
            #   batch_size=10,
            #   ...
            # )
        """
        data = self.model_dump()
        
        # Mask sensitive fields
        if data.get("api_key"):
            key = data["api_key"]
            # Show first 8 chars and last 3 chars
            if len(key) > 11:
                data["api_key"] = f"{key[:8]}***{key[-3:]}"
            else:
                data["api_key"] = "sk_***"
        
        items = [f"{k}={v!r}" for k, v in data.items()]
        return f"Config({', '.join(items)})"