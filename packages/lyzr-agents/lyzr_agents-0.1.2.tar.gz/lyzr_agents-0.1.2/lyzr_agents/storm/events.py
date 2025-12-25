"""Event types and classes for STORM agent execution tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional


class StormEventType(Enum):
    """Types of events emitted during STORM execution."""

    # Lifecycle events
    STORM_STARTED = "storm_started"
    STORM_COMPLETED = "storm_completed"
    STORM_FAILED = "storm_failed"

    # Step events
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"

    # Persona events
    PERSONA_GENERATION_STARTED = "persona_generation_started"
    PERSONA_GENERATION_COMPLETED = "persona_generation_completed"
    PERSONA_CREATED = "persona_created"

    # Question events
    QUESTION_GENERATION_STARTED = "question_generation_started"
    QUESTION_GENERATION_COMPLETED = "question_generation_completed"
    QUESTION_CREATED = "question_created"

    # Research events
    RESEARCH_STARTED = "research_started"
    RESEARCH_COMPLETED = "research_completed"
    RESEARCH_ANSWER_RECEIVED = "research_answer_received"

    # Outline events
    OUTLINE_GENERATION_STARTED = "outline_generation_started"
    OUTLINE_GENERATION_COMPLETED = "outline_generation_completed"
    SECTION_OUTLINED = "section_outlined"

    # Section writing events
    SECTION_WRITING_STARTED = "section_writing_started"
    SECTION_WRITING_COMPLETED = "section_writing_completed"
    SECTION_WRITTEN = "section_written"

    # Assembly events
    ARTICLE_ASSEMBLY_STARTED = "article_assembly_started"
    ARTICLE_ASSEMBLY_COMPLETED = "article_assembly_completed"

    # Persona conversation events (parallel Q&A sessions)
    PERSONA_CONVERSATION_STARTED = "persona_conversation_started"
    PERSONA_CONVERSATION_COMPLETED = "persona_conversation_completed"

    # Enrichment events (for reaching target character count)
    ENRICHMENT_STARTED = "enrichment_started"
    ENRICHMENT_COMPLETED = "enrichment_completed"
    SECTION_ENRICHED = "section_enriched"


@dataclass
class StormEvent:
    """Event emitted during STORM execution for visualization.

    Designed to support React Flow graph visualization with:
    - node_id: Unique ID for this node in the graph
    - parent_id: ID of parent node (for edges)
    - parallel_group: Group ID for parallel operations
    """

    event_type: StormEventType
    node_id: str
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    parallel_group: Optional[str] = None
    step_name: Optional[str] = None
    status: str = "running"  # running, completed, failed

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type.value,
            "node_id": self.node_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "parent_id": self.parent_id,
            "parallel_group": self.parallel_group,
            "step_name": self.step_name,
            "status": self.status,
        }


# Type alias for event callback
EventCallback = Callable[[StormEvent], None]
