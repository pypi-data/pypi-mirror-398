"""
Stage 5: Internal Links Generation

Maps to v4.1 Phase 5, Steps 14-19: create-more-section → URL generation and formatting

Generates "More Reading" / "Related Links" suggestions based on article content.

Input:
  - ExecutionContext.structured_data (ArticleOutput with headline, sections)
  - ExecutionContext.job_config (company_data for context)

Output:
  - ExecutionContext.parallel_results['internal_links_html'] (formatted HTML)

Process:
1. Extract article topics (headline + section titles)
2. Generate internal link suggestions (topic-based)
3. Filter and deduplicate
4. Format as HTML
"""

import logging
import asyncio
from typing import List, Dict, Any, Tuple
import httpx

from ..core import ExecutionContext, Stage
from ..models.internal_link import InternalLink, InternalLinkList

logger = logging.getLogger(__name__)


class InternalLinksStage(Stage):
    """
    Stage 5: Internal Links Generation.

    Handles:
    - Topic extraction from article
    - Link suggestion generation
    - Deduplication and filtering
    - HTML formatting
    """

    stage_num = 5
    stage_name = "Internal Links Generation"

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 5: Generate internal links.

        Input from context:
        - structured_data: ArticleOutput with headline and sections
        - job_config: Optional company context

        Output to context:
        - parallel_results['internal_links_html']: Formatted HTML

        Args:
            context: ExecutionContext from Stage 3

        Returns:
            Updated context with parallel_results populated
        """
        logger.info(f"Stage 5: {self.stage_name}")

        # Validate input
        if not context.structured_data:
            logger.warning("No structured_data available for internal links")
            context.parallel_results["internal_links_html"] = ""
            return context

        # Extract topics from article
        topics = self._extract_topics(context.structured_data)
        logger.info(f"Extracted {len(topics)} topics from article")

        # Generate link suggestions from:
        # 1) Batch siblings (cross-link within this batch)
        # 2) Sitemap URLs (from job_config or sitemap_pages)
        link_list = await self._generate_suggestions(topics, context)
        logger.info(f"Generated {link_list.count()} initial link suggestions (batch siblings + sitemap URLs)")

        # Validate URLs with HTTP HEAD checks (skip if nothing to validate)
        if link_list.count() > 0:
            logger.info(f"Validating {link_list.count()} internal link URLs...")
            validated_link_list = await self._validate_internal_link_urls(link_list, context)
        else:
            validated_link_list = link_list
        
        # Filter and optimize (keep only top 10)
        link_list = (
            validated_link_list.filter_valid()
            .sort_by_relevance()
            .deduplicate_domains()
            .limit(10)
        )

        logger.info(f"✅ Final link count: {link_list.count()}")
        for link in link_list.links:
            logger.debug(f"   {link.url} (relevance={link.relevance})")

        # Format as HTML (for "More on this topic" section at bottom)
        internal_links_html = link_list.to_html()
        logger.info(f"   HTML size: {len(internal_links_html)} chars")

        # NEW: Assign 1-2 links per section based on topic matching (1Komma5 style)
        section_internal_links = self._assign_links_per_section(
            context.structured_data, 
            link_list
        )
        logger.info(f"📎 Assigned internal links to {len([s for s in section_internal_links.values() if s])} sections")

        # NEW: Embed links directly into section content using Gemini (AI-only)
        if section_internal_links and context.structured_data:
            logger.info("🔗 Step 6: Embedding internal links into section content (AI-only)...")
            context = await self._embed_links_in_content(context, section_internal_links)
        else:
            logger.info("   Skipping link embedding (no links assigned or no structured_data)")

        # Store in context
        context.parallel_results["internal_links_html"] = internal_links_html
        context.parallel_results["internal_links_count"] = link_list.count()
        context.parallel_results["internal_links_list"] = link_list
        context.parallel_results["section_internal_links"] = section_internal_links  # NEW

        return context

    def _extract_topics(self, article) -> List[str]:
        """
        Extract topics from article.

        Uses headline and section titles to identify main topics.

        Args:
            article: ArticleOutput instance

        Returns:
            List of topic strings
        """
        topics = []

        # Add headline as primary topic
        if article.Headline:
            topics.append(article.Headline)

        # Add section titles
        section_titles = [
            article.section_01_title,
            article.section_02_title,
            article.section_03_title,
            article.section_04_title,
            article.section_05_title,
            article.section_06_title,
            article.section_07_title,
            article.section_08_title,
            article.section_09_title,
        ]

        for title in section_titles:
            if title and title.strip():
                topics.append(title.strip())

        logger.debug(f"Extracted topics: {topics}")
        return topics

    def _assign_links_per_section(
        self, 
        article, 
        link_list: InternalLinkList
    ) -> Dict[int, List[Dict[str, str]]]:
        """
        Assign 1-2 internal links per section based on topic matching.
        
        1Komma5 style: Links are placed BELOW each section, not embedded in text.
        This is easier to maintain and has the same SEO power.
        
        Args:
            article: ArticleOutput instance with section titles
            link_list: InternalLinkList with all available internal links
            
        Returns:
            Dict mapping section number (1-9) to list of link dicts {url, title}
        """
        section_links: Dict[int, List[Dict[str, str]]] = {}
        
        if not link_list or link_list.count() == 0:
            return section_links
        
        # Get all available links as list of dicts
        available_links = [
            {'url': link.url, 'title': link.title, 'relevance': link.relevance}
            for link in link_list.links
        ]
        
        # Track used links to avoid duplicates across sections
        used_urls = set()
        
        # Section titles for matching
        section_titles = [
            (1, getattr(article, 'section_01_title', '') or ''),
            (2, getattr(article, 'section_02_title', '') or ''),
            (3, getattr(article, 'section_03_title', '') or ''),
            (4, getattr(article, 'section_04_title', '') or ''),
            (5, getattr(article, 'section_05_title', '') or ''),
            (6, getattr(article, 'section_06_title', '') or ''),
            (7, getattr(article, 'section_07_title', '') or ''),
            (8, getattr(article, 'section_08_title', '') or ''),
            (9, getattr(article, 'section_09_title', '') or ''),
        ]
        
        for section_num, section_title in section_titles:
            if not section_title.strip():
                continue
            
            # Find best matching links for this section
            section_matches = []
            for link in available_links:
                if link['url'] in used_urls:
                    continue
                
                # Calculate relevance to this specific section
                relevance = self._calculate_relevance(
                    link['title'] + ' ' + link['url'], 
                    [section_title]
                )
                if relevance >= 2:  # Minimum threshold
                    section_matches.append({
                        'url': link['url'],
                        'title': link['title'],
                        'score': relevance
                    })
            
            # Sort by score and take top 2
            section_matches.sort(key=lambda x: x['score'], reverse=True)
            top_matches = section_matches[:2]
            
            if top_matches:
                section_links[section_num] = [
                    {'url': m['url'], 'title': m['title']} 
                    for m in top_matches
                ]
                # Mark as used
                for m in top_matches:
                    used_urls.add(m['url'])
        
        return section_links

    async def _generate_suggestions(
        self, topics: List[str], context: ExecutionContext
    ) -> InternalLinkList:
        """
        Generate internal link suggestions from sitemap URLs.

        Sources (in priority order):
        1. Batch siblings (cross-link within same batch)
        2. Sitemap URLs from job_config.sitemap_urls
        3. Sitemap pages from context.sitemap_pages (if available)

        Args:
            topics: List of article topics (headline + section titles)
            context: ExecutionContext with job_config and sitemap data

        Returns:
            InternalLinkList with suggested links, sorted by relevance
        """
        link_list = InternalLinkList()

        # Get company data for context
        company_data = context.company_data or {}
        competitors = company_data.get("company_competitors", [])
        
        # Priority 1: Batch siblings (highest priority)
        batch_siblings = context.job_config.get("batch_siblings", []) if context.job_config else []
        if batch_siblings:
            logger.info(f"Prioritizing {len(batch_siblings)} batch siblings for cross-linking")
            for idx, sibling in enumerate(batch_siblings):
                sibling_url = sibling.get("url", "") or sibling.get("slug", "")  # Support both "url" and "slug" keys
                sibling_title = sibling.get("title", "")
                sibling_keyword = sibling.get("keyword", "")
                sibling_description = sibling.get("description", "")
                if not sibling_url:
                    logger.warning(f"Skipping sibling {idx+1}: no URL/slug provided")
                    continue
                
                # Standardize URL format: always use /magazine/{slug}
                url = self._normalize_url(sibling_url)
                title = sibling_title or self._extract_title_from_url(url)
                
                # Calculate relevance based on keyword similarity to topics
                relevance = self._calculate_relevance(sibling_keyword or sibling_title, topics)
                # Boost batch siblings slightly
                relevance = min(relevance + 2, 10)
                
                logger.info(f"  Adding batch sibling {idx+1}: '{title}' → {url} (relevance={relevance})")
                
                link_list.add_link(
                    url=url,
                    title=title,
                    relevance=relevance,
                    domain=self._extract_domain(url),
                )

        # Priority 2: Sitemap URLs from job_config
        sitemap_urls = context.job_config.get("sitemap_urls", []) if context.job_config else []
        if sitemap_urls:
            logger.info(f"Processing {len(sitemap_urls)} sitemap URLs from job_config")
            
            # Process sitemap URLs - crawl XML sitemaps if needed
            individual_urls = await self._process_sitemap_urls(sitemap_urls, context)
            
            for url in individual_urls:
                if not url or not isinstance(url, str):
                    continue
                
                # Normalize URL format
                normalized_url = self._normalize_url(url)
                title = self._extract_title_from_url(normalized_url)
                
                # Calculate relevance based on topic matching
                relevance = self._calculate_relevance(normalized_url + " " + title, topics)
                
                # Only add if relevance is reasonable (>= 3)
                if relevance >= 3:
                    link_list.add_link(
                        url=normalized_url,
                        title=title,
                        relevance=relevance,
                        domain=self._extract_domain(normalized_url),
                    )

        # Priority 3: Sitemap pages from context (if available)
        # Check both context.sitemap_pages AND context.sitemap_data._sitemap_pages_object
        sitemap_pages_obj = None
        if hasattr(context, 'sitemap_pages') and context.sitemap_pages and hasattr(context.sitemap_pages, 'pages'):
            sitemap_pages_obj = context.sitemap_pages
        elif hasattr(context, 'sitemap_data') and context.sitemap_data and '_sitemap_pages_object' in context.sitemap_data:
            sitemap_pages_obj = context.sitemap_data['_sitemap_pages_object']
        
        if sitemap_pages_obj and hasattr(sitemap_pages_obj, 'pages'):
            logger.info(f"Processing {len(sitemap_pages_obj.pages)} sitemap pages from context")
            # Use ALL pages - services, solutions, case studies are all valid internal link targets
            # Not just blog pages! Any relevant page improves SEO and user experience
            all_pages = sitemap_pages_obj.pages[:100]  # Limit to 100 for performance
            
            for page in all_pages:
                if not page.url:
                    continue
                
                # Normalize URL format
                normalized_url = self._normalize_url(page.url)
                title = page.title or self._extract_title_from_url(normalized_url)
                
                # Calculate relevance based on topic matching
                relevance = self._calculate_relevance(normalized_url + " " + (title or ""), topics)
                
                # Only add if relevance is reasonable (>= 3)
                if relevance >= 3:
                    link_list.add_link(
                        url=normalized_url,
                        title=title,
                        relevance=relevance,
                        domain=self._extract_domain(normalized_url),
                    )

        logger.info(f"Generated {link_list.count()} initial suggestions from sitemap URLs")
        return link_list

    async def _validate_internal_link_urls(
        self, link_list: InternalLinkList, context: ExecutionContext
    ) -> InternalLinkList:
        """
        Validate internal link URLs with HTTP HEAD requests.
        
        Matches v4.1 behavior for internal link validation:
        - HTTP HEAD requests to check URL status
        - Remove URLs that return non-200 status codes
        - Parallel validation for performance
        
        Args:
            link_list: List of internal links to validate
            context: Execution context (for company URL base)
            
        Returns:
            InternalLinkList with only validated URLs
        """
        if not link_list.links:
            return link_list
        
        # Get company base URL for building full URLs
        company_url = context.company_data.get("company_url", "") if context.company_data else ""
        
        if not company_url:
            logger.warning("No company URL available for internal link validation")
            return link_list
        
        # Parse base URL
        from urllib.parse import urljoin, urlparse
        base_url = company_url.rstrip('/')
        
        # Validate links in parallel
        async def validate_single_link(link: InternalLink) -> InternalLink:
            """Validate a single internal link."""
            try:
                # Build full URL if relative
                if link.url.startswith('/'):
                    full_url = urljoin(base_url, link.url)
                else:
                    full_url = link.url
                
                # HTTP HEAD request with timeout
                async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                    response = await client.head(full_url)
                    
                    if response.status_code == 200:
                        logger.debug(f"✅ Internal link valid: {link.url}")
                        return link
                    else:
                        logger.warning(f"❌ Internal link invalid (HTTP {response.status_code}): {link.url}")
                        return None
                        
            except httpx.TimeoutException:
                logger.warning(f"❌ Internal link timeout: {link.url}")
                return None
            except httpx.RequestError as e:
                logger.warning(f"❌ Internal link error: {link.url} - {e}")
                return None
            except Exception as e:
                logger.warning(f"❌ Internal link validation failed: {link.url} - {e}")
                return None
        
        # Execute validations in parallel
        logger.info(f"Validating {len(link_list.links)} internal links against {base_url}")
        validation_tasks = [validate_single_link(link) for link in link_list.links]
        
        try:
            validated_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Internal link validation failed: {e}")
            return link_list  # Return original list on error
        
        # Filter out failed validations
        validated_links = []
        for result in validated_results:
            if isinstance(result, InternalLink):  # Successful validation
                validated_links.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Internal link validation exception: {result}")
        
        # Create new link list with validated links
        validated_link_list = InternalLinkList()
        for link in validated_links:
            validated_link_list.add_link(
                url=link.url,
                title=link.title,
                relevance=link.relevance,
                domain=link.domain
            )
        
        removed_count = len(link_list.links) - len(validated_links)
        if removed_count > 0:
            logger.warning(f"🔗 Internal link validation: {len(validated_links)} valid, {removed_count} removed (404/timeout)")
        else:
            logger.info(f"🔗 Internal link validation: All {len(validated_links)} links valid")
        
        return validated_link_list

    async def _process_sitemap_urls(
        self, sitemap_urls: List[str], context: ExecutionContext
    ) -> List[str]:
        """
        Process sitemap URLs - crawl XML sitemaps to extract individual URLs if needed.
        
        Args:
            sitemap_urls: List of sitemap URLs (can be XML sitemap URLs or individual URLs)
            context: Execution context
            
        Returns:
            List of individual article URLs
        """
        individual_urls = []
        
        for url in sitemap_urls:
            if not url or not isinstance(url, str):
                continue
            
            # Check if this is an XML sitemap URL
            is_xml_sitemap = (
                url.endswith('.xml') or 
                'sitemap' in url.lower() or
                url.endswith('/sitemap') or
                url.endswith('/sitemap_index.xml') or
                url.endswith('/post-sitemap.xml')
            )
            
            if is_xml_sitemap:
                # Fetch and parse XML sitemap directly to extract individual URLs
                logger.info(f"Fetching XML sitemap: {url}")
                try:
                    # Fetch the XML sitemap directly
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(url)
                        response.raise_for_status()
                        
                        # Extract URLs from XML
                        from pipeline.processors.sitemap_crawler import SitemapCrawler
                        urls = SitemapCrawler._extract_urls(response.content)
                        
                        if urls:
                            logger.info(f"Extracted {len(urls)} URLs from XML sitemap")
                            # Filter to blog URLs if possible (check for /blog/, /post/, /article/ patterns)
                            blog_urls = [
                                u for u in urls 
                                if any(pattern in u.lower() for pattern in ['/blog/', '/post/', '/article/', '/news/'])
                            ]
                            # Use blog URLs if found, otherwise use all URLs
                            final_urls = blog_urls[:50] if blog_urls else urls[:50]
                            logger.info(f"Using {len(final_urls)} URLs for internal linking")
                            individual_urls.extend(final_urls)
                        else:
                            logger.warning(f"No URLs found in XML sitemap: {url}")
                            
                except Exception as e:
                    logger.warning(f"Failed to fetch XML sitemap {url}: {e}")
                    # Try using SitemapCrawler as fallback
                    try:
                        from pipeline.processors.sitemap_crawler import SitemapCrawler
                        crawler = SitemapCrawler()
                        company_url = context.company_data.get("company_url", "") if context.company_data else ""
                        if company_url:
                            sitemap_pages = await crawler.crawl(company_url=company_url)
                            blog_urls = sitemap_pages.get_blog_urls(min_confidence=0.7)
                            if blog_urls:
                                individual_urls.extend(blog_urls[:50])
                    except Exception as e2:
                        logger.warning(f"Fallback crawl also failed: {e2}")
                    continue
            else:
                # Already an individual URL, use as-is
                individual_urls.append(url)
        
        return individual_urls

    def __repr__(self) -> str:
        """String representation."""
        return f"InternalLinksStage(stage_num={self.stage_num})"

    # Helpers
    @staticmethod
    def _normalize_url(url: str) -> str:
        """
        Normalize URL to /magazine/{slug} format.
        
        Args:
            url: URL string (can be full URL, relative path, or slug)
            
        Returns:
            Normalized URL in /magazine/{slug} format
        """
        if not url:
            return ""
        
        url = url.strip()
        
        # Skip external URLs (keep as-is)
        if url.startswith("http://") or url.startswith("https://"):
            return url
        
        # Skip anchor links
        if url.startswith("#"):
            return url
        
        # Already in correct format
        if url.startswith("/magazine/"):
            return url
        
        # Has leading slash but not /magazine/ → add magazine prefix
        if url.startswith("/"):
            return f"/magazine{url}"
        
        # No leading slash → add /magazine/ prefix
        return f"/magazine/{url}"

    @staticmethod
    def _extract_title_from_url(url: str) -> str:
        """
        Extract readable title from URL.
        
        Args:
            url: URL string
            
        Returns:
            Human-readable title extracted from URL
        """
        if not url:
            return "Related Article"
        
        # Extract last part of URL path
        parts = url.strip("/").split("/")
        if not parts:
            return "Related Article"
        
        # Get last part and convert to title
        slug = parts[-1]
        # Remove query params and fragments
        slug = slug.split("?")[0].split("#")[0]
        # Convert slug to title
        title = slug.replace("-", " ").replace("_", " ").title()
        return title if title else "Related Article"

    @staticmethod
    def _extract_domain(url: str) -> str:
        """
        Extract domain from URL for deduplication.
        
        Args:
            url: URL string
            
        Returns:
            Domain string for deduplication
        """
        if not url:
            return ""
        
        # For relative URLs, use first path segment
        if url.startswith("/"):
            parts = url.strip("/").split("/")
            return parts[0] if parts else "/magazine/"
        
        # For absolute URLs, extract domain
        if url.startswith("http://") or url.startswith("https://"):
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        
        # Fallback
        return "/magazine/"

    async def _embed_links_in_content(
        self,
        context: ExecutionContext,
        section_internal_links: Dict[int, List[Dict[str, str]]]
    ) -> ExecutionContext:
        """
        Embed internal links directly into section content using Gemini AI.
        
        Uses AI-only approach (similar to Stage 3) to naturally insert links
        into appropriate places in the content.
        
        Args:
            context: ExecutionContext with structured_data
            section_internal_links: Dict mapping section numbers to lists of link dicts
            
        Returns:
            Updated context with links embedded in section content
        """
        if not context.structured_data:
            return context
        
        # Initialize Gemini client
        if not hasattr(self, 'gemini_client') or not self.gemini_client:
            from ..models.gemini_client import GeminiClient
            self.gemini_client = GeminiClient()
        
        article_dict = context.structured_data.dict() if hasattr(context.structured_data, 'dict') else dict(context.structured_data)
        updated_fields = {}
        
        # Process sections with assigned links in parallel
        async def embed_links_in_section(section_num: int, links: List[Dict[str, str]]) -> Tuple[str, str]:
            """Embed links into a single section's content."""
            field_name = f"section_{section_num:02d}_content"
            content = article_dict.get(field_name, '')
            
            if not content or not isinstance(content, str) or len(content) < 50:
                return field_name, content or ''
            
            # Build links list for prompt
            links_text = "\n".join([
                f"- {link['title']}: {link['url']}"
                for link in links
            ])
            
            prompt = f"""You are an expert content editor. Your task is to naturally embed internal links into the provided content.

INTERNAL LINKS TO EMBED (embed these links naturally into the content):
{links_text}

CONTENT TO UPDATE:
{content}

INSTRUCTIONS:
1. Find 1-2 natural places in the content where each link would fit contextually
2. Embed links naturally using HTML anchor tags: <a href="{{url}}">{{title}}</a>
3. Make the link text flow naturally with the sentence - don't force it
4. Prefer embedding links in:
   - Sentences that mention related concepts
   - Transition sentences between paragraphs
   - Examples or case study mentions
   - Conclusion sentences
5. DO NOT:
   - Add links at the very beginning or end (too obvious)
   - Force links where they don't fit naturally
   - Change the meaning or structure of the content
   - Add more than 2 links per section (even if 2 links are provided)
6. Preserve all other content exactly as-is
7. Return ONLY the updated content with embedded links, no explanations

Example:
Original: "Cloud security requires multiple layers of protection."
With link: "Cloud security requires multiple layers of protection. Learn more about <a href="/blog/cloud-security-best-practices">cloud security best practices</a>."

Return the complete updated content with links naturally embedded.
"""
            
            try:
                response = await self.gemini_client.generate_content(
                    prompt=prompt,
                    enable_tools=False
                )
                
                if response and response.strip() and len(response.strip()) > len(content) * 0.3:
                    # Validate response is reasonable length (at least 30% of original)
                    return field_name, response.strip()
                else:
                    logger.warning(f"   ⚠️ Section {section_num}: Link embedding returned invalid response, keeping original")
                    return field_name, content
            except Exception as e:
                logger.warning(f"   ⚠️ Section {section_num}: Link embedding failed - {e}")
                return field_name, content
        
        # Create tasks for sections with links
        tasks = []
        for section_num, links in section_internal_links.items():
            if links:
                tasks.append(embed_links_in_section(section_num, links))
        
        if not tasks:
            logger.info("   No sections to update")
            return context
        
        # Process in parallel (max 5 concurrent to avoid rate limits)
        import asyncio
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Apply updates
        updated_count = 0
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"   ⚠️ Link embedding exception: {result}")
                continue
            
            field_name, updated_content = result
            if updated_content != article_dict.get(field_name, ''):
                updated_fields[field_name] = updated_content
                updated_count += 1
        
        # Update structured_data
        if updated_fields:
            for field_name, updated_content in updated_fields.items():
                if hasattr(context.structured_data, field_name):
                    setattr(context.structured_data, field_name, updated_content)
                elif isinstance(context.structured_data, dict):
                    context.structured_data[field_name] = updated_content
            
            logger.info(f"   ✅ Embedded links in {updated_count} section(s)")
        else:
            logger.info("   No content updates needed")
        
        return context

    @staticmethod
    def _calculate_relevance(text: str, topics: List[str]) -> int:
        """
        Calculate relevance score (1-10) based on topic matching.
        
        Uses simple keyword matching: counts how many topic words appear in text.
        
        Args:
            text: Text to match against (URL, title, keyword, etc.)
            topics: List of topic strings (headline + section titles)
            
        Returns:
            Relevance score from 1-10
        """
        if not text or not topics:
            return 5  # Default relevance
        
        text_lower = text.lower()
        matches = 0
        
        # Extract keywords from topics
        topic_keywords = set()
        for topic in topics:
            if not topic:
                continue
            # Split topic into words
            words = topic.lower().split()
            # Filter out common stop words
            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
            keywords = [w.strip(".,!?;:") for w in words if w not in stop_words and len(w) > 2]
            topic_keywords.update(keywords)
        
        # Count matches
        for keyword in topic_keywords:
            if keyword in text_lower:
                matches += 1
        
        # Calculate relevance score (1-10)
        # More matches = higher relevance
        if matches == 0:
            return 3  # Low relevance
        elif matches == 1:
            return 5  # Medium relevance
        elif matches == 2:
            return 7  # High relevance
        elif matches >= 3:
            return 9  # Very high relevance
        else:
            return 5  # Default
