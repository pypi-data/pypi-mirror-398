import asyncio
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .base_agent import BaseAgent
from .lyzr_agent import LyzrAgent


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


@dataclass
class StormAgentConfig:
    """Configuration for STORM agent Lyzr agent IDs.

    All agent IDs have defaults configured for Lyzr platform.
    You can override any of them as needed.
    """

    persona_generator_agent_id: str = "6947ba3881c8a74f1ca95fd4"
    question_generator_agent_id: str = "6947baab2be72f04a7d6440c"
    outline_generator_agent_id: str = "6947bb142be72f04a7d6449e"
    section_generator_agent_id: str = "6947bb786363be71980e845d"
    research_agent_id: str = "6946a84681c8a74f1ca95008"


@dataclass
class StormResult:
    """Fluent result object for STORM agent output.

    Supports method chaining:
        result.toFile("output.txt")
        result.print()
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


def test_config() -> StormAgentConfig:
    """Create a test configuration with dummy agent IDs."""
    return StormAgentConfig(
        research_agent_id="test",
        persona_generator_agent_id="test",
        question_generator_agent_id="test",
        outline_generator_agent_id="test",
        section_generator_agent_id="test",
    )


class StormAgent(BaseAgent):
    """Stanford STORM agent for generating long-form articles.

    STORM (Synthesis of Topic Outlines through Retrieval and Multi-perspective
    Question Asking) generates comprehensive articles by simulating conversations
    between multiple personas.

    Example:
        config = StormAgentConfig(
            research_agent_id="...",
            persona_generator_agent_id="...",
            question_generator_agent_id="...",
            outline_generator_agent_id="...",
            section_generator_agent_id="..."
        )

        agent = StormAgent(
            lyzr_api_key="your-api-key",
            user_id="user@example.com",
            config=config,
            on_event=lambda e: print(f"Event: {e.event_type.value}")
        )

        agent.write("quantum mechanics").toFile("article.md")

    Test Mode:
        # Use test_config() for dummy test runs without API calls
        agent = StormAgent(
            lyzr_api_key="test",
            user_id="test",
            config=test_config(),
        )
        result = agent.write("test topic")  # Returns mock data
    """

    def __init__(
        self,
        lyzr_api_key: str,
        user_id: str,
        config: StormAgentConfig,
        name: str = "storm-agent",
        description: str = "",
        context: Optional[str] = None,
        no_of_personas: int = 3,
        no_of_questions: int = 3,
        no_of_sections: int = 3,
        on_event: Optional[EventCallback] = None,
    ):
        """Initialize the STORM agent.

        Args:
            lyzr_api_key: API key for Lyzr platform (use "test" for test mode).
            user_id: User ID for Lyzr platform (use "test" for test mode).
            config: StormAgentConfig with Lyzr agent IDs (use test_config() for test mode).
            name: Name of this agent instance.
            description: Description of this agent.
            context: Optional additional context for article generation.
            no_of_personas: Number of personas to generate (default 3).
            no_of_questions: Number of questions per persona (default 3).
            no_of_sections: Number of sections in the article (default 3).
            on_event: Callback function for event notifications.
        """
        super().__init__(name=name, description=description)
        self.lyzr_api_key = lyzr_api_key
        self.user_id = user_id
        self.config = config
        self.context = context
        self.no_of_personas = no_of_personas
        self.no_of_questions = no_of_questions
        self.no_of_sections = no_of_sections
        self.on_event = on_event
        self._test_mode = self._is_test_mode()
        self._events: List[StormEvent] = []

        if not self._test_mode:
            self.client = LyzrAgent(api_key=lyzr_api_key, user_id=user_id)
        else:
            self.client = None

    def _is_test_mode(self) -> bool:
        """Check if running in test mode."""
        return (
            self.config.research_agent_id == "test"
            and self.config.persona_generator_agent_id == "test"
            and self.config.question_generator_agent_id == "test"
            and self.config.outline_generator_agent_id == "test"
            and self.config.section_generator_agent_id == "test"
        )

    def _mock_response(self, prompt: str, agent_type: str) -> str:
        """Generate mock responses for test mode."""
        import time
        time.sleep(0.1)  # Simulate API latency

        if agent_type == "persona":
            return json.dumps([
                "A university professor specializing in the field",
                "A technology journalist covering emerging trends",
                "A graduate student researching the topic",
                "An industry practitioner with hands-on experience",
                "A policy analyst studying societal implications",
            ][:self.no_of_personas])

        elif agent_type == "question":
            return json.dumps([
                "What are the fundamental principles underlying this topic?",
                "How has this field evolved over the past decade?",
                "What are the main challenges and limitations?",
                "What practical applications exist today?",
                "What future developments can we expect?",
            ][:self.no_of_questions])

        elif agent_type == "research":
            return f"""This is a mock research response for testing purposes.

The topic involves several key aspects that are important to understand.
First, the foundational concepts provide the basis for further exploration.
Second, recent developments have significantly advanced our understanding.
Third, practical applications demonstrate real-world relevance.

This mock response simulates what the research agent would return."""

        elif agent_type == "outline":
            return json.dumps([
                "Introduction and Overview",
                "Core Concepts and Principles",
                "Current State and Applications",
                "Challenges and Limitations",
                "Future Directions and Conclusion",
            ][:self.no_of_sections])

        elif agent_type == "section":
            section_match = prompt.split('"')[1] if '"' in prompt else "Section"
            return f"""## {section_match}

This is a mock section for testing the STORM agent flow.

The content here represents what would be generated by the section writing agent.
It includes multiple paragraphs to simulate realistic article content.

Key points covered in this section:
- Important concept one with detailed explanation
- Important concept two with supporting evidence
- Important concept three with practical examples

This mock content helps verify that the event system and graph visualization
are working correctly without making actual API calls."""

        return "Mock response"

    def _emit_event(
        self,
        event_type: StormEventType,
        node_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        parallel_group: Optional[str] = None,
        step_name: Optional[str] = None,
        status: str = "running",
        data: Optional[Dict[str, Any]] = None,
    ) -> StormEvent:
        """Emit an event and notify callback."""
        event = StormEvent(
            event_type=event_type,
            node_id=node_id or str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            parent_id=parent_id,
            parallel_group=parallel_group,
            step_name=step_name,
            status=status,
            data=data or {},
        )
        self._events.append(event)

        if self.on_event:
            self.on_event(event)

        return event

    def _parse_json_list(self, response: str, max_items: int) -> List[str]:
        """Parse JSON list from response with fallback."""
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned

        try:
            result = json.loads(cleaned)
            if isinstance(result, list):
                return [str(item) for item in result[:max_items]]
        except json.JSONDecodeError:
            pass

        # Fallback: split by newlines
        lines = []
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Remove list prefixes
            for prefix in ["-", "*", "•", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."]:
                if line.startswith(prefix):
                    line = line[len(prefix):].strip()
                    break
            if line:
                lines.append(line)

        return lines[:max_items]

    def _discover_personas(
        self, topic: str, context: Optional[str], no_of_personas: int, parent_id: str
    ) -> List[str]:
        """Step 1: Discover diverse personas/perspectives."""
        node_id = f"personas-{uuid.uuid4().hex[:6]}"
        self._emit_event(
            StormEventType.PERSONA_GENERATION_STARTED,
            node_id=node_id,
            parent_id=parent_id,
            step_name="Generate Personas",
            data={"topic": topic, "count": no_of_personas}
        )

        context_clause = f"\n\nAdditional context: {context}" if context else ""
        prompt = f"""Generate {no_of_personas} diverse personas who would have unique perspectives on: "{topic}"{context_clause}

Each persona should represent a different viewpoint, expertise, or background.
Return ONLY a JSON array of persona descriptions.
Example: ["A physics professor", "A science journalist", "A graduate student"]"""

        if self._test_mode:
            response_text = self._mock_response(prompt, "persona")
        else:
            response = self.client.execute(
                agent_id=self.config.persona_generator_agent_id,
                message=prompt
            )
            response_text = response.response

        personas = self._parse_json_list(response_text, no_of_personas)

        # Emit individual persona events
        for i, persona in enumerate(personas):
            self._emit_event(
                StormEventType.PERSONA_CREATED,
                node_id=f"persona-{i}-{uuid.uuid4().hex[:4]}",
                parent_id=node_id,
                parallel_group=f"personas-{node_id}",
                step_name=f"Persona {i+1}",
                status="completed",
                data={"persona": persona, "index": i}
            )

        self._emit_event(
            StormEventType.PERSONA_GENERATION_COMPLETED,
            node_id=node_id,
            parent_id=parent_id,
            step_name="Generate Personas",
            status="completed",
            data={"personas": personas, "count": len(personas)}
        )

        return personas

    def _generate_questions(
        self,
        topic: str,
        persona: str,
        persona_index: int,
        context: Optional[str],
        no_of_questions: int,
        parent_id: str,
        parallel_group: str,
    ) -> List[str]:
        """Step 2: Generate questions from a persona's perspective."""
        node_id = f"questions-p{persona_index}-{uuid.uuid4().hex[:6]}"
        self._emit_event(
            StormEventType.QUESTION_GENERATION_STARTED,
            node_id=node_id,
            parent_id=parent_id,
            parallel_group=parallel_group,
            step_name=f"Questions (Persona {persona_index+1})",
            data={"persona": persona, "count": no_of_questions}
        )

        context_clause = f"\n\nAdditional context: {context}" if context else ""
        prompt = f"""You are: {persona}

Generate {no_of_questions} insightful questions about "{topic}" from your perspective.{context_clause}

Return ONLY a JSON array of questions.
Example: ["What are the core principles?", "How does this impact society?"]"""

        if self._test_mode:
            response_text = self._mock_response(prompt, "question")
        else:
            response = self.client.execute(
                agent_id=self.config.question_generator_agent_id,
                message=prompt
            )
            response_text = response.response

        questions = self._parse_json_list(response_text, no_of_questions)

        # Emit individual question events
        for i, question in enumerate(questions):
            self._emit_event(
                StormEventType.QUESTION_CREATED,
                node_id=f"q-p{persona_index}-{i}-{uuid.uuid4().hex[:4]}",
                parent_id=node_id,
                parallel_group=f"questions-{node_id}",
                step_name=f"Q{i+1}",
                status="completed",
                data={"question": question, "persona": persona}
            )

        self._emit_event(
            StormEventType.QUESTION_GENERATION_COMPLETED,
            node_id=node_id,
            parent_id=parent_id,
            parallel_group=parallel_group,
            step_name=f"Questions (Persona {persona_index+1})",
            status="completed",
            data={"questions": questions, "count": len(questions)}
        )

        return questions

    def _research_question(
        self,
        topic: str,
        question: str,
        question_index: int,
        context: Optional[str],
        parent_id: str,
        parallel_group: str,
    ) -> str:
        """Step 3: Research and answer a question."""
        node_id = f"research-{question_index}-{uuid.uuid4().hex[:6]}"
        self._emit_event(
            StormEventType.RESEARCH_STARTED,
            node_id=node_id,
            parent_id=parent_id,
            parallel_group=parallel_group,
            step_name=f"Research Q{question_index+1}",
            data={"question": question[:50] + "..."}
        )

        context_clause = f"\n\nAdditional context: {context}" if context else ""
        prompt = f"""Topic: {topic}
Question: {question}{context_clause}

Provide a comprehensive, well-researched answer. Include relevant facts and insights."""

        if self._test_mode:
            response_text = self._mock_response(prompt, "research")
        else:
            response = self.client.execute(
                agent_id=self.config.research_agent_id,
                message=prompt
            )
            response_text = response.response

        self._emit_event(
            StormEventType.RESEARCH_ANSWER_RECEIVED,
            node_id=node_id,
            parent_id=parent_id,
            parallel_group=parallel_group,
            step_name=f"Research Q{question_index+1}",
            status="completed",
            data={"question": question, "answer_length": len(response_text)}
        )

        return response_text

    def _generate_outline(
        self,
        topic: str,
        research_results: Dict[str, str],
        context: Optional[str],
        no_of_sections: int,
        parent_id: str,
    ) -> List[str]:
        """Step 4: Generate article outline from research."""
        node_id = f"outline-{uuid.uuid4().hex[:6]}"
        self._emit_event(
            StormEventType.OUTLINE_GENERATION_STARTED,
            node_id=node_id,
            parent_id=parent_id,
            step_name="Generate Outline",
            data={"sections": no_of_sections, "research_items": len(research_results)}
        )

        context_clause = f"\n\nAdditional context: {context}" if context else ""
        research_summary = "\n".join([
            f"Q: {q}\nA: {a[:300]}..." for q, a in list(research_results.items())[:10]
        ])

        prompt = f"""Based on this research about "{topic}", create an outline with {no_of_sections} sections.{context_clause}

Research:
{research_summary}

Return ONLY a JSON array of section titles.
Example: ["Introduction", "Core Concepts", "Applications", "Conclusion"]"""

        if self._test_mode:
            response_text = self._mock_response(prompt, "outline")
        else:
            response = self.client.execute(
                agent_id=self.config.outline_generator_agent_id,
                message=prompt
            )
            response_text = response.response

        outline = self._parse_json_list(response_text, no_of_sections)

        # Emit section outline events
        for i, section in enumerate(outline):
            self._emit_event(
                StormEventType.SECTION_OUTLINED,
                node_id=f"outline-s{i}-{uuid.uuid4().hex[:4]}",
                parent_id=node_id,
                step_name=section[:20],
                status="completed",
                data={"section": section, "index": i}
            )

        self._emit_event(
            StormEventType.OUTLINE_GENERATION_COMPLETED,
            node_id=node_id,
            parent_id=parent_id,
            step_name="Generate Outline",
            status="completed",
            data={"outline": outline}
        )

        return outline

    def _write_section(
        self,
        topic: str,
        section_title: str,
        section_index: int,
        outline: List[str],
        research_results: Dict[str, str],
        context: Optional[str],
        parent_id: str,
        parallel_group: str,
    ) -> str:
        """Step 5: Write a single section."""
        node_id = f"section-{section_index}-{uuid.uuid4().hex[:6]}"
        self._emit_event(
            StormEventType.SECTION_WRITING_STARTED,
            node_id=node_id,
            parent_id=parent_id,
            parallel_group=parallel_group,
            step_name=f"Write: {section_title[:15]}...",
            data={"section": section_title, "index": section_index}
        )

        context_clause = f"\n\nAdditional context: {context}" if context else ""
        outline_text = "\n".join(f"- {s}" for s in outline)
        research_text = "\n".join(list(research_results.values())[:5])

        prompt = f"""Write the "{section_title}" section for an article about "{topic}".{context_clause}

Outline:
{outline_text}

Research to incorporate:
{research_text[:2000]}

Write a comprehensive section. Start with "## {section_title}" as the heading."""

        if self._test_mode:
            response_text = self._mock_response(prompt, "section")
        else:
            response = self.client.execute(
                agent_id=self.config.section_generator_agent_id,
                message=prompt
            )
            response_text = response.response

        self._emit_event(
            StormEventType.SECTION_WRITTEN,
            node_id=node_id,
            parent_id=parent_id,
            parallel_group=parallel_group,
            step_name=f"Write: {section_title[:15]}...",
            status="completed",
            data={"section": section_title, "length": len(response_text)}
        )

        return response_text

    def _run_persona_conversation(
        self,
        topic: str,
        persona: str,
        persona_index: int,
        context: Optional[str],
        no_of_questions: int,
        parent_id: str,
    ) -> Dict[str, str]:
        """Run a full Q&A conversation session for a single persona.

        This simulates a conversation where the persona asks questions
        and gets answers, potentially with follow-up questions.

        Returns:
            Dict mapping questions to research answers for this persona.
        """
        conv_id = f"conv-p{persona_index}-{uuid.uuid4().hex[:6]}"
        self._emit_event(
            StormEventType.PERSONA_CONVERSATION_STARTED,
            node_id=conv_id,
            parent_id=parent_id,
            parallel_group=f"conversations-{parent_id}",
            step_name=f"Expert {persona_index + 1} Session",
            data={"persona": persona[:50], "index": persona_index}
        )

        conversation_research: Dict[str, str] = {}
        previous_context = ""

        for q_idx in range(no_of_questions):
            # Generate question (with context from previous answers for follow-ups)
            question = self._generate_single_question(
                topic, persona, persona_index, q_idx, context,
                previous_context, conv_id
            )

            # Research the question
            answer = self._research_single_question(
                topic, question, persona_index, q_idx, context, conv_id
            )

            conversation_research[question] = answer

            # Build context for follow-up questions
            previous_context += f"\nQ: {question}\nA: {answer[:500]}...\n"

        self._emit_event(
            StormEventType.PERSONA_CONVERSATION_COMPLETED,
            node_id=conv_id,
            parent_id=parent_id,
            parallel_group=f"conversations-{parent_id}",
            step_name=f"Expert {persona_index + 1} Session",
            status="completed",
            data={
                "persona": persona[:50],
                "questions": len(conversation_research),
                "total_research_chars": sum(len(a) for a in conversation_research.values())
            }
        )

        return conversation_research

    def _generate_single_question(
        self,
        topic: str,
        persona: str,
        persona_index: int,
        question_index: int,
        context: Optional[str],
        previous_qa: str,
        parent_id: str,
    ) -> str:
        """Generate a single question, potentially as a follow-up."""
        node_id = f"q-p{persona_index}-{question_index}-{uuid.uuid4().hex[:4]}"

        self._emit_event(
            StormEventType.QUESTION_GENERATION_STARTED,
            node_id=node_id,
            parent_id=parent_id,
            step_name=f"Q{question_index + 1}",
            data={"persona": persona[:30], "is_followup": question_index > 0}
        )

        context_clause = f"\n\nAdditional context: {context}" if context else ""
        followup_clause = ""
        if previous_qa:
            followup_clause = f"\n\nPrevious conversation:\n{previous_qa}\n\nBased on the above, ask a follow-up question that digs deeper."

        prompt = f"""You are: {persona}

Generate 1 insightful question about "{topic}" from your perspective.{context_clause}{followup_clause}

Return ONLY the question text, nothing else."""

        if self._test_mode:
            import time
            time.sleep(0.05)
            questions = [
                "What are the fundamental principles underlying this topic?",
                "How has this field evolved and what recent breakthroughs occurred?",
                "What are the practical applications and real-world implications?",
                "What challenges remain and how might they be addressed?",
                "What future developments can we anticipate in the next decade?",
            ]
            response_text = questions[question_index % len(questions)]
        else:
            response = self.client.execute(
                agent_id=self.config.question_generator_agent_id,
                message=prompt
            )
            response_text = response.response.strip().strip('"').strip("'")

        self._emit_event(
            StormEventType.QUESTION_CREATED,
            node_id=node_id,
            parent_id=parent_id,
            step_name=f"Q{question_index + 1}",
            status="completed",
            data={"question": response_text[:60], "persona": persona[:30]}
        )

        return response_text

    def _research_single_question(
        self,
        topic: str,
        question: str,
        persona_index: int,
        question_index: int,
        context: Optional[str],
        parent_id: str,
    ) -> str:
        """Research a single question."""
        node_id = f"r-p{persona_index}-{question_index}-{uuid.uuid4().hex[:4]}"

        self._emit_event(
            StormEventType.RESEARCH_STARTED,
            node_id=node_id,
            parent_id=parent_id,
            step_name=f"Research Q{question_index + 1}",
            data={"question": question[:40] + "..."}
        )

        context_clause = f"\n\nAdditional context: {context}" if context else ""
        prompt = f"""Topic: {topic}
Question: {question}{context_clause}

Provide a comprehensive, well-researched answer. Include relevant facts and insights."""

        if self._test_mode:
            import time
            time.sleep(0.1)
            response_text = f"""This is a mock research response for: {question[:50]}

The topic involves several key aspects that are important to understand.
First, the foundational concepts provide the basis for further exploration.
Second, recent developments have significantly advanced our understanding.
Third, practical applications demonstrate real-world relevance.

This mock response simulates what the research agent would return."""
        else:
            response = self.client.execute(
                agent_id=self.config.research_agent_id,
                message=prompt
            )
            response_text = response.response

        self._emit_event(
            StormEventType.RESEARCH_ANSWER_RECEIVED,
            node_id=node_id,
            parent_id=parent_id,
            step_name=f"Research Q{question_index + 1}",
            status="completed",
            data={"answer_length": len(response_text)}
        )

        return response_text

    def _assemble_article(
        self, topic: str, outline: List[str], sections: Dict[str, str], parent_id: str
    ) -> str:
        """Step 6: Assemble final article."""
        node_id = f"assembly-{uuid.uuid4().hex[:6]}"
        self._emit_event(
            StormEventType.ARTICLE_ASSEMBLY_STARTED,
            node_id=node_id,
            parent_id=parent_id,
            step_name="Assemble Article",
            data={"sections": len(sections)}
        )

        article_parts = [f"# {topic}\n"]
        for section_title in outline:
            if section_title in sections:
                article_parts.append(sections[section_title])
                article_parts.append("\n")

        article = "\n".join(article_parts)

        self._emit_event(
            StormEventType.ARTICLE_ASSEMBLY_COMPLETED,
            node_id=node_id,
            parent_id=parent_id,
            step_name="Assemble Article",
            status="completed",
            data={"total_length": len(article)}
        )

        return article

    def write(self, topic: str, **kwargs) -> StormResult:
        """Write a long-form article using the STORM algorithm.

        Args:
            topic: The topic to write about.
            **kwargs: Override default parameters.

        Returns:
            StormResult with fluent API (.toFile, .print).
        """
        self._events = []  # Reset events

        context = kwargs.get('context', self.context)
        no_of_personas = kwargs.get('no_of_personas', self.no_of_personas)
        no_of_questions = kwargs.get('no_of_questions', self.no_of_questions)
        no_of_sections = kwargs.get('no_of_sections', self.no_of_sections)

        root_id = f"storm-{uuid.uuid4().hex[:6]}"
        self._emit_event(
            StormEventType.STORM_STARTED,
            node_id=root_id,
            step_name="STORM",
            data={"topic": topic, "personas": no_of_personas, "questions": no_of_questions, "sections": no_of_sections}
        )

        try:
            # Step 1: Discover personas
            personas = self._discover_personas(topic, context, no_of_personas, root_id)

            # Step 2: Generate questions (parallel per persona)
            all_questions: Dict[str, List[str]] = {}
            question_group = f"qgen-{uuid.uuid4().hex[:6]}"
            for i, persona in enumerate(personas):
                questions = self._generate_questions(
                    topic, persona, i, context, no_of_questions,
                    parent_id=root_id, parallel_group=question_group
                )
                all_questions[persona] = questions

            # Step 3: Research all questions (parallel)
            research_results: Dict[str, str] = {}
            research_group = f"research-{uuid.uuid4().hex[:6]}"
            question_idx = 0
            for persona, questions in all_questions.items():
                for question in questions:
                    answer = self._research_question(
                        topic, question, question_idx, context,
                        parent_id=root_id, parallel_group=research_group
                    )
                    research_results[question] = answer
                    question_idx += 1

            # Step 4: Generate outline
            outline = self._generate_outline(topic, research_results, context, no_of_sections, root_id)

            # Step 5: Write sections (parallel)
            sections: Dict[str, str] = {}
            section_group = f"sections-{uuid.uuid4().hex[:6]}"
            for i, section_title in enumerate(outline):
                content = self._write_section(
                    topic, section_title, i, outline, research_results, context,
                    parent_id=root_id, parallel_group=section_group
                )
                sections[section_title] = content

            # Step 6: Assemble article
            article = self._assemble_article(topic, outline, sections, root_id)

            self._emit_event(
                StormEventType.STORM_COMPLETED,
                node_id=root_id,
                step_name="STORM",
                status="completed",
                data={"article_length": len(article)}
            )

            return StormResult(
                success=True,
                article=article,
                topic=topic,
                personas=personas,
                questions=all_questions,
                research=research_results,
                outline=outline,
                sections=sections,
                events=self._events.copy(),
                metadata={
                    "no_of_personas": no_of_personas,
                    "no_of_questions": no_of_questions,
                    "no_of_sections": no_of_sections,
                }
            )

        except Exception as e:
            self._emit_event(
                StormEventType.STORM_FAILED,
                node_id=root_id,
                step_name="STORM",
                status="failed",
                data={"error": str(e)}
            )

            return StormResult(
                success=False,
                article="",
                topic=topic,
                error=str(e),
                events=self._events.copy(),
            )

    async def write_async(self, topic: str, **kwargs) -> StormResult:
        """Async version with TRUE PARALLEL per-persona conversations.

        Each persona runs their complete Q&A session in parallel:
        - Persona 1: Q1 → Research → Q2 (follow-up) → Research
        - Persona 2: Q1 → Research → Q2 (follow-up) → Research  (parallel)
        - Persona 3: Q1 → Research → Q2 (follow-up) → Research  (parallel)

        Args:
            topic: The topic to write about.
            **kwargs: Override default parameters.

        Returns:
            StormResult with fluent API.
        """
        self._events = []

        context = kwargs.get('context', self.context)
        no_of_personas = kwargs.get('no_of_personas', self.no_of_personas)
        no_of_questions = kwargs.get('no_of_questions', self.no_of_questions)
        no_of_sections = kwargs.get('no_of_sections', self.no_of_sections)

        root_id = f"storm-{uuid.uuid4().hex[:6]}"
        self._emit_event(
            StormEventType.STORM_STARTED,
            node_id=root_id,
            step_name="STORM",
            data={"topic": topic, "async": True, "parallel_conversations": True}
        )

        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=10)

        async def run_sync(func, *args, **kw):
            return await loop.run_in_executor(executor, lambda: func(*args, **kw))

        try:
            # Step 1: Discover personas
            personas = await run_sync(
                self._discover_personas, topic, context, no_of_personas, root_id
            )

            # Step 2 & 3: Run PARALLEL per-persona conversations
            # Each persona has their own Q&A session running simultaneously
            conversation_tasks = [
                run_sync(
                    self._run_persona_conversation,
                    topic, persona, i, context, no_of_questions, root_id
                )
                for i, persona in enumerate(personas)
            ]

            # All persona conversations run in parallel!
            conversation_results = await asyncio.gather(*conversation_tasks)

            # Merge all research results
            all_questions: Dict[str, List[str]] = {}
            research_results: Dict[str, str] = {}

            for persona, conv_research in zip(personas, conversation_results):
                all_questions[persona] = list(conv_research.keys())
                research_results.update(conv_research)

            # Step 4: Generate outline
            outline = await run_sync(
                self._generate_outline, topic, research_results, context, no_of_sections, root_id
            )

            # Step 5: Write sections (parallel)
            section_group = f"sections-{uuid.uuid4().hex[:6]}"
            section_tasks = [
                run_sync(
                    self._write_section,
                    topic, title, i, outline, research_results, context, root_id, section_group
                )
                for i, title in enumerate(outline)
            ]
            section_contents = await asyncio.gather(*section_tasks)
            sections = dict(zip(outline, section_contents))

            # Step 6: Assemble
            article = self._assemble_article(topic, outline, sections, root_id)

            self._emit_event(
                StormEventType.STORM_COMPLETED,
                node_id=root_id,
                step_name="STORM",
                status="completed",
                data={"article_length": len(article), "async": True}
            )

            executor.shutdown(wait=False)

            return StormResult(
                success=True,
                article=article,
                topic=topic,
                personas=personas,
                questions=all_questions,
                research=research_results,
                outline=outline,
                sections=sections,
                events=self._events.copy(),
                metadata={"async": True}
            )

        except Exception as e:
            self._emit_event(
                StormEventType.STORM_FAILED,
                node_id=root_id,
                step_name="STORM",
                status="failed",
                data={"error": str(e)}
            )
            executor.shutdown(wait=False)

            return StormResult(
                success=False,
                article="",
                topic=topic,
                error=str(e),
                events=self._events.copy(),
            )
