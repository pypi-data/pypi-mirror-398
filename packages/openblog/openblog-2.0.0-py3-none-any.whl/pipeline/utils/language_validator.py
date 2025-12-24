"""
Language Validator - Validates generated content matches target language.

Production-level language enforcement using langdetect library.
Detects language contamination (e.g., English phrases in German content)
and provides metrics for quality reporting.
"""

import logging
import re
from typing import Dict, Tuple, List, Optional

try:
    from langdetect import detect, detect_langs
    from langdetect.lang_detect_exception import LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

logger = logging.getLogger(__name__)


class LanguageValidator:
    """
    Validates generated content matches target language.
    
    Uses langdetect library for language detection and provides
    contamination scoring for quality reporting.
    """
    
    # Common English phrases that leak into non-English LLM output
    ENGLISH_CONTAMINATION_PATTERNS = [
        # Conversational starters
        r"\bhere's\b",
        r"\bhere is\b", 
        r"\bhere are\b",
        r"\byou can\b",
        r"\byou'll\b",
        r"\byou've\b",
        r"\byou're\b",
        r"\blet's\b",
        r"\blet us\b",
        r"\bwe'll\b",
        r"\bwe've\b",
        r"\bwe're\b",
        # Common AI filler phrases
        r"\bkey benefits\b",
        r"\bkey points\b",
        r"\bkey takeaways\b",
        r"\bthis is\b",
        r"\bthat's\b",
        r"\bit's\b",
        r"\bthere's\b",
        # Action phrases
        r"\bhow to\b",
        r"\bwhat is\b",
        r"\bwhy does\b",
        r"\bwhen should\b",
        r"\bwhere can\b",
    ]
    
    # Minimum content length for reliable detection
    MIN_CONTENT_LENGTH = 100
    
    # Language detection confidence threshold
    CONFIDENCE_THRESHOLD = 0.85
    
    # English contamination threshold (percentage)
    CONTAMINATION_THRESHOLD = 2.0  # Max 2% English phrases allowed
    
    def __init__(self):
        """Initialize the language validator."""
        if not LANGDETECT_AVAILABLE:
            logger.warning("langdetect not available - language validation disabled")
    
    def validate(
        self, 
        content: str, 
        target_lang: str,
        strict: bool = False
    ) -> Tuple[bool, Dict]:
        """
        Validate that content matches target language.
        
        Args:
            content: Text content to validate
            target_lang: Target language code (e.g., 'de', 'fr', 'es')
            strict: If True, fail on any English contamination
            
        Returns:
            Tuple of (is_valid, metrics) where metrics includes:
            - detected_language: Primary detected language
            - confidence: Detection confidence (0-1)
            - english_contamination_score: Percentage of English phrases
            - contamination_phrases: List of detected English phrases
            - validation_passed: Whether validation passed
            - reason: Reason for failure if validation failed
        """
        metrics = {
            "detected_language": None,
            "confidence": 0.0,
            "english_contamination_score": 0.0,
            "contamination_phrases": [],
            "validation_passed": True,
            "reason": None,
        }
        
        # Skip validation for English content
        if target_lang == "en":
            metrics["detected_language"] = "en"
            metrics["confidence"] = 1.0
            metrics["validation_passed"] = True
            return True, metrics
        
        # Check if langdetect is available
        if not LANGDETECT_AVAILABLE:
            logger.warning("langdetect not available - skipping language validation")
            metrics["reason"] = "langdetect not available"
            return True, metrics
        
        # Clean content for analysis
        clean_content = self._clean_content(content)
        
        if len(clean_content) < self.MIN_CONTENT_LENGTH:
            logger.warning(f"Content too short for language detection ({len(clean_content)} chars)")
            metrics["reason"] = "content_too_short"
            return True, metrics
        
        # Step 1: Detect primary language
        try:
            detected_langs = detect_langs(clean_content)
            if detected_langs:
                primary = detected_langs[0]
                metrics["detected_language"] = primary.lang
                metrics["confidence"] = primary.prob
                
                # Check for language mismatch
                if primary.lang != target_lang and primary.prob >= self.CONFIDENCE_THRESHOLD:
                    # High confidence wrong language
                    metrics["validation_passed"] = False
                    metrics["reason"] = f"wrong_language: detected {primary.lang} (confidence {primary.prob:.2f}), expected {target_lang}"
                    logger.warning(f"Language validation failed: {metrics['reason']}")
                    return False, metrics
                    
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {e}")
            metrics["reason"] = f"detection_error: {e}"
            # Don't fail on detection errors - continue with contamination check
        
        # Step 2: Check for English contamination (even if primary lang matches)
        contamination_score, contamination_phrases = self.get_english_contamination(clean_content)
        metrics["english_contamination_score"] = contamination_score
        metrics["contamination_phrases"] = contamination_phrases
        
        # Fail if contamination exceeds threshold
        threshold = 0.0 if strict else self.CONTAMINATION_THRESHOLD
        if contamination_score > threshold:
            metrics["validation_passed"] = False
            metrics["reason"] = f"english_contamination: {contamination_score:.1f}% (threshold: {threshold}%)"
            logger.warning(f"Language validation failed: {metrics['reason']}")
            return False, metrics
        
        logger.info(f"Language validation passed: {target_lang} (contamination: {contamination_score:.1f}%)")
        return True, metrics
    
    def get_english_contamination(self, content: str) -> Tuple[float, List[str]]:
        """
        Calculate English contamination score for non-English content.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Tuple of (contamination_percentage, list_of_detected_phrases)
        """
        if not content:
            return 0.0, []
        
        content_lower = content.lower()
        word_count = len(content_lower.split())
        
        if word_count == 0:
            return 0.0, []
        
        detected_phrases = []
        phrase_word_count = 0
        
        for pattern in self.ENGLISH_CONTAMINATION_PATTERNS:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            if matches:
                detected_phrases.extend(matches)
                # Count words in matched phrases
                for match in matches:
                    phrase_word_count += len(match.split())
        
        # Calculate contamination as percentage of total words
        contamination_score = (phrase_word_count / word_count) * 100
        
        # Deduplicate detected phrases
        unique_phrases = list(set(detected_phrases))
        
        return contamination_score, unique_phrases
    
    def _clean_content(self, content: str) -> str:
        """
        Clean content for language detection.
        
        Removes HTML tags, citations, and other non-text elements.
        
        Args:
            content: Raw content with potential HTML
            
        Returns:
            Clean text for analysis
        """
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', ' ', content)
        
        # Remove citation references [1], [2], etc.
        clean = re.sub(r'\[\d+\]', '', clean)
        
        # Remove URLs
        clean = re.sub(r'https?://\S+', '', clean)
        
        # Normalize whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        return clean
    
    def extract_content_for_validation(self, article: Dict) -> str:
        """
        Extract all text content from article for validation.
        
        Args:
            article: Article dictionary with sections
            
        Returns:
            Combined text content
        """
        parts = []
        
        # Main content fields
        for field in ["Intro", "Direct_Answer", "Teaser", "Headline", "Subtitle"]:
            if field in article and article[field]:
                parts.append(str(article[field]))
        
        # Section content
        for i in range(1, 15):
            content = article.get(f"section_{i:02d}_content", "")
            title = article.get(f"section_{i:02d}_title", "")
            if content:
                parts.append(content)
            if title:
                parts.append(title)
        
        # FAQ/PAA
        for i in range(1, 10):
            for prefix in ["faq", "paa"]:
                q = article.get(f"{prefix}_{i:02d}_question", "")
                a = article.get(f"{prefix}_{i:02d}_answer", "")
                if q:
                    parts.append(q)
                if a:
                    parts.append(a)
        
        return " ".join(parts)


# Singleton instance for convenience
_validator_instance: Optional[LanguageValidator] = None


def get_language_validator() -> LanguageValidator:
    """Get singleton LanguageValidator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = LanguageValidator()
    return _validator_instance


def validate_article_language(
    article: Dict,
    target_lang: str,
    strict: bool = False
) -> Tuple[bool, Dict]:
    """
    Convenience function to validate article language.
    
    Args:
        article: Article dictionary
        target_lang: Target language code
        strict: If True, fail on any English contamination
        
    Returns:
        Tuple of (is_valid, metrics)
    """
    validator = get_language_validator()
    content = validator.extract_content_for_validation(article)
    return validator.validate(content, target_lang, strict=strict)

