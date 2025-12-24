"""
Pydantic models for Keyword Generation V2

Defines data structures for AI-generated and gap analysis keywords
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime, UTC


class IntentType(str, Enum):
    """Keyword intent categories"""
    QUESTION = "question"
    INFORMATIONAL = "informational"
    COMMERCIAL = "commercial"
    TRANSACTIONAL = "transactional"
    NAVIGATIONAL = "navigational"
    LIST = "list"
    LOCAL = "local"
    OTHER = "other"


class KeywordSource(str, Enum):
    """Keyword data source"""
    AI_GENERATED = "ai_generated"
    GAP_ANALYSIS = "gap_analysis"
    COMBINED = "combined"


class SERPFeature(str, Enum):
    """SERP features found in search results"""
    FEATURED_SNIPPET = "featured_snippet"
    PEOPLE_ALSO_ASK = "people_also_ask"
    KNOWLEDGE_PANEL = "knowledge_panel"
    FAQ = "faq"
    SGE = "sge"  # Search Generative Experience


class Keyword(BaseModel):
    """Single keyword with all metadata"""

    keyword: str = Field(..., description="The keyword term")
    score: int = Field(default=0, ge=0, le=100, description="AI company-fit score (0-100)")
    aeo_score: Optional[float] = Field(default=None, description="AEO opportunity score (from gap analysis)")
    source: KeywordSource = Field(default=KeywordSource.AI_GENERATED, description="Where keyword came from")

    # Search metrics
    volume: Optional[int] = Field(default=None, description="Monthly search volume")
    difficulty: Optional[int] = Field(default=None, ge=0, le=100, description="Keyword difficulty (0-100)")
    cpc: Optional[float] = Field(default=None, description="Cost per click")
    competition: Optional[float] = Field(default=None, ge=0, le=1, description="Competition level (0-1)")

    # Intent and categorization
    intent: IntentType = Field(default=IntentType.INFORMATIONAL, description="Keyword intent type")
    intent_multiplier: Optional[float] = Field(default=None, description="Intent multiplier for AEO")
    word_count: Optional[int] = Field(default=None, description="Number of words in keyword")

    # SERP features
    serp_features: List[SERPFeature] = Field(default_factory=list, description="SERP features for keyword")
    has_aeo_features: bool = Field(default=False, description="Has AEO-friendly SERP features")
    aeo_feature_boost: Optional[float] = Field(default=None, description="Boost from AEO features")

    # Competitor data (from gap analysis)
    competitor: Optional[str] = Field(default=None, description="Competitor domain this gap came from")
    competitor_url: Optional[str] = Field(default=None, description="Competitor URL ranking for this keyword")
    competitor_position: Optional[int] = Field(default=None, description="Competitor's ranking position")

    # Additional metadata
    is_question: bool = Field(default=False, description="Is this a question-based keyword")
    matched_intents: List[str] = Field(default_factory=list, description="All matching intent patterns")
    notes: Optional[str] = Field(default=None, description="Additional notes or observations")

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Last update timestamp")


class KeywordCluster(BaseModel):
    """Semantic cluster of related keywords"""

    cluster_id: str = Field(..., description="Unique cluster ID")
    cluster_name: str = Field(..., description="Human-readable cluster name")
    keywords: List[Keyword] = Field(default_factory=list, description="Keywords in this cluster")
    primary_keyword: Optional[Keyword] = Field(default=None, description="Most important keyword in cluster")

    intent_breakdown: Dict[str, int] = Field(default_factory=dict, description="Count by intent type")
    avg_score: float = Field(default=0, description="Average AI score for cluster")
    avg_aeo_score: Optional[float] = Field(default=None, description="Average AEO score")


class KeywordGenerationStatistics(BaseModel):
    """Statistics from keyword generation"""

    total_keywords: int = Field(default=0, description="Total keywords generated")
    ai_keywords: int = Field(default=0, description="Keywords from AI generation")
    gap_keywords: int = Field(default=0, description="Keywords from gap analysis")

    avg_score: float = Field(default=0, description="Average AI score")
    avg_aeo_score: Optional[float] = Field(default=None, description="Average AEO score")
    avg_volume: Optional[int] = Field(default=None, description="Average search volume")
    avg_difficulty: Optional[float] = Field(default=None, description="Average difficulty")

    intent_breakdown: Dict[str, int] = Field(default_factory=dict, description="Count by intent")
    with_aeo_features: int = Field(default=0, description="Keywords with AEO SERP features")
    question_keywords: int = Field(default=0, description="Question-type keywords")

    clusters: int = Field(default=0, description="Number of semantic clusters")

    api_cost: Optional[float] = Field(default=None, description="Estimated API cost")
    processing_time_seconds: Optional[float] = Field(default=None, description="Processing time")


class KeywordGenerationResult(BaseModel):
    """Complete result from keyword generation"""

    keywords: List[Keyword] = Field(default_factory=list, description="All generated keywords")
    clusters: List[KeywordCluster] = Field(default_factory=list, description="Semantic clusters (optional)")

    statistics: KeywordGenerationStatistics = Field(default_factory=KeywordGenerationStatistics)

    primary_keyword: Optional[Keyword] = Field(default=None, description="Top recommended keyword")

    # Metadata
    company_name: str = Field(..., description="Company analyzed")
    company_url: str = Field(..., description="Company domain")
    location: Optional[str] = Field(default=None, description="Target location")

    generation_method: str = Field(default="hybrid", description="Generation method used")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class CompanyInfo(BaseModel):
    """Company information for keyword generation"""

    name: str = Field(..., description="Company name")
    url: str = Field(..., description="Company domain/URL")
    industry: Optional[str] = Field(default=None, description="Industry category")
    description: Optional[str] = Field(default=None, description="Company description")
    services: List[str] = Field(default_factory=list, description="Services offered")
    products: List[str] = Field(default_factory=list, description="Products offered")
    target_location: Optional[str] = Field(default=None, description="Target geographic location")
    target_audience: Optional[str] = Field(default=None, description="Target audience description")
    competitors: Optional[List[str]] = Field(default=None, description="Known competitors")


class KeywordGenerationConfig(BaseModel):
    """Configuration for keyword generation"""

    target_count: int = Field(default=80, description="Target number of keywords (before filtering)")
    ai_keywords_count: int = Field(default=40, description="Number of AI-generated keywords (50%)")
    gap_keywords_count: int = Field(default=40, description="Number of gap analysis keywords (50%)")
    
    @field_validator('target_count', 'ai_keywords_count', 'gap_keywords_count', 'long_tail_per_seed', 'max_competitors', 'gap_min_volume', 'gap_max_volume', 'gap_max_difficulty', 'gap_min_words')
    @classmethod
    def validate_positive_counts(cls, v: int) -> int:
        """Validate that count fields are non-negative"""
        if v < 0:
            raise ValueError(f"Count must be >= 0, got {v}")
        return v
    
    @field_validator('gap_max_competition')
    @classmethod
    def validate_competition_range(cls, v: float) -> float:
        """Validate competition level is between 0 and 1"""
        if v < 0 or v > 1:
            raise ValueError(f"Competition level must be between 0 and 1, got {v}")
        return v
    
    @field_validator('min_score')
    @classmethod
    def validate_score_range(cls, v: int) -> int:
        """Validate score is between 0 and 100"""
        if v < 0 or v > 100:
            raise ValueError(f"Score must be between 0 and 100, got {v}")
        return v

    # AI Generation settings
    enable_long_tail_expansion: bool = Field(default=True, description="Expand with long-tail variants")
    long_tail_per_seed: int = Field(default=2, description="Long-tail variants per seed")

    # Gap analysis settings
    enable_gap_analysis: bool = Field(default=True, description="Enable SERanking gap analysis")
    max_competitors: int = Field(default=3, description="Max competitors to analyze")
    auto_detect_competitors: bool = Field(default=True, description="Auto-detect competitors vs manual")

    # AEO filtering (gap analysis)
    gap_min_volume: int = Field(default=100, description="Minimum search volume")
    gap_max_volume: int = Field(default=5000, description="Maximum search volume")
    gap_max_difficulty: int = Field(default=35, description="Maximum keyword difficulty")
    gap_max_competition: float = Field(default=0.3, description="Maximum competition level")
    gap_min_words: int = Field(default=3, description="Minimum word count")

    # Scoring
    min_score: int = Field(default=40, description="Minimum score to include keyword")

    # Output
    enable_clustering: bool = Field(default=False, description="Enable semantic clustering")
    export_csv: bool = Field(default=False, description="Export to CSV")
    export_json: bool = Field(default=True, description="Export to JSON")
