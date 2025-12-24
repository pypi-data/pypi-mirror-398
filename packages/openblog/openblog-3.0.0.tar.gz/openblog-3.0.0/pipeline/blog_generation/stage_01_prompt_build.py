"""
Stage 1: Simple Prompt Construction

ABOUTME: Builds prompts using company context instead of complex market templates
ABOUTME: Simple, clean system that focuses on company information only

Builds the main article prompt by:
1. Loading company context (name, industry, description, etc.)
2. Injecting company variables into a simple prompt template
3. Adding optional sections (pain points, competitors, guidelines)
4. Validating prompt structure
5. Storing in context for Stage 2

This approach is SIMPLE and EFFECTIVE:
- Company-focused content generation
- All fields optional except company URL
- Clean prompt structure without market complexity
- Flexible content guidelines and instructions

Combined with tools (googleSearch, urlContext), this creates company-appropriate content.
"""

import logging
from typing import Dict, Any

from ..core import ExecutionContext, Stage
from ..core.company_context import CompanyContext
from ..prompts.simple_article_prompt import build_article_prompt, validate_prompt_inputs

logger = logging.getLogger(__name__)


class PromptBuildStage(Stage):
    """
    Stage 1: Build simple article prompt with company context injection.

    Builds the complete prompt that will be sent to Gemini using company information.
    Simple system without market complexity - company context only.
    """

    stage_num = 1
    stage_name = "Simple Prompt Construction"

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 1: Build simple article prompt using company context.

        Inputs from context:
        - job_config.primary_keyword: Main topic (required)
        - job_config.language: Target language (optional, default: en)
        - company_data: Company information (company_url required, rest optional)

        Outputs to context:
        - prompt: Complete prompt string ready for Gemini
        - company_context: Processed company information

        Args:
            context: ExecutionContext from Stage 0

        Returns:
            Updated context with simple prompt populated

        Raises:
            ValueError: If required fields missing
        """
        logger.info(f"Stage 1: {self.stage_name}")

        # Extract primary keyword (required)
        primary_keyword = context.job_config.get("primary_keyword", "")
        if not primary_keyword:
            raise ValueError("primary_keyword is required")

        # Get company_data first (needed for language detection below)
        company_data = context.company_data or {}

        # Extract language (optional, default to English)
        # Priority: job_config.language > company_data.language > "en"
        language = context.job_config.get("language") or company_data.get("language") or company_data.get("company_language", "en")

        # Extract word count (optional, dynamic)
        word_count = context.job_config.get("word_count")

        # Extract country (optional, for market-specific content)
        country = context.job_config.get("country")

        # Extract content generation instruction (optional, custom instructions)
        content_generation_instruction = context.job_config.get("content_generation_instruction")

        # Extract tone override (optional, overrides company_context.tone)
        tone_override = context.job_config.get("tone")

        # Extract system_prompts (batch-level instructions)
        # These apply to all articles in a batch and merge with article-level instructions
        system_prompts = context.job_config.get("system_prompts", [])
        
        # Handle both dict and CompanyContext inputs
        if isinstance(company_data, dict):
            company_context = CompanyContext.from_dict(company_data)
        else:
            company_context = company_data

        # Validate company context (requires company_url)
        company_context.validate()

        # Convert to prompt variables
        prompt_context = company_context.to_prompt_context()

        logger.debug(f"Keyword: '{primary_keyword}'")
        logger.debug(f"Language: {language}")
        logger.debug(f"Country: {country or 'Not specified'}")
        logger.debug(f"Word count: {word_count or 'Default (1,500-2,500)'}")
        logger.debug(f"Tone override: {tone_override or 'Using company tone'}")
        logger.debug(f"System prompts (batch-level): {len(system_prompts)} items")
        logger.debug(f"Company: {prompt_context.get('company_name', 'Unknown')}")
        logger.debug(f"Company URL: {prompt_context.get('company_url', 'Not provided')}")
        logger.debug(f"Industry: {prompt_context.get('industry', 'Not specified')}")

        # Validate inputs before building prompt
        validate_prompt_inputs(primary_keyword, prompt_context)

        # Build the simple prompt
        try:
            prompt = build_article_prompt(
                primary_keyword=primary_keyword,
                company_context=prompt_context,
                language=language,
                word_count=word_count,
                country=country,
                content_generation_instruction=content_generation_instruction,
                tone_override=tone_override,
                system_prompts=system_prompts
            )
        except Exception as e:
            logger.error(f"Failed to build prompt: {e}")
            raise ValueError(f"Unable to generate prompt: {e}")

        # Validate generated prompt
        if not prompt or len(prompt.strip()) < 500:
            raise ValueError(f"Generated prompt is too short ({len(prompt)} chars, expected > 500)")

        logger.info(f"✅ Simple prompt generated successfully")
        logger.info(f"   Length: {len(prompt)} characters")
        logger.info(f"   Language: {language}")
        logger.info(f"   Keyword: '{primary_keyword}'")
        logger.info(f"   Company: '{prompt_context.get('company_name', 'Unknown')}'")

        # Store in context
        context.prompt = prompt
        context.company_context = company_context
        context.language = language

        return context

    def _validate_prompt(self, prompt: str) -> None:
        """
        Basic prompt validation.
        
        Args:
            prompt: Prompt string to validate
            
        Raises:
            ValueError: If prompt is invalid
        """
        if not prompt or len(prompt.strip()) == 0:
            raise ValueError("Prompt is empty")
        
        if len(prompt) < 500:
            raise ValueError(f"Prompt too short ({len(prompt)} chars, expected > 500)")

        # Check for basic content
        if "Write a comprehensive" not in prompt and "write" not in prompt.lower():
            raise ValueError("Prompt doesn't appear to contain writing instructions")