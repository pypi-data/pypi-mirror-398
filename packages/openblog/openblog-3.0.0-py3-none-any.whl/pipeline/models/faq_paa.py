"""
FAQ and PAA Models

FAQ (Frequently Asked Questions) and PAA (People Also Ask) data models.

Structure:
- FAQItem: Single FAQ question-answer pair
- PAAItem: Single PAA question-answer pair
- FAQList: Collection of FAQ items
- PAAList: Collection of PAA items
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class FAQItem(BaseModel):
    """
    Single FAQ question-answer pair.

    Attributes:
        number: FAQ item number (1-6, v4.1 supports up to 6)
        question: FAQ question
        answer: FAQ answer
    """

    number: int = Field(
        ...,
        description="FAQ number (1-6)",
        ge=1,
        le=6,
    )
    question: str = Field(..., description="FAQ question (5-15 words)")
    answer: str = Field(..., description="FAQ answer (30-100 words)")

    def word_count_question(self) -> int:
        """Get question word count."""
        return len(self.question.split())

    def word_count_answer(self) -> int:
        """Get answer word count."""
        return len(self.answer.split())

    def is_valid(self) -> bool:
        """Validate FAQ item."""
        q_words = self.word_count_question()
        a_words = self.word_count_answer()

        if q_words < 2:
            logger.warning(f"FAQ question too short: {q_words} words")
            return False
        if a_words < 10:
            logger.warning(f"FAQ answer too short: {a_words} words")
            return False

        return True

    def __repr__(self) -> str:
        """String representation."""
        return f"FAQItem({self.number}: {self.question[:30]}...)"


class PAAItem(BaseModel):
    """
    Single PAA (People Also Ask) question-answer pair.

    Attributes:
        number: PAA item number (1-4, v4.1 supports 3-4)
        question: PAA question
        answer: PAA answer
    """

    number: int = Field(
        ...,
        description="PAA number (1-4)",
        ge=1,
        le=4,
    )
    question: str = Field(..., description="PAA question (5-10 words)")
    answer: str = Field(..., description="PAA answer (20-50 words)")

    def word_count_question(self) -> int:
        """Get question word count."""
        return len(self.question.split())

    def word_count_answer(self) -> int:
        """Get answer word count."""
        return len(self.answer.split())

    def is_valid(self) -> bool:
        """Validate PAA item."""
        q_words = self.word_count_question()
        a_words = self.word_count_answer()

        if q_words < 2:
            logger.warning(f"PAA question too short: {q_words} words")
            return False
        if a_words < 8:
            logger.warning(f"PAA answer too short: {a_words} words")
            return False

        return True

    def __repr__(self) -> str:
        """String representation."""
        return f"PAAItem({self.number}: {self.question[:30]}...)"


class FAQList(BaseModel):
    """Collection of FAQ items."""

    items: List[FAQItem] = Field(default_factory=list, description="FAQ items")
    min_items: int = Field(default=5, description="Minimum items required (v4.1: 5)")

    def add_item(self, number: int, question: str, answer: str) -> "FAQList":
        """Add FAQ item."""
        item = FAQItem(number=number, question=question, answer=answer)
        self.items.append(item)
        return self

    def count(self) -> int:
        """Get item count."""
        return len(self.items)

    def count_valid(self) -> int:
        """Count valid items."""
        return sum(1 for item in self.items if item.is_valid())

    def is_minimum_met(self) -> bool:
        """Check if minimum items requirement met."""
        return self.count() >= self.min_items

    def get_valid_items(self) -> List[FAQItem]:
        """Get only valid items."""
        return [item for item in self.items if item.is_valid()]

    def renumber(self) -> "FAQList":
        """Renumber items sequentially."""
        for i, item in enumerate(self.items, 1):
            item.number = min(i, 6)  # Cap at 6
        return self

    def to_dict_list(self) -> List[Dict]:
        """Convert to list of dictionaries."""
        return [
            {
                "number": item.number,
                "question": item.question,
                "answer": item.answer,
            }
            for item in self.items
        ]

    def __repr__(self) -> str:
        """String representation."""
        valid = self.count_valid()
        return f"FAQList({self.count()} items, {valid} valid)"


class PAAList(BaseModel):
    """Collection of PAA items."""

    items: List[PAAItem] = Field(default_factory=list, description="PAA items")
    min_items: int = Field(default=3, description="Minimum items required (v4.1: 3)")

    def add_item(self, number: int, question: str, answer: str) -> "PAAList":
        """Add PAA item."""
        item = PAAItem(number=number, question=question, answer=answer)
        self.items.append(item)
        return self

    def count(self) -> int:
        """Get item count."""
        return len(self.items)

    def count_valid(self) -> int:
        """Count valid items."""
        return sum(1 for item in self.items if item.is_valid())

    def is_minimum_met(self) -> bool:
        """Check if minimum items requirement met."""
        return self.count() >= self.min_items

    def get_valid_items(self) -> List[PAAItem]:
        """Get only valid items."""
        return [item for item in self.items if item.is_valid()]

    def renumber(self) -> "PAAList":
        """Renumber items sequentially."""
        for i, item in enumerate(self.items, 1):
            item.number = min(i, 4)  # Cap at 4
        return self

    def to_dict_list(self) -> List[Dict]:
        """Convert to list of dictionaries."""
        return [
            {
                "number": item.number,
                "question": item.question,
                "answer": item.answer,
            }
            for item in self.items
        ]

    def __repr__(self) -> str:
        """String representation."""
        valid = self.count_valid()
        return f"PAAList({self.count()} items, {valid} valid)"
