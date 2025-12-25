#!/usr/bin/env python3
"""Example: Live terminal visualization of STORM agent execution.

This example shows how to use StormVisualizer to display a real-time
tree view of the STORM agent's progress in the terminal.

Usage:
    # Test mode (no API calls)
    python examples/visualize_storm.py

    # Real mode with API
    LYZR_API_KEY=your-key LYZR_USER_ID=your-user python examples/visualize_storm.py --real
"""

import asyncio
import os
import sys

from lyzr_agents.storm import StormAgent, StormVisualizer, test_config


def run_sync_with_visualization():
    """Run STORM agent with live visualization (sync mode)."""
    print("Running STORM with live visualization (sync mode)...\n")

    agent = StormAgent(
        lyzr_api_key="test",
        user_id="test",
        config=test_config(),
        no_of_personas=3,
        no_of_questions=2,
        no_of_sections=3,
    )

    with StormVisualizer() as viz:
        result = agent.write("artificial intelligence", on_event=viz.on_event)

    print(f"\nArticle generated: {len(result.article)} characters")
    print(f"Total events: {len(result.events)}")


async def run_async_with_visualization():
    """Run STORM agent with live visualization (async mode)."""
    print("Running STORM with live visualization (async mode)...\n")

    agent = StormAgent(
        lyzr_api_key="test",
        user_id="test",
        config=test_config(),
        no_of_personas=3,
        no_of_questions=2,
        no_of_sections=3,
    )

    async with StormVisualizer() as viz:
        result = await agent.write_async("machine learning", on_event=viz.on_event)

    print(f"\nArticle generated: {len(result.article)} characters")
    print(f"Total events: {len(result.events)}")


def run_real_with_visualization():
    """Run STORM agent with real API and visualization."""
    api_key = os.environ.get("LYZR_API_KEY")
    user_id = os.environ.get("LYZR_USER_ID")

    if not api_key or not user_id:
        print("Error: Set LYZR_API_KEY and LYZR_USER_ID environment variables")
        sys.exit(1)

    print("Running STORM with real API and live visualization...\n")

    agent = StormAgent(
        lyzr_api_key=api_key,
        user_id=user_id,
        no_of_personas=2,
        no_of_questions=2,
        no_of_sections=3,
    )

    with StormVisualizer() as viz:
        result = agent.write("quantum computing", on_event=viz.on_event)

    if result.success:
        print(f"\nArticle generated: {len(result.article)} characters")
        result.toFile("output/quantum_computing.md")
        print("Saved to output/quantum_computing.md")
    else:
        print(f"\nError: {result.error}")


if __name__ == "__main__":
    if "--real" in sys.argv:
        run_real_with_visualization()
    elif "--async" in sys.argv:
        asyncio.run(run_async_with_visualization())
    else:
        run_sync_with_visualization()
