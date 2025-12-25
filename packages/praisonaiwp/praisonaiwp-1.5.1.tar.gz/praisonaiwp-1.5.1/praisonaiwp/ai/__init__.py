"""PraisonAI integration for WordPress CLI tool"""

# Check if PraisonAI is available
try:
    from praisonaiagents import Agent, PraisonAIAgents, Task
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    Agent = None
    Task = None
    PraisonAIAgents = None


def check_ai_available():
    """Check if AI features are available"""
    if not AI_AVAILABLE:
        raise ImportError(
            "AI features require praisonaiagents. "
            "Install with: pip install 'praisonaiwp[ai]'"
        )
    return True


__all__ = ['AI_AVAILABLE', 'check_ai_available', 'Agent', 'Task', 'PraisonAIAgents']
