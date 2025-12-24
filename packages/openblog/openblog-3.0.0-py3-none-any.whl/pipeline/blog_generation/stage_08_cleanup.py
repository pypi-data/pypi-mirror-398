"""
Stage 8: Merge & Link

Simplified stage that only handles essential post-processing:
1. Merge parallel results (from Stages 6-7)
2. Link citations in content (convert [1] to clickable links)
3. Flatten data structure for export compatibility

All content manipulation, quality refinement, and validation are handled by
Stage 3 (AI-based Quality Refinement).

Input:
  - ExecutionContext.structured_data (from Stage 5)
  - ExecutionContext.parallel_results (from Stages 6-7)

Output:
  - ExecutionContext.validated_article (merged, flat article)
"""

import logging
import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from ..core import ExecutionContext, Stage
from ..processors.citation_linker import CitationLinker
from ..models.output_schema import ArticleOutput

logger = logging.getLogger(__name__)


def _encode_html_entities_in_content(article_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encode HTML entities in HTML content fields.
    
    Properly encodes & characters in text content (not already part of entities).
    Uses minimal regex - only splits HTML tags from text content.
    
    This is a technical requirement (HTML validity), not content manipulation.
    Called after citation linking to ensure newly created links have properly encoded entities.
    
    Args:
        article_dict: Dictionary containing article fields
        
    Returns:
        Dictionary with HTML entities properly encoded
    """
    # HTML content fields that may contain entities
    html_fields = [
        'Intro', 'Direct_Answer',
        'section_01_content', 'section_02_content', 'section_03_content',
        'section_04_content', 'section_05_content', 'section_06_content',
        'section_07_content', 'section_08_content', 'section_09_content',
    ]
    
    encoded_dict = article_dict.copy()
    
    for field in html_fields:
        if field in encoded_dict and encoded_dict[field]:
            content = str(encoded_dict[field])
            
            # Only process if content contains HTML tags
            if '<' in content and '>' in content:
                # Split content into HTML tags and text content
                # This regex splits on HTML tags: <...>
                parts = re.split(r'(<[^>]+>)', content)
                encoded_parts = []
                
                for part in parts:
                    if part.startswith('<') and part.endswith('>'):
                        # This is an HTML tag - preserve as-is
                        encoded_parts.append(part)
                    else:
                        # This is text content - encode & that's not already part of an entity
                        # Only encode & that's not followed by amp;, lt;, gt;, quot;, #, or a letter
                        # This handles: & -> &amp; but preserves &amp;, &lt;, etc.
                        encoded_text = re.sub(
                            r'&(?!amp;|lt;|gt;|quot;|#\d+;|#[xX][0-9a-fA-F]+;|[a-zA-Z]+;)',
                            '&amp;',
                            part
                        )
                        # Replace em dashes (—) and en dashes (–) with regular hyphens (-)
                        encoded_text = re.sub(r'[—–]', '-', encoded_text)
                        encoded_parts.append(encoded_text)
                
                encoded_dict[field] = ''.join(encoded_parts)
            else:
                # No HTML tags, but still replace em/en dashes
                encoded_dict[field] = re.sub(r'[—–]', '-', content)
    
    return encoded_dict


class CleanupStage(Stage):
    """
    Stage 8: Merge & Link.

    Handles:
    - Merging parallel results (images from Stage 6, similarity check from Stage 7)
    - Citation linking (convert [1] to clickable links with URL validation)
    - Data flattening (for export compatibility)
    
    Note: All content manipulation is handled by Stage 3 (AI-based Quality Refinement).
    """

    stage_num = 8
    stage_name = "Merge & Link"

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 8: Merge parallel results and link citations.

        Args:
            context: ExecutionContext from Stages 6-7

        Returns:
            Updated context with validated_article
        """
        logger.info(f"Stage 8: {self.stage_name}")

        # Validate inputs
        if not context.structured_data:
            logger.error("No structured_data to merge")
            context.validated_article = {}
            return context

        # Convert to dict if needed
        if hasattr(context.structured_data, "model_dump"):
            article = context.structured_data.model_dump()
        else:
            article = dict(context.structured_data)

        # Step 1: Merge parallel results (images, similarity check, etc.)
        logger.debug("Merging parallel results...")
        merged_article = self._merge_parallel_results(article, context.parallel_results)

        # Step 2: Link citations in content (convert [1] to clickable links)
        logger.debug("Linking citations in content...")
        citations_list = context.parallel_results.get("citations_list")
        if citations_list and merged_article:
            merged_article = await self._link_citations(merged_article, citations_list)

        # Step 3: Flatten data structure for export compatibility
        logger.debug("Flattening data structure...")
        validated_article = self._flatten_article(merged_article)
                    
        # Store results
        context.validated_article = validated_article
        
        # Also store ArticleOutput for Stage 9
        try:
            context.article_output = ArticleOutput.model_validate(validated_article)
        except Exception as e:
            logger.debug(f"Could not create ArticleOutput (non-critical): {e}")
            context.article_output = None

        logger.info(f"✅ Merge & Link complete ({len(validated_article)} fields)")
        return context

    def _merge_parallel_results(
        self, article: Dict[str, Any], parallel_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge parallel results from Stages 6-7.

        Args:
            article: Current article dict
            parallel_results: Results from Stages 6-7

        Returns:
            Merged article
        """
        merged = article.copy()

        # Add metadata (if present from Stage 2)
        if "metadata" in parallel_results:
            metadata = parallel_results["metadata"]
            if hasattr(metadata, 'model_dump'):
                merged.update(metadata.model_dump())
            elif hasattr(metadata, 'dict'):
                merged.update(metadata.dict())
            elif isinstance(metadata, dict):
                merged.update(metadata)

        # Add generated images from Stage 6 (3 AI-generated images)
        generated_image_fields = [
            "image_url", "image_alt_text",
            "mid_image_url", "mid_image_alt", 
            "bottom_image_url", "bottom_image_alt"
        ]
        for field in generated_image_fields:
            if field in parallel_results:
                merged[field] = parallel_results[field]
        
        # Add researched images from Stage 2 (3 research-sourced images)
        # These come from the original structured_data, not parallel_results
        researched_image_fields = [
            "image_01_url", "image_01_alt_text", "image_01_credit",
            "image_02_url", "image_02_alt_text", "image_02_credit", 
            "image_03_url", "image_03_alt_text", "image_03_credit"
        ]
        for field in researched_image_fields:
            if field in article and article.get(field):
                merged[field] = article[field]
        
        # Create combined image lists for export compatibility
        researched_images = []
        generated_images = []
        
        # Collect researched images (from Stage 2 Gemini research)
        for i in range(1, 4):
            url_field = f"image_{i:02d}_url"
            alt_field = f"image_{i:02d}_alt_text"  
            credit_field = f"image_{i:02d}_credit"
            
            if merged.get(url_field):
                researched_images.append({
                    "url": merged[url_field],
                    "alt_text": merged.get(alt_field, ""),
                    "credit": merged.get(credit_field, ""),
                    "source": "research",
                    "position": f"position_{i}"
                })
        
        # Collect generated images (from Stage 6 AI generation)
        generated_fields = [
            ("image_url", "image_alt_text", "hero"),
            ("mid_image_url", "mid_image_alt", "mid"), 
            ("bottom_image_url", "bottom_image_alt", "bottom")
        ]
        for url_field, alt_field, position in generated_fields:
            if merged.get(url_field):
                generated_images.append({
                    "url": merged[url_field],
                    "alt_text": merged.get(alt_field, ""),
                    "credit": "Generated by AI",
                    "source": "generated", 
                    "position": position
                })
        
        # Store combined image data
        merged["researched_images"] = researched_images
        merged["generated_images"] = generated_images
        merged["total_images"] = len(researched_images) + len(generated_images)
        
        logger.debug(f"Merged images: {len(researched_images)} researched + {len(generated_images)} generated = {merged['total_images']} total")

        # Add ToC
        if "toc_dict" in parallel_results:
            merged["toc"] = parallel_results["toc_dict"]
            logger.debug(f"ToC merged: {len(merged['toc'])} entries")

        # Add FAQ/PAA items
        if "faq_items" in parallel_results:
            faq_list = parallel_results["faq_items"]
            if hasattr(faq_list, "to_dict_list"):
                merged["faq_items"] = faq_list.to_dict_list()

        if "paa_items" in parallel_results:
            paa_list = parallel_results["paa_items"]
            if hasattr(paa_list, "to_dict_list"):
                merged["paa_items"] = paa_list.to_dict_list()

        # Add HTML sections
        if "citations_html" in parallel_results:
            merged["citations_html"] = parallel_results["citations_html"]
        if "internal_links_html" in parallel_results:
            merged["internal_links_html"] = parallel_results["internal_links_html"]
        
        # Add validated citation maps for in-body linking
        if "validated_citation_map" in parallel_results:
            merged["validated_citation_map"] = parallel_results["validated_citation_map"]
        if "validated_source_name_map" in parallel_results:
            merged["validated_source_name_map"] = parallel_results["validated_source_name_map"]
        
        # Add source_name_map from Stage 2 grounding
        if "source_name_map_from_grounding" in parallel_results:
            merged["_source_name_map"] = parallel_results["source_name_map_from_grounding"]
        
        # Add internal links list
        if "internal_links_list" in parallel_results:
            merged["internal_links_list"] = parallel_results["internal_links_list"]
        
        # Add section-specific internal links
        if "section_internal_links" in parallel_results:
            merged["_section_internal_links"] = parallel_results["section_internal_links"]

        logger.debug(
            f"Merged {len(parallel_results)} parallel results into article "
            f"({len(merged)} fields)"
        )
        return merged

    async def _link_citations(
        self, article: Dict[str, Any], citations_list: Any
    ) -> Dict[str, Any]:
        """
        Link citations in content (convert [1] to clickable links).

        Args:
            article: Article dict
            citations_list: Citations list from Stage 4

        Returns:
            Article with linked citations
        """
        # Extract citations for linking
        citations_for_linking = []
        citation_map = {}  # For HTML rendering

        if hasattr(citations_list, 'citations'):
            for citation in citations_list.citations:
                citation_num = citation.number if hasattr(citation, 'number') else citation.get('number')
                citation_url = citation.url if hasattr(citation, 'url') else citation.get('url')
                citation_title = citation.title if hasattr(citation, 'title') else citation.get('title', '')

                if citation_num and citation_url:
                    # Validate URL format
                    if not await self._validate_citation_url(citation_url, citation_num):
                        continue

                    citations_for_linking.append({
                        'number': citation_num,
                        'url': citation_url,
                        'title': citation_title,
                    })

                    citation_map[citation_num] = citation_url
                    logger.debug(f"Citation map: [{citation_num}] → {citation_url[:60]}...")

        if citations_for_linking:
            article = CitationLinker.link_citations_in_content(
                article,
                citations_for_linking
            )
            logger.info(f"✅ Linked {len(citations_for_linking)} citations in content")
            
            # Encode HTML entities after citation linking
            # This ensures newly created citation links have properly encoded entities (e.g., "Bain & Company" -> "Bain &amp; Company")
            article = _encode_html_entities_in_content(article)
            logger.debug("✅ Encoded HTML entities in content after citation linking")
        
        # Set citation_map for HTML rendering
        if citation_map:
            article['_citation_map'] = citation_map
            logger.debug(f"Set citation_map with {len(citation_map)} entries")

        return article

    async def _validate_citation_url(self, url: str, citation_num: int) -> bool:
        """
        Validate citation URL format and accessibility.

        Args:
            url: URL to validate
            citation_num: Citation number (for logging)

        Returns:
            True if URL is valid, False otherwise
        """
        # Check URL format
        if not url.startswith(("http://", "https://")):
            logger.warning(f"⚠️  Rejecting non-HTTP URL for citation [{citation_num}]: {url}")
            return False

        # Check for malformed URLs (missing TLD)
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if "." not in domain and domain not in ['localhost']:
                # Check if it's an IP address
                try:
                    import ipaddress
                    ipaddress.ip_address(domain)
                except ValueError:
                    logger.warning(f"⚠️  Rejecting URL with missing TLD for citation [{citation_num}]: {url}")
                    return False
        except Exception as e:
            logger.warning(f"⚠️  Error validating URL for citation [{citation_num}]: {e}")
            return False

        # HTTP validation (check if URL exists)
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                response = await client.head(url)
                if response.status_code != 200:
                    logger.warning(f"⚠️  Rejecting invalid URL (HTTP {response.status_code}) for citation [{citation_num}]: {url}")
                    return False

                # Check for soft 404s (redirects to error pages)
                final_url = str(response.url)
                error_indicators = ['/404', '/not-found', '/error', 'notfound', 'page-not-found']
                if any(indicator in final_url.lower() for indicator in error_indicators):
                    logger.warning(f"⚠️  Rejecting URL (error page redirect) for citation [{citation_num}]: {url}")
                    return False

                return True
        except Exception as e:
            logger.warning(f"⚠️  Error checking URL status for citation [{citation_num}]: {e}")
            return False

    def _flatten_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten nested objects to single-level dictionary for export compatibility.

        Args:
            article: Article (may contain nested objects)

        Returns:
            Flattened article
        """
        flattened = {}
        
        # Keys that should NOT be flattened (preserved as nested dicts)
        preserve_as_is = {
            '_section_internal_links',  # Section-specific internal links
            '_citation_map',  # Citation number → URL mapping
            '_source_name_map',  # Source name → URL mapping
        }

        for key, value in article.items():
            if key in preserve_as_is:
                # Keep as-is (don't flatten)
                flattened[key] = value
            elif isinstance(value, dict):
                # Flatten nested dicts with prefix
                for nested_key, nested_value in value.items():
                    flattened[f"{key}_{nested_key}"] = nested_value
            elif hasattr(value, "model_dump"):
                # Convert Pydantic models
                flattened[key] = value.model_dump()
            elif hasattr(value, "__dict__"):
                # Convert objects to dict
                flattened[key] = value.__dict__
            else:
                # Keep as-is
                flattened[key] = value

        return flattened

    def __repr__(self) -> str:
        """String representation."""
        return f"CleanupStage(stage_num={self.stage_num})"
# Deploy trigger Tue Dec 16 21:07:34 CET 2025
