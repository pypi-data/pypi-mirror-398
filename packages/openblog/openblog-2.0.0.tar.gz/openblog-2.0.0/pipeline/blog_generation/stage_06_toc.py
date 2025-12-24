"""
Stage 6: Table of Contents (ToC) Generation

Maps to v4.1 Phase 6a, Steps 20-21: add-short-headers → reformat_short_headers

Generates short navigation labels (1-2 words) for each article section.

Input:
  - ExecutionContext.structured_data (section titles)

Output:
  - ExecutionContext.parallel_results['toc_dict'] (toc_01 → short label mapping)

Process:
1. Extract section titles from structured_data
2. Generate short labels (1-2 words) from full titles
3. Validate label format
4. Store as toc_01, toc_02, ..., toc_09
"""

import logging
from typing import Dict, Any

from ..core import ExecutionContext, Stage
from ..models.toc import TableOfContents, TOCEntry

logger = logging.getLogger(__name__)


class TableOfContentsStage(Stage):
    """
    Stage 6: Generate Table of Contents navigation labels.

    Handles:
    - Section title extraction
    - Short label generation
    - Label validation
    - ToC dictionary creation
    """

    stage_num = 6
    stage_name = "Table of Contents Generation"

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 6: Generate ToC labels.

        Input from context:
        - structured_data: ArticleOutput with section titles

        Output to context:
        - parallel_results['toc_dict']: {toc_01: label, toc_02: label, ...}

        Args:
            context: ExecutionContext from Stage 3

        Returns:
            Updated context with parallel_results populated
        """
        logger.info(f"Stage 6: {self.stage_name}")

        # Validate input
        if not context.structured_data:
            logger.warning("No structured_data available for ToC")
            context.parallel_results["toc_dict"] = {}
            return context

        # Extract section titles
        toc = self._extract_sections(context.structured_data)
        logger.info(f"Extracted {toc.count()} sections")

        # Generate short labels
        toc = self._generate_labels(toc)
        logger.info(f"Generated {toc.count()} ToC labels")

        # Validate labels
        is_valid = toc.validate_labels()
        if not is_valid:
            logger.warning("Some ToC labels may not meet requirements")

        # Log results
        for entry in toc.entries:
            logger.debug(f"   {entry.toc_key}: {entry.short_label} ({entry.word_count()} words)")

        # Convert to dict
        toc_dict = toc.to_dict()
        logger.info(f"✅ ToC complete: {len(toc_dict)} entries")

        # Store in context
        context.parallel_results["toc_dict"] = toc_dict
        context.parallel_results["toc_entries"] = toc

        return context

    def _extract_sections(self, article) -> TableOfContents:
        """
        Extract section titles from article.

        Args:
            article: ArticleOutput instance

        Returns:
            TableOfContents with entries (before label generation)
        """
        toc = TableOfContents()

        # Map section number to title
        sections = [
            (1, article.section_01_title),
            (2, article.section_02_title),
            (3, article.section_03_title),
            (4, article.section_04_title),
            (5, article.section_05_title),
            (6, article.section_06_title),
            (7, article.section_07_title),
            (8, article.section_08_title),
            (9, article.section_09_title),
        ]

        for num, title in sections:
            if title and title.strip():
                toc.add_entry(num, title.strip(), "")  # Empty label for now

        logger.debug(f"Extracted {toc.count()} non-empty sections")
        return toc

    def _generate_labels(self, toc: TableOfContents) -> TableOfContents:
        """
        Generate short navigation labels from full titles.

        Strategy:
        1. Take 1-2 most significant words from title
        2. Remove common words (a, the, and, or, in, on, to, for, etc.)
        3. Prefer nouns and verbs
        4. Truncate if necessary
        5. Capitalize properly

        Args:
            toc: TableOfContents with extracted sections

        Returns:
            TableOfContents with labels populated
        """
        # Common words to skip
        stop_words = {
            "a", "an", "and", "as", "at", "be", "by", "for", "from", "if",
            "in", "is", "it", "no", "of", "on", "or", "the", "to", "up",
            "we", "your", "you", "with", "that", "this", "when", "where",
            "which", "who", "how", "what", "why", "can", "will", "should",
            "must", "may", "might", "could"
        }

        new_toc = TableOfContents()

        for entry in toc.entries:
            # Split title into words
            words = entry.full_title.split()

            # Filter out stop words
            meaningful_words = [
                w for w in words
                if w.lower() not in stop_words and len(w) > 2
            ]

            # Take up to 2 meaningful words
            if meaningful_words:
                short_label = " ".join(meaningful_words[:2])
            else:
                # Fallback: use first 2 words
                short_label = " ".join(words[:2]) if words else "Section"

            # Truncate if too long
            if len(short_label) > 50:
                short_label = short_label[:47] + "..."

            logger.debug(f"Section {entry.section_num}: '{entry.full_title}' → '{short_label}'")

            new_entry = TOCEntry(
                section_num=entry.section_num,
                full_title=entry.full_title,
                short_label=short_label,
            )
            new_toc.add_entry(
                entry.section_num,
                entry.full_title,
                short_label,
            )

        return new_toc

    def __repr__(self) -> str:
        """String representation."""
        return f"TableOfContentsStage(stage_num={self.stage_num})"
