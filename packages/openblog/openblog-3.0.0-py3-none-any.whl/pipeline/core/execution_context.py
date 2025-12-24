"""
ExecutionContext - Shared data model for all workflow stages.

This is the data structure passed between all 10 stages (0-9).
Each stage receives it, modifies it, and passes to the next stage.

Clean design: no side effects, immutable chain of transformations.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from pipeline.models import SitemapPageList


@dataclass
class ExecutionContext:
    """
    Central data model for Python Blog Writing System.

    Flows through all 10 stages (0-9) in sequence:
    Preliminary → fetches and labels: sitemap_pages
    Stage 0 → populates: job_id, job_config, company_data, language
    Stage 1 → adds: prompt
    Stage 2 → adds: raw_article
    Stage 3 → adds: structured_data
    Stages 6-7 → populate: parallel_results (dict with image and similarity data)
    Stage 8 → adds: validated_article, quality_report
    Stage 9 → adds: final_article, storage_result

    No mutations - each stage works with full context and returns modified copy.
    """

    # ========== STAGE 0: Input ==========
    job_id: str
    """Unique job identifier from entry point or Supabase"""

    job_config: Dict[str, Any] = field(default_factory=dict)
    """Job configuration (primary_keyword, content_generation_instruction, etc)"""

    company_data: Dict[str, Any] = field(default_factory=dict)
    """
    Auto-detected company information:
    - company_name, company_url, company_location
    - company_competitors, company_info, company_language
    """

    blog_page: Dict[str, Any] = field(default_factory=dict)
    """Blog page configuration (primary_keyword, links, etc)"""

    sitemap_pages: Optional["SitemapPageList"] = None
    """
    Auto-fetched and labeled sitemap pages.

    Populated in preliminary step before Stage 0.
    Contains all URLs from company's sitemap with auto-detected labels.

    Usage:
    - For keyword gen: filter to blog pages only (avoid cannibalization)
    - For internal links: use full labeled set for richer linking options
    """

    language: str = ""
    """Target language for content generation (e.g., 'en', 'de')"""

    # ========== MARKET PROFILE DATA ==========
    target_market: str = ""
    """Target country/market for content generation (e.g., 'DE', 'AT', 'FR')"""
    
    market_profile: Optional[Dict[str, Any]] = None
    """
    Market-specific profile data for content generation.
    Contains cultural patterns, regulatory context, quality standards.
    Populated in Stage 1 when market-aware prompt is built.
    """

    # ========== STAGE 1: Prompt ==========
    prompt: str = ""
    """
    Complete prompt for Gemini.
    Built in Stage 1 by injecting variables into baseline template.
    """

    # ========== STAGE 2: Raw Content ==========
    raw_article: str = ""
    """
    Raw response from Gemini (text/plain with embedded JSON).
    Contains complete article content, unstructured.
    """

    # ========== STAGE 3: Quality Refinement Flag ==========
    stage_3_optimized: bool = False
    """
    Flag indicating if Stage 3 (Quality Refinement) has optimized AEO components.
    
    When True, Stage 8 should skip AEO enforcement to avoid conflicts:
    - Stage 3 uses Gemini to add natural language citations, conversational phrases, question patterns
    - Stage 8 uses regex to add academic citations [N] and inject phrases
    - Stage 8's academic citations get stripped by HTML renderer anyway
    
    Set to True in Stage 3 when _optimize_aeo_components() successfully optimizes content.
    """

    # ========== STAGE 3: Structured Data ==========
    structured_data: Optional[Any] = None
    """
    Extracted structured data (Pydantic model or dict).
    Contains all 30+ fields:
    - headline, subtitle, teaser, intro
    - section_01_title through section_09_title
    - section_01_content through section_09_content
    - faq_01_question through faq_06_question (+ answers)
    - paa_01_question through paa_04_question (+ answers)
    - key_takeaway_01, 02, 03
    - sources, search_queries
    """

    # ========== STAGES 6-7: Parallel Results ==========
    parallel_results: Dict[str, Any] = field(default_factory=dict)
    """
    Results from parallel stages 6-7.

    Keys:
    - 'citations': citations_html (HTML formatted citations)
    - 'internal_links': internal_links_html (HTML "More Reading" section)
    - 'toc': toc_dict (ToC labels: ToC01, ToC02, etc)
    - 'metadata': {read_time, publication_date}
    - 'faq_paa': {faq_items: [], paa_items: []}
    - 'image': {image_url, image_alt_text}
    """

    # ========== STAGE 8: Validated Article ==========
    validated_article: Optional[Dict[str, Any]] = None
    """
    Merged, cleaned, validated article.
    Contains all fields from structured_data + parallel_results, merged and sanitized.
    Ready for HTML generation.
    """

    quality_report: Dict[str, Any] = field(default_factory=dict)
    """
    Quality validation report from Stage 8.

    Structure:
    {
        'critical_issues': [],      # Errors that block publication
        'suggestions': [],           # Warnings for improvement
        'metrics': {
            'aeo_score': 80,        # 0-100 AEO quality score
            'readability': 60,      # Flesch-Kincaid readability
            'keyword_coverage': 95  # Primary keyword coverage %
        }
    }
    """

    # ========== STAGE 7: Similarity Check ==========
    similarity_report: Optional[Any] = None
    """
    Similarity check report from Stage 7.
    
    Contains SimilarityResult object with:
    - is_too_similar: bool
    - similarity_score: float (0-100%)
    - semantic_score: float (0.0-1.0) or None
    - shingle_score: float (0-100%) or None
    - similar_article: str (slug of similar article) or None
    - issues: List[str]
    - analysis_mode: str ("hybrid", "character", "none")
    """
    
    similarity_recommendations: Optional[Dict[str, Any]] = None
    """Recommendations from similarity check (action, severity, suggestions)"""
    
    batch_stats: Optional[Dict[str, Any]] = None
    """Batch similarity statistics (articles_count, embedding_stats, etc)"""
    
    regeneration_needed: bool = False
    """Flag indicating if regeneration is needed due to high similarity"""

    # ========== STAGE 8-9: ArticleOutput ==========
    article_output: Optional[Any] = None
    """
    ArticleOutput instance (Pydantic model) converted from validated_article.
    Used for comprehensive AEO scoring and schema generation.
    None if conversion failed or not yet converted.
    """

    # ========== STAGE 9: Final Output ==========
    final_article: Optional[Dict[str, Any]] = None
    """
    Final article data (all fields) ready for HTML generation and storage.
    Same as validated_article but confirmed ready for publication.
    """

    storage_result: Dict[str, Any] = field(default_factory=dict)
    """
    Result of Stage 9 storage operation.

    Structure:
    {
        'supabase': {...},           # Supabase upsert response
        'download_url': '...',       # Generated download link
        'google_drive': {...}        # Google Drive backup response (optional)
    }
    """

    # ========== Metadata ==========
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    """Timestamp when context was created"""

    execution_times: Dict[str, float] = field(default_factory=dict)
    """
    Stage execution times for performance tracking.
    Keys: 'stage_00', 'stage_01', etc.
    Values: execution time in seconds
    """

    errors: Dict[str, Any] = field(default_factory=dict)
    """
    Errors encountered during execution.
    Keys: stage names
    Values: error details
    """

    # ========== Utilities ==========
    def get_stage_input(self, stage_num: int) -> Dict[str, Any]:
        """
        Get input data for a specific stage.

        Args:
            stage_num: Stage number (0-13)

        Returns:
            Dictionary of inputs required by that stage
        """
        stage_inputs = {
            0: {
                "job_id": self.job_id,
            },
            1: {
                "job_config": self.job_config,
                "company_data": self.company_data,
                "language": self.language,
            },
            2: {
                "prompt": self.prompt,
            },
            3: {
                "raw_article": self.raw_article,
                "language": self.language,
            },
            4: {
                "structured_data": self.structured_data,
                "company_data": self.company_data,
            },
            5: {
                "structured_data": self.structured_data,
                "company_data": self.company_data,
                "language": self.language,
            },
            6: {
                "structured_data": self.structured_data,
                "language": self.language,
            },
            7: {
                "structured_data": self.structured_data,
            },
            8: {
                "structured_data": self.structured_data,
                "job_config": self.job_config,
                "language": self.language,
            },
            9: {
                "structured_data": self.structured_data,
                "company_data": self.company_data,
                "language": self.language,
                "blog_page": self.blog_page,
            },
            10: {
                "structured_data": self.structured_data,
                "parallel_results": self.parallel_results,
                "job_config": self.job_config,
            },
            11: {
                "validated_article": self.validated_article,
                "quality_report": self.quality_report,
                "job_id": self.job_id,
                "company_data": self.company_data,
                "language": self.language,
            },
            12: {
                "validated_article": self.validated_article,
                "job_config": self.job_config,
                "job_id": self.job_id,
            },
            13: {
                "validated_article": self.validated_article,
                "job_config": self.job_config,
            },
        }
        return stage_inputs.get(stage_num, {})

    def add_execution_time(self, stage_name: str, duration: float) -> None:
        """
        Record execution time for a stage.

        Args:
            stage_name: Name of stage (e.g., 'stage_02')
            duration: Execution time in seconds
        """
        self.execution_times[stage_name] = duration

    def add_error(self, stage_name: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Record an error encountered in a stage with enhanced context.

        Args:
            stage_name: Name of stage (e.g., 'stage_02')
            error: Exception object or error details
            context: Additional context (job_id, stage_num, etc.)
        """
        error_data = {
            "type": type(error).__name__,
            "message": str(error),
            "timestamp": datetime.now().isoformat(),
        }
        
        # Add error class module if available
        if hasattr(error, '__class__') and hasattr(error.__class__, '__module__'):
            error_data["module"] = error.__class__.__module__
        
        # Add traceback summary if available
        if hasattr(error, '__traceback__') and error.__traceback__:
            import traceback
            tb_lines = traceback.format_tb(error.__traceback__)
            if tb_lines:
                # Store last few lines of traceback
                error_data["traceback_summary"] = "".join(tb_lines[-3:])
        
        # Add additional context
        if context:
            error_data["context"] = context
        
        # Add stage number if available
        if hasattr(self, 'job_config') and 'primary_keyword' in self.job_config:
            error_data["job_keyword"] = self.job_config.get('primary_keyword', '')
        
        self.errors[stage_name] = error_data

    def get_total_execution_time(self) -> float:
        """
        Get total execution time across all stages.

        Returns:
            Total time in seconds
        """
        return sum(self.execution_times.values())

    def __repr__(self) -> str:
        """String representation for debugging."""
        populated_fields = []

        if self.sitemap_pages:
            populated_fields.append(f"sitemap_pages({self.sitemap_pages.count()} urls)")
        if self.job_id:
            populated_fields.append("job_id")
        if self.job_config:
            populated_fields.append("job_config")
        if self.prompt:
            populated_fields.append("prompt")
        if self.raw_article:
            populated_fields.append("raw_article")
        if self.structured_data:
            populated_fields.append("structured_data")
        if self.parallel_results:
            populated_fields.append(f"parallel_results({len(self.parallel_results)} keys)")
        if self.validated_article:
            populated_fields.append("validated_article")
        if self.final_article:
            populated_fields.append("final_article")

        return f"ExecutionContext({', '.join(populated_fields)})"
