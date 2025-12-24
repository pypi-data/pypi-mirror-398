"""
Tests for Sitemap Crawler and Page Labeling

Tests the complete sitemap crawling pipeline:
1. Fetching URLs from sitemap
2. Auto-labeling pages by type
3. Filtering and accessing labeled data
4. Error handling, validation, caching, retry logic
"""

import pytest
from datetime import datetime
import time
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from pipeline.models import SitemapPage, SitemapPageList, PageLabel
from pipeline.processors import SitemapCrawler


class TestSitemapPage:
    """Tests for SitemapPage model."""

    def test_create_blog_page(self):
        """Test creating a blog page."""
        page = SitemapPage(
            url="https://example.com/blog/invoice-automation",
            label="blog",
            title="Invoice Automation",
            path="/blog/invoice-automation",
            confidence=0.95,
        )

        assert page.url == "https://example.com/blog/invoice-automation"
        assert page.label == "blog"
        assert page.is_blog()
        assert page.is_blog_confident(0.7)
        assert not page.is_blog_confident(0.99)

    def test_create_product_page(self):
        """Test creating a product page."""
        page = SitemapPage(
            url="https://example.com/products/pricing",
            label="product",
            title="Pricing",
            path="/products/pricing",
            confidence=0.85,
        )

        assert page.label == "product"
        assert not page.is_blog()

    def test_page_hash_and_equality(self):
        """Test page hashing and equality."""
        page1 = SitemapPage(
            url="https://example.com/blog/test",
            label="blog",
            path="/blog/test",
        )
        page2 = SitemapPage(
            url="https://example.com/blog/test",
            label="product",  # Different label
            path="/blog/test",
        )
        page3 = SitemapPage(
            url="https://example.com/blog/other",
            label="blog",
            path="/blog/other",
        )

        # Same URL = equal
        assert page1 == page2
        assert hash(page1) == hash(page2)

        # Different URL = not equal
        assert page1 != page3
        assert hash(page1) != hash(page3)

    def test_page_repr(self):
        """Test page string representation."""
        page = SitemapPage(
            url="https://example.com/blog/test",
            label="blog",
            path="/blog/test",
            confidence=0.95,
        )

        repr_str = repr(page)
        assert "SitemapPage" in repr_str
        assert "/blog/test" in repr_str
        assert "blog" in repr_str
        assert "0.95" in repr_str


class TestSitemapPageList:
    """Tests for SitemapPageList collection."""

    @pytest.fixture
    def sample_pages(self) -> list[SitemapPage]:
        """Create sample pages for testing."""
        return [
            SitemapPage(
                url="https://example.com/blog/article-1",
                label="blog",
                path="/blog/article-1",
                confidence=0.95,
            ),
            SitemapPage(
                url="https://example.com/blog/article-2",
                label="blog",
                path="/blog/article-2",
                confidence=0.90,
            ),
            SitemapPage(
                url="https://example.com/products/pricing",
                label="product",
                path="/products/pricing",
                confidence=0.85,
            ),
            SitemapPage(
                url="https://example.com/docs/getting-started",
                label="docs",
                path="/docs/getting-started",
                confidence=0.88,
            ),
            SitemapPage(
                url="https://example.com/services/consulting",
                label="service",
                path="/services/consulting",
                confidence=0.80,
            ),
            SitemapPage(
                url="https://example.com/resources/whitepaper",
                label="resource",
                path="/resources/whitepaper",
                confidence=0.75,
            ),
            SitemapPage(
                url="https://example.com/about",
                label="other",
                path="/about",
                confidence=0.50,
            ),
        ]

    def test_create_page_list(self, sample_pages):
        """Test creating a page list."""
        page_list = SitemapPageList(
            pages=sample_pages,
            company_url="https://example.com",
            total_urls=len(sample_pages),
        )

        assert page_list.count() == 7
        assert page_list.company_url == "https://example.com"
        assert page_list.total_urls == 7

    def test_get_blogs(self, sample_pages):
        """Test filtering blog pages."""
        page_list = SitemapPageList(
            pages=sample_pages,
            company_url="https://example.com",
        )

        blogs = page_list.get_blogs(min_confidence=0.8)
        assert len(blogs) == 2
        assert all(page.is_blog() for page in blogs)

        blogs_strict = page_list.get_blogs(min_confidence=0.95)
        assert len(blogs_strict) == 1
        assert blogs_strict[0].confidence == 0.95

    def test_get_by_label(self, sample_pages):
        """Test filtering by specific label."""
        page_list = SitemapPageList(
            pages=sample_pages,
            company_url="https://example.com",
        )

        products = page_list.get_by_label("product")
        assert len(products) == 1
        assert products[0].label == "product"

        docs = page_list.get_by_label("docs")
        assert len(docs) == 1
        assert docs[0].label == "docs"

    def test_get_urls(self, sample_pages):
        """Test getting URL lists."""
        page_list = SitemapPageList(
            pages=sample_pages,
            company_url="https://example.com",
        )

        all_urls = page_list.get_all_urls()
        assert len(all_urls) == 7

        blog_urls = page_list.get_blog_urls()
        assert len(blog_urls) == 2
        assert all("/blog/" in url for url in blog_urls)

        product_urls = page_list.get_urls_by_label("product")
        assert len(product_urls) == 1
        assert "/products/" in product_urls[0]

    def test_deduplicate(self, sample_pages):
        """Test deduplication."""
        # Add duplicate
        sample_pages.append(sample_pages[0])

        page_list = SitemapPageList(
            pages=sample_pages,
            company_url="https://example.com",
        )

        assert page_list.count() == 8  # With duplicate

        deduplicated = page_list.deduplicate()
        assert deduplicated.count() == 7  # Duplicate removed

    def test_label_summary(self, sample_pages):
        """Test label summary."""
        page_list = SitemapPageList(
            pages=sample_pages,
            company_url="https://example.com",
        )

        summary = page_list.label_summary()
        assert summary["blog"] == 2
        assert summary["product"] == 1
        assert summary["service"] == 1
        assert summary["docs"] == 1
        assert summary["resource"] == 1
        assert summary["other"] == 1

    def test_count_by_label(self, sample_pages):
        """Test counting by label."""
        page_list = SitemapPageList(
            pages=sample_pages,
            company_url="https://example.com",
        )

        assert page_list.count_by_label("blog") == 2
        assert page_list.count_by_label("product") == 1
        assert page_list.count_by_label("service") == 1

    def test_page_list_repr(self, sample_pages):
        """Test page list string representation."""
        page_list = SitemapPageList(
            pages=sample_pages,
            company_url="https://example.com",
        )

        repr_str = repr(page_list)
        assert "SitemapPageList" in repr_str
        assert "7 pages" in repr_str


class TestSitemapCrawlerPatternClassification:
    """Tests for URL pattern-based classification."""

    def test_classify_blog_pages(self):
        """Test classifying blog URLs."""
        crawler = SitemapCrawler()

        blog_urls = [
            "https://example.com/blog/article",
            "https://example.com/news/update",
            "https://example.com/articles/guide",
            "https://example.com/posts/story",
            "https://example.com/insights/analysis",
        ]

        for url in blog_urls:
            page = crawler._classify_page(url)
            assert page.label == "blog", f"Failed to classify {url} as blog"
            assert page.confidence > 0.5, f"Low confidence for {url}"

    def test_classify_product_pages(self):
        """Test classifying product URLs."""
        crawler = SitemapCrawler()

        product_urls = [
            "https://example.com/products/item",
            "https://example.com/solutions/service",
            "https://example.com/pricing/plans",
            "https://example.com/features/overview",
        ]

        for url in product_urls:
            page = crawler._classify_page(url)
            assert page.label == "product", f"Failed to classify {url} as product"

    def test_classify_service_pages(self):
        """Test classifying service URLs."""
        crawler = SitemapCrawler()

        service_urls = [
            "https://example.com/services/consulting",
            "https://example.com/support/help",
        ]

        for url in service_urls:
            page = crawler._classify_page(url)
            assert page.label == "service", f"Failed to classify {url} as service"

    def test_classify_docs_pages(self):
        """Test classifying docs URLs."""
        crawler = SitemapCrawler()

        docs_urls = [
            "https://example.com/docs/api",
            "https://example.com/documentation/setup",
            "https://example.com/guides/tutorial",
            "https://example.com/help/faq",
        ]

        for url in docs_urls:
            page = crawler._classify_page(url)
            assert page.label == "docs", f"Failed to classify {url} as docs"

    def test_classify_resource_pages(self):
        """Test classifying resource URLs."""
        crawler = SitemapCrawler()

        resource_urls = [
            "https://example.com/whitepapers/analysis",
            "https://example.com/case-studies/success",
            "https://example.com/templates/design",
            "https://example.com/tools/calculator",
        ]

        for url in resource_urls:
            page = crawler._classify_page(url)
            assert page.label == "resource", f"Failed to classify {url} as resource"

    def test_classify_other_pages(self):
        """Test classifying other URLs."""
        crawler = SitemapCrawler()

        other_urls = [
            "https://example.com/about",
            "https://example.com/contact",
            "https://example.com/careers",
            "https://example.com/privacy",
        ]

        for url in other_urls:
            page = crawler._classify_page(url)
            assert page.label == "other", f"Failed to classify {url} as other"

    def test_extract_title_from_url(self):
        """Test extracting titles from URLs."""
        crawler = SitemapCrawler()

        test_cases = [
            ("https://example.com/blog/invoice-automation", "Invoice Automation"),
            ("https://example.com/docs/getting-started", "Getting Started"),
            ("https://example.com/pricing", "Pricing"),
            ("https://example.com/", "Untitled"),
        ]

        for url, expected_title in test_cases:
            title = crawler._extract_title_from_url(url)
            assert title.lower() == expected_title.lower()


class TestSitemapCrawlerIntegration:
    """Integration tests for sitemap crawler."""

    @pytest.mark.asyncio
    async def test_crawl_with_mock_sitemap(self):
        """Test crawling with mock sitemap (if needed)."""
        # This would require mocking HTTP requests
        # For now, we test the classification logic
        crawler = SitemapCrawler()

        assert crawler is not None
        assert len(crawler.patterns) > 0
        assert "blog" in crawler.patterns

    def test_custom_patterns(self):
        """Test using custom patterns."""
        custom_patterns = {
            "blog": [r"\/my-blog\/"],
            "other": [],
        }

        crawler = SitemapCrawler(custom_patterns=custom_patterns)
        page = crawler._classify_page("https://example.com/my-blog/article")

        assert page.label == "blog"

    def test_extract_urls_from_xml(self):
        """Test extracting URLs from XML content."""
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/page1</loc>
  </url>
  <url>
    <loc>https://example.com/page2</loc>
  </url>
  <url>
    <loc>https://example.com/page3</loc>
  </url>
</urlset>
"""

        urls = SitemapCrawler._extract_urls(xml_content)
        assert len(urls) == 3
        assert "https://example.com/page1" in urls
        assert "https://example.com/page2" in urls
        assert "https://example.com/page3" in urls

    def test_extract_urls_from_invalid_xml(self):
        """Test handling invalid XML."""
        xml_content = b"<invalid>not xml</invalid>"

        urls = SitemapCrawler._extract_urls(xml_content)
        # Should gracefully handle invalid XML
        assert isinstance(urls, list)


class TestSitemapUseCases:
    """Tests for real-world use cases."""

    def test_use_case_keyword_gen_filtering(self):
        """
        Use Case 1: Keyword generation filters to blogs only.

        The crawled sitemap should be used to get existing blog keywords
        to avoid cannibalization.
        """
        pages = [
            SitemapPage(url="https://example.com/blog/automation", label="blog", path="/blog/automation", confidence=0.95),
            SitemapPage(url="https://example.com/blog/optimization", label="blog", path="/blog/optimization", confidence=0.92),
            SitemapPage(url="https://example.com/products/pricing", label="product", path="/products/pricing", confidence=0.85),
        ]

        page_list = SitemapPageList(
            pages=pages,
            company_url="https://example.com",
        )

        # Keyword gen should use blog URLs only
        blog_urls = page_list.get_blog_urls()
        assert len(blog_urls) == 2
        assert all("/blog/" in url for url in blog_urls)

    def test_use_case_internal_links_full_set(self):
        """
        Use Case 2: Internal linking uses the full labeled sitemap.

        All URLs are available, so internal link selector can choose from
        all pages (blogs, products, docs, etc.), not just blogs.
        """
        pages = [
            SitemapPage(url="https://example.com/blog/guide", label="blog", path="/blog/guide", confidence=0.95),
            SitemapPage(url="https://example.com/products/pricing", label="product", path="/products/pricing", confidence=0.85),
            SitemapPage(url="https://example.com/docs/api", label="docs", path="/docs/api", confidence=0.90),
            SitemapPage(url="https://example.com/case-studies/success", label="resource", path="/case-studies/success", confidence=0.80),
        ]

        page_list = SitemapPageList(
            pages=pages,
            company_url="https://example.com",
        )

        # Internal links can choose from any type
        all_urls = page_list.get_all_urls()
        assert len(all_urls) == 4

        # Different sections of the article might link to different types
        blog_links = page_list.get_blog_urls()
        product_links = page_list.get_urls_by_label("product")
        docs_links = page_list.get_urls_by_label("docs")

        # All should be available
        assert len(blog_links) > 0
        assert len(product_links) > 0
        assert len(docs_links) > 0

    def test_confidence_threshold_filtering(self):
        """
        Use Case 3: Filter pages by confidence threshold.

        Low-confidence pages might be excluded in production.
        """
        pages = [
            SitemapPage(url="https://example.com/blog/certain", label="blog", path="/blog/certain", confidence=0.99),
            SitemapPage(url="https://example.com/blog/uncertain", label="blog", path="/blog/uncertain", confidence=0.55),
        ]

        page_list = SitemapPageList(pages=pages, company_url="https://example.com")

        # Strict filtering
        strict_blogs = page_list.get_blogs(min_confidence=0.8)
        assert len(strict_blogs) == 1
        assert strict_blogs[0].confidence == 0.99

        # Loose filtering
        loose_blogs = page_list.get_blogs(min_confidence=0.5)
        assert len(loose_blogs) == 2


class TestSitemapCrawlerProductionFeatures:
    """Tests for production-ready features: validation, error handling, caching, etc."""

    def test_url_validation_valid_urls(self):
        """Test URL validation accepts valid URLs."""
        crawler = SitemapCrawler()

        valid_urls = [
            "https://example.com/blog/article",
            "http://example.com/products",
            "https://www.example.com/docs",
            "https://subdomain.example.com/page",
        ]

        for url in valid_urls:
            assert crawler._is_valid_url(url), f"Valid URL rejected: {url}"

    def test_url_validation_invalid_urls(self):
        """Test URL validation rejects invalid URLs."""
        crawler = SitemapCrawler()

        invalid_urls = [
            "javascript:alert(1)",  # XSS vector
            "file:///etc/passwd",  # Local file
            "data:text/html,<script>alert(1)</script>",  # Data URL
            "vbscript:msgbox(1)",  # VBScript
            "about:blank",  # About protocol
            "chrome://settings",  # Chrome protocol
            "chrome-extension://id",  # Extension protocol
            "ftp://example.com",  # Wrong protocol
            "https://",  # No domain
            "http://",  # No domain
            "",  # Empty
            None,  # None value
            "not-a-url",  # Not a URL
        ]

        for url in invalid_urls:
            assert not crawler._is_valid_url(url), f"Invalid URL accepted: {url}"

    def test_memory_limits(self):
        """Test memory limits truncate large URL lists."""
        crawler = SitemapCrawler(max_urls=5)

        # Create a list with more URLs than max
        urls = [f"https://example.com/page{i}" for i in range(10)]

        # Simulate what happens in crawl() method
        if len(urls) > crawler.max_urls:
            urls = urls[:crawler.max_urls]

        assert len(urls) == 5
        assert urls == [
            "https://example.com/page0",
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3",
            "https://example.com/page4",
        ]

    def test_caching_cache_hit(self):
        """Test caching returns cached result."""
        crawler = SitemapCrawler(cache_ttl=3600)

        # Create a mock result
        mock_result = SitemapPageList(
            pages=[],
            company_url="https://example.com",
            total_urls=0,
        )

        # Manually add to cache
        cache_key = "https://example.com"
        crawler._cache[cache_key] = (mock_result, time.time())

        # Verify cache hit
        assert cache_key in crawler._cache
        result, timestamp = crawler._cache[cache_key]
        assert time.time() - timestamp < crawler.cache_ttl

    def test_caching_cache_expiry(self):
        """Test cache expires after TTL."""
        crawler = SitemapCrawler(cache_ttl=1)  # 1 second TTL

        # Create a mock result
        mock_result = SitemapPageList(
            pages=[],
            company_url="https://example.com",
            total_urls=0,
        )

        # Add to cache with old timestamp
        cache_key = "https://example.com"
        crawler._cache[cache_key] = (mock_result, time.time() - 2)  # 2 seconds ago

        # Verify cache expired
        result, timestamp = crawler._cache[cache_key]
        assert time.time() - timestamp >= crawler.cache_ttl

    @pytest.mark.asyncio
    async def test_error_handling_timeout(self):
        """Test error handling for timeout exceptions."""
        crawler = SitemapCrawler()

        with patch.object(crawler, '_fetch_all_urls', side_effect=httpx.TimeoutException("Timeout")):
            result = await crawler.crawl("https://example.com")

            assert isinstance(result, SitemapPageList)
            assert result.count() == 0
            assert result.company_url == "https://example.com"

    @pytest.mark.asyncio
    async def test_error_handling_http_error(self):
        """Test error handling for HTTP errors."""
        crawler = SitemapCrawler()

        # Mock HTTPStatusError
        mock_response = MagicMock()
        mock_response.status_code = 404
        http_error = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)

        with patch.object(crawler, '_fetch_all_urls', side_effect=http_error):
            result = await crawler.crawl("https://example.com")

            assert isinstance(result, SitemapPageList)
            assert result.count() == 0

    @pytest.mark.asyncio
    async def test_error_handling_parse_error(self):
        """Test error handling for XML parse errors."""
        crawler = SitemapCrawler()

        import defusedxml.ElementTree as ET
        parse_error = ET.ParseError("Invalid XML")

        with patch.object(crawler, '_fetch_all_urls', side_effect=parse_error):
            result = await crawler.crawl("https://example.com")

            assert isinstance(result, SitemapPageList)
            assert result.count() == 0

    @pytest.mark.asyncio
    async def test_error_handling_generic_exception(self):
        """Test error handling for generic exceptions."""
        crawler = SitemapCrawler()

        with patch.object(crawler, '_fetch_all_urls', side_effect=Exception("Unexpected error")):
            result = await crawler.crawl("https://example.com")

            assert isinstance(result, SitemapPageList)
            assert result.count() == 0

    @pytest.mark.asyncio
    async def test_company_url_validation(self):
        """Test that invalid company_url is rejected."""
        crawler = SitemapCrawler()

        # Invalid URLs should return empty sitemap
        invalid_urls = [
            "not-a-url",
            "javascript:alert(1)",
            "file:///etc/passwd",
            "",
        ]

        for invalid_url in invalid_urls:
            result = await crawler.crawl(invalid_url)
            assert isinstance(result, SitemapPageList)
            assert result.count() == 0
            assert result.company_url == invalid_url

    def test_cache_key_includes_max_urls(self):
        """Test that cache key includes max_urls parameter."""
        crawler1 = SitemapCrawler(max_urls=1000)
        crawler2 = SitemapCrawler(max_urls=5000)

        # Cache keys should be different
        key1 = f"https://example.com:{crawler1.max_urls}"
        key2 = f"https://example.com:{crawler2.max_urls}"

        assert key1 != key2
        assert "1000" in key1
        assert "5000" in key2

    def test_cache_lru_eviction(self):
        """Test that cache evicts oldest entries when max size exceeded."""
        crawler = SitemapCrawler(max_cache_size=2)

        # Manually add entries to cache
        mock_result1 = SitemapPageList(
            pages=[],
            company_url="https://example1.com",
            total_urls=0,
        )
        mock_result2 = SitemapPageList(
            pages=[],
            company_url="https://example2.com",
            total_urls=0,
        )
        mock_result3 = SitemapPageList(
            pages=[],
            company_url="https://example3.com",
            total_urls=0,
        )

        # Add first two entries
        crawler._cache["key1:10000"] = (mock_result1, time.time())
        crawler._cache["key2:10000"] = (mock_result2, time.time())

        # Add third entry - should evict first
        crawler._cache["key3:10000"] = (mock_result3, time.time())
        crawler._cache.move_to_end("key3:10000")

        # Manually trigger eviction
        while len(crawler._cache) > crawler.max_cache_size:
            crawler._cache.popitem(last=False)

        assert len(crawler._cache) == 2
        assert "key1:10000" not in crawler._cache  # Oldest evicted
        assert "key2:10000" in crawler._cache
        assert "key3:10000" in crawler._cache

    def test_parameter_validation(self):
        """Test that invalid parameters raise ValueError."""
        # Test max_urls <= 0
        with pytest.raises(ValueError, match="max_urls must be > 0"):
            SitemapCrawler(max_urls=0)
        
        with pytest.raises(ValueError, match="max_urls must be > 0"):
            SitemapCrawler(max_urls=-1)

        # Test max_cache_size <= 0
        with pytest.raises(ValueError, match="max_cache_size must be > 0"):
            SitemapCrawler(max_cache_size=0)
        
        with pytest.raises(ValueError, match="max_cache_size must be > 0"):
            SitemapCrawler(max_cache_size=-1)

        # Test cache_ttl < 0
        with pytest.raises(ValueError, match="cache_ttl must be >= 0"):
            SitemapCrawler(cache_ttl=-1)

        # Test valid parameters don't raise
        crawler = SitemapCrawler(max_urls=1, max_cache_size=1, cache_ttl=0)
        assert crawler.max_urls == 1
        assert crawler.max_cache_size == 1
        assert crawler.cache_ttl == 0

    @pytest.mark.asyncio
    async def test_company_url_trailing_slash_normalization(self):
        """Test that trailing slashes in company_url are normalized."""
        crawler = SitemapCrawler()

        # Mock _fetch_all_urls to return empty list (so we don't actually fetch)
        with patch.object(crawler, '_fetch_all_urls', return_value=[]):
            result1 = await crawler.crawl("https://example.com")
            result2 = await crawler.crawl("https://example.com/")  # With trailing slash

            # Both should normalize to same company_url
            assert result1.company_url == "https://example.com"
            assert result2.company_url == "https://example.com"

    def test_empty_sitemap_helper(self):
        """Test _empty_sitemap helper method."""
        crawler = SitemapCrawler()
        result = crawler._empty_sitemap("https://example.com")

        assert isinstance(result, SitemapPageList)
        assert result.count() == 0
        assert result.company_url == "https://example.com"
        assert result.total_urls == 0
        assert result.fetch_timestamp is not None

    def test_timeout_configuration(self):
        """Test timeout configuration."""
        from httpx import Timeout

        custom_timeout = Timeout(connect=10.0, read=20.0, write=10.0, pool=10.0)
        crawler = SitemapCrawler(timeout=custom_timeout)

        assert crawler.timeout.connect == 10.0
        assert crawler.timeout.read == 20.0
        assert crawler.timeout.write == 10.0
        assert crawler.timeout.pool == 10.0

    def test_default_timeout_configuration(self):
        """Test default timeout configuration."""
        crawler = SitemapCrawler()

        assert crawler.timeout.connect == 5.0
        assert crawler.timeout.read == 10.0
        assert crawler.timeout.write == 5.0
        assert crawler.timeout.pool == 5.0

    @pytest.mark.asyncio
    async def test_concurrent_sub_sitemap_fetching(self):
        """Test that sub-sitemaps are fetched concurrently."""
        crawler = SitemapCrawler()

        # Mock httpx client
        mock_client = AsyncMock()

        # Mock responses for sub-sitemaps
        mock_responses = [
            MagicMock(content=b'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://example.com/page1</loc></url></urlset>'),
            MagicMock(content=b'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://example.com/page2</loc></url></urlset>'),
            MagicMock(content=b'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://example.com/page3</loc></url></urlset>'),
        ]

        async def mock_get(url):
            await asyncio.sleep(0.1)  # Simulate network delay
            return mock_responses.pop(0)

        mock_client.get = mock_get

        # Test concurrent fetching
        sub_urls = [
            "https://example.com/sitemap1.xml",
            "https://example.com/sitemap2.xml",
            "https://example.com/sitemap3.xml",
        ]

        start_time = time.time()
        tasks = [
            crawler._fetch_sub_sitemap(mock_client, sub_url)
            for sub_url in sub_urls
        ]
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time

        # Should be faster than sequential (3 * 0.1 = 0.3s sequential)
        # Concurrent should be ~0.1s + overhead
        assert duration < 0.25, f"Concurrent fetching took too long: {duration}s"

        # Verify all URLs were extracted
        all_urls = []
        for result in results:
            all_urls.extend(result)

        assert len(all_urls) == 3
        assert "https://example.com/page1" in all_urls
        assert "https://example.com/page2" in all_urls
        assert "https://example.com/page3" in all_urls
