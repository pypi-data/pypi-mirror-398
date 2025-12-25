"""
Run STORM Agent with default Lyzr agents.

This example uses all default agent IDs configured for Lyzr platform.
"""

import sys
from src.agents import StormAgent, StormAgentConfig, StormEvent, StormEventType


def on_event(event: StormEvent):
    """Display events as they occur."""

    # Status icons
    icons = {
        "running": "⏳",
        "completed": "✅",
        "failed": "❌",
    }
    icon = icons.get(event.status, "•")

    # Indent parallel operations
    indent = "    " if event.parallel_group else "  "

    # Color-code by event type
    step = event.step_name or event.event_type.value

    # Print event
    print(f"{indent}{icon} {step}")
    sys.stdout.flush()

    # Show details for key events
    if event.event_type == StormEventType.PERSONA_CREATED:
        persona = event.data.get("persona", "")[:60]
        print(f"{indent}   └─ {persona}")

    elif event.event_type == StormEventType.QUESTION_CREATED:
        question = event.data.get("question", "")[:60]
        print(f"{indent}   └─ {question}")

    elif event.event_type == StormEventType.RESEARCH_ANSWER_RECEIVED:
        length = event.data.get("answer_length", 0)
        print(f"{indent}   └─ Received {length} chars")

    elif event.event_type == StormEventType.SECTION_WRITTEN:
        section = event.data.get("section", "")
        length = event.data.get("length", 0)
        print(f"{indent}   └─ {section} ({length} chars)")

    elif event.event_type == StormEventType.STORM_COMPLETED:
        length = event.data.get("article_length", 0)
        print(f"\n{'='*50}")
        print(f"📄 Article generated: {length} characters")


def main():
    print("=" * 60)
    print("🌩️  STORM Agent - Long-form Article Generator")
    print("=" * 60)
    print()

    # Create agent with all default Lyzr agent IDs
    agent = StormAgent(
        lyzr_api_key="sk-default-obhGvAo6gG9YT9tu6ChjyXLqnw7TxSGY",
        user_id="demo@lyzr.ai",
        config=StormAgentConfig(),  # All defaults!
        no_of_personas=3,
        no_of_questions=2,
        no_of_sections=4,
        on_event=on_event,
    )

    # Topic to write about
    topic = "The Future of Artificial Intelligence"

    print(f"📝 Topic: {topic}")
    print(f"👥 Personas: {agent.no_of_personas}")
    print(f"❓ Questions per persona: {agent.no_of_questions}")
    print(f"📑 Sections: {agent.no_of_sections}")
    print()
    print("Starting STORM pipeline...")
    print("-" * 60)

    # Generate article
    result = agent.write(topic)

    print("-" * 60)

    if result.success:
        # Save article
        result.toFile("output/storm_article.md")
        print(f"\n✅ Article saved to: output/storm_article.md")

        # Show summary
        print(f"\n📊 Summary:")
        print(f"   • Personas: {len(result.personas)}")
        print(f"   • Questions: {sum(len(q) for q in result.questions.values())}")
        print(f"   • Research answers: {len(result.research)}")
        print(f"   • Sections: {len(result.sections)}")
        print(f"   • Total events: {len(result.events)}")

        # Show personas
        print(f"\n👥 Personas used:")
        for i, p in enumerate(result.personas, 1):
            print(f"   {i}. {p[:70]}")

        # Show outline
        print(f"\n📑 Article outline:")
        for i, section in enumerate(result.outline, 1):
            print(f"   {i}. {section}")

        # Preview article
        print(f"\n📄 Article preview:")
        print("-" * 40)
        print(result.article[:800])
        print("...")

        # Get graph data for React Flow
        graph = result.get_graph_data()
        print(f"\n🔗 React Flow graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")

    else:
        print(f"\n❌ Error: {result.error}")


if __name__ == "__main__":
    import os
    os.makedirs("output", exist_ok=True)
    main()
