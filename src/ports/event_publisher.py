from abc import ABC, abstractmethod
from src.domain.events import DomainEvent

class EventPublisherPort(ABC):
    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Publica un evento de dominio."""
        pass
