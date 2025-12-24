"""
Citation Model

Represents a single citation/source in the article.

Structure:
- Number: Citation index [1], [2], etc.
- URL: Source URL
- Title: Short title/description of source
- HTML: Formatted HTML output
"""

from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, field_validator
import logging

logger = logging.getLogger(__name__)


class Citation(BaseModel):
    """
    Single citation/source reference.

    Attributes:
        number: Citation index (1, 2, 3, ...)
        url: Source URL
        title: Citation title/description (8-15 words as per v4.1)
        accessed_date: Optional: date accessed
    """

    number: int = Field(..., description="Citation number [1], [2], etc.", ge=1, le=999)
    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Short citation title (8-15 words)")
    meta_description: Optional[str] = Field(default="", description="Short meta description (50-100 chars) for citation preview/tooltip")
    accessed_date: Optional[str] = Field(default="", description="Date accessed (YYYY-MM-DD)")

    @field_validator("title")
    @classmethod
    def validate_title_length(cls, v):
        """Validate title is reasonable length."""
        words = len(v.split())
        if words < 3:
            logger.warning(f"Citation title too short ({words} words): {v}")
        elif words > 25:
            logger.warning(f"Citation title too long ({words} words): {v}")
        return v

    @field_validator("url")
    @classmethod
    def validate_url_format(cls, v):
        """Validate URL format."""
        # CRITICAL FIX: Reject relative URLs and malformed URLs
        if not v.startswith(("http://", "https://")):
            if v.startswith("/"):
                # Relative URL - reject it
                logger.error(f"Rejecting relative URL: {v}")
                raise ValueError(f"Relative URLs are not allowed: {v}")
            logger.warning(f"URL missing protocol: {v}")
            # Only prepend https:// if it looks like a domain (has a dot)
            if "." in v and not v.startswith("/"):
                v = f"https://{v}"
            else:
                logger.error(f"Invalid URL format: {v}")
                raise ValueError(f"Invalid URL format: {v}")
        
        # CRITICAL FIX: Validate URL has proper domain structure
        from urllib.parse import urlparse
        try:
            parsed = urlparse(v)
            if not parsed.netloc:
                logger.error(f"URL missing domain: {v}")
                raise ValueError(f"URL missing domain: {v}")
            
            # Check domain has TLD (at least one dot in netloc)
            domain = parsed.netloc.lower()
            if "." not in domain and domain not in ['localhost']:
                # Check if it's an IP address
                try:
                    import ipaddress
                    ipaddress.ip_address(domain)
                except ValueError:
                    logger.error(f"URL missing TLD: {v}")
                    raise ValueError(f"URL missing TLD (invalid domain): {v}")
        except Exception as e:
            logger.error(f"URL validation error for {v}: {e}")
            raise ValueError(f"Invalid URL format: {v}")
        
        return v

    def to_html(self) -> str:
        """
        Convert to HTML format.

        Format: [n]: <a href="url">title</a>
        """
        meta_attr = f' data-description="{self.meta_description}"' if self.meta_description else ""
        return f'[{self.number}]: <a href="{self.url}" target="_blank"{meta_attr}>{self.title}</a>'

    def to_markdown(self) -> str:
        """Convert to Markdown format."""
        return f"[{self.number}]: [{self.title}]({self.url})"

    def __repr__(self) -> str:
        """String representation."""
        return f"Citation({self.number}: {self.url})"


class CitationList(BaseModel):
    """
    Collection of citations.

    Manages multiple citations and provides formatting options.
    """

    citations: List[Citation] = Field(default_factory=list, description="List of citations")
    max_citations: int = Field(default=20, description="Maximum allowed citations (v4.1)")

    @field_validator("citations")
    @classmethod
    def validate_citation_count(cls, v, info):
        """Validate citation count doesn't exceed maximum."""
        if len(v) > 20:
            logger.warning(f"Citation count exceeds 20: {len(v)} citations")
        return v

    def add_citation(self, url: str, title: str, accessed_date: str = "") -> "CitationList":
        """
        Add a citation to the list.

        Returns self for chaining.
        """
        next_number = len(self.citations) + 1
        citation = Citation(
            number=next_number,
            url=url,
            title=title,
            accessed_date=accessed_date,
        )
        self.citations.append(citation)
        return self

    def to_html(self) -> str:
        """
        Convert all citations to HTML.

        Returns:
            HTML block with all citations.
            Format:
            <div class="citations">
              [1]: <a href="url">title</a>
              [2]: <a href="url">title</a>
              ...
            </div>
        """
        if not self.citations:
            return ""

        html_lines = ["<div class=\"citations\">"]
        for citation in self.citations:
            html_lines.append(f"  <p>{citation.to_html()}</p>")
        html_lines.append("</div>")

        return "\n".join(html_lines)

    def to_html_paragraph_list(self) -> str:
        """
        Convert to HTML paragraph list (v4.1 format).

        Returns:
            HTML section with citations as list items.
        """
        if not self.citations:
            return ""

        items = []
        for citation in self.citations:
            # Create clickable link - clean the title for display
            clean_title = citation.title.strip() if citation.title else f"Source {citation.number}"
            
            # Extract keywords from title and URL
            keywords = self._extract_keywords(citation.title, citation.url)
            keywords_text = f" | {keywords}" if keywords else ""
            
            meta_attr = f' data-description="{citation.meta_description}"' if citation.meta_description else ""
            items.append(
                f'<li id="source-{citation.number}">'
                f'<a href="{citation.url}" target="_blank" rel="noopener noreferrer"{meta_attr}>{clean_title}{keywords_text}</a>'
                f'</li>'
            )

        return f"""<section class="citations">
        <h2>Sources</h2>
        <ol>
            {''.join(items)}
        </ol>
    </section>"""
    
    @staticmethod
    def _extract_keywords(title: str, url: str) -> str:
        """
        Extract 2-3 topic keywords from citation title.
        
        Focuses on meaningful topic keywords, skipping company names and generic terms.
        
        Args:
            title: Citation title
            url: Citation URL (not used, kept for API compatibility)
            
        Returns:
            Keywords separated by | (e.g., "automation | enterprise | ROI")
        """
        import re
        
        if not title:
            return ""
        
        keywords = []
        
        # Stop words to skip
        stop_words = {
            "a", "an", "and", "as", "at", "be", "by", "for", "from", "if",
            "in", "is", "it", "no", "of", "on", "or", "the", "to", "up",
            "we", "your", "you", "with", "that", "this", "when", "where",
            "which", "who", "how", "what", "why", "can", "will", "should",
            "must", "may", "might", "could"
        }
        
        # Common words to skip (too generic)
        generic_words = {
            "top", "best", "guide", "report", "trends", "predictions", 
            "insights", "analysis", "study", "research", "article", "blog",
            "post", "page", "news", "press", "release", "whitepaper", "use",
            "cases", "case", "study", "studies"
        }
        
        # Company names to skip (only actual company names, not topic words)
        company_names = {
            "ibm", "gartner", "forrester", "mckinsey", "deloitte", "pwc",
            "bain", "bcg", "accenture", "kanerika", "evoluteiq", "intellectyx",
            "infinite", "salesforce", "microsoft", "google", "amazon", "aws",
            "serrala", "appian", "anywhere", "umu", "svitla",
            "willdom", "rand", "switch", "cxotoday"
        }
        
        # Remove common prefixes and suffixes
        title_clean = re.sub(r'^(Top|Best|Guide|Report|Trends|Predictions|Insights|Analysis|Study|Research|The)\s+', '', title, flags=re.IGNORECASE)
        title_clean = re.sub(r'\s+(Report|Trends|Predictions|Insights|Analysis|Study|Research|2024|2025|2026)$', '', title_clean, flags=re.IGNORECASE)
        
        # Split into words
        words = title_clean.split()
        
        # Filter meaningful words (3+ chars, not stop/generic/company words)
        meaningful = []
        for w in words:
            w_clean = w.lower().strip('.,;:!?()[]{}')
            # Skip if it's a stop word, generic word, company name, or too short
            # Allow 3+ chars (not just 4+) to catch important short keywords like "AI", "AP", "ROI"
            if (len(w_clean) >= 2 and  # At least 2 chars (allows "AI", "AP", "ROI")
                w_clean not in stop_words and 
                w_clean not in generic_words and
                w_clean not in company_names and
                not w_clean.isdigit()):  # Skip years/numbers
                # Capitalize properly (handle acronyms)
                if w_clean.isupper() or len(w_clean) <= 3:
                    kw = w_clean.upper()
                else:
                    kw = w_clean.title()
                meaningful.append(kw)
        
        # Take top 2-3 most meaningful keywords
        keywords = meaningful[:3]
        
        return " | ".join(keywords) if keywords else ""

    def count(self) -> int:
        """Get citation count."""
        return len(self.citations)

    def get_urls(self) -> List[str]:
        """Get list of all URLs."""
        return [c.url for c in self.citations]

    def get_citation_by_number(self, number: int) -> Optional[Citation]:
        """Get citation by number."""
        for citation in self.citations:
            if citation.number == number:
                return citation
        return None

    def __repr__(self) -> str:
        """String representation."""
        return f"CitationList({len(self.citations)} citations)"
