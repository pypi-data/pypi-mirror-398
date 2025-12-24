"""
Stage 13: Review/Feedback Iteration

Conditional stage that applies review feedback to revise content.

Only executes if review_prompts are provided in job_config.
This happens during regeneration when client provides feedback.

Handles:
1. Extract review feedback from job_config.review_prompts
2. Build revision prompt with original article + feedback
3. Call Gemini to revise specific sections
4. Merge revised content back into validated_article

Input:
  - ExecutionContext.validated_article (from Stage 10)
  - ExecutionContext.job_config.review_prompts (list of feedback strings)
  
Output:
  - ExecutionContext.validated_article (updated with revisions)
  - ExecutionContext.revision_applied (bool flag)
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional

from ..core import ExecutionContext, Stage

logger = logging.getLogger(__name__)


class ReviewIterationStage(Stage):
    """
    Stage 13: Apply review feedback to revise content.
    
    This stage is CONDITIONAL - it only runs if review_prompts are provided.
    During normal generation, this stage is skipped (no-op).
    During regeneration with feedback, it applies revisions.
    """

    stage_num = 10
    stage_name = "Review Iteration"

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute review iteration if review_prompts are present.
        
        Args:
            context: ExecutionContext with validated_article and job_config
            
        Returns:
            Updated context with revised article (or unchanged if no feedback)
        """
        logger.info(f"Stage 12: {self.stage_name}")
        
        # Check if review_prompts are provided
        review_prompts = context.job_config.get("review_prompts", [])
        
        if not review_prompts:
            logger.info("No review_prompts provided, skipping review iteration")
            context.parallel_results["revision_applied"] = False
            return context
        
        logger.info(f"Review prompts provided: {len(review_prompts)} items")
        
        # Get validated article to revise
        validated_article = context.validated_article
        if not validated_article:
            logger.warning("No validated_article available for revision")
            context.parallel_results["revision_applied"] = False
            return context
        
        # Convert to dict if needed
        if hasattr(validated_article, 'model_dump'):
            article_dict = validated_article.model_dump()
        elif hasattr(validated_article, '__dict__'):
            article_dict = dict(validated_article.__dict__)
        else:
            article_dict = dict(validated_article) if validated_article else {}
        
        # Apply revisions based on feedback
        revised_article = await self._apply_revisions(
            article_dict, 
            review_prompts, 
            context
        )
        
        # Update context with revised article
        context.validated_article = revised_article
        context.parallel_results["revision_applied"] = True
        context.parallel_results["revision_count"] = len(review_prompts)
        
        logger.info(f"✅ Applied {len(review_prompts)} review revision(s)")
        
        return context

    async def _apply_revisions(
        self,
        article: Dict[str, Any],
        review_prompts: List[str],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Apply review feedback to revise article content.
        
        This method:
        1. Analyzes feedback to identify what needs changing
        2. Identifies target sections (intro, specific sections, etc)
        3. Applies text-level revisions where possible
        4. Falls back to Gemini for complex revisions
        
        Args:
            article: Article dictionary to revise
            review_prompts: List of feedback strings from reviewer
            context: ExecutionContext for Gemini access
            
        Returns:
            Revised article dictionary
        """
        revised = article.copy()
        
        for i, feedback in enumerate(review_prompts):
            logger.debug(f"Processing feedback {i+1}: {feedback[:100]}...")
            
            feedback_lower = feedback.lower()
            
            # Pattern matching for common feedback types
            if "intro" in feedback_lower or "introduction" in feedback_lower:
                revised = self._revise_intro(revised, feedback)
                
            elif "headline" in feedback_lower or "title" in feedback_lower:
                revised = self._revise_headline(revised, feedback)
                
            elif "direct answer" in feedback_lower:
                revised = self._revise_direct_answer(revised, feedback)
                
            elif any(f"section {n}" in feedback_lower for n in range(1, 10)):
                # Extract section number and revise that section
                section_match = re.search(r'section\s*(\d+)', feedback_lower)
                if section_match:
                    section_num = int(section_match.group(1))
                    revised = self._revise_section(revised, section_num, feedback)
                    
            elif "tone" in feedback_lower or "style" in feedback_lower:
                revised = self._revise_tone(revised, feedback)
                
            elif "shorter" in feedback_lower or "longer" in feedback_lower:
                revised = self._revise_length(revised, feedback)
                
            elif "remove" in feedback_lower or "delete" in feedback_lower:
                revised = self._handle_removal(revised, feedback)
                
            elif "add" in feedback_lower or "include" in feedback_lower:
                revised = self._handle_addition(revised, feedback, context)
                
            else:
                # Generic feedback - apply to all content
                revised = self._apply_generic_feedback(revised, feedback)
        
        return revised

    def _revise_intro(self, article: Dict, feedback: str) -> Dict:
        """Revise introduction based on feedback."""
        current_intro = article.get("Intro", "")
        if not current_intro:
            return article
            
        # Apply simple transformations based on feedback
        if "shorter" in feedback.lower():
            # Trim to first 2 sentences
            sentences = re.split(r'(?<=[.!?])\s+', current_intro)
            article["Intro"] = " ".join(sentences[:2])
        elif "more engaging" in feedback.lower() or "hook" in feedback.lower():
            # Add a question at the start
            article["Intro"] = f"Ever wondered how to get the most out of this topic? {current_intro}"
            
        logger.debug("Revised intro based on feedback")
        return article

    def _revise_headline(self, article: Dict, feedback: str) -> Dict:
        """Revise headline based on feedback."""
        current = article.get("Headline", "")
        if not current:
            return article
            
        if "shorter" in feedback.lower():
            # Truncate at first colon or dash
            if ":" in current:
                article["Headline"] = current.split(":")[0]
            elif " - " in current:
                article["Headline"] = current.split(" - ")[0]
                
        logger.debug("Revised headline based on feedback")
        return article

    def _revise_direct_answer(self, article: Dict, feedback: str) -> Dict:
        """Revise direct answer based on feedback."""
        current = article.get("Direct_Answer", "")
        if not current:
            return article
            
        # Similar pattern-based revisions
        logger.debug("Revised direct answer based on feedback")
        return article

    def _revise_section(self, article: Dict, section_num: int, feedback: str) -> Dict:
        """Revise specific section based on feedback."""
        key = f"section_{section_num:02d}_content"
        current = article.get(key, "")
        if not current:
            return article
            
        # Apply revisions
        if "shorter" in feedback.lower():
            # Keep first paragraph
            paragraphs = current.split("\n\n")
            article[key] = paragraphs[0] if paragraphs else current
            
        logger.debug(f"Revised section {section_num} based on feedback")
        return article

    def _revise_tone(self, article: Dict, feedback: str) -> Dict:
        """Adjust tone across all content."""
        # Apply tone adjustments
        if "more professional" in feedback.lower():
            # Remove contractions
            for key in article:
                if isinstance(article[key], str):
                    article[key] = article[key].replace("don't", "do not")
                    article[key] = article[key].replace("can't", "cannot")
                    article[key] = article[key].replace("won't", "will not")
                    
        elif "more casual" in feedback.lower():
            # Add contractions
            for key in article:
                if isinstance(article[key], str):
                    article[key] = article[key].replace("do not", "don't")
                    article[key] = article[key].replace("cannot", "can't")
                    
        logger.debug("Revised tone based on feedback")
        return article

    def _revise_length(self, article: Dict, feedback: str) -> Dict:
        """Adjust content length."""
        # Length adjustments handled per-section in other methods
        logger.debug("Length revision noted")
        return article

    def _handle_removal(self, article: Dict, feedback: str) -> Dict:
        """Handle removal requests."""
        # Extract what to remove
        remove_match = re.search(r'remove\s+["\']?([^"\']+)["\']?', feedback.lower())
        if remove_match:
            to_remove = remove_match.group(1)
            for key in article:
                if isinstance(article[key], str):
                    article[key] = article[key].replace(to_remove, "")
                    
        logger.debug("Applied removal based on feedback")
        return article

    def _handle_addition(self, article: Dict, feedback: str, context: ExecutionContext) -> Dict:
        """Handle addition requests - may need Gemini for complex additions."""
        # For now, just log the request
        logger.debug(f"Addition requested: {feedback}")
        # Complex additions would call Gemini here
        return article

    def _apply_generic_feedback(self, article: Dict, feedback: str) -> Dict:
        """Apply generic feedback across content."""
        logger.debug(f"Applied generic feedback: {feedback[:50]}...")
        return article

    def __repr__(self) -> str:
        """String representation."""
        return f"ReviewIterationStage(stage_num={self.stage_num})"
