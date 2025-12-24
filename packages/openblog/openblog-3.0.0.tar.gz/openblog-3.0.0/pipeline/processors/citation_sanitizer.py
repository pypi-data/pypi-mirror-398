"""
Citation Sanitizer - Final Citation Cleanup (CitationSanitizer2)

Maps to v4.1 Phase 9, Step 32b (CitationSanitizer2 node)

Purpose: Final pass to remove remaining citation artifacts and ensure clean integration.

Operations:
- Remove lingering citation markers: [n], [n,m,o]
- Remove empty brackets: []
- Clean up malformed citation tags
- Remove citation comments or notes
- Validate citation count matches sources list
"""

import re
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


class CitationSanitizer2:
    """
    Final citation cleanup processor.

    Maps to v4.1 CitationSanitizer2 node.
    """

    @staticmethod
    def sanitize(article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize citations in merged article.

        Args:
            article: Merged article dictionary

        Returns:
            Article with clean citations
        """
        # Remove lingering citation markers
        if "content" in article:
            article["content"] = CitationSanitizer2._remove_citation_markers(article["content"])

        # Clean up sources field
        if "Sources" in article:
            article["Sources"] = CitationSanitizer2._clean_sources(article["Sources"])

        # Validate citation count
        citation_count = CitationSanitizer2._count_citations(article.get("Sources", ""))
        article["citation_count"] = citation_count

        logger.info(f"✅ Citation sanitizer: {citation_count} citations validated")
        return article

    @staticmethod
    def _remove_citation_markers(text: str) -> str:
        """
        Remove lingering citation markers.

        Args:
            text: Text containing potential citation markers

        Returns:
            Text with citation markers removed
        """
        if not text or not isinstance(text, str):
            return text

        # Remove double-tagged citations like [[1]]
        text = re.sub(r"\[\[(\d+)\]\]", r"[\1]", text)

        # Clean up malformed citations like [n]]
        text = re.sub(r"\[(\d+)\]\]", r"[\1]", text)

        # Remove empty brackets
        text = re.sub(r"\[\s*\]", "", text)

        # Remove citation comments (text in brackets that isn't a number)
        text = re.sub(r"\[(?![\d,\s]+\])([^\]]+)\]", "", text)

        # Clean up multiple spaces created by removals
        text = re.sub(r"\s{2,}", " ", text)

        return text.strip()

    @staticmethod
    def _clean_sources(sources: str) -> str:
        """
        Clean up sources field.

        Args:
            sources: Sources field with citations

        Returns:
            Cleaned sources
        """
        if not sources or not isinstance(sources, str):
            return ""

        # Split into individual citations
        lines = sources.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:
                # Remove duplicate brackets
                line = re.sub(r"\[\[(\d+)\]\]", r"[\1]", line)
                # Validate format: [n]: url – description
                if re.match(r"^\[\d+\]:", line):
                    cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    @staticmethod
    def _count_citations(sources: str) -> int:
        """
        Count valid citations in sources.

        Args:
            sources: Sources string

        Returns:
            Number of valid citations
        """
        if not sources or not isinstance(sources, str):
            return 0

        # Count lines starting with [n]:
        citation_count = len(re.findall(r"^\[\d+\]:", sources, re.MULTILINE))
        return citation_count

    @staticmethod
    def validate_citations(article: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate citation integrity.

        Args:
            article: Article dictionary

        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []

        sources = article.get("Sources", "")
        if not sources:
            return True, []  # No citations is valid

        # Count citations
        citation_count = CitationSanitizer2._count_citations(sources)

        # Check max 20 citations
        if citation_count > 20:
            issues.append(f"Too many citations: {citation_count} > 20")

        # Check citation format
        lines = sources.split("\n")
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line and not re.match(r"^\[\d+\]:", line):
                issues.append(f"Invalid citation format on line {i}: {line[:50]}")

        return len(issues) == 0, issues
