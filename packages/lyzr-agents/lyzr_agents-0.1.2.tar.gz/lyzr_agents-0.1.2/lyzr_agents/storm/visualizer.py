"""Live terminal visualization for STORM agent execution."""

from typing import Dict, Optional

from rich.live import Live
from rich.text import Text
from rich.tree import Tree

from .events import StormEvent, StormEventType


class StormVisualizer:
    """Live terminal visualization of STORM agent execution.

    Displays a real-time tree showing the progress of each step
    with color-coded status indicators.

    Example:
        from lyzr_agents.storm import StormAgent, StormVisualizer

        agent = StormAgent(lyzr_api_key="...", user_id="...")

        with StormVisualizer() as viz:
            result = agent.write("quantum mechanics", on_event=viz.on_event)

        # Async usage
        async with StormVisualizer() as viz:
            result = await agent.write_async("topic", on_event=viz.on_event)
    """

    # Status to color mapping
    STATUS_STYLES = {
        "running": "bold yellow",
        "completed": "bold green",
        "failed": "bold red",
        "pending": "dim white",
    }

    # Status indicators
    STATUS_ICONS = {
        "running": "[yellow]...[/yellow]",
        "completed": "[green]OK[/green]",
        "failed": "[red]X[/red]",
    }

    def __init__(self, refresh_rate: int = 4, show_details: bool = True):
        """Initialize the visualizer.

        Args:
            refresh_rate: How many times per second to refresh the display.
            show_details: Whether to show additional details like timing.
        """
        self.refresh_rate = refresh_rate
        self.show_details = show_details
        self.tree: Optional[Tree] = None
        self.nodes: Dict[str, Tree] = {}
        self.live: Optional[Live] = None
        self._topic: Optional[str] = None

    def _get_label(self, event: StormEvent) -> Text:
        """Create a styled label for a tree node."""
        style = self.STATUS_STYLES.get(event.status, "white")
        name = event.step_name or event.event_type.value

        # Build label with status indicator
        if event.status == "running":
            label = Text()
            label.append(name, style=style)
            label.append(" ", style="white")
            label.append("...", style="yellow blink")
        elif event.status == "completed":
            label = Text()
            label.append(name, style=style)
            label.append(" ", style="white")
            label.append("[OK]", style="green")
        elif event.status == "failed":
            label = Text()
            label.append(name, style=style)
            label.append(" ", style="white")
            label.append("[FAILED]", style="red")
        else:
            label = Text(name, style=style)

        # Add details if available
        if self.show_details and event.data:
            if "article_length" in event.data:
                label.append(f" ({event.data['article_length']} chars)", style="dim")
            elif "count" in event.data:
                label.append(f" ({event.data['count']} items)", style="dim")
            elif "length" in event.data:
                label.append(f" ({event.data['length']} chars)", style="dim")
            elif "answer_length" in event.data:
                label.append(f" ({event.data['answer_length']} chars)", style="dim")

        return label

    def on_event(self, event: StormEvent) -> None:
        """Handle a STORM event and update the visualization.

        This is the callback to pass to StormAgent.write() or write_async().

        Args:
            event: The StormEvent emitted by the agent.
        """
        if self.tree is None:
            return

        # Handle root STORM event specially
        if event.event_type == StormEventType.STORM_STARTED:
            topic = event.data.get("topic", "STORM")
            self._topic = topic
            self.tree.label = Text(f"STORM: {topic}", style="bold blue")
            self.nodes[event.node_id] = self.tree
            return

        # Update root on completion/failure
        if event.event_type in (StormEventType.STORM_COMPLETED, StormEventType.STORM_FAILED):
            if self._topic:
                style = "bold green" if event.status == "completed" else "bold red"
                status = "[OK]" if event.status == "completed" else "[FAILED]"
                label = Text()
                label.append(f"STORM: {self._topic} ", style=style)
                label.append(status, style=style)
                if event.data.get("article_length"):
                    label.append(f" ({event.data['article_length']} chars)", style="dim")
                self.tree.label = label
            return

        # Find parent node
        parent = self.nodes.get(event.parent_id, self.tree)

        # Create label
        label = self._get_label(event)

        # Update existing node or create new one
        if event.node_id in self.nodes:
            # Update the label of existing node
            self.nodes[event.node_id].label = label
        else:
            # Add new node to tree
            node = parent.add(label)
            self.nodes[event.node_id] = node

    def __enter__(self) -> "StormVisualizer":
        """Enter the context manager and start live display."""
        self.tree = Tree("STORM", guide_style="dim")
        self.nodes = {}
        self.live = Live(
            self.tree,
            refresh_per_second=self.refresh_rate,
            vertical_overflow="visible",
        )
        self.live.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager and stop live display."""
        if self.live:
            self.live.__exit__(exc_type, exc_val, exc_tb)
        self.live = None
        self.tree = None
        self.nodes = {}

    async def __aenter__(self) -> "StormVisualizer":
        """Async context manager entry."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        self.__exit__(exc_type, exc_val, exc_tb)
