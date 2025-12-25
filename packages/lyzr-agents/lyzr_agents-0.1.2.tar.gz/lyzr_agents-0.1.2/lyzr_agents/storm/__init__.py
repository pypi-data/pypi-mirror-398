"""
STORM Agent - Stanford STORM algorithm for long-form article generation.

Usage:
    from lyzr_agents.storm import StormAgent, StormAgentConfig

    agent = StormAgent(
        lyzr_api_key="your-api-key",
        user_id="your-user-id",
    )

    # Sync usage
    result = agent.write("quantum mechanics")
    result.toFile("article.md")

    # Async usage (parallel execution)
    result = await agent.write_async("quantum mechanics")

Test mode:
    from lyzr_agents.storm import StormAgent, test_config

    agent = StormAgent(
        lyzr_api_key="test",
        user_id="test",
        config=test_config(),
    )
    result = agent.write("test topic")  # Returns mock data
"""

from .agent import StormAgent
from .config import StormAgentConfig, test_config
from .events import EventCallback, StormEvent, StormEventType
from .result import StormResult
from .visualizer import StormVisualizer

__all__ = [
    "StormAgent",
    "StormAgentConfig",
    "StormResult",
    "StormEvent",
    "StormEventType",
    "EventCallback",
    "StormVisualizer",
    "test_config",
]
