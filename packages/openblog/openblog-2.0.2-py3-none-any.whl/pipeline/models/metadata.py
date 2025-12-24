"""
Article Metadata Model

Represents article metadata: read time, publication date, etc.

Structure:
- read_time: Reading time in minutes
- publication_date: Publication date (DD.MM.YYYY format)
- word_count: Total word count
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)


class ArticleMetadata(BaseModel):
    """
    Article metadata.

    Attributes:
        read_time: Reading time in minutes (min 1, max 30)
        publication_date: Publication date (DD.MM.YYYY format)
        word_count: Total word count
        created_at: Timestamp when metadata was created
    """

    read_time: int = Field(
        default=5,
        description="Reading time in minutes",
        ge=1,
        le=30,
    )
    publication_date: str = Field(
        default="",
        description="Publication date (DD.MM.YYYY format)",
    )
    word_count: int = Field(
        default=0,
        description="Total word count",
        ge=0,
    )
    created_at: Optional[str] = Field(
        default="",
        description="Timestamp when created",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"ArticleMetadata(read_time={self.read_time}min, date={self.publication_date}, words={self.word_count})"


class MetadataCalculator:
    """
    Calculate article metadata.

    Methods for computing:
    - Reading time from word count
    - Publication date generation
    """

    WORDS_PER_MINUTE = 200  # Standard reading speed
    MIN_READ_TIME = 1
    MAX_READ_TIME = 30

    @staticmethod
    def calculate_read_time(word_count: int) -> int:
        """
        Calculate reading time in minutes.

        Algorithm:
        - Divide word count by 200 (words per minute)
        - Round to integer
        - Clamp between 1 and 30 minutes

        Args:
            word_count: Total word count

        Returns:
            Reading time in minutes
        """
        if word_count <= 0:
            return MetadataCalculator.MIN_READ_TIME

        read_time = max(1, round(word_count / MetadataCalculator.WORDS_PER_MINUTE))
        read_time = min(read_time, MetadataCalculator.MAX_READ_TIME)

        logger.debug(f"Calculated read time: {word_count} words → {read_time} minutes")
        return read_time

    @staticmethod
    def generate_publication_date(days_back: int = 90) -> str:
        """
        Generate a publication date within last N days.

        Simulates article being published within the specified range.

        Algorithm:
        - Generate random date within last N days
        - Format as ISO 8601 (YYYY-MM-DD) for compatibility with meta tags
        - Avoid future dates

        Args:
            days_back: How many days back to consider (default 90)

        Returns:
            Publication date string (YYYY-MM-DD ISO 8601 format)
        """
        today = datetime.now()
        random_days = random.randint(0, days_back)
        publication_datetime = today - timedelta(days=random_days)
        publication_date = publication_datetime.strftime("%Y-%m-%d")

        logger.debug(f"Generated publication date: {publication_date}")
        return publication_date

    @staticmethod
    def count_words(text: str) -> int:
        """
        Count words in text.

        Simple word count (split by whitespace).

        Args:
            text: Text to count

        Returns:
            Word count
        """
        if not text:
            return 0

        words = text.split()
        return len(words)

    @staticmethod
    def count_words_from_html(html_content: str) -> int:
        """
        Count words in HTML content.

        Removes common HTML tags to get text content.

        Args:
            html_content: HTML content

        Returns:
            Word count
        """
        import re

        if not html_content:
            return 0

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", html_content)
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Count words
        return MetadataCalculator.count_words(text.strip())
