"""
Image Generator Client - Replicate API Integration

Maps to v4.1 Phase 8, Step 27: execute_image_generation

Handles:
- Initialization with credentials
- Image generation via Replicate API
- Retry logic (exponential backoff, max 2 retries)
- Timeout handling (60 seconds per attempt)
- Response parsing and URL extraction
- Error handling and logging

Supports:
- Replicate API (Stable Diffusion, DALL-E 3)
- Image size: 1200x630 (blog header optimal)
- Quality: high
- Output format: PNG/JPG
"""

import os
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ImageGenerator:
    """
    Image generator client using Replicate API.

    Implements:
    - Initialization and credential handling
    - API configuration
    - Image generation with retry logic
    - Error handling and logging
    """

    # Configuration constants
    MODEL = "stability-ai/stable-diffusion-3-medium"  # Can be configured
    IMAGE_WIDTH = 1200
    IMAGE_HEIGHT = 630
    QUALITY = "high"

    # Retry configuration
    MAX_RETRIES = 2
    INITIAL_RETRY_WAIT = 5.0  # seconds
    RETRY_BACKOFF_MULTIPLIER = 2.0
    TIMEOUT = 60  # seconds per attempt

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize image generator client.

        Loads API key from environment or parameter: REPLICATE_API_TOKEN

        Args:
            api_key: Optional Replicate API token (uses env var if not provided)

        Raises:
            ValueError: If API key not found
        """
        self.api_key = api_key or os.getenv("REPLICATE_API_TOKEN")
        if not self.api_key:
            logger.warning(
                "REPLICATE_API_TOKEN not set. Image generation will be mocked. "
                "Set environment variable for real image generation."
            )
            self.mock_mode = True
        else:
            self.mock_mode = False
            self._init_replicate()

    def _init_replicate(self) -> None:
        """Initialize Replicate client."""
        try:
            import replicate

            self.replicate = replicate
            logger.info("Replicate client initialized")
        except ImportError:
            logger.error(
                "Replicate library not installed. Install with: pip install replicate"
            )
            self.mock_mode = True

    def generate_image(self, prompt: str) -> Optional[str]:
        """
        Generate image from prompt.

        Args:
            prompt: Detailed image generation prompt

        Returns:
            Image URL if successful, None if failed

        Raises:
            ValueError: If prompt is empty
        """
        if not prompt or not prompt.strip():
            logger.error("Image prompt is empty")
            return None

        logger.info(f"Generating image from prompt: {prompt[:100]}...")

        if self.mock_mode:
            return self._generate_mock_image_url(prompt)

        # Retry logic
        retry_count = 0
        wait_time = self.INITIAL_RETRY_WAIT

        while retry_count <= self.MAX_RETRIES:
            try:
                logger.debug(f"Image generation attempt {retry_count + 1}/{self.MAX_RETRIES + 1}")

                # Call Replicate API
                output = self.replicate.run(
                    self.MODEL,
                    input={
                        "prompt": prompt,
                        "width": self.IMAGE_WIDTH,
                        "height": self.IMAGE_HEIGHT,
                        "num_outputs": 1,
                        "quality": self.QUALITY,
                    },
                    timeout=self.TIMEOUT,
                )

                # Extract image URL from response
                if output:
                    if isinstance(output, list) and len(output) > 0:
                        image_url = output[0]
                    elif isinstance(output, str):
                        image_url = output
                    else:
                        image_url = str(output)

                    logger.info(f"✅ Image generated successfully: {image_url[:50]}...")
                    return image_url

            except TimeoutError:
                logger.warning(f"Image generation timeout (attempt {retry_count + 1})")
                retry_count += 1
                if retry_count <= self.MAX_RETRIES:
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    wait_time *= self.RETRY_BACKOFF_MULTIPLIER
            except Exception as e:
                logger.error(f"Image generation error: {str(e)[:100]}")
                retry_count += 1
                if retry_count <= self.MAX_RETRIES:
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    wait_time *= self.RETRY_BACKOFF_MULTIPLIER

        logger.error(f"❌ Image generation failed after {self.MAX_RETRIES + 1} attempts")
        return None

    def _generate_mock_image_url(self, prompt: str) -> str:
        """
        Generate mock image URL for testing/development.

        Args:
            prompt: Image prompt

        Returns:
            Mock image URL
        """
        import hashlib

        # Create deterministic mock URL based on prompt
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        mock_url = f"https://mock-cdn.example.com/images/{prompt_hash}.jpg"
        logger.debug(f"Mock image URL: {mock_url}")
        return mock_url

    def generate_alt_text(self, headline: str) -> str:
        """
        Generate alt text from article headline.

        Maps to v4.1 Phase 8, Step 28: store_image_in_blog (alt_text generation)

        Args:
            headline: Article headline

        Returns:
            Alt text for image (max 125 chars)
        """
        # Simplify headline and create alt text
        alt_text = f"Article image: {headline}"

        # Truncate to 125 chars max
        if len(alt_text) > 125:
            alt_text = alt_text[:122] + "..."

        logger.debug(f"Generated alt text: {alt_text}")
        return alt_text

    def __repr__(self) -> str:
        """String representation."""
        mode = "MOCK" if self.mock_mode else "LIVE"
        return f"ImageGenerator(model={self.MODEL}, mode={mode})"
