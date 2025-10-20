"""
CSM.ai API client for generative 3D assets.
CSM (Common Sense Machines) provides text-to-3D generation capabilities.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
import aiohttp
import asyncio
import time

from .base import Generative3DClient


class CSMClient(Generative3DClient):
    """Client for CSM.ai generative 3D API."""

    BASE_URL = "https://api.csm.ai/v1"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CSM client.

        Args:
            api_key: CSM API key. If None, reads from CSM_API_KEY environment variable.
        """
        super().__init__(api_key or os.getenv("CSM_API_KEY"))
        if not self.api_key:
            raise ValueError(
                "CSM API key is required. Provide it as argument or set CSM_API_KEY env var."
            )

    async def generate_from_prompt(
        self,
        prompt: str,
        output_format: str = "usd",
        output_dir: Optional[Path] = None,
        quality: str = "medium",
        timeout: int = 300,
        **kwargs
    ) -> Path:
        """
        Generate 3D asset from text prompt using CSM.ai.

        Args:
            prompt: Text description of the 3D asset
            output_format: Output format (usd, obj, glb)
            output_dir: Directory to save the output file
            quality: Quality level (low, medium, high)
            timeout: Maximum time to wait for generation (seconds)
            **kwargs: Additional CSM-specific parameters

        Returns:
            Path to the generated asset file
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        if output_dir is None:
            output_dir = Path("generated_assets")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Start generation job
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": prompt,
            "output_format": output_format,
            "quality": quality,
            **kwargs
        }

        async with aiohttp.ClientSession() as session:
            # Submit generation request
            async with session.post(
                f"{self.BASE_URL}/generate",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(
                        f"CSM API request failed: {response.status} - {error_text}"
                    )

                result = await response.json()
                job_id = result.get("job_id")

                if not job_id:
                    raise RuntimeError("No job_id returned from CSM API")

            # Poll for completion
            start_time = time.time()
            while time.time() - start_time < timeout:
                status = await self.check_generation_status(job_id)

                if status["state"] == "completed":
                    download_url = status.get("download_url")
                    if not download_url:
                        raise RuntimeError("No download URL in completed job")

                    # Download the asset
                    output_path = output_dir / f"{job_id}.{output_format}"
                    async with session.get(download_url) as dl_response:
                        if dl_response.status != 200:
                            raise RuntimeError(f"Failed to download asset: {dl_response.status}")

                        content = await dl_response.read()
                        output_path.write_bytes(content)

                    return output_path

                elif status["state"] == "failed":
                    error_msg = status.get("error", "Unknown error")
                    raise RuntimeError(f"CSM generation failed: {error_msg}")

                # Wait before polling again
                await asyncio.sleep(5)

            raise TimeoutError(f"CSM generation timed out after {timeout} seconds")

    async def check_generation_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check status of a CSM generation job.

        Args:
            job_id: Job identifier

        Returns:
            Status dictionary with keys: state, progress, download_url (if completed)
        """
        if not job_id:
            raise ValueError("job_id cannot be empty")

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/jobs/{job_id}",
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(
                        f"Failed to check job status: {response.status} - {error_text}"
                    )

                return await response.json()
