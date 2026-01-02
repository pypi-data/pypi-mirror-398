# agent_observability/decorator.py
"""
Main decorator for observability with token counting and cost tracking.

This decorator:
1. Accepts llm_model and llm_provider parameters
2. Delegates to wrapper.py for actual implementation
3. Handles both sync and async functions
4. Auto-detects config from environment
"""

import functools
import inspect
import logging
from typing import Callable, Any, Optional, TypeVar

from .config import Config
from .wrapper import wrap_agent_function

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def observe(
    config: Optional[Config] = None,
    agent_name: Optional[str] = None,
    llm_model: Optional[str] = None,  # ← NEW: Model name (e.g., "gpt-4")
    llm_provider: str = "openai",     # ← NEW: Provider (e.g., "openai", "anthropic")
    enabled: Optional[bool] = None,
) -> Callable[[F], F]:
    """
    Decorator for instrumenting agent functions with observability.
    
    NOW INCLUDES: Token counting and cost calculation for LLMs
    
    This decorator:
    1. Wraps your function with automatic event creation
    2. Counts input and output tokens based on LLM model
    3. Calculates LLM cost automatically
    4. Preserves function signature and behavior
    5. Handles both sync and async functions
    
    Args:
        config: Config instance. If None, loads from environment.
        agent_name: Custom name for this agent. Defaults to function name.
        llm_model: LLM model name (e.g., "gpt-4", "gpt-3.5-turbo", "claude-3-opus")
        llm_provider: LLM provider (default "openai", can be "anthropic", "google")
        enabled: Override config.enabled setting for this agent.
    
    Returns:
        Callable: Decorator function
    
    Example 1: Basic usage with gpt-4
        from agent_observability.decorator import observe
        
        @observe(agent_name="researcher", llm_model="gpt-4")
        def research_agent(query: str) -> dict:
            # Agent code here
            return {"results": ["paper1", "paper2"]}
        
        result = research_agent("What is AI?")
        # ↓ Automatically:
        # 1. Counts input tokens
        # 2. Executes agent
        # 3. Counts output tokens
        # 4. Calculates cost: (input_tokens/1000 * $0.03) + (output_tokens/1000 * $0.06)
        # 5. Sends events with cost to backend
    
    Example 2: Using cheaper model (gpt-3.5-turbo)
        @observe(agent_name="analyzer", llm_model="gpt-3.5-turbo")
        def analyze_agent(data: str) -> dict:
            return {"analysis": "..."}
        
        # Cost 100x cheaper than gpt-4!
    
    Example 3: Using Anthropic Claude
        @observe(
            agent_name="writer",
            llm_model="claude-3-opus-20240229",
            llm_provider="anthropic"
        )
        def write_agent(topic: str) -> str:
            return "..."
    
    Example 4: Custom config + disable for testing
        config = Config.from_file("config.yaml")
        
        @observe(config=config, llm_model="gpt-4", enabled=False)
        def test_agent(x):
            return x * 2  # Won't send events to backend
    """
    
    def decorator(func: F) -> F:
        """
        The actual decorator that wraps the function.
        
        Args:
            func: The function to decorate
        
        Returns:
            Callable: Wrapped function
        """
        
        # Determine config to use
        if config is None:
            try:
                final_config = Config.from_env()
            except Exception as e:
                logger.warning(
                    f"Failed to load Config from environment: {e}. "
                    f"Observability disabled for {func.__name__}"
                )
                # Create disabled config so decorator doesn't break
                final_config = Config(
                    api_key="sk_dummy_disabled",
                    enabled=False
                )
        else:
            final_config = config
        
        # Override enabled if specified
        if enabled is not None:
            config_dict = final_config.to_dict()
            config_dict["enabled"] = enabled
            final_config = Config(**config_dict)
        
        final_agent_name = agent_name or func.__name__
        
        # Check if async
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            # Async function wrapper
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                """Async wrapper that tracks execution with token counting."""
                wrapped_func = wrap_agent_function(
                    func,
                    final_config,
                    agent_name=final_agent_name,
                    llm_model=llm_model,           # ← Pass to wrapper
                    llm_provider=llm_provider,     # ← Pass to wrapper
                )
                # wrapped_func is still async, can await it
                return await wrapped_func(*args, **kwargs)
            
            return async_wrapper  # type: ignore
        
        else:
            # Sync function wrapper
            wrapped_func = wrap_agent_function(
                func,
                final_config,
                agent_name=final_agent_name,
                llm_model=llm_model,              # ← Pass to wrapper
                llm_provider=llm_provider,        # ← Pass to wrapper
            )
            return wrapped_func  # type: ignore
    
    return decorator


def observe_class(
    config: Optional[Config] = None,
    enabled: Optional[bool] = None,
) -> Callable:
    """
    Decorator for instrumenting all methods of a class.
    
    This applies the @observe decorator to all public methods of a class.
    Useful for instrumenting entire agent classes or tool classes.
    
    Args:
        config: Config instance. If None, loads from environment.
        enabled: Override config.enabled setting.
    
    Returns:
        Callable: Decorator function
    
    Example:
        from agent_observability.decorator import observe_class
        
        @observe_class()
        class ResearchAgent:
            def search(self, query: str) -> list:
                return ["paper1", "paper2"]
            
            def analyze(self, papers: list) -> dict:
                return {"count": len(papers)}
        
        agent = ResearchAgent()
        results = agent.search("AI")       # Tracked!
        analysis = agent.analyze(results)  # Tracked!
    
    Note:
        - Skips private methods (starting with _)
        - Skips special methods (__init__, __str__, etc.)
        - Skips static methods and class methods
    """
    
    def class_decorator(cls):
        """Decorate all methods of a class."""
        
        if config is None:
            try:
                final_config = Config.from_env()
            except Exception as e:
                logger.warning(
                    f"Failed to load Config from environment: {e}. "
                    f"Observability disabled for {cls.__name__}"
                )
                final_config = Config(
                    api_key="sk_dummy_disabled",
                    enabled=False
                )
        else:
            final_config = config
        
        # Override enabled if specified
        if enabled is not None:
            config_dict = final_config.to_dict()
            config_dict["enabled"] = enabled
            final_config = Config(**config_dict)
        
        for attr_name in dir(cls):
            # Skip private/special methods
            if attr_name.startswith("_"):
                continue
            
            # Get the attribute
            try:
                attr = getattr(cls, attr_name)
            except AttributeError:
                continue
            
            # Skip non-callables
            if not callable(attr):
                continue
            
            # Skip static/class methods
            if isinstance(inspect.getattr_static(cls, attr_name), (staticmethod, classmethod)):
                continue
            
            # Create agent name for this method
            method_agent_name = f"{cls.__name__}.{attr_name}"
            
            # Decorate the method
            decorated = observe(
                config=final_config,
                agent_name=method_agent_name,
                enabled=enabled
            )(attr)
            
            # Set the decorated method back on the class
            setattr(cls, attr_name, decorated)
        
        return cls
    
    return class_decorator
