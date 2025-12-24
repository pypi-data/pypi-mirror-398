"""
Stage 0: Data Fetch & Auto-Detection

Maps to v4.1 Phase 1, Steps 1-3:
- Step 1: Schedule trigger (entry point)
- Step 2: get_supabase_information (or direct input)
- Step 3: set_field_names (normalize and validate)

New feature: Auto-detection of company information from company_url
- Scrape website for metadata
- Use Gemini to analyze business info
- Fetch sitemap for internal links pool

Input:
  - job_id: Unique identifier
  - primary_keyword: Blog topic/keyword
  - company_url: Company website (for auto-detection)
  - Optional: company_name, company_location, company_language (overrides)

Output:
  - ExecutionContext with populated:
    - job_config (primary_keyword, content_generation_instruction, etc)
    - company_data (auto-detected or overridden)
    - language
    - blog_page (internal links, keyword, etc)
"""

import logging
import os
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import re

import httpx

from ..core import ExecutionContext, Stage
from ..data_sources import SitemapCrawler, SitemapPageList

logger = logging.getLogger(__name__)

# OpenContext API URL - Railway service or localhost fallback
OPENCONTEXT_API_URL = os.getenv("OPENCONTEXT_API_URL", "http://localhost:3000/api/analyze")


class DataFetchStage(Stage):
    """
    Stage 0: Fetch and auto-detect job data.

    Handles:
    - Validating required input fields
    - Auto-detecting company information from website
    - Applying user overrides
    - Normalizing field names
    - Building ExecutionContext
    """

    stage_num = 0
    stage_name = "Data Fetch & Auto-Detection"

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 0: Data fetch and auto-detection.

        Args:
            context: ExecutionContext with job_id and job_config

        Returns:
            Updated ExecutionContext with company_data, language, blog_page

        Raises:
            ValueError: If required fields missing
            Exception: If auto-detection fails
        """
        logger.info(f"Stage 0: {self.stage_name}")
        logger.info(f"Job ID: {context.job_id}")

        # Step 1: Validate required input
        self._validate_input(context)
        logger.info("✅ Input validation passed")

        # Step 2: Auto-detect company information
        company_data = await self._auto_detect_company(
            context.job_config.get("company_url", "")
        )
        logger.info("✅ Company information auto-detected")

        # Step 2b: Crawl sitemap for internal links
        context.sitemap_data = await self._crawl_company_sitemap(
            context.job_config.get("company_url", "")
        )
        if context.sitemap_data:
            logger.info(f"✅ Sitemap crawled: {context.sitemap_data.get('total_pages', 0)} pages found")
        else:
            logger.info("⚠️ No sitemap data found")

        # Step 3: Apply overrides
        company_data = self._apply_overrides(company_data, context.job_config)
        logger.info("✅ User overrides applied")

        # Step 4: Build normalized context
        context.company_data = company_data
        # Language priority: job_config.language > company_data.company_language > "en"
        context.language = context.job_config.get("language") or company_data.get("company_language", "en")
        context.blog_page = self._build_blog_page(context)
        context.job_config = self._normalize_job_config(context.job_config)

        logger.info(f"✅ ExecutionContext built")
        logger.info(f"   Company: {company_data.get('company_name', 'Unknown')}")
        logger.info(f"   Language: {context.language}")
        logger.info(f"   Keyword: {context.job_config.get('primary_keyword', 'Unknown')}")

        return context

    def _validate_input(self, context: ExecutionContext) -> None:
        """
        Validate required input fields.

        Args:
            context: ExecutionContext to validate

        Raises:
            ValueError: If required fields missing
        """
        required_fields = {
            "primary_keyword": "Blog topic/keyword",
            "company_url": "Company website URL",
        }

        job_config = context.job_config
        missing = []

        for field, description in required_fields.items():
            if not job_config.get(field):
                missing.append(f"{field} ({description})")

        if missing:
            raise ValueError(
                f"Missing required fields:\n  - " + "\n  - ".join(missing)
            )

        logger.debug(f"Required fields present: {', '.join(required_fields.keys())}")

    async def _call_opencontext(self, company_url: str) -> Optional[Dict[str, Any]]:
        """
        Call OpenContext API to get rich company context.

        OpenContext analyzes the company website using Gemini and returns:
        - company_name, industry, description, products
        - competitors, tone, pain_points, value_propositions
        - use_cases, content_themes, country, language

        Args:
            company_url: Company website URL to analyze

        Returns:
            OpenContext response dict or None if failed
        """
        logger.info(f"Calling OpenContext API: {OPENCONTEXT_API_URL}")
        logger.debug(f"URL to analyze: {company_url}")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:  # Matches OpenContext maxDuration
                response = await client.post(
                    OPENCONTEXT_API_URL,
                    json={"url": company_url},
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()

                logger.info(f"✅ OpenContext returned {len(data)} fields")
                logger.debug(f"OpenContext fields: {list(data.keys())}")
                return data

        except httpx.TimeoutException:
            logger.warning(f"OpenContext API timeout (90s) for {company_url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"OpenContext API HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.warning(f"OpenContext API error: {e}")
            return None

    async def _auto_detect_company(self, company_url: str) -> Dict[str, Any]:
        """
        Auto-detect company information from URL.

        Operations:
        1. Try OpenContext API for rich company data (preferred)
        2. Fall back to basic domain parsing if OpenContext unavailable
        3. Extract domain and company name from URL

        Args:
            company_url: Company website URL

        Returns:
            Dictionary with company information:
            - company_url: Validated URL
            - company_name: From OpenContext or domain extraction
            - industry: From OpenContext (if available)
            - description: From OpenContext (if available)
            - products: From OpenContext (if available)
            - competitors: From OpenContext (if available)
            - tone: From OpenContext (if available)
            - pain_points, value_propositions, use_cases, content_themes
            - company_language: From OpenContext or default
            - company_location: From OpenContext or default
        """
        logger.debug(f"Auto-detecting company info from: {company_url}")

        # Step 1: Try OpenContext API for rich company data
        opencontext_data = await self._call_opencontext(company_url)

        if opencontext_data:
            logger.info("✅ Using OpenContext data for company context")

            # Map OpenContext fields to our company_data format
            company_data = {
                "company_url": opencontext_data.get("company_url", company_url),
                "company_name": opencontext_data.get("company_name", self._extract_company_name(self._extract_domain(company_url))),
                "company_language": opencontext_data.get("language", "en"),
                "company_location": opencontext_data.get("country", "Unknown"),
                "company_info": {
                    "description": opencontext_data.get("description", ""),
                    "industry": opencontext_data.get("industry", "Unknown"),
                    "business_model": "Unknown",
                },
                "company_competitors": opencontext_data.get("competitors", []),
                # Pass through rich OpenContext fields for prompt building
                "industry": opencontext_data.get("industry", ""),
                "description": opencontext_data.get("description", ""),
                "products": opencontext_data.get("products", ""),
                "target_audience": opencontext_data.get("target_audience", ""),
                "tone": opencontext_data.get("tone", "professional"),
                "pain_points": opencontext_data.get("pain_points", ""),
                "value_propositions": opencontext_data.get("value_propositions", ""),
                "use_cases": opencontext_data.get("use_cases", ""),
                "content_themes": opencontext_data.get("content_themes", ""),
                # Voice persona - dynamically generated by OpenContext (CRITICAL for quality)
                "voice_persona": opencontext_data.get("voice_persona", {}),
                # Flag that we used OpenContext
                "_opencontext_enriched": True,
            }

            # Log voice persona availability
            if company_data.get("voice_persona"):
                logger.info("✅ Voice persona received from OpenContext")
            else:
                logger.warning("⚠️ No voice_persona in OpenContext response")

            logger.debug(f"OpenContext company data: {list(company_data.keys())}")
            return company_data

        # Step 2: Fall back to basic domain parsing
        logger.info("⚠️ OpenContext unavailable, using basic auto-detection")

        # Extract domain and basic info
        domain = self._extract_domain(company_url)
        company_name = self._extract_company_name(domain)

        logger.debug(f"Domain: {domain}")
        logger.debug(f"Company name: {company_name}")

        # Build basic company_data (fallback)
        company_data = {
            "company_url": company_url,
            "company_name": company_name,
            "company_language": "en",  # Default to English, can be overridden
            "company_location": "Unknown",  # Can be overridden
            "company_info": {
                "description": f"Information about {company_name}",
                "industry": "Unknown",
                "business_model": "Unknown",
            },
            "company_competitors": [],
            # Empty fields for consistency
            "industry": "",
            "description": "",
            "products": "",
            "target_audience": "",
            "tone": "professional",
            "pain_points": "",
            "value_propositions": "",
            "use_cases": "",
            "content_themes": "",
            "_opencontext_enriched": False,
        }

        logger.debug(f"Fallback company data: {company_data}")
        return company_data

    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL.

        Args:
            url: Full URL (e.g., https://www.example.com)

        Returns:
            Domain (e.g., example.com)

        Raises:
            ValueError: If URL is invalid
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            if not domain:
                raise ValueError(f"Invalid URL: {url}")
            return domain
        except Exception as e:
            raise ValueError(f"Could not parse URL '{url}': {e}")

    def _extract_company_name(self, domain: str) -> str:
        """
        Extract company name from domain.

        Examples:
        - "acme.com" → "ACME"
        - "my-company.co.uk" → "My Company"
        - "example.org" → "Example"

        Args:
            domain: Domain name (e.g., "example.com")

        Returns:
            Company name (title case)
        """
        # Remove TLD
        name = domain.split(".")[0]

        # Replace hyphens with spaces
        name = name.replace("-", " ")

        # Title case
        name = " ".join(word.capitalize() for word in name.split())

        return name

    async def _crawl_company_sitemap(self, company_url: str) -> Optional[Dict[str, Any]]:
        """
        Crawl company sitemap to extract internal links and site structure.
        
        Operations:
        1. Crawl sitemap using SitemapCrawler
        2. Extract blog URLs for internal linking
        3. Analyze site structure for competitive intelligence
        
        Args:
            company_url: Company website URL
            
        Returns:
            Dictionary with sitemap analysis:
            - total_pages: Total URLs found
            - blog_count: Number of blog pages
            - blog_urls: List of blog URLs for internal linking
            - page_summary: Breakdown by page type
            - site_structure: Analysis of content patterns
        """
        if not company_url:
            logger.debug("No company_url provided, skipping sitemap crawl")
            return None
            
        try:
            logger.debug(f"Crawling sitemap for: {company_url}")
            
            # Initialize crawler with reasonable limits for blog generation
            crawler = SitemapCrawler(
                max_urls=500,  # Limit for performance
                cache_ttl=3600,  # 1 hour cache
                max_cache_size=50  # Reasonable memory usage
            )
            
            # Crawl the sitemap
            sitemap_pages = await crawler.crawl(company_url)
            
            if not sitemap_pages or sitemap_pages.count() == 0:
                logger.debug(f"No sitemap URLs found for {company_url}")
                return None
                
            # Extract URLs by type for internal linking (high confidence only)
            blog_urls = sitemap_pages.get_blog_urls(min_confidence=0.7)
            resource_urls = sitemap_pages.get_urls_by_label("resource", min_confidence=0.6)
            product_urls = sitemap_pages.get_urls_by_label("product", min_confidence=0.6)
            docs_urls = sitemap_pages.get_urls_by_label("docs", min_confidence=0.6)
            company_urls = sitemap_pages.get_urls_by_label("company", min_confidence=0.6)
            
            # Get page breakdown
            page_summary = sitemap_pages.label_summary()
            
            # Build analysis
            sitemap_data = {
                "total_pages": sitemap_pages.count(),
                "blog_count": len(blog_urls),
                "blog_urls": blog_urls[:20],  # Limit to 20 for prompt efficiency
                "resource_urls": resource_urls[:10],  # Limit resources
                "product_urls": product_urls[:8],     # Limit products
                "docs_urls": docs_urls[:6],           # Limit docs
                "company_urls": company_urls[:4],     # Limit company pages
                "page_summary": page_summary,
                "fetch_timestamp": sitemap_pages.fetch_timestamp,
                "site_structure": self._analyze_site_structure(sitemap_pages),
                # CRITICAL: Include raw sitemap_pages for Stage 5 internal links
                "_sitemap_pages_object": sitemap_pages,
            }
            
            logger.info(f"Sitemap analysis complete: {sitemap_data['total_pages']} total pages, {sitemap_data['blog_count']} blogs")
            return sitemap_data
            
        except Exception as e:
            logger.warning(f"Failed to crawl sitemap for {company_url}: {e}")
            return None

    def _analyze_site_structure(self, sitemap_pages: SitemapPageList) -> Dict[str, Any]:
        """
        Analyze site structure from sitemap data for competitive intelligence.
        
        Args:
            sitemap_pages: Crawled sitemap data
            
        Returns:
            Site structure analysis
        """
        page_summary = sitemap_pages.label_summary()
        total_pages = sitemap_pages.count()
        
        # Calculate content focus percentages
        content_focus = {
            "content_heavy": (page_summary.get("blog", 0) + page_summary.get("resource", 0)) / max(total_pages, 1) * 100,
            "product_focus": page_summary.get("product", 0) / max(total_pages, 1) * 100,
            "service_focus": page_summary.get("service", 0) / max(total_pages, 1) * 100,
            "documentation": page_summary.get("docs", 0) / max(total_pages, 1) * 100
        }
        
        # Determine site type
        if content_focus["content_heavy"] > 30:
            site_type = "content_marketing"
        elif content_focus["product_focus"] > 40:
            site_type = "product_focused"
        elif content_focus["service_focus"] > 30:
            site_type = "service_focused"
        else:
            site_type = "corporate"
            
        return {
            "site_type": site_type,
            "content_focus": content_focus,
            "has_blog": page_summary.get("blog", 0) > 0,
            "content_volume": "high" if page_summary.get("blog", 0) > 20 else "medium" if page_summary.get("blog", 0) > 5 else "low"
        }

    def _apply_overrides(
        self, company_data: Dict[str, Any], job_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply user overrides to auto-detected company data.

        User can override:
        - company_name
        - company_location
        - company_language
        - company_competitors
        - content_generation_instruction
        - author_name, author_bio, author_url (for E-E-A-T scoring)

        Args:
            company_data: Auto-detected company data
            job_config: User-provided job configuration

        Returns:
            Updated company_data with overrides applied
        """
        override_fields = [
            "company_name",
            "company_location",
            "company_language",
            "company_competitors",
            "content_generation_instruction",
            # Author fields for E-E-A-T scoring
            "author_name",
            "author_bio",
            "author_url",
        ]

        for field in override_fields:
            if field in job_config and job_config[field]:
                value = job_config[field]
                # Special handling for competitors: normalize comma-separated strings
                if field == "company_competitors" and isinstance(value, list):
                    value = self._normalize_competitors_list(value)
                company_data[field] = value
                logger.debug(f"Override {field}: {value}")
        
        # Also check for author fields inside job_config["company_data"] (from API request)
        if "company_data" in job_config and isinstance(job_config["company_data"], dict):
            nested_company_data = job_config["company_data"]
            author_fields = ["author_name", "author_bio", "author_url"]
            for field in author_fields:
                if field in nested_company_data and nested_company_data[field]:
                    company_data[field] = nested_company_data[field]
                    logger.debug(f"Override {field} from company_data: {nested_company_data[field]}")
            
            # Also handle competitors from nested company_data
            if "competitors" in nested_company_data:
                competitors = nested_company_data["competitors"]
                if isinstance(competitors, list):
                    competitors = self._normalize_competitors_list(competitors)
                company_data["company_competitors"] = competitors
                logger.debug(f"Override company_competitors from company_data: {competitors}")

        return company_data
    
    def _normalize_competitors_list(self, competitors: List[Any]) -> List[str]:
        """
        Normalize competitors list to handle both formats:
        - ["competitor1.com", "competitor2.com"] (proper format)
        - ["competitor1.com, competitor2.com"] (comma-separated string in list)
        
        Args:
            competitors: List of competitors (may contain comma-separated strings)
            
        Returns:
            Normalized list of individual competitor strings
        """
        if not competitors:
            return []
        
        normalized = []
        for item in competitors:
            if isinstance(item, str):
                # Check if it's a comma-separated string
                if "," in item:
                    # Split by comma and clean up
                    split_items = [comp.strip() for comp in item.split(",") if comp.strip()]
                    normalized.extend(split_items)
                else:
                    # Single competitor string
                    normalized.append(item.strip())
            elif isinstance(item, (list, tuple)):
                # Nested list (shouldn't happen, but handle it)
                normalized.extend(self._normalize_competitors_list(item))
        
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for comp in normalized:
            if comp and comp.lower() not in seen:
                seen.add(comp.lower())
                result.append(comp)
        
        return result

    def _build_blog_page(self, context: ExecutionContext) -> Dict[str, Any]:
        """
        Build blog_page configuration with enhanced sitemap integration.

        Contains blog-specific settings for this article:
        - primary_keyword
        - internal links (from sitemap crawling + user provided)
        - output settings

        Args:
            context: ExecutionContext with job_config, company_data, and sitemap_data

        Returns:
            blog_page dictionary
        """
        job_config = context.job_config
        
        # Build internal links with priority: user provided > sitemap crawled > legacy sitemap_urls
        provided_links = job_config.get("links", "")
        
        if not provided_links:
            # Priority 1: Use crawled sitemap data (fresh, classified URLs)
            if hasattr(context, 'sitemap_data') and context.sitemap_data:
                relevant_urls = self._get_relevant_internal_links(context.sitemap_data)
                if relevant_urls:
                    provided_links = self._format_sitemap_links(relevant_urls)
                    logger.info(f"Built {len(relevant_urls)} internal links from sitemap crawl (multiple page types)")
                
            # Priority 2: Fall back to legacy sitemap_urls + batch_siblings
            if not provided_links:
                sitemap_urls = list(job_config.get("sitemap_urls") or [])
                batch_siblings = job_config.get("batch_siblings") or []
                
                # Merge batch siblings into URL pool for LLM prompt
                if batch_siblings:
                    logger.info(f"Adding {len(batch_siblings)} batch siblings to link pool for prompt")
                    for sibling in batch_siblings:
                        sibling_url = sibling.get("slug", "")
                        if sibling_url and sibling_url not in sitemap_urls:
                            sitemap_urls.append(sibling_url)
                
                if sitemap_urls:
                    provided_links = self._format_legacy_links(sitemap_urls)
                    logger.info(f"Built {len(sitemap_urls[:10])} links from legacy sitemap_urls + batch_siblings")
        
        blog_page = {
            "primary_keyword": job_config.get("primary_keyword", ""),
            "links": provided_links,
            "image_url": job_config.get("image_url"),  # Optional: pre-generated image
        }

        return blog_page

    def _get_relevant_internal_links(self, sitemap_data: Dict[str, Any]) -> List[str]:
        """
        Get relevant internal links from sitemap data across multiple page types.
        
        Prioritizes high-value pages for internal linking:
        1. Blog articles (highest priority)
        2. Resource pages (case studies, guides, tools)
        3. Product pages (features, pricing) 
        4. Documentation (help, tutorials)
        5. Company pages (about, team) - limited quantity
        
        Args:
            sitemap_data: Sitemap analysis data
            
        Returns:
            List of relevant URLs for internal linking
        """
        if not sitemap_data:
            return []
        
        relevant_urls = []
        link_counts = {}
        
        # Priority 1: Blog URLs (highest priority)
        blog_urls = sitemap_data.get("blog_urls", [])
        relevant_urls.extend(blog_urls[:6])  # Max 6 blog links
        link_counts["blogs"] = len(blog_urls[:6])
        
        # Priority 2: Resource pages (case studies, whitepapers, tools)
        resource_urls = sitemap_data.get("resource_urls", [])
        relevant_urls.extend(resource_urls[:4])  # Max 4 resource links
        link_counts["resources"] = len(resource_urls[:4])
        
        # Priority 3: Product pages (features, pricing, solutions)
        product_urls = sitemap_data.get("product_urls", [])
        relevant_urls.extend(product_urls[:3])  # Max 3 product links
        link_counts["products"] = len(product_urls[:3])
        
        # Priority 4: Documentation (guides, tutorials, help)
        docs_urls = sitemap_data.get("docs_urls", [])
        relevant_urls.extend(docs_urls[:2])  # Max 2 docs links
        link_counts["docs"] = len(docs_urls[:2])
        
        # Priority 5: Company pages (about, team) - very limited
        company_urls = sitemap_data.get("company_urls", [])
        relevant_urls.extend(company_urls[:1])  # Max 1 company link
        link_counts["company"] = len(company_urls[:1])
        
        logger.debug(f"Selected {len(relevant_urls)} relevant links: {link_counts}")
        return relevant_urls

    def _format_sitemap_links(self, urls: List[str]) -> str:
        """
        Format sitemap URLs into internal link suggestions for the LLM prompt.
        
        Args:
            urls: List of URLs from sitemap crawling (any page type)
            
        Returns:
            Formatted string of internal links
        """
        link_lines = []
        for i, url in enumerate(urls[:12], 1):  # Limit to 12 for prompt efficiency
            # Extract readable title from URL slug
            parts = url.strip("/").split("/")
            slug = parts[-1] if parts else ""
            
            # Convert slug to readable title
            title = slug.replace("-", " ").replace("_", " ").title()
            if not title:
                title = "Related Article"
                
            link_lines.append(f"[{i}] {url} - {title}")
        
        return "\n".join(link_lines)

    def _format_legacy_links(self, sitemap_urls: List[str]) -> str:
        """
        Format legacy sitemap_urls into internal link suggestions (backward compatibility).
        
        Args:
            sitemap_urls: List of URLs from job_config.sitemap_urls or batch_siblings
            
        Returns:
            Formatted string of internal links
        """
        link_lines = []
        for i, url in enumerate(sitemap_urls[:10], 1):
            # Extract readable title from URL
            parts = url.strip("/").split("/")
            title = parts[-1].replace("-", " ").title() if parts else "Related"
            link_lines.append(f"[{i}] {url} - {title}")
        
        return "\n".join(link_lines)

    def _normalize_job_config(self, job_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize and validate job configuration fields.

        Maps v4.1 field names to Python names if needed.

        Args:
            job_config: Original job configuration

        Returns:
            Normalized job configuration
        """
        normalized = job_config.copy()

        # Ensure primary_keyword is set
        if "primary_keyword" not in normalized:
            normalized["primary_keyword"] = ""

        # Set default content generation instruction if not provided
        if "content_generation_instruction" not in normalized:
            normalized["content_generation_instruction"] = (
                "Write a comprehensive, SEO-optimized blog post. "
                "Follow all content rules strictly. "
                "Ensure paragraph length ≤ 25 words. "
                "Include 8+ sources, 1+ internal link per H2 section. "
                "Generate 5 FAQ items and 3 PAA items minimum."
            )

        return normalized
