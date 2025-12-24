"""
Output Schema Model

Defines the complete structure of extracted and validated article data.
This model matches the exact JSON schema output from Gemini in Stage 2.

Fields:
- Core: Headline, Subtitle, Teaser, Direct_Answer, Intro
- SEO: Meta Title, Meta Description
- Lead Gen: Lead_Survey_Title, Lead_Survey_Button (optional)
- Content: 9 sections × (title + content pairs)
- Engagement: 3 key takeaways + 4 PAA + 6 FAQ items
- Citations: Sources + Search Queries

Validation:
- Required fields must be non-empty strings
- Optional fields (Lead Survey, unused sections) may be empty
- HTML content fields must contain valid HTML
"""

from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import logging

logger = logging.getLogger(__name__)


class ComparisonTable(BaseModel):
    """
    Structured comparison table for products, tools, or features.
    
    Used for content that benefits from side-by-side comparisons.
    Examples: pricing tiers, tool features, before/after scenarios.
    """
    
    title: str = Field(..., description="Table title (e.g., 'AI Code Tools Comparison')")
    headers: List[str] = Field(..., description="Column headers (e.g., ['Tool', 'Price', 'Speed'])")
    rows: List[List[str]] = Field(..., description="Table rows, each row is a list matching header count")
    
    @field_validator('headers')
    @classmethod
    def validate_headers(cls, v):
        """Ensure headers exist and are reasonable."""
        if not v or len(v) < 2:
            raise ValueError("Table must have at least 2 columns")
        if len(v) > 6:
            raise ValueError("Table should not exceed 6 columns for readability")
        return v
    
    @field_validator('rows')
    @classmethod
    def validate_rows(cls, v, info):
        """Ensure rows match header count."""
        if not v:
            raise ValueError("Table must have at least one row")
        headers = info.data.get('headers', [])
        header_count = len(headers)
        
        for idx, row in enumerate(v):
            if len(row) != header_count:
                raise ValueError(f"Row {idx} has {len(row)} cells but table has {header_count} columns")
        
        if len(v) > 10:
            raise ValueError("Table should not exceed 10 rows for readability")
        
        return v


class ArticleOutput(BaseModel):
    """
    Complete article output schema (30+ fields).

    Maps to the exact JSON output from Gemini API response.
    """

    # Core content
    Headline: str = Field(..., description="Main article headline with primary keyword")
    Subtitle: Optional[str] = Field(
        default="",
        description="Optional sub-headline for context or angle",
    )
    Teaser: str = Field(
        ...,
        description="2-3 sentence hook highlighting pain point or benefit",
    )
    Direct_Answer: str = Field(
        ...,
        description="40-60 word direct answer to primary question",
    )
    Intro: str = Field(
        ...,
        description="Opening paragraph (80-120 words) framing the problem",
    )

    # SEO metadata
    Meta_Title: str = Field(
        ...,
        description="≤55 character SEO title with primary keyword",
    )
    Meta_Description: str = Field(
        ...,
        description="≤130 character SEO description with CTA",
    )

    # Lead generation (optional)
    Lead_Survey_Title: Optional[str] = Field(default="", description="Optional survey title")
    Lead_Survey_Button: Optional[str] = Field(
        default="",
        description="Optional survey CTA button text",
    )

    # Content sections (9 sections × 2 fields)
    # Section 1 is REQUIRED (article must have at least one section)
    section_01_title: str = Field(..., description="Section 1 heading (REQUIRED)")
    section_01_content: str = Field(..., description="Section 1 HTML content (REQUIRED)")
    section_02_title: Optional[str] = Field(default="", description="Section 2 heading")
    section_02_content: Optional[str] = Field(default="", description="Section 2 HTML content")
    section_03_title: Optional[str] = Field(default="", description="Section 3 heading")
    section_03_content: Optional[str] = Field(default="", description="Section 3 HTML content")
    section_04_title: Optional[str] = Field(default="", description="Section 4 heading")
    section_04_content: Optional[str] = Field(default="", description="Section 4 HTML content")
    section_05_title: Optional[str] = Field(default="", description="Section 5 heading")
    section_05_content: Optional[str] = Field(default="", description="Section 5 HTML content")
    section_06_title: Optional[str] = Field(default="", description="Section 6 heading")
    section_06_content: Optional[str] = Field(default="", description="Section 6 HTML content")
    section_07_title: Optional[str] = Field(default="", description="Section 7 heading")
    section_07_content: Optional[str] = Field(default="", description="Section 7 HTML content")
    section_08_title: Optional[str] = Field(default="", description="Section 8 heading")
    section_08_content: Optional[str] = Field(default="", description="Section 8 HTML content")
    section_09_title: Optional[str] = Field(default="", description="Section 9 heading")
    section_09_content: Optional[str] = Field(default="", description="Section 9 HTML content")

    # Key takeaways (3 items, at least 1 required)
    key_takeaway_01: Optional[str] = Field(default="", description="Key insight #1")
    key_takeaway_02: Optional[str] = Field(default="", description="Key insight #2")
    key_takeaway_03: Optional[str] = Field(default="", description="Key insight #3")

    # People Also Ask (PAA) - 4 items
    paa_01_question: Optional[str] = Field(default="", description="PAA question #1")
    paa_01_answer: Optional[str] = Field(default="", description="PAA answer #1")
    paa_02_question: Optional[str] = Field(default="", description="PAA question #2")
    paa_02_answer: Optional[str] = Field(default="", description="PAA answer #2")
    paa_03_question: Optional[str] = Field(default="", description="PAA question #3")
    paa_03_answer: Optional[str] = Field(default="", description="PAA answer #3")
    paa_04_question: Optional[str] = Field(default="", description="PAA question #4")
    paa_04_answer: Optional[str] = Field(default="", description="PAA answer #4")

    # FAQ - 6 items (5 minimum required)
    faq_01_question: Optional[str] = Field(default="", description="FAQ question #1")
    faq_01_answer: Optional[str] = Field(default="", description="FAQ answer #1")
    faq_02_question: Optional[str] = Field(default="", description="FAQ question #2")
    faq_02_answer: Optional[str] = Field(default="", description="FAQ answer #2")
    faq_03_question: Optional[str] = Field(default="", description="FAQ question #3")
    faq_03_answer: Optional[str] = Field(default="", description="FAQ answer #3")
    faq_04_question: Optional[str] = Field(default="", description="FAQ question #4")
    faq_04_answer: Optional[str] = Field(default="", description="FAQ answer #4")
    faq_05_question: Optional[str] = Field(default="", description="FAQ question #5")
    faq_05_answer: Optional[str] = Field(default="", description="FAQ answer #5")
    faq_06_question: Optional[str] = Field(default="", description="FAQ question #6")
    faq_06_answer: Optional[str] = Field(default="", description="FAQ answer #6")

    # Images (image_01_url is REQUIRED, others optional)
    image_01_url: str = Field(
        ...,
        description="REQUIRED: URL to hero image (1200x630) - primary article image. Use Unsplash URLs (e.g., https://images.unsplash.com/photo-...). This field is MANDATORY.",
    )
    image_01_alt_text: str = Field(
        ...,
        description="REQUIRED: Alt text for hero image (max 125 chars). This field is MANDATORY.",
    )
    image_01_credit: Optional[str] = Field(
        default="",
        description="Image credit/attribution (e.g., 'Photo by John Doe on Unsplash')",
    )
    image_02_url: Optional[str] = Field(
        default="",
        description="URL to mid-article image (optional)",
    )
    image_02_alt_text: Optional[str] = Field(
        default="",
        description="Alt text for mid-article image (max 125 chars)",
    )
    image_02_credit: Optional[str] = Field(
        default="",
        description="Image credit/attribution for mid-article image",
    )
    image_03_url: Optional[str] = Field(
        default="",
        description="URL to bottom image (optional)",
    )
    image_03_alt_text: Optional[str] = Field(
        default="",
        description="Alt text for bottom image (max 125 chars)",
    )
    image_03_credit: Optional[str] = Field(
        default="",
        description="Image credit/attribution for bottom image",
    )
    
    # Legacy single image field (for backward compatibility)
    image_url: Optional[str] = Field(
        default="",
        description="[DEPRECATED] Use image_01_url instead. URL to generated article image (1200x630)",
    )
    image_alt_text: Optional[str] = Field(
        default="",
        description="[DEPRECATED] Use image_01_alt_text instead. Alt text for article image (max 125 chars)",
    )
    
    # TL;DR (optional, for long articles)
    TLDR: Optional[str] = Field(
        default="",
        description="TL;DR summary (2-3 sentences) - include for articles 3000+ words",
    )

    # Sources and research
    Sources: Optional[str] = Field(
        default="",
        description="Citations as [1]: URL – description. Limited to 20 sources.",
    )
    Search_Queries: Optional[str] = Field(
        default="",
        description="Research queries documented (Q1: keyword...). One per line.",
    )
    
    # Comparison tables (optional, used when content benefits from structured comparison)
    tables: Optional[List[ComparisonTable]] = Field(
        default=[],
        description="Comparison tables (max 2 per article). Use for product comparisons, pricing tiers, feature matrices.",
    )

    # Quality metrics (set by Stage 3 validation)
    quality_score: Optional[int] = Field(
        default=None,
        description="Quality score 0-100. Set by Stage 3 validation.",
    )
    quality_failed: Optional[bool] = Field(
        default=False,
        description="True if quality score < 60. Use for filtering/review.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "Headline": "Complete Guide to Python Blog Writing in 2024",
                "Subtitle": "Master the art of writing engaging technical content",
                "Teaser": "Writing about Python can be challenging. This guide shows exactly how to craft engaging, SEO-optimized blog posts that rank.",
                "Direct_Answer": "Blog writing about Python requires balancing technical depth with accessibility, consistent research, and SEO optimization for discovery.",
                "Intro": "Python is one of the most discussed programming languages online...",
                "Meta_Title": "Python Blog Writing Guide 2024 | SCAILE",
                "Meta_Description": "Learn professional Python blog writing techniques for maximum reach and engagement.",
                "section_01_title": "Why Python Blog Writing Matters",
                "section_01_content": "<p>Python content serves multiple audiences...</p>",
                "Sources": "[1]: https://example.com – Research on Python trends",
            }
        }
    )

    @field_validator("Headline", "Teaser", "Direct_Answer", "Intro", "Meta_Title", "Meta_Description")
    @classmethod
    def required_fields_not_empty(cls, v):
        """Validate required fields are non-empty."""
        if not v or not v.strip():
            raise ValueError("This field is required and cannot be empty")
        return v.strip()

    @field_validator("Meta_Title")
    @classmethod
    def meta_title_length(cls, v):
        """Validate and intelligently truncate Meta Title to SEO limits (55 chars)."""
        if len(v) > 55:
            logger.warning(f"Meta Title exceeds 55 chars: {len(v)} chars, applying smart truncation...")
            # Smart truncation: try to break at word boundaries
            if len(v) <= 55:
                return v
            
            # Find the last complete word that fits in 52 chars (leaving room for "...")
            truncated = v[:52]
            last_space = truncated.rfind(' ')
            
            if last_space > 35:  # Only use word boundary if it doesn't make title too short
                truncated = v[:last_space]
            
            # Only add "..." if we actually truncated
            return truncated + "..." if len(truncated) < len(v) else v
        return v

    @field_validator("Meta_Description")
    @classmethod
    def meta_description_length(cls, v):
        """Validate and auto-truncate Meta Description to SEO limits."""
        if len(v) > 160:
            logger.warning(f"Meta Description exceeds 160 chars: {len(v)} chars, truncating...")
            # Truncate to 160 chars with ellipsis
            truncated = v[:157] + "..."
            return truncated[:160]
        return v

    def get_active_sections(self) -> int:
        """Count non-empty section titles."""
        sections = [
            self.section_01_title,
            self.section_02_title,
            self.section_03_title,
            self.section_04_title,
            self.section_05_title,
            self.section_06_title,
            self.section_07_title,
            self.section_08_title,
            self.section_09_title,
        ]
        return sum(1 for s in sections if s and s.strip())

    def get_active_faqs(self) -> int:
        """Count non-empty FAQ questions."""
        faqs = [
            self.faq_01_question,
            self.faq_02_question,
            self.faq_03_question,
            self.faq_04_question,
            self.faq_05_question,
            self.faq_06_question,
        ]
        return sum(1 for f in faqs if f and f.strip())

    def get_active_paas(self) -> int:
        """Count non-empty PAA questions."""
        paas = [
            self.paa_01_question,
            self.paa_02_question,
            self.paa_03_question,
            self.paa_04_question,
        ]
        return sum(1 for p in paas if p and p.strip())

    def get_active_takeaways(self) -> int:
        """Count non-empty key takeaways."""
        takeaways = [
            self.key_takeaway_01,
            self.key_takeaway_02,
            self.key_takeaway_03,
        ]
        return sum(1 for t in takeaways if t and t.strip())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    def __repr__(self) -> str:
        """String representation."""
        sections = self.get_active_sections()
        faqs = self.get_active_faqs()
        return (
            f"ArticleOutput(headline_len={len(self.Headline)}, "
            f"sections={sections}, faqs={faqs})"
        )
