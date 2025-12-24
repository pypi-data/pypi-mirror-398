"""Configuration for keyword generation"""

from .models import KeywordGenerationConfig

# Default configuration
DEFAULT_CONFIG = KeywordGenerationConfig(
    target_count=80,
    ai_keywords_count=40,
    gap_keywords_count=40,
    enable_long_tail_expansion=True,
    long_tail_per_seed=2,
    enable_gap_analysis=True,
    max_competitors=3,
    auto_detect_competitors=True,
    gap_min_volume=100,
    gap_max_volume=5000,
    gap_max_difficulty=35,
    gap_max_competition=0.3,
    gap_min_words=3,
    min_score=40,
    enable_clustering=False,
    export_csv=False,
    export_json=True,
    api_timeout_seconds=120.0,  # Increased from 60.0 for scoring batches
    api_rate_limit_delay=0.5,
    max_batch_size=25,  # Reduced from 50 to prevent timeouts
)

# Fast mode (less API calls)
FAST_CONFIG = KeywordGenerationConfig(
    target_count=60,
    ai_keywords_count=30,
    gap_keywords_count=30,
    enable_long_tail_expansion=False,  # Skip to save API calls
    enable_gap_analysis=True,
    max_competitors=2,
    auto_detect_competitors=True,
    min_score=45,
    enable_clustering=False,
)

# Comprehensive mode (more data)
COMPREHENSIVE_CONFIG = KeywordGenerationConfig(
    target_count=120,
    ai_keywords_count=60,
    gap_keywords_count=60,
    enable_long_tail_expansion=True,
    long_tail_per_seed=3,
    enable_gap_analysis=True,
    max_competitors=5,
    auto_detect_competitors=True,
    gap_min_volume=50,  # Lower minimum
    gap_max_volume=10000,  # Higher maximum
    gap_max_difficulty=50,  # Higher difficulty OK
    min_score=35,  # Lower score threshold
    enable_clustering=True,
)

# AI-only mode (no gap analysis)
AI_ONLY_CONFIG = KeywordGenerationConfig(
    target_count=100,
    ai_keywords_count=100,
    gap_keywords_count=0,
    enable_long_tail_expansion=True,
    long_tail_per_seed=2,
    enable_gap_analysis=False,  # Disabled
    min_score=40,
    enable_clustering=False,
)

# Gap-only mode (no AI generation)
GAP_ONLY_CONFIG = KeywordGenerationConfig(
    target_count=100,
    ai_keywords_count=0,
    gap_keywords_count=100,
    enable_long_tail_expansion=False,
    enable_gap_analysis=True,
    max_competitors=3,
    auto_detect_competitors=True,
    min_score=40,
    enable_clustering=False,
)
