"""
Stage 7: Metadata Calculation

Maps to v4.1 Phase 6b, Steps 22-23: add-readtime → add_date

Calculates article metadata: reading time and publication date.

Input:
  - ExecutionContext.structured_data (article content for word count)

Output:
  - ExecutionContext.parallel_results['metadata'] (ArticleMetadata instance)

Process:
1. Count total words in article (headline + intro + sections)
2. Calculate reading time (word_count / 200 WPM)
3. Generate publication date (random within last 90 days)
4. Store metadata
"""

import logging
from typing import Dict, Any

from ..core import ExecutionContext, Stage
from ..models.metadata import ArticleMetadata, MetadataCalculator

logger = logging.getLogger(__name__)


class MetadataStage(Stage):
    """
    Stage 7: Calculate article metadata.

    Handles:
    - Word count calculation
    - Reading time computation
    - Publication date generation
    """

    stage_num = 8
    stage_name = "Metadata Calculation"

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 7: Calculate metadata.

        Input from context:
        - structured_data: ArticleOutput with content

        Output to context:
        - parallel_results['metadata']: ArticleMetadata instance

        Args:
            context: ExecutionContext from Stage 3

        Returns:
            Updated context with parallel_results populated
        """
        logger.info(f"Stage 7: {self.stage_name}")

        # Validate input
        if not context.structured_data:
            logger.warning("No structured_data available for metadata")
            context.parallel_results["metadata"] = ArticleMetadata()
            return context

        # Count total words
        word_count = self._count_article_words(context.structured_data)
        logger.info(f"Counted {word_count} words")

        # Calculate reading time
        read_time = MetadataCalculator.calculate_read_time(word_count)
        logger.info(f"✅ Reading time: {read_time} minutes")

        # Generate publication date
        publication_date = MetadataCalculator.generate_publication_date(days_back=90)
        logger.info(f"✅ Publication date: {publication_date}")

        # Create metadata
        metadata = ArticleMetadata(
            word_count=word_count,
            read_time=read_time,
            publication_date=publication_date,
        )

        # Store in context
        context.parallel_results["metadata"] = metadata
        context.parallel_results["word_count"] = word_count
        context.parallel_results["read_time"] = read_time
        context.parallel_results["publication_date"] = publication_date

        return context

    def _count_article_words(self, article) -> int:
        """
        Count total words in article.

        Includes: headline, teaser, intro, all sections.

        Args:
            article: ArticleOutput instance

        Returns:
            Total word count
        """
        word_count = 0

        # Headline
        if article.Headline:
            word_count += MetadataCalculator.count_words(article.Headline)

        # Teaser
        if article.Teaser:
            word_count += MetadataCalculator.count_words(article.Teaser)

        # Direct Answer
        if article.Direct_Answer:
            word_count += MetadataCalculator.count_words(article.Direct_Answer)

        # Intro
        if article.Intro:
            word_count += MetadataCalculator.count_words(article.Intro)

        # All section content
        section_contents = [
            article.section_01_content,
            article.section_02_content,
            article.section_03_content,
            article.section_04_content,
            article.section_05_content,
            article.section_06_content,
            article.section_07_content,
            article.section_08_content,
            article.section_09_content,
        ]

        for content in section_contents:
            if content:
                # Use HTML-aware word counting
                section_words = MetadataCalculator.count_words_from_html(content)
                word_count += section_words

        logger.debug(f"Total word count: {word_count}")

        # Word count validation (surgical fix for read time issue)
        if word_count > 4000:
            logger.warning(f"⚠️ High word count detected: {word_count} words - check for inflation")
        elif word_count < 500:
            logger.warning(f"⚠️ Low word count detected: {word_count} words - check for missing content")

        # Calculate read time with validation
        read_time = MetadataCalculator.calculate_read_time(word_count)
        expected_range_min = max(1, round(word_count / 250))  # Slow reading
        expected_range_max = max(1, round(word_count / 150))  # Fast reading
        
        if read_time < expected_range_min or read_time > expected_range_max:
            logger.warning(f"⚠️ Read time {read_time}m outside expected range {expected_range_min}-{expected_range_max}m for {word_count} words")

        return word_count

    def __repr__(self) -> str:
        """String representation."""
        return f"MetadataStage(stage_num={self.stage_num})"
