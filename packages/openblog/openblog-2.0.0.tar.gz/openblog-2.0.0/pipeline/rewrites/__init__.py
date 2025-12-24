"""
Rewrites Module - Targeted Article Rewriting

This module provides surgical edit capabilities for:
1. Quality fixes (Stage 2b) - keyword density, paragraph length, AI markers
2. Content refresh (API endpoint) - update content with new information

Key Components:
- RewriteEngine: Core rewrite logic
- RewriteInstruction: Rewrite configuration
- RewriteResult: Rewrite outcome
- targeted_rewrite(): Convenience function

Example Usage (Quality Fix):
    from pipeline.rewrites import targeted_rewrite, RewriteInstruction, RewriteMode
    
    instruction = RewriteInstruction(
        target="section_03_content",
        instruction="Reduce keyword mentions from 12 to 5-8",
        mode=RewriteMode.QUALITY_FIX
    )
    
    updated_article = await targeted_rewrite(
        article=article_dict,
        rewrites=[instruction]
    )

Example Usage (Content Refresh):
    instruction = RewriteInstruction(
        target="section_02_content",
        instruction="Update statistics with Q4 2025 data",
        mode=RewriteMode.REFRESH
    )
    
    updated_article = await targeted_rewrite(
        article=article_dict,
        rewrites=[instruction]
    )
"""

from .rewrite_engine import (
    RewriteEngine,
    targeted_rewrite
)

from .rewrite_instructions import (
    RewriteInstruction,
    RewriteResult,
    RewriteMode,
    RewriteTarget,
    RewriteBatchRequest,
    RewriteBatchResponse,
    QUALITY_FIX_TEMPLATES
)

from .rewrite_prompts import (
    get_quality_fix_prompt,
    get_refresh_prompt,
    get_keyword_reduction_prompt,
    get_paragraph_expansion_prompt,
    get_ai_marker_removal_prompt
)

__all__ = [
    # Core engine
    "RewriteEngine",
    "targeted_rewrite",
    
    # Models
    "RewriteInstruction",
    "RewriteResult",
    "RewriteMode",
    "RewriteTarget",
    "RewriteBatchRequest",
    "RewriteBatchResponse",
    
    # Prompt builders
    "get_quality_fix_prompt",
    "get_refresh_prompt",
    "get_keyword_reduction_prompt",
    "get_paragraph_expansion_prompt",
    "get_ai_marker_removal_prompt",
    
    # Templates
    "QUALITY_FIX_TEMPLATES"
]

