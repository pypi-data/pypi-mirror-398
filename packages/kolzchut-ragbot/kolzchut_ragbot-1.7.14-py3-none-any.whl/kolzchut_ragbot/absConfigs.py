from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional


class AbstractConfigs(ABC):
    """
    Abstract base class for managing configurations.
    Defines the interface and common behavior for configuration management.
    """

    current_config: Optional[Dict[str, Any]] = None
    last_updated: Optional[datetime] = None

    def __init__(self):
        """
        Initialize the configuration manager.
        """
        self.current_config = None
        self.last_updated = datetime.now()

    @abstractmethod
    def create_index(self, index_name: str) -> None:
        """
        Create an index or data store if it doesn't exist.
        """
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        Retrieve the latest configuration.
        """
        pass

    @abstractmethod
    def set_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Store a new configuration.
        """
        pass

    @abstractmethod
    def organize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge, version, and timestamp configurations.
        """
        pass
