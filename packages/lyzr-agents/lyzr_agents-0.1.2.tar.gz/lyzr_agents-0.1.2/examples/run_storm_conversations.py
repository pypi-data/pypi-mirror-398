"""
Run STORM with TRUE PARALLEL per-persona conversations.

Each expert has their own Q&A session running in parallel:
┌─────────────────┬─────────────────┬─────────────────┐
│ EXPERT 1        │ EXPERT 2        │ EXPERT 3        │
│ Q1 → Research   │ Q1 → Research   │ Q1 → Research   │
│ Q2 → Research   │ Q2 → Research   │ Q2 → Research   │
│ (follow-ups!)   │ (follow-ups!)   │ (follow-ups!)   │
└─────────────────┴─────────────────┴─────────────────┘
              All running simultaneously!
"""

import asyncio
import sys
import time
from src.agents import StormAgent, StormAgentConfig, StormEvent, StormEventType, test_config


start_time = None


def on_event(event: StormEvent):
    """Display events with timing and conversation grouping."""
    global start_time

    if start_time is None:
        start_time = time.time()

    elapsed = time.time() - start_time
    icons = {"running": "⏳", "completed": "✅", "failed": "❌"}
    icon = icons.get(event.status, "•")
    step = event.step_name or event.event_type.value

    # Show conversation structure
    if event.event_type == StormEventType.PERSONA_CONVERSATION_STARTED:
        print(f"\n[{elapsed:6.1f}s] ┌── {icon} {step}")
        print(f"          │    Persona: {event.data.get('persona', '')[:40]}")
    elif event.event_type == StormEventType.PERSONA_CONVERSATION_COMPLETED:
        chars = event.data.get('total_research_chars', 0)
        print(f"[{elapsed:6.1f}s] └── {icon} {step} ({chars} chars researched)")
    elif event.event_type in [StormEventType.QUESTION_GENERATION_STARTED,
                               StormEventType.QUESTION_CREATED,
                               StormEventType.RESEARCH_STARTED,
                               StormEventType.RESEARCH_ANSWER_RECEIVED]:
        # Inside conversation
        detail = ""
        if event.event_type == StormEventType.QUESTION_CREATED:
            detail = f" → {event.data.get('question', '')[:40]}..."
        elif event.event_type == StormEventType.RESEARCH_ANSWER_RECEIVED:
            detail = f" → {event.data.get('answer_length', 0)} chars"
        print(f"[{elapsed:6.1f}s]     │ {icon} {step}{detail}")
    elif event.event_type == StormEventType.STORM_COMPLETED:
        total = time.time() - start_time
        print(f"\n{'='*55}")
        print(f"⚡ Completed in {total:.1f}s with PARALLEL conversations!")
    else:
        indent = "    " if event.parallel_group else "  "
        print(f"[{elapsed:6.1f}s] {indent}{icon} {step}")

    sys.stdout.flush()


async def main():
    global start_time

    print("=" * 60)
    print("🌩️  STORM - Parallel Expert Conversations")
    print("=" * 60)
    print("""
Each expert runs their Q&A session in parallel:
┌─────────────┬─────────────┬─────────────┐
│ Expert 1    │ Expert 2    │ Expert 3    │
│ Q→R→Q→R     │ Q→R→Q→R     │ Q→R→Q→R     │
└─────────────┴─────────────┴─────────────┘
         All simultaneous!
""")

    # Use real Lyzr API with parallel conversations
    agent = StormAgent(
        lyzr_api_key="sk-default-obhGvAo6gG9YT9tu6ChjyXLqnw7TxSGY",
        user_id="demo@lyzr.ai",
        config=StormAgentConfig(),  # All defaults
        no_of_personas=3,
        no_of_questions=2,
        no_of_sections=4,
        on_event=on_event,
    )

    topic = "The Future of Renewable Energy"

    print(f"📝 Topic: {topic}")
    print(f"👥 Parallel Expert Sessions: {agent.no_of_personas}")
    print(f"❓ Questions per expert (with follow-ups): {agent.no_of_questions}")
    print("-" * 60)

    start_time = time.time()

    # Run with parallel conversations
    result = await agent.write_async(topic)

    print("-" * 60)

    if result.success:
        print(f"\n📊 Summary:")
        print(f"   • Personas: {len(result.personas)}")
        print(f"   • Questions: {sum(len(q) for q in result.questions.values())}")
        print(f"   • Research: {len(result.research)} answers")
        print(f"   • Sections: {len(result.sections)}")
        print(f"   • Events: {len(result.events)}")

        # Count conversation events
        conv_events = [e for e in result.events
                       if e.event_type == StormEventType.PERSONA_CONVERSATION_COMPLETED]
        print(f"\n   ✅ {len(conv_events)} parallel conversations completed!")

    else:
        print(f"\n❌ Error: {result.error}")


if __name__ == "__main__":
    asyncio.run(main())
