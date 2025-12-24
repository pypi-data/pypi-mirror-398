"""
Internal Link Model

Represents a single internal link/related reading suggestion.

Structure:
- URL: Link destination
- Title: Link text/anchor text
- Relevance: How relevant to article (1-10 score)
- Status: HTTP status (200 = valid, else invalid)
"""

from typing import Optional, List
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class InternalLink(BaseModel):
    """
    Single internal link/related reading.

    Attributes:
        url: Link destination URL
        title: Link text/title
        relevance: Relevance score (1-10, higher = more relevant)
        status: HTTP status code (200 = valid)
        domain: Domain of link (for deduplication)
    """

    url: str = Field(..., description="Internal link URL")
    title: str = Field(..., description="Link anchor text/title (5-10 words)")
    relevance: int = Field(
        default=5,
        description="Relevance score (1-10, higher = more relevant)",
        ge=1,
        le=10,
    )
    status: Optional[int] = Field(default=200, description="HTTP status (200 = valid)")
    domain: Optional[str] = Field(default="", description="Domain for deduplication")

    def is_valid(self) -> bool:
        """Check if link is valid (HTTP 200)."""
        return self.status == 200

    def to_html(self) -> str:
        """Convert to HTML list item format."""
        return f'<li><a href="{self.url}">{self.title}</a></li>'

    def __repr__(self) -> str:
        """String representation."""
        return f"InternalLink({self.url}, relevance={self.relevance})"


class InternalLinkList(BaseModel):
    """
    Collection of internal links.

    Manages related reading suggestions.
    """

    links: List[InternalLink] = Field(default_factory=list, description="List of links")
    max_links: int = Field(default=10, description="Maximum suggested links")
    section_title: str = Field(default="More on this topic", description="Section heading")

    def add_link(
        self, url: str, title: str, relevance: int = 5, status: int = 200, domain: str = ""
    ) -> "InternalLinkList":
        """
        Add an internal link.

        Returns self for chaining.
        """
        link = InternalLink(url=url, title=title, relevance=relevance, status=status, domain=domain)
        self.links.append(link)
        return self

    def filter_valid(self) -> "InternalLinkList":
        """Return only valid links (HTTP 200)."""
        valid_links = [link for link in self.links if link.is_valid()]
        new_list = InternalLinkList(section_title=self.section_title)
        new_list.links = valid_links
        return new_list

    def sort_by_relevance(self) -> "InternalLinkList":
        """Sort links by relevance score (highest first)."""
        sorted_links = sorted(self.links, key=lambda x: x.relevance, reverse=True)
        new_list = InternalLinkList(section_title=self.section_title)
        new_list.links = sorted_links
        return new_list

    def deduplicate_domains(self) -> "InternalLinkList":
        """
        Keep only one link per domain for EXTERNAL links.
        For internal links (same domain), deduplicate by URL path instead.
        """
        seen_domains = set()
        seen_paths = set()
        deduplicated = []

        for link in self.links:
            # Extract path from URL for internal link deduplication
            path = link.url.split('/')[-1] if '/' in link.url else link.url
            
            # For internal links (scaile.tech), deduplicate by path
            if link.domain and ('scaile' in link.domain.lower()):
                if path not in seen_paths:
                    deduplicated.append(link)
                    seen_paths.add(path)
            # For external links, deduplicate by domain
            elif link.domain and link.domain not in seen_domains:
                deduplicated.append(link)
                seen_domains.add(link.domain)
            elif not link.domain:
                # If no domain specified, deduplicate by full URL
                if link.url not in seen_paths:
                    deduplicated.append(link)
                    seen_paths.add(link.url)

        new_list = InternalLinkList(section_title=self.section_title)
        new_list.links = deduplicated
        return new_list

    def limit(self, max_count: int) -> "InternalLinkList":
        """Limit to max number of links."""
        limited = self.links[:max_count]
        new_list = InternalLinkList(section_title=self.section_title)
        new_list.links = limited
        return new_list

    def to_html(self) -> str:
        """
        Convert to HTML section.

        Returns:
            HTML with "More on this topic" section containing links.
        """
        if not self.links:
            return ""

        html_lines = [
            '<div class="more-links">',
            f"<h3>{self.section_title}</h3>",
            "<ul>",
        ]

        for link in self.links:
            html_lines.append(f"  {link.to_html()}")

        html_lines.extend(["</ul>", "</div>"])

        return "\n".join(html_lines)

    def count(self) -> int:
        """Get link count."""
        return len(self.links)

    def get_urls(self) -> List[str]:
        """Get list of all URLs."""
        return [link.url for link in self.links]

    def __repr__(self) -> str:
        """String representation."""
        return f"InternalLinkList({len(self.links)} links)"
