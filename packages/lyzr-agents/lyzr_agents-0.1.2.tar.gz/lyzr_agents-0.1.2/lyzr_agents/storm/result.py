"""Result class for STORM agent output."""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .events import StormEvent


@dataclass
class StormResult:
    """Fluent result object for STORM agent output.

    Supports method chaining:
        result.toFile("output.txt")
        result.print()

    Example:
        result = agent.write("Topic")
        result.toFile("article.md").print()

        # Get graph data for React Flow
        graph = result.get_graph_data()
    """

    success: bool
    article: str
    topic: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    personas: List[str] = field(default_factory=list)
    questions: Dict[str, List[str]] = field(default_factory=dict)
    research: Dict[str, str] = field(default_factory=dict)
    outline: List[str] = field(default_factory=list)
    sections: Dict[str, str] = field(default_factory=dict)
    events: List[StormEvent] = field(default_factory=list)

    def toFile(self, filepath: str, include_metadata: bool = False) -> "StormResult":
        """Write the article to a file.

        Args:
            filepath: Path to the output file.
            include_metadata: If True, include metadata as YAML frontmatter.

        Returns:
            Self for method chaining.
        """
        content = self._format_output(include_metadata)

        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return self

    def print(self, include_metadata: bool = False) -> "StormResult":
        """Print the article to stdout.

        Returns:
            Self for method chaining.
        """
        content = self._format_output(include_metadata)
        print(content)
        return self

    def _format_output(self, include_metadata: bool) -> str:
        """Format the output content."""
        if not include_metadata:
            return self.article

        meta = {
            "topic": self.topic,
            "success": self.success,
            "personas_count": len(self.personas),
            "questions_count": sum(len(q) for q in self.questions.values()),
            "sections_count": len(self.sections),
        }
        meta_str = "\n".join(f"{k}: {v}" for k, v in meta.items())
        return f"---\n{meta_str}\n---\n\n{self.article}"

    def get_graph_data(self) -> Dict[str, Any]:
        """Get data formatted for React Flow graph visualization.

        Returns:
            Dict with 'nodes' and 'edges' for React Flow.
        """
        nodes = []
        edges = []

        for event in self.events:
            node = {
                "id": event.node_id,
                "type": "stormNode",
                "data": {
                    "label": event.step_name or event.event_type.value,
                    "status": event.status,
                    "event_type": event.event_type.value,
                    **event.data
                },
                "position": {"x": 0, "y": 0},  # Layout calculated by frontend
            }
            nodes.append(node)

            if event.parent_id:
                edge = {
                    "id": f"e-{event.parent_id}-{event.node_id}",
                    "source": event.parent_id,
                    "target": event.node_id,
                    "animated": event.status == "running",
                }
                edges.append(edge)

        return {"nodes": nodes, "edges": edges}

    def __str__(self) -> str:
        return self.article

    def __bool__(self) -> bool:
        return self.success
