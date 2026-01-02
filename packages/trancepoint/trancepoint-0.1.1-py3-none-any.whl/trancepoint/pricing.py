"""
LLM Pricing Table

Prices from official API documentation (as of Dec 2024)
Format: price per 1,000 tokens
"""

LLM_PRICING = {
    "openai": {
        "gpt-4": {
            "input": 0.03,          # $0.03 per 1K input tokens
            "output": 0.06,         # $0.06 per 1K output tokens
        },
        "gpt-4-turbo": {
            "input": 0.01,
            "output": 0.03,
        },
        "gpt-4o": {
            "input": 0.005,
            "output": 0.015,
        },
        "gpt-3.5-turbo": {
            "input": 0.0005,        # Cheapest OpenAI option
            "output": 0.0015,
        },
        "gpt-3.5-turbo-16k": {
            "input": 0.003,
            "output": 0.004,
        },
    },
    "anthropic": {
        "claude-3-opus-20240229": {
            "input": 0.015,
            "output": 0.075,        # Most expensive Anthropic
        },
        "claude-3-sonnet-20240229": {
            "input": 0.003,
            "output": 0.015,
        },
        "claude-3-haiku-20240307": {
            "input": 0.00025,       # Cheapest Claude
            "output": 0.00125,
        },
    },
    "google": {
        "gemini-pro": {
            "input": 0.001,
            "output": 0.002,
        },
        "gemini-1.5-pro": {
            "input": 0.0035,
            "output": 0.0105,
        },
    },
}

# Default fallback pricing (generic $0.01 per 1K tokens)
DEFAULT_PRICING = {
    "input": 0.01,
    "output": 0.01,
}
