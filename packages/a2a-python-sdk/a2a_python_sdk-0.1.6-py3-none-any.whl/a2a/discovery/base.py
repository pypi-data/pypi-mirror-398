from abc import ABC, abstractmethod
from a2a.schema.agent_card import AgentCard


class DiscoveryStrategy(ABC):
    """
    Abstract discovery strategy as per A2A spec.
    """

    @abstractmethod
    def discover(self, target: str) -> AgentCard:
        pass
