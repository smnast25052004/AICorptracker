from abc import ABC, abstractmethod
from typing import Generator
from shared.schemas.events import CorporateEvent


class BaseSource(ABC):
    """Base class for all data source connectors."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @abstractmethod
    def fetch_events(self) -> Generator[CorporateEvent, None, None]:
        """Fetch events from the source system."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if source system is accessible."""
        pass
