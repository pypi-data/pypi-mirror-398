"""
Run STORM Agent with PARALLEL execution for faster results.

Uses write_async() to parallelize:
- Question generation across all personas
- Research across all questions
- Section writing across all sections
"""

import asyncio
import sys
import time
from src.agents import StormAgent, StormAgentConfig, StormEvent, StormEventType


start_time = None
step_times = {}


def on_event(event: StormEvent):
    """Display events with timing."""
    global start_time, step_times

    if start_time is None:
        start_time = time.time()

    elapsed = time.time() - start_time

    icons = {"running": "⏳", "completed": "✅", "failed": "❌"}
    icon = icons.get(event.status, "•")
    indent = "    " if event.parallel_group else "  "
    step = event.step_name or event.event_type.value

    # Track timing for major steps
    if event.status == "completed":
        step_times[event.node_id] = elapsed

    print(f"[{elapsed:6.1f}s] {indent}{icon} {step}")
    sys.stdout.flush()

    # Show details for key events
    if event.event_type == StormEventType.PERSONA_CREATED:
        persona = event.data.get("persona", "")[:50]
        print(f"          {indent}   └─ {persona}")
    elif event.event_type == StormEventType.RESEARCH_ANSWER_RECEIVED:
        length = event.data.get("answer_length", 0)
        print(f"          {indent}   └─ {length} chars")
    elif event.event_type == StormEventType.SECTION_WRITTEN:
        length = event.data.get("length", 0)
        print(f"          {indent}   └─ {length} chars")
    elif event.event_type == StormEventType.STORM_COMPLETED:
        total = time.time() - start_time
        print(f"\n{'='*50}")
        print(f"⚡ PARALLEL execution completed in {total:.1f} seconds")


async def main():
    global start_time

    print("=" * 60)
    print("🌩️  STORM Agent - PARALLEL Execution")
    print("=" * 60)
    print()

    agent = StormAgent(
        lyzr_api_key="sk-default-obhGvAo6gG9YT9tu6ChjyXLqnw7TxSGY",
        user_id="demo@lyzr.ai",
        config=StormAgentConfig(),
        no_of_personas=3,
        no_of_questions=2,
        no_of_sections=4,
        on_event=on_event,
    )

    topic = "The Future of Quantum Computing"

    print(f"📝 Topic: {topic}")
    print(f"👥 Personas: {agent.no_of_personas}")
    print(f"❓ Questions per persona: {agent.no_of_questions}")
    print(f"📑 Sections: {agent.no_of_sections}")
    print()
    print("⚡ Using PARALLEL execution (write_async)")
    print("-" * 60)

    start_time = time.time()

    # Use async version for parallel execution
    result = await agent.write_async(topic)

    total_time = time.time() - start_time

    print("-" * 60)

    if result.success:
        result.toFile("output/storm_article_parallel.md")

        print(f"\n✅ Article saved to: output/storm_article_parallel.md")
        print(f"\n📊 Summary:")
        print(f"   • Personas: {len(result.personas)}")
        print(f"   • Questions: {sum(len(q) for q in result.questions.values())}")
        print(f"   • Research answers: {len(result.research)}")
        print(f"   • Sections: {len(result.sections)}")
        print(f"   • Article length: {len(result.article)} chars")
        print(f"   • Total events: {len(result.events)}")
        print(f"\n⏱️  Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")

        # Compare with sequential estimate
        sequential_estimate = total_time * 2.5  # Rough estimate
        print(f"   Estimated sequential time: ~{sequential_estimate:.0f}s ({sequential_estimate/60:.1f} min)")
        print(f"   Speedup: ~{sequential_estimate/total_time:.1f}x faster")

    else:
        print(f"\n❌ Error: {result.error}")


if __name__ == "__main__":
    import os
    os.makedirs("output", exist_ok=True)
    asyncio.run(main())
