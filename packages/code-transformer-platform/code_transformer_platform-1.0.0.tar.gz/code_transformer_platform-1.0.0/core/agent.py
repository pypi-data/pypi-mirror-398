from abc import ABC, abstractmethod
from typing import Any


class Agent(ABC):
    """
    Base class for all agents.
    Every agent:
    - Has one responsibility
    - Consumes artifacts
    - Produces artifacts
    """

    name: str = "base-agent"

    @abstractmethod
    def run(self, context: Any) -> None:
        """
        Execute agent logic.
        Must update context with new artifacts.
        """
        pass
