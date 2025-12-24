#!/usr/bin/env python3
"""
Test script for Sitemap Crawler functionality.

Tests the sitemap crawler against real websites to validate functionality.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from sitemap_crawler import SitemapCrawler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_sitemap_crawler():
    """Test sitemap crawler with various websites."""
    
    test_urls = [
        "https://example.com",           # Simple test
        "https://github.com",            # Large sitemap_index
        "https://stripe.com",            # Well-structured sitemap  
        "https://anthropic.com",         # AI company example
        "https://nonexistent-test-url-12345.com"  # Error handling test
    ]
    
    crawler = SitemapCrawler(max_urls=100, cache_ttl=300)  # Small limits for testing
    
    for url in test_urls:
        logger.info(f"\n🔍 Testing: {url}")
        try:
            result = await crawler.crawl(url)
            
            logger.info(f"✅ Results for {url}:")
            logger.info(f"   Total URLs: {result.count()}")
            logger.info(f"   Blog URLs: {len(result.get_blog_urls())}")
            logger.info(f"   Label Summary: {result.label_summary()}")
            
            if result.get_blog_urls():
                logger.info(f"   Sample blog URLs:")
                for blog_url in result.get_blog_urls()[:3]:
                    logger.info(f"     - {blog_url}")
                    
        except Exception as e:
            logger.error(f"❌ Error testing {url}: {e}")
        
        await asyncio.sleep(1)  # Be nice to servers
    
    logger.info(f"\n📊 Cache Stats:")
    logger.info(f"   Cache hits: {crawler._cache_hits}")
    logger.info(f"   Cache misses: {crawler._cache_misses}")
    logger.info(f"   Cache size: {len(crawler._cache)}")


async def test_specific_patterns():
    """Test specific URL pattern classification."""
    
    test_cases = [
        ("https://example.com/blog/ai-trends-2024", "blog"),
        ("https://example.com/products/pricing", "product"), 
        ("https://example.com/about-us", "company"),
        ("https://example.com/contact", "contact"),
        ("https://example.com/privacy-policy", "legal"),
        ("https://example.com/docs/api", "docs"),
        ("https://example.com/case-studies/success", "resource"),
        ("https://example.com/random/page", "other"),
    ]
    
    crawler = SitemapCrawler()
    
    logger.info(f"\n🎯 Testing URL Classification:")
    
    for url, expected_label in test_cases:
        page = crawler._classify_page(url)
        status = "✅" if page.label == expected_label else "❌"
        logger.info(f"   {status} {url}")
        logger.info(f"       Expected: {expected_label}, Got: {page.label} (confidence: {page.confidence:.2f})")


async def main():
    """Run all tests."""
    logger.info("🚀 Starting Sitemap Crawler Tests")
    
    await test_specific_patterns()
    await test_sitemap_crawler()
    
    logger.info("✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())