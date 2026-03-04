"""
Base connector interface for Kensa-AI.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

import structlog


logger = structlog.get_logger()


class BaseConnector(ABC):
    """
    Abstract base class for target connectors.
    
    Connectors normalize how prompts are sent to different AI APIs.
    """
    
    def __init__(self, config: Any):
        """
        Initialize the connector.
        
        Args:
            config: Configuration object with connection details
        """
        self.config = config
        self._logger = logger.bind(connector=self.__class__.__name__)
    
    @abstractmethod
    async def send_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Send a prompt to the target AI system.
        
        Args:
            prompt: The user prompt to send
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Returns:
            The response text from the AI system
        """
        pass
    
    @abstractmethod
    async def validate(self) -> bool:
        """
        Validate the connection to the target.
        
        Returns:
            True if connection is valid
            
        Raises:
            ConnectionError: If connection fails
        """
        pass
    
    async def close(self) -> None:
        """Clean up resources."""
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(base_url={getattr(self.config, 'base_url', 'N/A')})"
