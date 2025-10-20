"""
Spline AI API client for generative 3D assets.
Spline provides AI-powered 3D generation and modeling capabilities.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
import aiohttp
import asyncio
import time

from .base import Generative3DClient


class SplineClient(Generative3DClient):
    """Client for Spline AI generative 3D API."""

    BASE_URL = "https://api.spline.design/v1"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Spline client.

        Args:
            api_key: Spline API key. If None, reads from SPLINE_API_KEY environment variable.
        """
        super().__init__(api_key or os.getenv("SPLINE_API_KEY"))
        if not self.api_key:
            raise ValueError(
                "Spline API key is required. Provide it as argument or set SPLINE_API_KEY env var."
            )

    async def generate_from_prompt(
        self,
        prompt: str,
        output_format: str = "usd",
        output_dir: Optional[Path] = None,
        style: str = "realistic",
        resolution: str = "1k",
        timeout: int = 300,
        **kwargs
    ) -> Path:
        """
        Generate 3D asset from text prompt using Spline AI.

        Args:
            prompt: Text description of the 3D asset
            output_format: Output format (usd, obj, glb, fbx)
            output_dir: Directory to save the output file
            style: Style preset (realistic, stylized, low_poly, etc.)
            resolution: Texture resolution (512, 1k, 2k, 4k)
            timeout: Maximum time to wait for generation (seconds)
            **kwargs: Additional Spline-specific parameters

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
            "style": style,
            "resolution": resolution,
            **kwargs
        }

        async with aiohttp.ClientSession() as session:
            # Submit generation request
            async with session.post(
                f"{self.BASE_URL}/ai/generate-3d",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(
                        f"Spline API request failed: {response.status} - {error_text}"
                    )

                result = await response.json()
                job_id = result.get("generation_id")

                if not job_id:
                    raise RuntimeError("No generation_id returned from Spline API")

            # Poll for completion
            start_time = time.time()
            while time.time() - start_time < timeout:
                status = await self.check_generation_status(job_id)

                if status["status"] == "completed":
                    asset_url = status.get("asset_url")
                    if not asset_url:
                        raise RuntimeError("No asset URL in completed generation")

                    # Download the asset
                    output_path = output_dir / f"{job_id}.{output_format}"
                    async with session.get(asset_url) as dl_response:
                        if dl_response.status != 200:
                            raise RuntimeError(f"Failed to download asset: {dl_response.status}")

                        content = await dl_response.read()
                        output_path.write_bytes(content)

                    return output_path

                elif status["status"] in ["failed", "error"]:
                    error_msg = status.get("message", "Unknown error")
                    raise RuntimeError(f"Spline generation failed: {error_msg}")

                # Wait before polling again
                await asyncio.sleep(5)

            raise TimeoutError(f"Spline generation timed out after {timeout} seconds")

    async def check_generation_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check status of a Spline generation job.

        Args:
            job_id: Generation identifier

        Returns:
            Status dictionary with keys: status, progress, asset_url (if completed)
        """
        if not job_id:
            raise ValueError("job_id cannot be empty")

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/ai/generation/{job_id}",
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(
                        f"Failed to check generation status: {response.status} - {error_text}"
                    )

                return await response.json()
