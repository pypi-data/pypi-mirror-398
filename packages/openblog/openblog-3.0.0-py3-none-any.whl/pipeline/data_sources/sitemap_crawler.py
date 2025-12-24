"""
Sitemap Crawler Processor

Fetches and labels all URLs from a company's sitemap.
Auto-detects page types (blog, product, service, docs, resource, other).

Usage:
    crawler = SitemapCrawler()
    sitemap_pages = await crawler.crawl(company_url="https://example.com")
"""

import defusedxml.ElementTree as ET
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from collections import OrderedDict
import httpx
from httpx import Timeout, Limits
import logging
from urllib.parse import urlparse
import re
import asyncio
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

try:
    from .sitemap_page import SitemapPage, SitemapPageList, PageLabel
except ImportError:
    # For standalone testing
    from sitemap_page import SitemapPage, SitemapPageList, PageLabel

logger = logging.getLogger(__name__)


class SitemapCrawler:
    """
    Crawls company sitemap and auto-labels all URLs.

    Responsibilities:
    1. Fetch sitemap from standard locations (/sitemap.xml, /sitemap_index.xml)
    2. Handle recursive sitemap_index.xml (multiple sitemaps)
    3. Extract all URLs
    4. Auto-detect page type (blog, product, service, docs, resource, other)
    5. Return labeled SitemapPageList for downstream filtering

    Design:
    - Single responsibility: Crawl and label
    - Pattern matching for classification
    - Configurable: Custom patterns, confidence thresholds, caching
    """

    # Default URL patterns for common page types
    # Patterns use optional trailing slash: \/pattern\/?
    DEFAULT_PATTERNS = {
        "blog": [
            r"\/blog\/?",
            r"\/news\/?",
            r"\/articles\/?",
            r"\/posts\/?",
            r"\/insights\/?",
            r"\/stories\/?",
            r"\/updates\/?",
            r"\/press\/?",
        ],
        "product": [
            r"\/products?\/?",         # /product or /products
            r"\/solutions?\/?",
            r"\/pricing\/?",
            r"\/features\/?",
            r"\/plans\/?",
            r"\/offerings?\/?",
            r"\/store\/?",
            r"\/shop\/?",
            r"\/catalog\/?",
            # E-commerce patterns
            r"\/deals?\/?",
            r"\/inventory\/?",
        ],
        "service": [
            r"\/services?\/?",
            r"\/consulting\/?",
            r"\/agency\/?",
            r"\/professional-services\/?",
        ],
        "docs": [
            r"\/docs?\/?",
            r"\/documentation\/?",
            r"\/guides?\/?",
            r"\/tutorials?\/?",
            r"\/help\/?",
            r"\/kb\/?",
            r"\/knowledge-base\/?",
            r"\/faq\/?",
        ],
        "resource": [
            r"\/whitepapers?\/?",
            r"\/case-studies?\/?",
            r"\/templates?\/?",
            r"\/tools?\/?",
            r"\/calculators?\/?",
            r"\/webinars?\/?",
            r"\/videos?\/?",
            r"\/ebooks?\/?",
            r"\/reports?\/?",
        ],
        "company": [
            r"\/about\/?",
            r"\/about-us\/?",
            r"\/team\/?",
            r"\/careers?\/?",
            r"\/jobs?\/?",
            r"\/culture\/?",
            r"\/company\/?",
            r"\/who-we-are\/?",
            r"\/mission\/?",
            r"\/vision\/?",
            r"\/values?\/?",
            r"\/leadership\/?",
            r"\/newsroom\/?",
        ],
        "legal": [
            r"\/imprint\/?",
            r"\/impressum\/?",
            r"\/privacy\/?",
            r"\/privacy-policy\/?",
            r"\/terms?\/?",
            r"\/terms-of-service\/?",
            r"\/terms-of-use\/?",
            r"\/legal\/?",
            r"\/disclaimer\/?",
            r"\/cookies?\/?",
            r"\/data-protection\/?",
            r"\/gdpr\/?",
        ],
        "contact": [
            r"\/contact\/?",
            r"\/contact-us\/?",
            r"\/get-in-touch\/?",
            r"\/reach-us\/?",
            r"\/talk-to-us\/?",
            r"\/support\/?",
            r"\/customer-support\/?",
            r"\/help-desk\/?",
            r"\/email-us\/?",
        ],
        "landing": [
            r"\/campaigns?\/?",
            r"\/lp\/?",
            r"\/landing\/?",
            r"\/offers?\/?",
            r"\/promotions?\/?",
            r"\/deals?\/?",
            r"\/promos?\/?",
        ],
    }

    # Dangerous URL protocols that should be rejected
    DANGEROUS_PROTOCOLS = [
        'javascript:', 'file:', 'data:', 'vbscript:', 
        'about:', 'chrome:', 'chrome-extension:'
    ]

    def __init__(
        self,
        custom_patterns: Optional[Dict[str, List[str]]] = None,
        timeout: Optional[Timeout] = None,
        cache_ttl: int = 3600,
        max_urls: int = 10000,
        max_cache_size: int = 100,
    ):
        """
        Initialize SitemapCrawler.

        Args:
            custom_patterns: Optional custom URL patterns for classification
            timeout: HTTP request timeout configuration (default: connect=5s, read=10s, write=5s, pool=5s)
            cache_ttl: Cache time-to-live in seconds (default: 3600 = 1 hour)
            max_urls: Maximum URLs to process (default: 10000, must be > 0)
            max_cache_size: Maximum number of cache entries (default: 100, uses LRU eviction, must be > 0)

        Raises:
            ValueError: If max_urls or max_cache_size is <= 0
        """
        # Validate parameters
        if max_urls <= 0:
            raise ValueError(f"max_urls must be > 0, got {max_urls}")
        if max_cache_size <= 0:
            raise ValueError(f"max_cache_size must be > 0, got {max_cache_size}")
        if cache_ttl < 0:
            raise ValueError(f"cache_ttl must be >= 0, got {cache_ttl}")

        self.patterns = custom_patterns or self.DEFAULT_PATTERNS
        self.timeout = timeout or Timeout(
            connect=5.0,
            read=10.0,
            write=5.0,
            pool=5.0,
        )
        self.cache_ttl = cache_ttl
        self.max_urls = max_urls
        self.max_cache_size = max_cache_size
        self._cache: OrderedDict[str, Tuple[SitemapPageList, float]] = OrderedDict()
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_lock = asyncio.Lock()  # Thread-safety for cache operations

    async def crawl(
        self,
        company_url: str,
    ) -> SitemapPageList:
        """
        Crawl company's sitemap and return labeled pages.

        Args:
            company_url: Company website URL (e.g., "https://example.com")

        Returns:
            SitemapPageList with labeled pages, ready for filtering
        """
        start_time = time.time()
        
        # Normalize company_url (remove trailing slash)
        company_url = company_url.rstrip('/')
        
        logger.info(f"Starting sitemap crawl for {company_url}")

        # Validate company_url first
        if not self._is_valid_url(company_url):
            logger.error(f"Invalid company_url: {company_url}")
            return self._empty_sitemap(company_url)

        # Check cache (include max_urls in cache key) - thread-safe
        cache_key = f"{company_url}:{self.max_urls}"
        async with self._cache_lock:
            if cache_key in self._cache:
                result, timestamp = self._cache[cache_key]
                if time.time() - timestamp < self.cache_ttl:
                    self._cache_hits += 1
                    # Move to end (LRU - most recently used)
                    self._cache.move_to_end(cache_key)
                    duration = time.time() - start_time
                    logger.info(
                        f"Sitemap crawl complete (cached): {result.count()} URLs in {duration:.2f}s"
                    )
                    return result
                else:
                    # Cache expired, remove it
                    del self._cache[cache_key]

            self._cache_misses += 1

        try:
            # Step 1: Fetch all URLs from sitemap
            urls = await self._fetch_all_urls(company_url)
            logger.info(f"Fetched {len(urls)} URLs from sitemap")

            if not urls:
                logger.warning(f"No URLs found in sitemap for {company_url}")
                result = self._empty_sitemap(company_url)
                duration = time.time() - start_time
                logger.info(f"Sitemap crawl complete: 0 URLs in {duration:.2f}s")
                return result

            # Step 2: Apply memory limit
            if len(urls) > self.max_urls:
                logger.warning(
                    f"Sitemap has {len(urls)} URLs, limiting to {self.max_urls}"
                )
                urls = urls[:self.max_urls]

            # Step 3: Create SitemapPage objects with pattern-based classification
            pages = []
            invalid_url_count = 0
            for url in urls:
                if not self._is_valid_url(url):
                    invalid_url_count += 1
                    logger.debug(f"Invalid URL skipped: {url}")
                    continue
                page = self._classify_page(url)
                pages.append(page)

            if invalid_url_count > 0:
                logger.warning(f"Skipped {invalid_url_count} invalid URLs")

            # Step 4: Return labeled page list
            sitemap_pages = SitemapPageList(
                pages=pages,
                company_url=company_url,
                total_urls=len(urls),
                fetch_timestamp=datetime.now().isoformat()
            )

            # Store in cache with LRU eviction - thread-safe
            async with self._cache_lock:
                self._cache[cache_key] = (sitemap_pages, time.time())
                self._cache.move_to_end(cache_key)  # Mark as most recently used
                
                # Evict oldest entries if cache exceeds max size
                while len(self._cache) > self.max_cache_size:
                    self._cache.popitem(last=False)  # Remove oldest (LRU)

            duration = time.time() - start_time
            logger.info(
                f"Sitemap crawl complete: {sitemap_pages.count()} URLs "
                f"(cache_hits={self._cache_hits}, cache_misses={self._cache_misses}, "
                f"cache_size={len(self._cache)}) "
                f"in {duration:.2f}s"
            )
            return sitemap_pages

        except httpx.TimeoutException as e:
            logger.warning(f"Sitemap crawl timeout for {company_url}: {e}")
            return self._empty_sitemap(company_url)
        except httpx.HTTPStatusError as e:
            logger.warning(
                f"Sitemap HTTP error {e.response.status_code} for {company_url}: {e}"
            )
            return self._empty_sitemap(company_url)
        except ET.ParseError as e:
            logger.warning(f"Invalid XML in sitemap for {company_url}: {e}")
            return self._empty_sitemap(company_url)
        except Exception as e:
            logger.error(
                f"Unexpected error crawling sitemap for {company_url}: {e}",
                exc_info=True
            )
            return self._empty_sitemap(company_url)

    def _empty_sitemap(self, company_url: str) -> SitemapPageList:
        """
        Create an empty SitemapPageList for error cases.

        Args:
            company_url: Company website URL

        Returns:
            Empty SitemapPageList
        """
        return SitemapPageList(
            pages=[],
            company_url=company_url,
            total_urls=0,
            fetch_timestamp=datetime.now().isoformat()
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def _fetch_all_urls(self, company_url: str) -> List[str]:
        """
        Fetch all URLs from sitemap(s).

        Handles:
        - Single sitemap.xml
        - sitemap_index.xml with multiple sitemaps
        - Non-existent sitemaps gracefully
        - HTTP redirects
        - Concurrent sub-sitemap fetching

        Args:
            company_url: Company website URL

        Returns:
            List of all URLs found
        """
        all_urls = []
        sitemap_locations = [
            f"{company_url}/sitemap.xml",
            f"{company_url}/sitemap_index.xml",
            f"{company_url}/sitemap/sitemap.xml",
        ]

        # Also try www version if no www (preserve http/https protocol)
        parsed = urlparse(company_url)
        if parsed.netloc and not parsed.netloc.startswith("www."):
            # Preserve original protocol (http or https)
            protocol = parsed.scheme
            domain = parsed.netloc
            base = f"{protocol}://www.{domain}"
            sitemap_locations.extend([
                f"{base}/sitemap.xml",
                f"{base}/sitemap_index.xml",
                f"{base}/sitemap/sitemap.xml",
            ])

        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            limits=Limits(max_connections=5, max_keepalive_connections=2)
        ) as client:
            for sitemap_url in sitemap_locations:
                try:
                    # Rate limiting: delay between attempts
                    await asyncio.sleep(0.5)

                    response = await client.get(sitemap_url)
                    response.raise_for_status()

                    root = ET.fromstring(response.content)
                    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

                    # Check if this is a sitemap_index (has sitemaps, not urls)
                    sitemaps = root.findall(".//sm:sitemap/sm:loc", ns)
                    if sitemaps:
                        # This is a sitemap_index, fetch all sub-sitemaps concurrently
                        logger.info(
                            f"Found sitemap_index at {sitemap_url}, "
                            f"fetching {len(sitemaps)} sitemaps concurrently"
                        )
                        sub_sitemap_urls = [
                            sitemap_elem.text
                            for sitemap_elem in sitemaps
                            if sitemap_elem.text
                        ]

                        # Fetch all sub-sitemaps concurrently
                        tasks = [
                            self._fetch_sub_sitemap(client, sub_url)
                            for sub_url in sub_sitemap_urls
                        ]
                        results = await asyncio.gather(*tasks, return_exceptions=True)

                        for result in results:
                            if isinstance(result, list):
                                all_urls.extend(result)
                            elif isinstance(result, Exception):
                                logger.warning(
                                    f"Sub-sitemap fetch failed: {result}"
                                )

                        if all_urls:
                            break  # Success, don't try other locations
                    else:
                        # This is a regular sitemap with urls
                        urls = self._extract_urls(response.content)
                        all_urls.extend(urls)
                        logger.info(f"Fetched {len(urls)} URLs from {sitemap_url}")
                        break  # Success, don't try other locations

                except httpx.HTTPStatusError as e:
                    # Don't retry on permanent failures (404, 403, 401)
                    if e.response.status_code in (404, 403, 401):
                        logger.debug(f"Sitemap not found at {sitemap_url}: {e}")
                        continue
                    # Retry on transient failures (503, 429, 500, 502, 504)
                    if e.response.status_code in (503, 429, 500, 502, 504):
                        logger.warning(f"Transient error {e.response.status_code} at {sitemap_url}, will retry")
                        raise
                    # Other status codes: log and continue
                    logger.debug(f"HTTP error {e.response.status_code} at {sitemap_url}: {e}")
                    continue
                except httpx.TimeoutException as e:
                    # Retry on timeout - handled by @retry decorator
                    logger.warning(f"Timeout fetching {sitemap_url}, will retry")
                    raise
                except ET.ParseError as e:
                    logger.warning(f"Failed to parse {sitemap_url}: {e}")
                    continue
                except Exception as e:
                    logger.debug(f"Failed to fetch {sitemap_url}: {e}")
                    continue

        # Deduplicate and return
        return list(set(all_urls))

    async def _fetch_sub_sitemap(
        self, client: httpx.AsyncClient, sub_sitemap_url: str
    ) -> List[str]:
        """
        Fetch URLs from a single sub-sitemap.

        Args:
            client: httpx AsyncClient instance
            sub_sitemap_url: URL of the sub-sitemap

        Returns:
            List of URLs from the sub-sitemap
        """
        try:
            # Rate limiting: delay between sub-sitemap fetches
            await asyncio.sleep(0.2)

            response = await client.get(sub_sitemap_url)
            response.raise_for_status()
            urls = self._extract_urls(response.content)
            logger.debug(f"Fetched {len(urls)} URLs from {sub_sitemap_url}")
            return urls
        except Exception as e:
            logger.warning(f"Failed to fetch {sub_sitemap_url}: {e}")
            return []

    @staticmethod
    def _extract_urls(content: bytes) -> List[str]:
        """
        Extract URLs from sitemap XML content.

        Args:
            content: XML content

        Returns:
            List of URLs
        """
        urls = []
        try:
            root = ET.fromstring(content)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            for url_elem in root.findall(".//sm:url/sm:loc", ns):
                if url_elem.text:
                    urls.append(url_elem.text)
        except ET.ParseError as e:
            logger.warning(f"Failed to parse XML: {e}")

        return urls

    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL before processing.

        Checks:
        - Scheme is http or https
        - Netloc is present and contains a dot
        - No dangerous protocols (javascript:, file:, data:, vbscript:, etc.)

        Args:
            url: URL to validate

        Returns:
            True if URL is valid, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
        
        try:
            # Check for dangerous protocols
            url_lower = url.lower().strip()
            if any(url_lower.startswith(proto) for proto in self.DANGEROUS_PROTOCOLS):
                return False
            
            parsed = urlparse(url)
            return (
                parsed.scheme in ['http', 'https'] and
                parsed.netloc and
                '.' in parsed.netloc
            )
        except Exception:
            return False

    def _classify_page(self, url: str) -> SitemapPage:
        """
        Classify a page based on URL patterns.

        Uses pattern matching to detect page type with confidence score.

        Args:
            url: URL to classify

        Returns:
            SitemapPage with detected label and confidence
        """
        path = urlparse(url).path.lower()

        # Initialize scores for all labels from patterns
        scores: Dict[PageLabel, float] = {
            label: 0.0 for label in self.patterns.keys()
        }  # type: ignore
        scores["other"] = 0.1  # Default base score

        for label, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, path):
                    scores[label] += 0.4  # Increase score for each match
                    logger.debug(f"Pattern '{pattern}' matched for {url}")

        # Determine label and confidence
        best_label: PageLabel = max(scores, key=scores.get)  # type: ignore
        best_score = scores[best_label]

        # Confidence: normalize to 0-1 range
        # Higher score = higher confidence, max ~1.0 with multiple matches
        confidence = min(best_score, 1.0)

        # Extract title from URL slug (last path component)
        title = self._extract_title_from_url(url)

        page = SitemapPage(
            url=url,
            label=best_label,
            title=title,
            path=path,
            confidence=confidence,
        )

        logger.debug(f"Classified: {page}")
        return page

    @staticmethod
    def _extract_title_from_url(url: str) -> str:
        """
        Extract a human-readable title from URL.

        Examples:
        - "/blog/invoice-automation-software" → "Invoice Automation Software"
        - "/products/pricing" → "Pricing"
        - "/" → "Untitled"

        Args:
            url: URL to extract title from

        Returns:
            Human-readable title
        """
        path = urlparse(url).path
        parts = path.rstrip("/").split("/")

        # Get the last non-empty part
        slug = None
        for part in reversed(parts):
            if part:
                slug = part
                break

        if not slug:
            return "Untitled"

        # Replace hyphens with spaces and capitalize
        title = slug.replace("-", " ").replace("_", " ")
        title = " ".join(word.capitalize() for word in title.split())

        return title or "Untitled"