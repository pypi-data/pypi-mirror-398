from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class AgentResult:
    """Result returned from agent invocation."""

    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for all agents.

    Subclasses must implement the `invoke` method to define
    the agent's core behavior.
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    @abstractmethod
    def write(self, message: Any, **kwargs) -> AgentResult:
        """Write content based on the given message.

        Args:
            message: The message/topic to write about.
            **kwargs: Additional arguments for the write operation.

        Returns:
            AgentResult containing the output and metadata.
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
