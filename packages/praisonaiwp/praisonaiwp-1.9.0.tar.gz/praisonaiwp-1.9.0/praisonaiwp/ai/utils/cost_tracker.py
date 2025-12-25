"""Cost tracking for AI operations"""
from typing import Dict, Optional


class CostTracker:
    """Track API costs for different models"""

    # Pricing per 1K tokens (as of Nov 2024)
    PRICING = {
        'gpt-4o-mini': {
            'input': 0.00015,   # $0.15 per 1M tokens
            'output': 0.0006,   # $0.60 per 1M tokens
        },
        'gpt-4o': {
            'input': 0.005,     # $5.00 per 1M tokens
            'output': 0.015,    # $15.00 per 1M tokens
        },
        'gpt-4-turbo': {
            'input': 0.01,
            'output': 0.03,
        },
        'gpt-3.5-turbo': {
            'input': 0.0005,
            'output': 0.0015,
        },
    }

    def __init__(self):
        """Initialize cost tracker"""
        self.total_cost = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.generations = []

    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for a generation

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            float: Cost in USD
        """
        if model not in self.PRICING:
            # Default to gpt-4o-mini pricing if unknown
            model = 'gpt-4o-mini'

        pricing = self.PRICING[model]

        # Convert per-1K pricing to per-token
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']

        total_cost = input_cost + output_cost

        return round(total_cost, 6)

    def track(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Track a generation

        Args:
            model: Model name
            input_tokens: Input tokens used
            output_tokens: Output tokens generated
            metadata: Optional metadata

        Returns:
            dict: Generation info with cost
        """
        cost = self.calculate_cost(model, input_tokens, output_tokens)

        generation = {
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'cost': cost,
            'metadata': metadata or {}
        }

        self.generations.append(generation)
        self.total_cost += cost
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        return generation

    def get_summary(self) -> Dict:
        """Get cost summary

        Returns:
            dict: Summary of all tracked generations
        """
        return {
            'total_generations': len(self.generations),
            'total_cost': round(self.total_cost, 6),
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'total_tokens': self.total_input_tokens + self.total_output_tokens,
            'average_cost': (
                round(self.total_cost / len(self.generations), 6)
                if self.generations else 0.0
            )
        }

    def reset(self):
        """Reset tracker"""
        self.total_cost = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.generations = []
