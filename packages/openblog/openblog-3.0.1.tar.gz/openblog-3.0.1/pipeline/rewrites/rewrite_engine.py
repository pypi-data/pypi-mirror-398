"""
Rewrite Engine - Core targeted rewrite functionality.

This is the heart of the surgical edit system.
Handles both quality fixes (Stage 2b) and content refresh (API endpoint).
"""

import logging
import time
import re
import os
from typing import Dict, Any, List, Optional
from difflib import SequenceMatcher

from .rewrite_instructions import (
    RewriteInstruction,
    RewriteResult,
    RewriteMode,
    RewriteBatchRequest,
    RewriteBatchResponse
)
from .rewrite_prompts import (
    get_quality_fix_prompt,
    get_refresh_prompt,
    get_keyword_reduction_prompt,
    get_paragraph_expansion_prompt,
    get_ai_marker_removal_prompt
)
from ..models.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class RewriteEngine:
    """
    Core engine for targeted article rewrites.
    
    Supports two modes:
    - quality_fix: Fix quality issues (keyword density, paragraph length, AI markers)
    - refresh: Update content with new information
    
    Key features:
    - Surgical edits (minimal changes)
    - Validation (diff check, citation check)
    - Retry logic
    - Rollback on failure
    """
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """
        Initialize rewrite engine.
        
        Args:
            gemini_client: Optional GeminiClient instance (creates new if None)
        """
        self.gemini_client = gemini_client or GeminiClient()
        self.logger = logger
    
    async def rewrite(
        self,
        article: Dict[str, Any],
        instruction: RewriteInstruction
    ) -> RewriteResult:
        """
        Execute a single targeted rewrite.
        
        Args:
            article: Article data (ArticleOutput.dict())
            instruction: Rewrite instruction
        
        Returns:
            RewriteResult with success status and updated content
        """
        start_time = time.time()
        
        # Extract original content
        original_content = self._get_field(article, instruction.target)
        
        if not original_content:
            return RewriteResult(
                target=instruction.target,
                success=False,
                original_content="",
                updated_content=None,
                attempts_used=0,
                validation_passed=False,
                error_message=f"Field '{instruction.target}' not found or empty"
            )
        
        self.logger.info(f"Rewriting {instruction.target} (mode={instruction.mode})")
        
        # Try up to max_attempts times
        for attempt in range(1, instruction.max_attempts + 1):
            try:
                self.logger.debug(f"  Attempt {attempt}/{instruction.max_attempts}")
                
                # Build prompt
                prompt = self._build_prompt(
                    original_content=original_content,
                    instruction=instruction,
                    article=article
                )
                
                # Call Gemini
                updated_content = await self._call_gemini(
                    prompt=prompt,
                    temperature=instruction.temperature
                )
                
                # Validate the edit
                validation_result = self._validate_edit(
                    original=original_content,
                    updated=updated_content,
                    instruction=instruction
                )
                
                if validation_result["valid"]:
                    # Success!
                    execution_time = time.time() - start_time
                    
                    self.logger.info(
                        f"✅ Rewrite successful: {instruction.target} "
                        f"(similarity={validation_result['similarity']:.2f}, attempts={attempt}, time={execution_time:.1f}s)"
                    )
                    
                    return RewriteResult(
                        target=instruction.target,
                        success=True,
                        original_content=original_content,
                        updated_content=updated_content,
                        similarity_score=validation_result["similarity"],
                        attempts_used=attempt,
                        validation_passed=True,
                        metadata={
                            "execution_time": execution_time,
                            "validation_details": validation_result
                        }
                    )
                else:
                    # Validation failed, retry
                    self.logger.warning(
                        f"  ⚠️  Validation failed: {validation_result['reason']} "
                        f"(similarity={validation_result['similarity']:.2f})"
                    )
                    
                    if attempt == instruction.max_attempts:
                        # Last attempt failed
                        execution_time = time.time() - start_time
                        
                        return RewriteResult(
                            target=instruction.target,
                            success=False,
                            original_content=original_content,
                            updated_content=updated_content,
                            similarity_score=validation_result["similarity"],
                            attempts_used=attempt,
                            validation_passed=False,
                            error_message=f"Validation failed: {validation_result['reason']}",
                            metadata={
                                "execution_time": execution_time,
                                "validation_details": validation_result
                            }
                        )
            
            except Exception as e:
                self.logger.error(f"  ❌ Rewrite error on attempt {attempt}: {str(e)}")
                
                if attempt == instruction.max_attempts:
                    # Last attempt failed
                    execution_time = time.time() - start_time
                    
                    return RewriteResult(
                        target=instruction.target,
                        success=False,
                        original_content=original_content,
                        updated_content=None,
                        attempts_used=attempt,
                        validation_passed=False,
                        error_message=f"Exception: {str(e)}",
                        metadata={"execution_time": execution_time}
                    )
        
        # Should never reach here
        return RewriteResult(
            target=instruction.target,
            success=False,
            original_content=original_content,
            updated_content=None,
            attempts_used=instruction.max_attempts,
            validation_passed=False,
            error_message="Unknown error"
        )
    
    async def rewrite_batch(
        self,
        request: RewriteBatchRequest
    ) -> RewriteBatchResponse:
        """
        Execute multiple rewrites in sequence.
        
        Args:
            request: Batch rewrite request
        
        Returns:
            RewriteBatchResponse with all results
        """
        start_time = time.time()
        
        updated_article = request.article.copy()
        results = []
        total_attempts = 0
        failures = 0
        
        for i, instruction in enumerate(request.rewrites, 1):
            self.logger.info(f"Executing rewrite {i}/{len(request.rewrites)}: {instruction.target}")
            
            # Execute rewrite
            result = await self.rewrite(
                article=updated_article,
                instruction=instruction
            )
            
            results.append(result)
            total_attempts += result.attempts_used
            
            if result.success:
                # Apply the update
                updated_article = self._set_field(
                    updated_article,
                    result.target,
                    result.updated_content
                )
            else:
                failures += 1
                self.logger.warning(f"⚠️  Rewrite failed: {result.error_message}")
                
                if request.stop_on_failure:
                    self.logger.warning("Stopping batch on failure (stop_on_failure=True)")
                    break
        
        execution_time = time.time() - start_time
        success = failures == 0
        
        self.logger.info(
            f"{'✅' if success else '⚠️ '} Batch complete: "
            f"{len(results)} rewrites, {failures} failures, {total_attempts} attempts, {execution_time:.1f}s"
        )
        
        return RewriteBatchResponse(
            success=success,
            updated_article=updated_article,
            results=results,
            total_attempts=total_attempts,
            total_time=execution_time,
            failures=failures
        )
    
    def _build_prompt(
        self,
        original_content: str,
        instruction: RewriteInstruction,
        article: Dict[str, Any]
    ) -> str:
        """
        Build the Gemini prompt based on instruction mode.
        """
        context = instruction.context or {}
        context.update({
            "primary_keyword": article.get("primary_keyword", ""),
            "headline": article.get("Headline", "")
        })
        
        # Check for specialized builders first
        if instruction.mode == RewriteMode.QUALITY_FIX:
            # Check if this is a keyword reduction fix
            if "keyword" in context and "current_count" in context:
                return get_keyword_reduction_prompt(
                    original_content=original_content,
                    keyword=context["keyword"],
                    current_count=context["current_count"],
                    target_min=context.get("target_min", 5),
                    target_max=context.get("target_max", 8),
                    variations=context.get("variations", [])
                )
            
            # Check if this is a paragraph expansion fix
            if "current_words" in context:
                return get_paragraph_expansion_prompt(
                    original_content=original_content,
                    current_words=context["current_words"],
                    target_min=context.get("target_min", 60),
                    target_max=context.get("target_max", 100),
                    paragraph_index=context.get("paragraph_index", 1)
                )
            
            # Check if this is AI marker removal
            if "markers_found" in context:
                return get_ai_marker_removal_prompt(
                    original_content=original_content,
                    markers_found=context["markers_found"]
                )
            
            # Default quality fix prompt
            return get_quality_fix_prompt(
                original_content=original_content,
                instruction=instruction.instruction,
                target_field=instruction.target,
                context=context
            )
        
        elif instruction.mode == RewriteMode.REFRESH:
            return get_refresh_prompt(
                original_content=original_content,
                instruction=instruction.instruction,
                target_field=instruction.target,
                context=context
            )
        
        elif instruction.mode == RewriteMode.COMPREHENSIVE_TRANSFORM:
            from .rewrite_prompts import get_comprehensive_content_transformation_prompt
            return get_comprehensive_content_transformation_prompt(
                original_content=original_content,
                citations=context.get("citations", []),
                primary_keyword=context.get("primary_keyword", ""),
                company_name=context.get("company_name", "")
            )
        
        else:
            raise ValueError(f"Unsupported rewrite mode: {instruction.mode}")
    
    async def _call_gemini(self, prompt: str, temperature: float) -> str:
        """
        Call Gemini API for rewrite.
        
        Returns raw text output (not JSON).
        """
        # Note: GeminiClient doesn't support temperature parameter directly
        # It uses the default model temperature
        response = await self.gemini_client.generate_content(
            prompt=prompt,
            enable_tools=False,  # No grounding needed for rewrites
            response_schema=None  # Raw text output
        )
        
        return response.strip()
    
    def _validate_edit(
        self,
        original: str,
        updated: str,
        instruction: RewriteInstruction
    ) -> Dict[str, Any]:
        """
        Validate that the edit meets requirements.
        
        Returns:
            {"valid": bool, "reason": str, "similarity": float, ...}
        """
        # Calculate similarity
        similarity = self._calculate_similarity(original, updated)
        
        # Check similarity bounds
        if similarity < instruction.min_similarity:
            return {
                "valid": False,
                "reason": f"Edit too aggressive (similarity={similarity:.2f} < {instruction.min_similarity})",
                "similarity": similarity
            }
        
        if similarity > instruction.max_similarity:
            return {
                "valid": False,
                "reason": f"Edit too minimal (similarity={similarity:.2f} > {instruction.max_similarity})",
                "similarity": similarity
            }
        
        # Check HTML structure preserved
        if not self._html_structure_preserved(original, updated):
            return {
                "valid": False,
                "reason": "HTML structure changed (tags added/removed)",
                "similarity": similarity
            }
        
        # Check citations preserved (if required)
        if instruction.preserve_citations:
            if not self._citations_preserved(original, updated):
                return {
                    "valid": False,
                    "reason": "Citations were removed or modified",
                    "similarity": similarity
                }
        
        # Check links preserved (if required)
        if instruction.preserve_links:
            if not self._links_preserved(original, updated):
                return {
                    "valid": False,
                    "reason": "Internal links were removed",
                    "similarity": similarity
                }
        
        # All checks passed
        return {
            "valid": True,
            "reason": "All validation checks passed",
            "similarity": similarity
        }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two strings (0.0-1.0).
        
        Uses SequenceMatcher for character-level comparison.
        """
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _html_structure_preserved(self, original: str, updated: str) -> bool:
        """
        Check if HTML structure is preserved (same tags, same order).
        """
        # Extract tags from both
        original_tags = re.findall(r'<[^>]+>', original)
        updated_tags = re.findall(r'<[^>]+>', updated)
        
        # Simple check: same number and order of tags
        # (More sophisticated check could compare tag types only)
        return original_tags == updated_tags
    
    def _citations_preserved(self, original: str, updated: str) -> bool:
        """
        Check if citations are preserved.
        
        Allows adding new citations (higher numbers), but not removing existing ones.
        """
        # Extract citation numbers from both
        original_citations = set(re.findall(r'\[(\d+)\]', original))
        updated_citations = set(re.findall(r'\[(\d+)\]', updated))
        
        # Original citations must still be present
        return original_citations.issubset(updated_citations)
    
    def _links_preserved(self, original: str, updated: str) -> bool:
        """
        Check if internal links are preserved.
        """
        # Extract internal links from both
        original_links = set(re.findall(r'<a href="/magazine/([^"]+)">', original))
        updated_links = set(re.findall(r'<a href="/magazine/([^"]+)">', updated))
        
        # Original links must still be present
        return original_links.issubset(updated_links)
    
    def _get_field(self, article: Dict[str, Any], field_path: str) -> str:
        """
        Get field value from article.
        
        Supports:
        - Simple fields: "Headline", "Intro"
        - Section fields: "section_03_content"
        - Special: "all_sections", "all_content"
        """
        if field_path == "all_sections":
            # Concatenate all section_XX_content fields
            content_parts = []
            for i in range(1, 10):
                field = f"section_{i:02d}_content"
                if field in article and article[field]:
                    content_parts.append(article[field])
            return "\n\n".join(content_parts)
        
        elif field_path == "all_content":
            # Concatenate intro + all sections
            parts = []
            if "Intro" in article and article["Intro"]:
                parts.append(article["Intro"])
            for i in range(1, 10):
                field = f"section_{i:02d}_content"
                if field in article and article[field]:
                    parts.append(article[field])
            return "\n\n".join(parts)
        
        else:
            # Simple field lookup
            return article.get(field_path, "")
    
    def _set_field(
        self,
        article: Dict[str, Any],
        field_path: str,
        value: str
    ) -> Dict[str, Any]:
        """
        Set field value in article.
        
        Supports:
        - Simple fields: "Headline", "Intro"
        - Section fields: "section_03_content"
        - Special: "all_sections" (splits and updates all sections)
        - Special: "all_content" (splits intro + sections)
        """
        updated = article.copy()
        
        if field_path == "all_sections":
            # Split content back into sections using section markers
            return self._split_and_update_sections(updated, value, include_intro=False)
        
        elif field_path == "all_content":
            # Split intro + sections
            return self._split_and_update_sections(updated, value, include_intro=True)
        
        else:
            # Simple field update
            updated[field_path] = value
            return updated
    
    def _split_and_update_sections(
        self,
        article: Dict[str, Any],
        content: str,
        include_intro: bool = True
    ) -> Dict[str, Any]:
        """
        Split rewritten content back into individual section fields.
        
        Uses section headers (## or <h2>) to identify section boundaries.
        Maps back to section_01_content, section_02_content, etc.
        
        Args:
            article: Original article dict
            content: Combined content to split
            include_intro: Whether first part is Intro
            
        Returns:
            Updated article dict
        """
        updated = article.copy()
        
        # Split by section headers (## or <h2>)
        # Pattern matches: ## Title or <h2>Title</h2>
        section_pattern = r'(?:^|\n)(?:##\s+|<h2[^>]*>)([^#\n<]+)(?:</h2>)?'
        
        # Find all section boundaries
        matches = list(re.finditer(section_pattern, content))
        
        if not matches:
            self.logger.warning("Could not find section headers in rewritten content")
            return updated
        
        # Extract sections
        sections = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            section_content = content[start:end].strip()
            sections.append(section_content)
        
        # If include_intro, the content before first header is the intro
        if include_intro and matches[0].start() > 0:
            intro_content = content[:matches[0].start()].strip()
            if intro_content:
                updated["Intro"] = intro_content
                self.logger.info(f"Updated Intro ({len(intro_content)} chars)")
        
        # Map sections to fields
        for i, section_content in enumerate(sections):
            field_name = f"section_{i+1:02d}_content"
            if field_name in updated or i < 9:  # Allow up to 9 sections
                updated[field_name] = section_content
                self.logger.info(f"Updated {field_name} ({len(section_content)} chars)")
        
        self.logger.info(f"✅ Split and updated {len(sections)} sections")
        return updated


# Convenience function for direct use
async def targeted_rewrite(
    article: Dict[str, Any],
    rewrites: List[RewriteInstruction],
    mode: Optional[RewriteMode] = None
) -> Dict[str, Any]:
    """
    Convenience function for targeted rewrites.
    
    Args:
        article: Article data
        rewrites: List of rewrite instructions
        mode: Optional default mode for all rewrites
    
    Returns:
        Updated article
    """
    # Set default mode if provided
    if mode:
        for rewrite in rewrites:
            if not rewrite.mode:
                rewrite.mode = mode
    
    # Create batch request
    request = RewriteBatchRequest(
        article=article,
        rewrites=rewrites,
        stop_on_failure=False
    )
    
    # Execute
    engine = RewriteEngine()
    response = await engine.rewrite_batch(request)
    
    return response.updated_article

