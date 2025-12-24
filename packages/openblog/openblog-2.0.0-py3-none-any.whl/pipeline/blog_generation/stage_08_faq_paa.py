"""
Stage 8: FAQ/PAA Validation and Enhancement

Maps to v4.1 Phase 7, Step 24: faq_creator

Validates extracted FAQ/PAA items and ensures minimum counts:
- Minimum 5 FAQ items (v4.1 requirement)
- Minimum 3 PAA items (v4.1 requirement)

Input:
  - ExecutionContext.structured_data (faq_*_question/answer, paa_*_question/answer)

Output:
  - ExecutionContext.parallel_results['faq_items'] (FAQList with validation)
  - ExecutionContext.parallel_results['paa_items'] (PAAList with validation)

Process:
1. Extract FAQ items from structured_data (faq_01 through faq_06)
2. Extract PAA items from structured_data (paa_01 through paa_04)
3. Validate each item
4. Remove duplicates
5. Ensure minimum counts
6. Renumber sequentially
"""

import logging
from typing import Dict, Any

from ..core import ExecutionContext, Stage
from ..models.faq_paa import FAQItem, FAQList, PAAItem, PAAList

logger = logging.getLogger(__name__)


class FAQPAAStage(Stage):
    """
    Stage 8: FAQ/PAA Validation and Enhancement.

    Handles:
    - FAQ/PAA extraction from structured data
    - Item validation
    - Deduplication
    - Minimum count enforcement
    """

    stage_num = 10
    stage_name = "FAQ/PAA Validation & Enhancement"

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 8: Validate and enhance FAQ/PAA.

        Input from context:
        - structured_data: ArticleOutput with faq/paa items

        Output to context:
        - parallel_results['faq_items']: FAQList
        - parallel_results['paa_items']: PAAList

        Args:
            context: ExecutionContext from Stage 3

        Returns:
            Updated context with parallel_results populated
        """
        logger.info(f"Stage 8: {self.stage_name}")

        # Validate input
        if not context.structured_data:
            logger.warning("No structured_data available for FAQ/PAA")
            context.parallel_results["faq_items"] = FAQList()
            context.parallel_results["paa_items"] = PAAList()
            return context

        # Extract FAQ items
        faq_list = self._extract_faq(context.structured_data)
        logger.info(f"Extracted {faq_list.count()} FAQ items")

        # Extract PAA items
        paa_list = self._extract_paa(context.structured_data)
        logger.info(f"Extracted {paa_list.count()} PAA items")

        # Validate and clean
        faq_list = self._validate_and_clean(faq_list)
        paa_list = self._validate_and_clean(paa_list)

        logger.info(f"✅ FAQ items after validation: {faq_list.count_valid()} valid")
        logger.info(f"✅ PAA items after validation: {paa_list.count_valid()} valid")

        # Check minimum requirements
        if not faq_list.is_minimum_met():
            logger.warning(
                f"⚠️  FAQ count below minimum: {faq_list.count()} < {faq_list.min_items}"
            )
        if not paa_list.is_minimum_met():
            logger.warning(
                f"⚠️  PAA count below minimum: {paa_list.count()} < {paa_list.min_items}"
            )

        # Renumber
        faq_list.renumber()
        paa_list.renumber()

        # Store in context
        context.parallel_results["faq_items"] = faq_list
        context.parallel_results["paa_items"] = paa_list
        context.parallel_results["faq_count"] = faq_list.count()
        context.parallel_results["paa_count"] = paa_list.count()

        return context

    def _extract_faq(self, article) -> FAQList:
        """
        Extract FAQ items from article.

        Articles have faq_01_question/answer through faq_06_question/answer.

        Args:
            article: ArticleOutput instance

        Returns:
            FAQList with extracted items
        """
        faq_list = FAQList()

        # Map FAQ fields
        faq_fields = [
            (1, article.faq_01_question, article.faq_01_answer),
            (2, article.faq_02_question, article.faq_02_answer),
            (3, article.faq_03_question, article.faq_03_answer),
            (4, article.faq_04_question, article.faq_04_answer),
            (5, article.faq_05_question, article.faq_05_answer),
            (6, article.faq_06_question, article.faq_06_answer),
        ]

        for num, question, answer in faq_fields:
            if question and question.strip() and answer and answer.strip():
                faq_list.add_item(num, question.strip(), answer.strip())

        logger.debug(f"Extracted {faq_list.count()} FAQ items")
        return faq_list

    def _extract_paa(self, article) -> PAAList:
        """
        Extract PAA items from article.

        Articles have paa_01_question/answer through paa_04_question/answer.

        Args:
            article: ArticleOutput instance

        Returns:
            PAAList with extracted items
        """
        paa_list = PAAList()

        # Map PAA fields
        paa_fields = [
            (1, article.paa_01_question, article.paa_01_answer),
            (2, article.paa_02_question, article.paa_02_answer),
            (3, article.paa_03_question, article.paa_03_answer),
            (4, article.paa_04_question, article.paa_04_answer),
        ]

        for num, question, answer in paa_fields:
            if question and question.strip() and answer and answer.strip():
                paa_list.add_item(num, question.strip(), answer.strip())

        logger.debug(f"Extracted {paa_list.count()} PAA items")
        return paa_list

    def _validate_and_clean(self, item_list) -> "FAQList | PAAList":
        """
        Validate items and remove invalid ones.

        Removes:
        - Empty items
        - Duplicate questions
        - Items that fail validation

        Args:
            item_list: FAQList or PAAList

        Returns:
            Cleaned list with only valid items
        """
        # Remove duplicates by question (case-insensitive)
        seen_questions = set()
        unique_items = []

        for item in item_list.items:
            q_lower = item.question.lower().strip()
            if q_lower not in seen_questions and item.is_valid():
                unique_items.append(item)
                seen_questions.add(q_lower)
            else:
                if q_lower in seen_questions:
                    logger.debug(f"Removed duplicate: {item.question[:30]}...")
                else:
                    logger.debug(f"Removed invalid: {item.question[:30]}...")

        # Create new list with unique items
        if isinstance(item_list, FAQList):
            new_list = FAQList(items=unique_items)
        else:
            new_list = PAAList(items=unique_items)

        logger.debug(f"Cleaned: {len(item_list.items)} → {new_list.count()} items")
        return new_list

    def __repr__(self) -> str:
        """String representation."""
        return f"FAQPAAStage(stage_num={self.stage_num})"
