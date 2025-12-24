"""
SEO Metadata - Generate meta tags, Open Graph, and Twitter cards.

This module handles all SEO-related HTML generation:
- Meta description and title tags
- Open Graph (Facebook) tags
- Twitter Card tags
- Canonical URLs

Following Single Responsibility Principle - only SEO metadata, no content rendering.
"""

import logging
from typing import Optional, List
from datetime import datetime

from .html_utils import escape_attr, escape_html

logger = logging.getLogger(__name__)


def generate_meta_tags(
    title: str,
    description: str,
    keywords: Optional[List[str]] = None,
    author: Optional[str] = None,
    canonical_url: Optional[str] = None,
    robots: str = "index, follow"
) -> str:
    """
    Generate standard HTML meta tags.
    
    Args:
        title: Page title
        description: Meta description (ideally 150-160 chars)
        keywords: Optional list of keywords
        author: Optional author name
        canonical_url: Optional canonical URL
        robots: Robots directive (default: index, follow)
        
    Returns:
        HTML string with meta tags
    """
    tags = [
        f'<meta name="description" content="{escape_attr(description)}">',
        f'<meta name="robots" content="{escape_attr(robots)}">',
    ]
    
    if keywords:
        keywords_str = ", ".join(keywords[:10])  # Limit to 10 keywords
        tags.append(f'<meta name="keywords" content="{escape_attr(keywords_str)}">')
    
    if author:
        tags.append(f'<meta name="author" content="{escape_attr(author)}">')
    
    if canonical_url:
        tags.append(f'<link rel="canonical" href="{escape_attr(canonical_url)}">')
    
    return '\n    '.join(tags)


def generate_og_tags(
    title: str,
    description: str,
    url: Optional[str] = None,
    image: Optional[str] = None,
    site_name: Optional[str] = None,
    og_type: str = "article",
    publication_date: Optional[str] = None,
    author: Optional[str] = None
) -> str:
    """
    Generate Open Graph meta tags for social sharing.
    
    Args:
        title: OG title
        description: OG description
        url: Page URL
        image: Featured image URL
        site_name: Website name
        og_type: Content type (default: article)
        publication_date: ISO date string
        author: Author name
        
    Returns:
        HTML string with Open Graph tags
    """
    tags = [
        f'<meta property="og:title" content="{escape_attr(title)}">',
        f'<meta property="og:description" content="{escape_attr(description)}">',
        f'<meta property="og:type" content="{escape_attr(og_type)}">',
    ]
    
    if url:
        tags.append(f'<meta property="og:url" content="{escape_attr(url)}">')
    
    if image:
        tags.append(f'<meta property="og:image" content="{escape_attr(image)}">')
        # Add image dimensions if available (improves preview quality)
        tags.append('<meta property="og:image:width" content="1200">')
        tags.append('<meta property="og:image:height" content="630">')
    
    if site_name:
        tags.append(f'<meta property="og:site_name" content="{escape_attr(site_name)}">')
    
    # Article-specific tags
    if og_type == "article":
        if publication_date:
            tags.append(f'<meta property="article:published_time" content="{escape_attr(publication_date)}">')
        if author:
            tags.append(f'<meta property="article:author" content="{escape_attr(author)}">')
    
    return '\n    '.join(tags)


def generate_twitter_tags(
    title: str,
    description: str,
    image: Optional[str] = None,
    site_handle: Optional[str] = None,
    creator_handle: Optional[str] = None,
    card_type: str = "summary_large_image"
) -> str:
    """
    Generate Twitter Card meta tags.
    
    Args:
        title: Card title
        description: Card description
        image: Card image URL
        site_handle: Site's Twitter handle (e.g., @company)
        creator_handle: Author's Twitter handle
        card_type: Card type (summary, summary_large_image, etc.)
        
    Returns:
        HTML string with Twitter Card tags
    """
    tags = [
        f'<meta name="twitter:card" content="{escape_attr(card_type)}">',
        f'<meta name="twitter:title" content="{escape_attr(title)}">',
        f'<meta name="twitter:description" content="{escape_attr(description)}">',
    ]
    
    if image:
        tags.append(f'<meta name="twitter:image" content="{escape_attr(image)}">')
    
    if site_handle:
        # Ensure @ prefix
        handle = site_handle if site_handle.startswith('@') else f'@{site_handle}'
        tags.append(f'<meta name="twitter:site" content="{escape_attr(handle)}">')
    
    if creator_handle:
        handle = creator_handle if creator_handle.startswith('@') else f'@{creator_handle}'
        tags.append(f'<meta name="twitter:creator" content="{escape_attr(handle)}">')
    
    return '\n    '.join(tags)


def generate_all_social_tags(
    title: str,
    description: str,
    url: Optional[str] = None,
    image: Optional[str] = None,
    site_name: Optional[str] = None,
    author: Optional[str] = None,
    publication_date: Optional[str] = None,
    twitter_site: Optional[str] = None
) -> str:
    """
    Generate complete set of social sharing tags (OG + Twitter).
    
    Convenience function that generates both Open Graph and Twitter Card
    tags with consistent data.
    
    Args:
        title: Content title
        description: Content description
        url: Page URL
        image: Featured image URL
        site_name: Website name
        author: Author name
        publication_date: ISO date string
        twitter_site: Twitter handle for site
        
    Returns:
        HTML string with all social tags
    """
    parts = []
    
    # Open Graph
    og = generate_og_tags(
        title=title,
        description=description,
        url=url,
        image=image,
        site_name=site_name,
        publication_date=publication_date,
        author=author
    )
    parts.append(f'<!-- Open Graph -->\n    {og}')
    
    # Twitter Card
    twitter = generate_twitter_tags(
        title=title,
        description=description,
        image=image,
        site_handle=twitter_site
    )
    parts.append(f'<!-- Twitter Card -->\n    {twitter}')
    
    return '\n    '.join(parts)


def generate_article_metadata(
    title: str,
    description: str,
    url: str,
    image: Optional[str] = None,
    author: Optional[str] = None,
    publication_date: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    company_name: Optional[str] = None,
    read_time: Optional[int] = None
) -> str:
    """
    Generate complete metadata block for blog article.
    
    Combines standard meta, Open Graph, and Twitter tags
    optimized for blog/article content.
    
    Args:
        title: Article title
        description: Article description/excerpt
        url: Article URL
        image: Featured image URL
        author: Author name
        publication_date: ISO date string
        keywords: List of keywords
        company_name: Company/site name
        read_time: Reading time in minutes
        
    Returns:
        Complete HTML metadata block
    """
    parts = []
    
    # Standard meta tags
    meta = generate_meta_tags(
        title=title,
        description=description,
        keywords=keywords,
        author=author,
        canonical_url=url
    )
    parts.append(meta)
    
    # Social tags
    social = generate_all_social_tags(
        title=title,
        description=description,
        url=url,
        image=image,
        site_name=company_name,
        author=author,
        publication_date=publication_date
    )
    parts.append(social)
    
    # Reading time (custom meta)
    if read_time:
        parts.append(f'<meta name="twitter:label1" content="Reading time">')
        parts.append(f'<meta name="twitter:data1" content="{read_time} min read">')
    
    return '\n    '.join(parts)

