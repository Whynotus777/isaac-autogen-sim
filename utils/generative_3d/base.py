"""
Base class for generative 3D API clients.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path
import asyncio


class Generative3DClient(ABC):
    """Abstract base class for generative 3D API clients."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the client.

        Args:
            api_key: API key for authentication. If None, will try to read from environment.
        """
        self.api_key = api_key

    @abstractmethod
    async def generate_from_prompt(
        self,
        prompt: str,
        output_format: str = "usd",
        **kwargs
    ) -> Path:
        """
        Generate a 3D asset from a text prompt.

        Args:
            prompt: Text description of the desired 3D asset
            output_format: Desired output format (usd, obj, glb, etc.)
            **kwargs: Additional provider-specific parameters

        Returns:
            Path to the generated 3D asset file

        Raises:
            ValueError: If the prompt is invalid or empty
            RuntimeError: If the generation fails
        """
        pass

    @abstractmethod
    async def check_generation_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the status of a generation job.

        Args:
            job_id: Unique identifier for the generation job

        Returns:
            Dictionary containing status information

        Raises:
            ValueError: If the job_id is invalid
        """
        pass

    def generate_sync(
        self,
        prompt: str,
        output_format: str = "usd",
        **kwargs
    ) -> Path:
        """
        Synchronous wrapper for generate_from_prompt.

        Args:
            prompt: Text description of the desired 3D asset
            output_format: Desired output format
            **kwargs: Additional parameters

        Returns:
            Path to the generated 3D asset file
        """
        return asyncio.run(self.generate_from_prompt(prompt, output_format, **kwargs))
