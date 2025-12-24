"""Wrapper for gap analyzer output conversion"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


class GapAnalyzerWrapper:
    """
    Wrapper to convert gap analyzer output to Keyword models

    The gap analyzer returns raw data. This wrapper:
    - Validates data
    - Converts to standard format
    - Provides convenience methods
    """

    @staticmethod
    def convert_gap_to_keyword_dict(gap: Dict) -> Dict:
        """
        Convert gap analyzer keyword to standard keyword dict

        Args:
            gap: Gap keyword data from analyzer

        Returns:
            Standardized keyword dictionary
        """
        keyword_text = gap.get("keyword", "")

        return {
            "keyword": keyword_text,
            "score": 0,  # Will be set by AI scorer
            "aeo_score": gap.get("aeo_score"),
            "source": "gap_analysis",
            "volume": gap.get("volume"),
            "difficulty": gap.get("difficulty"),
            "cpc": gap.get("cpc"),
            "competition": gap.get("competition"),
            "intent": gap.get("intent", "informational"),
            "intent_multiplier": gap.get("intent_multiplier"),
            "word_count": gap.get("word_count"),
            "serp_features": gap.get("aeo_serp_features", []),
            "has_aeo_features": gap.get("has_aeo_features", False),
            "aeo_feature_boost": gap.get("aeo_feature_boost"),
            "competitor": gap.get("competitor"),
            "competitor_url": gap.get("url"),
            "competitor_position": gap.get("position"),
            "is_question": gap.get("intent") == "question",
            "matched_intents": gap.get("matched_intents", []),
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

    @staticmethod
    def batch_convert_gaps(gaps: List[Dict]) -> List[Dict]:
        """
        Convert multiple gap keywords

        Args:
            gaps: List of gap keyword data

        Returns:
            List of standardized keyword dictionaries
        """
        return [
            GapAnalyzerWrapper.convert_gap_to_keyword_dict(gap)
            for gap in gaps
        ]

    @staticmethod
    def filter_by_score_range(
        keywords: List[Dict],
        min_aeo_score: Optional[float] = None,
        max_aeo_score: Optional[float] = None,
    ) -> List[Dict]:
        """Filter keywords by AEO score range"""
        filtered = keywords

        if min_aeo_score is not None:
            filtered = [kw for kw in filtered if (kw.get("aeo_score") or 0) >= min_aeo_score]

        if max_aeo_score is not None:
            filtered = [kw for kw in filtered if (kw.get("aeo_score") or 0) <= max_aeo_score]

        return filtered

    @staticmethod
    def sort_by_aeo_score(keywords: List[Dict]) -> List[Dict]:
        """Sort keywords by AEO score (highest first)"""
        return sorted(
            keywords,
            key=lambda kw: kw.get("aeo_score") or 0,
            reverse=True
        )

    @staticmethod
    def group_by_competitor(keywords: List[Dict]) -> Dict[str, List[Dict]]:
        """Group keywords by competitor source"""
        grouped = {}
        for kw in keywords:
            competitor = kw.get("competitor", "unknown")
            if competitor not in grouped:
                grouped[competitor] = []
            grouped[competitor].append(kw)
        return grouped

    @staticmethod
    def get_statistics(keywords: List[Dict]) -> Dict:
        """Get statistics about gap keywords"""
        if not keywords:
            return {}

        aeo_scores = [kw.get("aeo_score") or 0 for kw in keywords]
        volumes = [kw.get("volume") or 0 for kw in keywords]
        difficulties = [kw.get("difficulty") or 0 for kw in keywords]

        # Intent breakdown
        intent_counts = {}
        for kw in keywords:
            intent = kw.get("intent", "other")
            intent_counts[intent] = intent_counts.get(intent, 0) + 1

        # Count AEO features
        with_features = sum(1 for kw in keywords if kw.get("has_aeo_features", False))
        question_kw = sum(1 for kw in keywords if kw.get("intent") == "question")

        return {
            "total": len(keywords),
            "avg_aeo_score": sum(aeo_scores) / len(keywords) if aeo_scores else 0,
            "max_aeo_score": max(aeo_scores) if aeo_scores else 0,
            "min_aeo_score": min(aeo_scores) if aeo_scores else 0,
            "avg_volume": sum(volumes) / len(keywords) if volumes else 0,
            "avg_difficulty": sum(difficulties) / len(keywords) if difficulties else 0,
            "with_aeo_features": with_features,
            "question_keywords": question_kw,
            "intent_breakdown": intent_counts,
        }
