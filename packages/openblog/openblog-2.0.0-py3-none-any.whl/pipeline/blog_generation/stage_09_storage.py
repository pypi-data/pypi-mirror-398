"""
Stage 9: HTML Generation & Export

Maps to v4.1 Phase 9, Step 34: publish-to-wordpress + storage

Final stage: Convert validated article to HTML and export in multiple formats.

Handles:
1. HTML rendering from validated article (HTML is generated here, not earlier)
2. Metadata extraction and indexing
3. Storage (Supabase or file system)
4. Multi-format export: HTML, Markdown, PDF, JSON, CSV, XLSX
5. Final validation and reporting

Input:
  - ExecutionContext.validated_article (from Stage 8)
  - ExecutionContext.quality_report (from Stage 8)
  - ExecutionContext.job_id
  - ExecutionContext.company_data
  - ExecutionContext.job_config.export_formats (optional: list of formats to export)

Output:
  - ExecutionContext.final_article (validated_article confirmed for delivery)
  - ExecutionContext.storage_result (storage operation result + exported_files)
  
Export Formats:
  - HTML: Rendered article (always generated)
  - Markdown: Converted from HTML
  - PDF: Converted from HTML via PDF service
  - JSON: Structured article data
  - CSV: Flat table format
  - XLSX: Excel format with multiple sheets (Overview, Sections, FAQ, PAA)
"""

import logging
import re
from typing import Dict, Any, Optional, List

from ..core import ExecutionContext, Stage
from ..processors.html_renderer_simple import HTMLRendererSimple as HTMLRenderer
from ..processors.storage import StorageProcessor

logger = logging.getLogger(__name__)


class StorageStage(Stage):
    """
    Stage 9: HTML Generation & Export.

    Handles:
    - HTML rendering (HTML is generated here, not earlier in pipeline)
    - Metadata extraction
    - Article storage (Supabase or file system)
    - Multi-format export (HTML, Markdown, PDF, JSON, CSV, XLSX)
    - Final validation
    
    Note: HTML is generated in this stage from validated_article.
    Previous stages work with structured data, not HTML.
    """

    stage_num = 9
    stage_name = "HTML Generation & Storage"

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 9: Generate HTML and store article.

        Input from context:
        - validated_article: Cleaned, merged article from Stage 8
        - quality_report: Validation report from Stage 8
        - job_id: Unique job identifier
        - company_data: Company information

        Output to context:
        - final_article: Confirmed article ready for delivery
        - storage_result: Storage operation result

        Args:
            context: ExecutionContext from Stage 8

        Returns:
            Updated context with final_article and storage_result

        Raises:
            ValueError: If validated_article missing
        """
        logger.info(f"Stage 9: {self.stage_name}")

        # Step 1: Validate input
        if not context.validated_article:
            logger.error("No validated_article available")
            context.final_article = {}
            context.storage_result = {
                "success": False,
                "error": "No validated article from Stage 8",
            }
            return context

        # Step 2: Log quality status (non-blocking)
        # NOTE: Quality gates are informational only - we don't block content in production
        # This ensures users always get blogs, even if quality is below target
        passed_quality = context.quality_report.get("passed", False)
        if not passed_quality:
            critical_issues = context.quality_report.get("critical_issues", [])
            aeo_score = context.quality_report.get("metrics", {}).get("aeo_score", 0)
            logger.warning(f"⚠️  Quality below target (AEO: {aeo_score}/100): {critical_issues[:2]}")
            logger.warning(f"   Continuing with article generation (non-blocking quality gate)")
            # Log all critical issues for monitoring
            for issue in critical_issues[:5]:
                logger.warning(f"   - {issue}")
        else:
            aeo_score = context.quality_report.get("metrics", {}).get("aeo_score", 0)
            logger.info(f"✅ Quality checks passed (AEO: {aeo_score}/100)")

        # Step 3: Extract FAQ/PAA items and generate article URL
        logger.debug("Extracting FAQ/PAA items and generating article URL...")
        
        # Extract FAQ/PAA items from parallel_results with error handling
        faq_items_dict = []
        paa_items_dict = []
        
        try:
            # Extract FAQ items
            faq_list = context.parallel_results.get('faq_items') if context.parallel_results else None
            if faq_list:
                if hasattr(faq_list, 'to_dict_list'):
                    faq_items_dict = faq_list.to_dict_list()
                elif isinstance(faq_list, list):
                    faq_items_dict = faq_list
        except Exception as e:
            logger.warning(f"Failed to extract FAQ items: {e}. Continuing without FAQs.")
            faq_items_dict = []
        
        try:
            # Extract PAA items
            paa_list = context.parallel_results.get('paa_items') if context.parallel_results else None
            if paa_list:
                if hasattr(paa_list, 'to_dict_list'):
                    paa_items_dict = paa_list.to_dict_list()
                elif isinstance(paa_list, list):
                    paa_items_dict = paa_list
        except Exception as e:
            logger.warning(f"Failed to extract PAA items: {e}. Continuing without PAAs.")
            paa_items_dict = []
        
        # Generate article URL with error handling
        article_url = None
        try:
            headline = context.validated_article.get("Headline", "")
            company_url = context.company_data.get("company_url") if context.company_data else None
            article_url = self._generate_article_url(headline, company_url)
            if article_url:
                logger.debug(f"Generated article URL: {article_url}")
        except Exception as e:
            logger.warning(f"Failed to generate article URL: {e}. Continuing without URL.")
            article_url = None
        
        # OPTIMIZED: Parallelize HTML rendering and metadata extraction
        import asyncio
        
        logger.debug("Rendering HTML and extracting metadata in parallel...")
        
        # Prepare article dict for HTMLRenderer
        if paa_items_dict and not context.validated_article.get("paa_items"):
            context.validated_article["paa_items"] = paa_items_dict
        
        # Run HTML rendering and metadata extraction in parallel
        def render_html():
            try:
                # Get validated citations HTML from Stage 4 (if available)
                validated_citations_html = context.parallel_results.get("citations_html") if hasattr(context, 'parallel_results') else None
                
                html = HTMLRenderer.render(
                    article=context.validated_article,
                    company_data=context.company_data,
                    article_output=context.article_output,
                    article_url=article_url,
                    faq_items=faq_items_dict,
                    validated_citations_html=validated_citations_html,
                )
                logger.info(f"   HTML rendered ({len(html)} bytes)")
                return html
            except Exception as e:
                logger.error(f"HTML rendering failed: {e}")
                # Fallback: render without AEO features
                try:
                    html = HTMLRenderer.render(
                        article=context.validated_article,
                        company_data=context.company_data,
                        article_output=None,
                        article_url=None,
                        faq_items=[],
                        validated_citations_html=None,
                    )
                    logger.warning("HTML rendered with fallback (no AEO features)")
                    return html
                except Exception as e2:
                    logger.error(f"Fallback HTML rendering also failed: {e2}")
                    return f"<html><body><h1>Error rendering article</h1><p>{str(e2)}</p></body></html>"
        
        def extract_metadata():
            metadata = StorageProcessor.extract_metadata(context.validated_article)
            return metadata
        
        # Execute both in parallel
        html_content, metadata = await asyncio.gather(
            asyncio.to_thread(render_html),
            asyncio.to_thread(extract_metadata)
        )
        
        context.validated_article["metadata_extracted"] = metadata

        # Step 6: Store article
        logger.debug("Storing article...")
        success, storage_result = StorageProcessor.store(
            context.validated_article,
            context.job_id,
            html_content,
            storage_type="supabase",
        )

        # Step 7: Export in multiple formats (if requested)
        export_formats = ["html", "json"]  # Default formats
        if context.job_config and isinstance(context.job_config, dict):
            export_formats = context.job_config.get("export_formats", export_formats)
        else:
            logger.debug("job_config not available or not a dict, using default export_formats")
        
        exported_files = {}
        
        try:
            from ..processors.article_exporter import ArticleExporter
            output_dir = Path("output") / context.job_id
            logger.debug(f"Exporting to: {output_dir} with formats: {export_formats}")
            exported_files = ArticleExporter.export_all(
                article=context.validated_article,
                html_content=html_content,
                output_dir=output_dir,
                formats=export_formats,
            )
            if exported_files:
                logger.info(f"✅ Exported {len(exported_files)} format(s): {', '.join(exported_files.keys())}")
            else:
                logger.warning("⚠️  ArticleExporter.export_all() returned empty dict - no files exported")
        except Exception as e:
            logger.error(f"❌ Export failed: {e}")
            import traceback
            logger.debug(f"Export exception traceback:\n{traceback.format_exc()}")

        # Step 8: Set final article and storage result
        context.final_article = context.validated_article
        context.final_article["html_content"] = html_content
        context.storage_result = {
            "success": success,
            **storage_result,
            "exported_files": exported_files,
        }

        # Log completion
        if success:
            logger.info(f"✅ Article stored successfully")
            logger.info(f"   Job ID: {context.job_id}")
            logger.info(
                f"   Storage: {storage_result.get('storage_type', 'unknown')}"
            )
            headline = context.validated_article.get("Headline", "Unknown")
            logger.info(f"   Headline: {headline}")
            logger.info(
                f"   Quality: AEO={context.quality_report.get('metrics', {}).get('aeo_score', 0)}/100"
            )
        else:
            logger.error(f"❌ Storage failed: {storage_result.get('error', 'Unknown')}")

        return context

    @staticmethod
    def _generate_article_url(headline: str, company_url: Optional[str]) -> Optional[str]:
        """
        Generate article URL from headline and company URL.
        
        Args:
            headline: Article headline
            company_url: Company base URL
            
        Returns:
            Full article URL or None if company_url is missing
        """
        if not company_url or not headline:
            return None
        
        # ROOT-LEVEL FIX: Strip ALL HTML tags from headline before creating slug
        from html import unescape
        clean_headline = re.sub(r'<[^>]+>', '', headline)  # Remove HTML tags
        clean_headline = unescape(clean_headline)  # Unescape HTML entities
        
        # Create slug from clean headline
        slug = clean_headline.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars
        slug = re.sub(r'[-\s]+', '-', slug)   # Replace spaces with hyphens
        slug = slug.strip('-')
        
        # Ensure company_url doesn't end with /
        base_url = company_url.rstrip('/')
        return f"{base_url}/blog/{slug}"

    def __repr__(self) -> str:
        """String representation."""
        return f"StorageStage(stage_num={self.stage_num})"
