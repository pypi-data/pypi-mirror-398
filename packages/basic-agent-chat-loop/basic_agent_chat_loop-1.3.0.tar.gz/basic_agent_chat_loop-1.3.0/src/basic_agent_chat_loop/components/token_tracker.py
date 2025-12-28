"""
Token tracking and cost estimation.

Tracks token usage per query and session with model-based cost estimation.
"""



class TokenTracker:
    """Track token usage and cost estimation."""

    # Model pricing (per 1M tokens)
    PRICING = {
        "Claude Sonnet 4.5": {"input": 3.00, "output": 15.00},
        "Sonnet 4.5": {"input": 3.00, "output": 15.00},
        "Claude Sonnet 4": {"input": 3.00, "output": 15.00},
        "Sonnet 4": {"input": 3.00, "output": 15.00},
        "Claude Sonnet 3.5": {"input": 3.00, "output": 15.00},
        "Sonnet 3.5": {"input": 3.00, "output": 15.00},
        "Claude Opus": {"input": 15.00, "output": 75.00},
        "Opus": {"input": 15.00, "output": 75.00},
        "Claude Haiku": {"input": 0.25, "output": 1.25},
        "Haiku": {"input": 0.25, "output": 1.25},
        "GPT-4": {"input": 30.00, "output": 60.00},
        "GPT-4 Turbo": {"input": 10.00, "output": 30.00},
        "GPT-3.5": {"input": 0.50, "output": 1.50},
    }

    def __init__(self, model_name: str = "Unknown"):
        """
        Initialize token tracker.

        Args:
            model_name: Name of the model for pricing
        """
        self.model_name = model_name
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.query_history: list[tuple[int, int]] = []  # List of (input, output) tuples

    def add_usage(self, input_tokens: int, output_tokens: int):
        """
        Add token usage for a query.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.query_history.append((input_tokens, output_tokens))

    def get_total_tokens(self) -> int:
        """Get total tokens (input + output)."""
        return self.total_input_tokens + self.total_output_tokens

    def get_cost(self) -> float:
        """
        Calculate estimated cost in USD.

        Returns:
            Estimated cost in dollars
        """
        # Try to find pricing for this model
        pricing = None
        for model_key in self.PRICING:
            if model_key.lower() in self.model_name.lower():
                pricing = self.PRICING[model_key]
                break

        if not pricing:
            return 0.0  # Unknown model

        # Calculate cost (pricing is per 1M tokens)
        input_cost = (self.total_input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.total_output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def format_cost(self) -> str:
        """Format cost as currency string."""
        cost = self.get_cost()
        if cost < 0.01:
            return f"${cost:.4f}"
        elif cost < 1.0:
            return f"${cost:.3f}"
        else:
            return f"${cost:.2f}"

    def format_tokens(self, tokens: int) -> str:
        """Format token count with K/M suffix."""
        if tokens >= 1_000_000:
            return f"{tokens / 1_000_000:.1f}M"
        elif tokens >= 1_000:
            return f"{tokens / 1_000:.1f}K"
        else:
            return str(tokens)
