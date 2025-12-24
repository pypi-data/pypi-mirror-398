"""
HTML Utilities - Pure utility functions for HTML processing.

This module contains stateless, pure functions for:
- HTML escaping and sanitization
- URL manipulation
- Text transformations (slugify, etc.)

Following Single Responsibility Principle - only utility functions, no business logic.
"""

import re
import html
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def escape_html(text: str) -> str:
    """
    Escape HTML special characters in text.
    
    Args:
        text: Raw text that may contain HTML special characters
        
    Returns:
        Text with <, >, &, " escaped for safe HTML rendering
    """
    if not text:
        return ""
    return html.escape(str(text))


def escape_attr(text: str) -> str:
    """
    Escape text for use in HTML attributes.
    
    More aggressive than escape_html - also escapes quotes and newlines.
    
    Args:
        text: Text to be used in an HTML attribute
        
    Returns:
        Attribute-safe escaped text
    """
    if not text:
        return ""
    escaped = html.escape(str(text), quote=True)
    # Also escape newlines which can break attributes
    return escaped.replace('\n', ' ').replace('\r', '')


def strip_html(text: str) -> str:
    """
    Remove all HTML tags from text, leaving only plain text content.
    
    Args:
        text: HTML string
        
    Returns:
        Plain text with all HTML tags removed
    """
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', str(text))
    # Also clean up HTML entities
    clean = html.unescape(clean)
    # Normalize whitespace
    clean = ' '.join(clean.split())
    return clean.strip()


def slugify(text: str) -> str:
    """
    Convert text to URL-safe slug.
    
    Args:
        text: Any text string
        
    Returns:
        Lowercase, hyphenated slug suitable for URLs and HTML IDs
        
    Example:
        slugify("Hello World! How Are You?") → "hello-world-how-are-you"
    """
    if not text:
        return ""
    # Convert to lowercase
    slug = text.lower()
    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    # Remove non-alphanumeric characters (except hyphens)
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    # Remove consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Strip leading/trailing hyphens
    return slug.strip('-')


def make_absolute_url(url: str, base_url: str) -> str:
    """
    Convert relative URL to absolute URL.
    
    Args:
        url: Potentially relative URL
        base_url: Base URL (e.g., company website)
        
    Returns:
        Absolute URL
    """
    if not url:
        return ""
    if not base_url:
        return url
        
    # Already absolute
    if url.startswith(('http://', 'https://', '//')):
        return url
    
    # Local file path (for development)
    if url.startswith('output/'):
        return url
        
    # Make absolute
    base = base_url.rstrip('/')
    path = url.lstrip('/')
    return f"{base}/{path}"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length, adding suffix if truncated.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: String to append if truncated (default "...")
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text or ""
    
    # Account for suffix length
    truncate_at = max_length - len(suffix)
    if truncate_at <= 0:
        return suffix[:max_length]
    
    # Try to break at word boundary
    truncated = text[:truncate_at]
    last_space = truncated.rfind(' ')
    if last_space > truncate_at * 0.7:  # Only break at word if reasonable
        truncated = truncated[:last_space]
    
    return truncated.rstrip() + suffix


def normalize_whitespace(text: str) -> str:
    """
    Normalize all whitespace in text to single spaces.
    
    Args:
        text: Text with potentially irregular whitespace
        
    Returns:
        Text with normalized whitespace
    """
    if not text:
        return ""
    # Replace all whitespace sequences with single space
    return ' '.join(text.split())


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    Args:
        url: Full URL
        
    Returns:
        Domain name or None if invalid
        
    Example:
        extract_domain("https://www.example.com/path") → "example.com"
    """
    if not url:
        return None
    
    try:
        # Remove protocol
        domain = re.sub(r'^https?://', '', url)
        # Remove www.
        domain = re.sub(r'^www\.', '', domain)
        # Get just the domain part
        domain = domain.split('/')[0]
        # Remove port if present
        domain = domain.split(':')[0]
        return domain if domain else None
    except Exception:
        return None


def is_valid_url(url: str) -> bool:
    """
    Check if string is a valid URL.
    
    Args:
        url: String to check
        
    Returns:
        True if valid URL format
    """
    if not url:
        return False
    
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize string for use as filename.
    
    Args:
        filename: Proposed filename
        
    Returns:
        Safe filename with invalid characters removed
    """
    if not filename:
        return "unnamed"
    
    # Remove/replace invalid characters
    safe = re.sub(r'[<>:"/\\|?*]', '', filename)
    safe = re.sub(r'\s+', '_', safe)
    safe = safe.strip('._')
    
    return safe if safe else "unnamed"

