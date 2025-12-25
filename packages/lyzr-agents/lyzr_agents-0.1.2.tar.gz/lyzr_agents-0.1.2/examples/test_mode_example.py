"""
Test Mode Example - Run STORM without API calls.

This demonstrates the full STORM flow with mock data,
useful for testing the event system and React Flow visualization.
"""

import json
from src.agents import StormAgent, StormEvent, test_config


def on_event(event: StormEvent):
    """Print events as they occur."""
    status_icons = {"running": "⏳", "completed": "✅", "failed": "❌"}
    icon = status_icons.get(event.status, "•")
    indent = "    " if event.parallel_group else "  "

    print(f"{indent}{icon} {event.step_name or event.event_type.value}")


def main():
    print("=" * 60)
    print("🧪 STORM Agent - TEST MODE")
    print("=" * 60)
    print()

    # Create agent in test mode - no API calls will be made
    agent = StormAgent(
        lyzr_api_key="test",
        user_id="test",
        config=test_config(),  # All agent IDs set to "test"
        no_of_personas=3,
        no_of_questions=2,
        no_of_sections=3,
        on_event=on_event,
    )

    print(f"📝 Test Mode: {agent._test_mode}")
    print()

    # Run the STORM algorithm with mock responses
    result = agent.write("Artificial Intelligence")

    print()
    print("=" * 60)
    print("📊 RESULTS")
    print("=" * 60)

    if result.success:
        print(f"\n✅ Success!")
        print(f"\n📋 Summary:")
        print(f"   Personas: {len(result.personas)}")
        for i, p in enumerate(result.personas):
            print(f"      {i+1}. {p}")

        print(f"\n   Questions: {sum(len(q) for q in result.questions.values())}")
        print(f"   Research answers: {len(result.research)}")
        print(f"   Sections: {len(result.sections)}")
        print(f"   Total events: {len(result.events)}")

        # Show outline
        print(f"\n📑 Outline:")
        for i, section in enumerate(result.outline):
            print(f"      {i+1}. {section}")

        # Show article preview
        print(f"\n📄 Article Preview (first 500 chars):")
        print("-" * 40)
        print(result.article[:500])
        print("...")

        # Show React Flow graph data
        graph = result.get_graph_data()
        print(f"\n🔗 React Flow Graph:")
        print(f"   Nodes: {len(graph['nodes'])}")
        print(f"   Edges: {len(graph['edges'])}")

        # Save graph data for frontend
        with open("output/graph_data.json", "w") as f:
            # Convert events for JSON serialization
            serializable_graph = {
                "nodes": graph["nodes"],
                "edges": graph["edges"],
            }
            json.dump(serializable_graph, f, indent=2, default=str)
        print(f"\n   Graph data saved to output/graph_data.json")

        # Save article
        result.toFile("output/test_article.md")
        print(f"   Article saved to output/test_article.md")

    else:
        print(f"\n❌ Error: {result.error}")


if __name__ == "__main__":
    import os
    os.makedirs("output", exist_ok=True)
    main()
