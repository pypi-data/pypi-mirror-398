"""
Stage 6: Image/Graphics Generation

Maps to v4.1 Phase 8, Steps 25-28: get-insights → image_empty? → execute_image_generation → store_image_in_blog

Generates **3 article images or graphics**:
1. Hero image/graphic (from headline)
2. Mid-article image/graphic (from sections 3-4)
3. Bottom image/graphic (from sections 6-7)

Supports two modes:
- Image generation (default): Uses Gemini Image Creator (gemini-2.5-flash-image)
- Graphics generation (optional): Uses OpenFigma for HTML-based graphics in company design language

Input:
  - ExecutionContext.structured_data (headline + section titles)
  - ExecutionContext.company_data (industry, description)
  - ExecutionContext.job_config (language, use_graphics flag)

Output:
  - ExecutionContext.parallel_results['image_url'] (Hero CDN URL)
  - ExecutionContext.parallel_results['image_alt_text'] (Hero alt text)
  - ExecutionContext.parallel_results['mid_image_url'] (Mid CDN URL)
  - ExecutionContext.parallel_results['mid_image_alt'] (Mid alt text)
  - ExecutionContext.parallel_results['bottom_image_url'] (Bottom CDN URL)
  - ExecutionContext.parallel_results['bottom_image_alt'] (Bottom alt text)

Process:
1. Check if images already exist (conditional skip)
2. Check job_config['use_graphics'] to determine mode
3. Generate images or graphics based on mode:
   - Images: Get image generation prompts from headline + section titles, call image generator
   - Graphics: Get graphics configs from headline + section titles, call graphics generator
4. Generate alt texts
5. Store results in parallel_results
"""

import logging
from typing import Optional

from ..core.execution_context import ExecutionContext
from ..core.workflow_engine import Stage
from ..core.error_handling import with_image_fallback, GracefulDegradation, error_reporter
from ..models.google_imagen_client import GoogleImagenClient
from ..models.image_generator import ImageGenerator  # Keep as fallback
from ..prompts.image_prompt import generate_image_prompt
from ..prompts.graphics_prompt import generate_graphics_config

logger = logging.getLogger(__name__)


class ImageStage(Stage):
    """
    Stage 6: Image/Graphics Generation.

    Handles:
    - Conditional skip (if images already exist)
    - Image or graphics generation based on job_config['use_graphics']
    - Image prompt generation from headline + section titles (image mode)
    - Graphics config generation from headline + section titles (graphics mode)
    - Google Imagen API integration (image mode, 3x calls)
    - OpenFigma graphics generation (graphics mode, 3x calls)
    - Alt text generation (3x)
    - Error handling and retry logic
    """

    stage_num = 6
    stage_name = "Image/Graphics Generation"

    def __init__(self) -> None:
        """Initialize image stage with lazy loading to avoid import hangs."""
        # Lazy initialization - defer Google Imagen and Replicate initialization until first use
        self.primary_generator = None
        self.fallback_generator = None
        self._graphics_generator = None
        self._generators_initialized = False
        
        logger.info("Image stage initialized with lazy loading")

    def _ensure_generators_initialized(self):
        """Initialize generators on first use to avoid import hangs."""
        if self._generators_initialized:
            return
            
        # Try Google Imagen first (primary)
        try:
            self.primary_generator = GoogleImagenClient()
            if not self.primary_generator.mock_mode:
                logger.info("Using Imagen 4.0 for image generation (via Gemini SDK)")
            else:
                logger.warning("⚠️ Imagen 4.0 in mock mode - check GEMINI_API_KEY environment variable")
        except Exception as e:
            logger.error(f"❌ Google Imagen initialization failed: {e}")
            self.primary_generator = None
        
        # Initialize Replicate fallback
        try:
            self.fallback_generator = ImageGenerator()
            logger.info("Replicate fallback generator initialized")
        except Exception as e:
            logger.warning(f"Replicate fallback initialization failed: {e}")
            self.fallback_generator = None
        
        self._generators_initialized = True

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 6: Generate 3 article images or graphics.

        Input from context:
        - structured_data: ArticleOutput with headline + section titles
        - company_data: Company information
        - job_config: Job configuration with language and use_graphics flag

        Output to context:
        - parallel_results['image_url']: Hero image/graphic CDN URL
        - parallel_results['image_alt_text']: Hero alt text
        - parallel_results['mid_image_url']: Mid-article image/graphic URL
        - parallel_results['mid_image_alt']: Mid alt text
        - parallel_results['bottom_image_url']: Bottom image/graphic URL
        - parallel_results['bottom_image_alt']: Bottom alt text

        Args:
            context: ExecutionContext from parallel stages

        Returns:
            Updated context with parallel_results populated
        """
        # Initialize generators on first use (lazy loading to avoid import hangs)
        self._ensure_generators_initialized()
        
        # Check if graphics mode is enabled
        use_graphics = context.job_config.get("use_graphics", False)
        mode_name = "graphics" if use_graphics else "images"
        
        logger.info(f"Stage 6: {self.stage_name} (3 {mode_name})")

        # Validate input
        if not context.structured_data:
            logger.warning(f"No structured_data available for {mode_name} generation")
            context.parallel_results["image_url"] = ""
            context.parallel_results["image_alt_text"] = ""
            context.parallel_results["mid_image_url"] = ""
            context.parallel_results["mid_image_alt"] = ""
            context.parallel_results["bottom_image_url"] = ""
            context.parallel_results["bottom_image_alt"] = ""
            return context

        headline = context.structured_data.Headline
        
        # Extract section titles for mid and bottom images
        mid_title = self._get_section_title(context.structured_data, [3, 4]) or headline
        bottom_title = self._get_section_title(context.structured_data, [6, 7]) or headline
        
        logger.info(f"Generating 3 {mode_name}:")
        logger.info(f"  Hero: {headline[:50]}...")
        logger.info(f"  Mid: {mid_title[:50]}...")
        logger.info(f"  Bottom: {bottom_title[:50]}...")

        if use_graphics:
            # Graphics generation mode - PARALLELIZED
            from pipeline.prompts.graphics_prompt import generate_graphics_config_async
            import asyncio
            
            # Generate all configs in parallel
            async def generate_graphic_with_alt(title: str, position: str):
                """Generate graphic config, then graphic, then return URL and alt text."""
                config = await generate_graphics_config_async(
                    headline=title,
                    company_data=context.company_data,
                    job_config=context.job_config,
                )
                url = await self._generate_graphic_with_retry(config, context)
                alt = self._generate_alt_text(title)
                
                # Ensure url is a string
                url = url if isinstance(url, str) else (url.get("image_url", "") if isinstance(url, dict) else "")
                return url or "", alt
            
            # Generate all 3 graphics in parallel
            logger.info("   🔄 Generating 3 graphics in parallel...")
            hero_result, mid_result, bottom_result = await asyncio.gather(
                generate_graphic_with_alt(headline, "hero"),
                generate_graphic_with_alt(mid_title, "mid"),
                generate_graphic_with_alt(bottom_title, "bottom"),
                return_exceptions=True
            )
            
            # Process results
            hero_url, hero_alt = hero_result if not isinstance(hero_result, Exception) else ("", self._generate_alt_text(headline))
            if isinstance(hero_result, Exception):
                logger.debug(f"   ⚠️ Hero graphic generation failed: {hero_result}")
            
            mid_url, mid_alt = mid_result if not isinstance(mid_result, Exception) else ("", self._generate_alt_text(mid_title))
            if isinstance(mid_result, Exception):
                logger.debug(f"   ⚠️ Mid graphic generation failed: {mid_result}")
            
            bottom_url, bottom_alt = bottom_result if not isinstance(bottom_result, Exception) else ("", self._generate_alt_text(bottom_title))
            if isinstance(bottom_result, Exception):
                logger.debug(f"   ⚠️ Bottom graphic generation failed: {bottom_result}")
            
            # Store results
            context.parallel_results["image_url"] = hero_url
            context.parallel_results["image_alt_text"] = hero_alt
            context.parallel_results["mid_image_url"] = mid_url
            context.parallel_results["mid_image_alt"] = mid_alt
            context.parallel_results["bottom_image_url"] = bottom_url
            context.parallel_results["bottom_image_alt"] = bottom_alt

            graphics_generated = sum([bool(hero_url), bool(mid_url), bool(bottom_url)])
            logger.info(f"✅ Generated {graphics_generated}/3 graphics successfully")
        else:
            # Image generation mode (default) - PARALLELIZED
            import asyncio
            
            # Generate all prompts (synchronous, fast)
            hero_prompt = generate_image_prompt(
                headline=headline,
                company_data=context.company_data,
                job_config=context.job_config,
            )
            mid_prompt = generate_image_prompt(
                headline=mid_title,
                company_data=context.company_data,
                job_config=context.job_config,
            )
            bottom_prompt = generate_image_prompt(
                headline=bottom_title,
                company_data=context.company_data,
                job_config=context.job_config,
            )
            
            # Generate all 3 images in parallel
            async def generate_image_with_alt(prompt: str, title: str):
                """Generate image and return URL and alt text."""
                url = await self._generate_image_with_retry(prompt, context)
                alt = self._generate_alt_text(title)
                
                # Ensure url is a string
                url = url if isinstance(url, str) else (url.get("image_url", "") if isinstance(url, dict) else "")
                return url or "", alt
            
            logger.info("   🔄 Generating 3 images in parallel...")
            hero_result, mid_result, bottom_result = await asyncio.gather(
                generate_image_with_alt(hero_prompt, headline),
                generate_image_with_alt(mid_prompt, mid_title),
                generate_image_with_alt(bottom_prompt, bottom_title),
                return_exceptions=True
            )
            
            # Process results
            hero_url, hero_alt = hero_result if not isinstance(hero_result, Exception) else ("", self._generate_alt_text(headline))
            if isinstance(hero_result, Exception):
                logger.debug(f"   ⚠️ Hero image generation failed: {hero_result}")
            
            mid_url, mid_alt = mid_result if not isinstance(mid_result, Exception) else ("", self._generate_alt_text(mid_title))
            if isinstance(mid_result, Exception):
                logger.debug(f"   ⚠️ Mid image generation failed: {mid_result}")
            
            bottom_url, bottom_alt = bottom_result if not isinstance(bottom_result, Exception) else ("", self._generate_alt_text(bottom_title))
            if isinstance(bottom_result, Exception):
                logger.debug(f"   ⚠️ Bottom image generation failed: {bottom_result}")
            
            # Store results
            context.parallel_results["image_url"] = hero_url
            context.parallel_results["image_alt_text"] = hero_alt
            context.parallel_results["mid_image_url"] = mid_url
            context.parallel_results["mid_image_alt"] = mid_alt
            context.parallel_results["bottom_image_url"] = bottom_url
            context.parallel_results["bottom_image_alt"] = bottom_alt

            images_generated = sum([bool(hero_url), bool(mid_url), bool(bottom_url)])
            logger.info(f"✅ Generated {images_generated}/3 images successfully")

        return context

    @with_image_fallback("stage_09")
    async def _generate_image_with_retry(self, image_prompt: str, context: ExecutionContext) -> Optional[str]:
        """
        Generate image with comprehensive error handling and retries.
        
        Args:
            image_prompt: Generated image prompt
            context: Execution context
            
        Returns:
            Image URL if successful, fallback URL if failed
        """
        try:
            image_url = self._generate_image_with_fallback(image_prompt, context)
            
            if not image_url:
                raise Exception("All image generation services failed")
                
            return image_url
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            # The decorator will handle fallback to placeholder image
            raise e

    def _generate_image_with_fallback(self, image_prompt: str, context: ExecutionContext) -> Optional[str]:
        """
        Generate image using Google Imagen (primary) with Replicate fallback.
        
        Args:
            image_prompt: Generated image prompt
            context: Execution context (for project folder ID if needed)
            
        Returns:
            Image URL if successful, None if failed
        """
        # Try Google Imagen first (force real image generation)
        if self.primary_generator:
            logger.info("Attempting image generation with Imagen 4.0...")
            try:
                # Extract project folder ID if available
                project_folder_id = context.company_data.get("project_folder_id")
                image_url = self.primary_generator.generate_image(image_prompt, project_folder_id)
                
                # Check if we got a real image URL (not a mock)
                if image_url and not image_url.startswith("https://drive.google.com/uc?id="):
                    logger.info("✅ Imagen 4.0 generation successful")
                    return image_url
                elif image_url and image_url.startswith("https://drive.google.com/uc?id="):
                    logger.warning("⚠️ Imagen 4.0 returned mock URL - API key may be missing or invalid")
                else:
                    logger.warning("⚠️ Imagen 4.0 generation returned empty result")
            except Exception as e:
                logger.error(f"❌ Google Imagen error: {e}")
        else:
            logger.warning("⚠️ Primary image generator not available")
        
        # Try Replicate fallback
        if self.fallback_generator:
            logger.info("Attempting image generation with Replicate fallback...")
            try:
                image_url = self.fallback_generator.generate_image(image_prompt)
                
                # Check if we got a real image URL (not a mock)
                if image_url and not image_url.startswith("https://drive.google.com/uc?id="):
                    logger.info("✅ Replicate fallback generation successful")
                    return image_url
                elif image_url and image_url.startswith("https://drive.google.com/uc?id="):
                    logger.warning("⚠️ Replicate returned mock URL - API key may be missing or invalid")
                else:
                    logger.warning("⚠️ Replicate generation returned empty result")
            except Exception as e:
                logger.error(f"❌ Replicate error: {e}")
        else:
            logger.warning("⚠️ Fallback image generator not available")
        
        # Both failed, create better mock URL with clear identification
        logger.error("❌ All image generators failed - using clearly identifiable mock URL")
        if self.primary_generator:
            return self.primary_generator._generate_mock_image_url(image_prompt)
        elif self.fallback_generator:
            return self.fallback_generator._generate_mock_image_url(image_prompt)
        else:
            # Final fallback - create clearly identifiable mock URL
            import hashlib
            prompt_hash = hashlib.md5(image_prompt.encode()).hexdigest()
            logger.warning(f"⚠️ Using final fallback mock URL for prompt: {image_prompt[:100]}...")
            return f"https://drive.google.com/uc?id=MOCK-{prompt_hash}&export=view"

    def _generate_alt_text(self, headline: str) -> str:
        """
        Generate alt text from article headline.
        
        Args:
            headline: Article headline
            
        Returns:
            Alt text for image (max 125 chars)
        """
        if self.primary_generator:
            return self.primary_generator.generate_alt_text(headline)
        elif self.fallback_generator:
            return self.fallback_generator.generate_alt_text(headline)
        else:
            # Fallback alt text generation
            alt_text = f"Article image: {headline}"
            if len(alt_text) > 125:
                alt_text = alt_text[:122] + "..."
            return alt_text

    def _get_graphics_generator(self):
        """Lazy initialization of graphics generator."""
        if self._graphics_generator is None:
            try:
                from service.graphics_generator import GraphicsGenerator
                self._graphics_generator = GraphicsGenerator()
                logger.info("Graphics generator initialized")
            except Exception as e:
                logger.warning(f"Graphics generator initialization failed: {e}")
                self._graphics_generator = None
        return self._graphics_generator

    @with_image_fallback("stage_09")
    async def _generate_graphic_with_retry(self, graphics_config: dict, context: ExecutionContext) -> Optional[str]:
        """
        Generate graphic with comprehensive error handling and retries.
        
        Args:
            graphics_config: Generated graphics config dict
            context: Execution context
            
        Returns:
            Graphic URL if successful, fallback URL if failed
        """
        try:
            generator = self._get_graphics_generator()
            if not generator:
                raise Exception("Graphics generator not available")
            
            # Extract project folder ID if available
            project_folder_id = context.company_data.get("project_folder_id")
            
            # Generate graphic (dimensions: 1200x630 for blog header)
            result = await generator.generate_from_config(
                config=graphics_config,
                dimensions=(1200, 630),  # Blog header optimal size
                project_folder_id=project_folder_id,
            )
            
            if result.success and result.image_url:
                logger.info("✅ Graphics generation successful")
                return result.image_url
            else:
                raise Exception(f"Graphics generation failed: {result.error}")
                
        except Exception as e:
            logger.error(f"Graphics generation failed: {e}")
            # The decorator will handle fallback to placeholder image
            raise e

    def _get_section_title(self, structured_data, section_nums: list) -> Optional[str]:
        """
        Get the first non-empty section title from a list of section numbers.
        
        Args:
            structured_data: ArticleOutput object
            section_nums: List of section numbers to try (e.g., [3, 4])
            
        Returns:
            First non-empty section title, or None if all are empty
        """
        for num in section_nums:
            title_key = f"section_{num:02d}_title"
            title = getattr(structured_data, title_key, "")
            if title and title.strip():
                return title.strip()
        return None

    def __repr__(self) -> str:
        """String representation."""
        primary = "GoogleImagen4.0" if self.primary_generator and not self.primary_generator.mock_mode else "Mock"
        fallback = "Replicate" if self.fallback_generator and not getattr(self.fallback_generator, 'mock_mode', True) else "Mock"
        graphics = "Available" if self._graphics_generator else "Not initialized"
        return f"ImageStage(primary={primary}, fallback={fallback}, graphics={graphics})"
