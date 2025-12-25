"""
Example usage of StormAgent with event callbacks for React Flow visualization.
"""

from src.agents import (
    StormAgent,
    StormAgentConfig,
    StormEvent,
    StormEventType,
)


def on_event(event: StormEvent):
    """Callback that receives all events in real-time.

    You can extend this to:
    - Send events via WebSocket to a React frontend
    - Stream via Server-Sent Events (SSE)
    - Log to a file or database
    """
    status_icons = {
        "running": "⏳",
        "completed": "✅",
        "failed": "❌",
    }
    icon = status_icons.get(event.status, "•")

    # Show parallel operations with indentation
    indent = "  " if event.parallel_group else ""

    print(f"{indent}{icon} [{event.event_type.value}] {event.step_name or ''}")

    # Show extra data for certain events
    if event.event_type == StormEventType.PERSONA_CREATED:
        print(f"{indent}   → {event.data.get('persona', '')[:50]}")
    elif event.event_type == StormEventType.QUESTION_CREATED:
        print(f"{indent}   → {event.data.get('question', '')[:50]}")
    elif event.event_type == StormEventType.STORM_COMPLETED:
        print(f"\n📄 Article length: {event.data.get('article_length', 0)} chars")


def main():
    # Configure the Lyzr agent IDs for each STORM step
    config = StormAgentConfig(
        research_agent_id="your-research-agent-id",
        persona_generator_agent_id="your-persona-agent-id",
        question_generator_agent_id="your-question-agent-id",
        outline_generator_agent_id="your-outline-agent-id",
        section_generator_agent_id="your-section-agent-id",
    )

    # Create the STORM agent with event callback
    agent = StormAgent(
        lyzr_api_key="your-lyzr-api-key",
        user_id="user@example.com",
        config=config,
        no_of_personas=3,
        no_of_questions=3,
        no_of_sections=5,
        context="Focus on practical applications and recent developments",
        on_event=on_event,  # Real-time event callback
    )

    print("=" * 60)
    print("STORM Agent - Generating Article")
    print("=" * 60)
    print()

    # Generate article with fluent API
    result = agent.write("Quantum Computing")

    if result.success:
        # Save to file
        result.toFile("output/quantum_computing.md")
        print(f"\n✅ Article saved to output/quantum_computing.md")

        # Get React Flow graph data
        graph_data = result.get_graph_data()
        print(f"\n📊 Graph data: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")

        # Print summary
        print(f"\n📋 Summary:")
        print(f"   Personas: {len(result.personas)}")
        print(f"   Questions: {sum(len(q) for q in result.questions.values())}")
        print(f"   Sections: {len(result.sections)}")
        print(f"   Total events: {len(result.events)}")
    else:
        print(f"\n❌ Error: {result.error}")


async def main_async():
    """Async version with parallel execution."""
    import asyncio

    config = StormAgentConfig(
        research_agent_id="your-research-agent-id",
        persona_generator_agent_id="your-persona-agent-id",
        question_generator_agent_id="your-question-agent-id",
        outline_generator_agent_id="your-outline-agent-id",
        section_generator_agent_id="your-section-agent-id",
    )

    agent = StormAgent(
        lyzr_api_key="your-lyzr-api-key",
        user_id="user@example.com",
        config=config,
        on_event=on_event,
    )

    # Async execution with parallel API calls
    result = await agent.write_async("Artificial Intelligence")

    if result.success:
        result.toFile("output/ai_article.md")
        print(f"\n✅ Article saved!")


# Example: React Flow integration
def get_react_flow_graph(result):
    """Convert StormResult to React Flow format.

    Use this to send graph data to your React frontend.
    """
    graph = result.get_graph_data()

    # Example: Add layout positions (you'd use dagre or similar in React)
    y_positions = {}
    for i, node in enumerate(graph["nodes"]):
        event_type = node["data"]["event_type"]

        # Group by event type for vertical layout
        if event_type not in y_positions:
            y_positions[event_type] = len(y_positions) * 150

        node["position"] = {
            "x": (i % 5) * 200,  # Spread horizontally
            "y": y_positions[event_type],
        }

    return graph


# Example: WebSocket streaming
class WebSocketEventHandler:
    """Example handler for streaming events to a WebSocket client."""

    def __init__(self, websocket):
        self.websocket = websocket

    async def handle_event(self, event: StormEvent):
        """Send event to connected WebSocket client."""
        import json

        message = {
            "type": "storm_event",
            "payload": event.to_dict(),
        }
        await self.websocket.send(json.dumps(message))


if __name__ == "__main__":
    main()

    # For async:
    # import asyncio
    # asyncio.run(main_async())
