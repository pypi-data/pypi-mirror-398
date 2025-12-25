"""Configuration for STORM agent."""

from dataclasses import dataclass


@dataclass
class StormAgentConfig:
    """Configuration for STORM agent Lyzr agent IDs.

    All agent IDs have defaults configured for Lyzr platform.
    You can override any of them as needed.

    Example:
        # Use all defaults
        config = StormAgentConfig()

        # Override specific agents
        config = StormAgentConfig(
            research_agent_id="your-custom-research-agent"
        )
    """

    persona_generator_agent_id: str = "6947ba3881c8a74f1ca95fd4"
    question_generator_agent_id: str = "6947baab2be72f04a7d6440c"
    outline_generator_agent_id: str = "6947bb142be72f04a7d6449e"
    section_generator_agent_id: str = "6947bb786363be71980e845d"
    research_agent_id: str = "6946a84681c8a74f1ca95008"


def test_config() -> StormAgentConfig:
    """Create a test configuration with dummy agent IDs.

    Use this for testing without making API calls.

    Example:
        agent = StormAgent(
            lyzr_api_key="test",
            user_id="test",
            config=test_config(),
        )
        result = agent.write("Test topic")  # Returns mock data
    """
    return StormAgentConfig(
        research_agent_id="test",
        persona_generator_agent_id="test",
        question_generator_agent_id="test",
        outline_generator_agent_id="test",
        section_generator_agent_id="test",
    )
