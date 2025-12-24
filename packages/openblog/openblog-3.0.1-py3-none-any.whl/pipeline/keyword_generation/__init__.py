"""Keyword Generation V2 Module

Hybrid keyword generation combining:
- 50% AI-generated keywords (via Gemini)
- 50% SERanking gap analysis (from competitors)
- AI-based scoring layer
"""

from .generator import KeywordGeneratorV2
from .models import (
    Keyword,
    KeywordGenerationResult,
    CompanyInfo,
    KeywordGenerationConfig,
)
from .adapter import KeywordV2Adapter
from .exceptions import (
    KeywordGenerationError,
    AIGenerationError,
    GapAnalysisError,
    ScoringError,
    APIError,
    ConfigurationError,
    ValidationError,
)

__all__ = [
    "KeywordGeneratorV2",
    "KeywordV2Adapter",
    "Keyword",
    "KeywordGenerationResult",
    "CompanyInfo",
    "KeywordGenerationConfig",
    "KeywordGenerationError",
    "AIGenerationError",
    "GapAnalysisError",
    "ScoringError",
    "APIError",
    "ConfigurationError",
    "ValidationError",
]
