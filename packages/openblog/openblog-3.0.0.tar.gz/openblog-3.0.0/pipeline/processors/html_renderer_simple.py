"""
HTML Renderer - PURE VIEWER.

This is a pure HTML viewer - like "html online viewer .net":
1. Takes validated article data
2. Renders to semantic HTML5 page structure
3. Does ZERO content manipulation, linking, or processing

The renderer is just for visualization - it has no functionality.
All content should already be correct from Stage 2/2b.

NO:
- Citation linking
- Content cleanup
- Paragraph wrapping (content is already HTML)
- Regex processing
- Any business logic

YES:
- Wrap content in page structure (header, footer, styles)
- Display content as-is
"""

import logging
# NO REGEX - removed per user requirement
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..utils.schema_markup import generate_all_schemas, render_schemas_as_json_ld
from ..models.output_schema import ArticleOutput

logger = logging.getLogger(__name__)


class HTMLRendererSimple:
    """Simple HTML renderer - no content manipulation."""

    @staticmethod
    def render(
        article: Dict[str, Any],
        company_data: Optional[Dict[str, Any]] = None,
        article_output: Optional[ArticleOutput] = None,
        article_url: Optional[str] = None,
        faq_items: Optional[List[Dict[str, str]]] = None,
        validated_citations_html: Optional[str] = None,
    ) -> str:
        """
        Render validated article data to production HTML.
        
        NO CLEANUP - content should already be correct from Stage 2/2b.
        """
        company = company_data or {}
        
        # Extract article fields - strip HTML from titles/headings
        # Handle both uppercase and lowercase keys
        headline = HTMLRendererSimple._strip_html(article.get("Headline") or article.get("headline", "Untitled"))
        teaser_raw = article.get("Teaser") or article.get("teaser", "")
        teaser = HTMLRendererSimple._strip_html(teaser_raw)  # Strip HTML from teaser
        intro = article.get("Intro") or article.get("intro", "")  # Keep HTML for intro (it's content)
        sources = article.get("Sources") or article.get("sources", "")
        meta_title = HTMLRendererSimple._strip_html(article.get("Meta_Title") or article.get("meta_title", headline))
        meta_desc_raw = article.get("Meta_Description") or article.get("meta_description", "")
        meta_desc = HTMLRendererSimple._strip_html(meta_desc_raw) if meta_desc_raw else teaser  # Use teaser as fallback
        direct_answer = article.get("Direct_Answer") or article.get("direct_answer", "")
        
        # Company info
        company_name = company.get("company_name", "")
        company_url = company.get("company_url", "")
        logo_url = company.get("logo_url", "")
        author_name = company.get("author_name", company_name)
        
        # Images
        featured_image = article.get("_featured_image_url", "")
        featured_alt = f"Article image: {headline}"
        mid_image = article.get("_mid_image_url", "")
        mid_alt = article.get("_mid_image_alt", f"Article image: {headline}")
        
        # Dates
        publication_date = article.get("publication_date", datetime.now().strftime("%Y-%m-%d"))
        display_date = HTMLRendererSimple._format_date(publication_date)
        
        # Render sections - NO processing, just display
        sections_html = HTMLRendererSimple._render_sections(article, mid_image, mid_alt)
        
        # Render intro - NO linking, just display
        intro_html = ""
        if intro:
            intro_html = f'<div class="intro">{intro}</div>'
        
        # Render citations section
        citations_html = validated_citations_html if validated_citations_html else HTMLRendererSimple._render_citations(sources)
        
        # Render FAQ/PAA
        faq_html = HTMLRendererSimple._render_faq(faq_items) if faq_items else ""
        paa_items = article.get("_paa_items", [])
        paa_html = HTMLRendererSimple._render_paa(paa_items) if paa_items else ""
        
        # Render TOC
        toc_html = HTMLRendererSimple._render_toc(article)
        
        # Schema markup - try with article_output first, fallback to article dict
        schemas_html = ""
        if company_data:
            try:
                if article_output:
                    schemas = generate_all_schemas(
                        output=article_output,
                        company_data=company_data,
                        article_url=article_url or "",
                    )
                else:
                    # Fallback: try to create ArticleOutput from article dict
                    try:
                        from ..models.output_schema import ArticleOutput
                        article_obj = ArticleOutput.model_validate(article)
                        schemas = generate_all_schemas(
                            output=article_obj,
                            company_data=company_data,
                            article_url=article_url or "",
                        )
                    except Exception:
                        # If that fails, skip schema generation
                        schemas = None
                
                if schemas:
                    schemas_html = render_schemas_as_json_ld(schemas)
            except Exception as e:
                logger.warning(f"Schema generation failed: {e}")
                schemas_html = ""
        
        # Build final HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{HTMLRendererSimple._escape(meta_title)}</title>
    <meta name="description" content="{HTMLRendererSimple._escape(meta_desc)}">
    
    <!-- Open Graph -->
    <meta property="og:title" content="{HTMLRendererSimple._escape(meta_title)}">
    <meta property="og:description" content="{HTMLRendererSimple._escape(meta_desc)}">
    <meta property="og:type" content="article">
    {f'<meta property="og:image" content="{HTMLRendererSimple._escape(featured_image)}">' if featured_image else ''}
    
    <!-- Schema.org -->
    {schemas_html}
    
    <style>
        :root {{
            --primary: #2563eb;
            --text: #1f2937;
            --text-light: #6b7280;
            --bg: #ffffff;
            --bg-light: #f9fafb;
            --border: #e5e7eb;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.7; 
            color: var(--text);
            background: var(--bg);
        }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        header {{ padding: 40px 0 20px; border-bottom: 1px solid var(--border); margin-bottom: 30px; }}
        h1 {{ font-size: 2.2em; line-height: 1.2; margin-bottom: 15px; }}
        .teaser {{ font-size: 1.2em; color: var(--text-light); margin-bottom: 15px; }}
        .meta {{ font-size: 0.9em; color: var(--text-light); }}
        .featured-image {{ width: 100%; height: auto; border-radius: 8px; margin-bottom: 30px; }}
        .intro {{ font-size: 1.1em; margin-bottom: 30px; padding: 20px; background: var(--bg-light); border-radius: 8px; }}
        .intro p {{ margin-bottom: 15px; }}
        .toc {{ margin: 30px 0; padding: 20px; background: var(--bg-light); border-radius: 8px; }}
        .toc h2 {{ font-size: 1.2em; margin-bottom: 15px; }}
        .toc ul {{ list-style: none; }}
        .toc li {{ margin: 8px 0; }}
        .toc a {{ color: var(--primary); text-decoration: none; }}
        article {{ margin: 40px 0; }}
        article h2 {{ font-size: 1.6em; margin: 40px 0 20px; }}
        article h3 {{ font-size: 1.3em; margin: 30px 0 15px; }}
        article p {{ margin: 15px 0; }}
        article ul, article ol {{ margin: 15px 0 15px 30px; }}
        article li {{ margin: 8px 0; }}
        article a {{ color: var(--primary); }}
        .inline-image {{ width: 100%; height: auto; border-radius: 8px; margin: 30px 0; }}
        .section-related {{ margin: 20px 0; padding: 10px 15px; background: var(--bg-light); border-radius: 4px; font-size: 0.9em; }}
        .section-related span {{ font-weight: 600; margin-right: 10px; }}
        .comparison-table {{ width: 100%; border-collapse: collapse; margin: 30px 0; }}
        .comparison-table th, .comparison-table td {{ padding: 12px; text-align: left; border: 1px solid var(--border); }}
        .comparison-table th {{ background: var(--bg-light); font-weight: 600; }}
        .citations {{ margin: 40px 0; padding: 20px; background: var(--bg-light); border-left: 4px solid var(--primary); }}
        .citations h2 {{ font-size: 1.2em; margin-bottom: 15px; }}
        .citations ol {{ margin: 0 0 0 20px; }}
        .citations li {{ margin: 10px 0; }}
        .citation {{ color: var(--primary); text-decoration: none; font-weight: 500; }}
        .faq, .paa {{ margin: 40px 0; }}
        .faq h2, .paa h2 {{ font-size: 1.4em; margin-bottom: 20px; }}
        .faq-item, .paa-item {{ margin: 20px 0; }}
        .faq-item h3, .paa-item h3 {{ font-size: 1.1em; margin-bottom: 10px; color: var(--text); }}
        .faq-item p, .paa-item p {{ color: var(--text-light); }}
    </style>
</head>
<body>
    <header class="container">
        <h1>{HTMLRendererSimple._escape(headline)}</h1>
        {f'<p class="teaser">{HTMLRendererSimple._escape(teaser)}</p>' if teaser else f'<p class="teaser">{HTMLRendererSimple._escape(meta_desc[:200])}</p>' if meta_desc else ''}
        <p class="meta">By {HTMLRendererSimple._escape(author_name)} • {display_date}</p>
    </header>

    <main class="container">
        {f'<img src="{HTMLRendererSimple._escape(featured_image)}" alt="{HTMLRendererSimple._escape(featured_alt)}" class="featured-image">' if featured_image else ''}
        
        {intro_html}
        
        {toc_html}
        
        <article>
            {sections_html}
        </article>
        
        {paa_html}
        {faq_html}
        
        {citations_html}
    </main>
</body>
</html>"""
        
        return html

    @staticmethod
    def _render_sections(
        article: Dict[str, Any], 
        mid_image: str,
        mid_alt: str
    ) -> str:
        """Render article sections - PURE VIEWER, NO processing."""
        parts = []
        tables = article.get("_comparison_tables", [])
        section_internal_links = article.get("_section_internal_links", {})
        
        for i in range(1, 10):
            # Handle both uppercase and lowercase keys
            title = article.get(f"section_{i:02d}_title") or article.get(f"section_{i:02d}_title", "")
            content = article.get(f"section_{i:02d}_content") or article.get(f"section_{i:02d}_content", "")
            
            if not title and not content:
                continue
            
            # Render title - strip HTML tags (titles should be plain text)
            anchor_key = f"toc_{i:02d}"
            if title:
                clean_title = HTMLRendererSimple._strip_html(title)
                parts.append(f'<h2 id="{anchor_key}">{HTMLRendererSimple._escape(clean_title)}</h2>')
            
            # Render content AS-IS - content is already HTML from Stage 2/3
            # NO string manipulation - AI should have formatted it correctly
            if content and content.strip():
                parts.append(content)
                
                # Add related links if available
                section_links = section_internal_links.get(i, [])
                if section_links:
                    links_html = ' • '.join([
                        f'<a href="{HTMLRendererSimple._escape(link["url"])}">{HTMLRendererSimple._escape(link["title"])}</a>'
                        for link in section_links[:2]
                    ])
                    parts.append(f'<aside class="section-related"><span>Related:</span> {links_html}</aside>')
            
            # Inject comparison table after section 2
            if i == 2 and tables and len(tables) >= 1:
                parts.append(HTMLRendererSimple._render_table(tables[0]))
            
            # Inject mid-article image after section 3
            if i == 3 and mid_image:
                parts.append(f'<img src="{HTMLRendererSimple._escape(mid_image)}" alt="{HTMLRendererSimple._escape(mid_alt)}" class="inline-image">')
            
            # Inject second table after section 5
            if i == 5 and tables and len(tables) >= 2:
                parts.append(HTMLRendererSimple._render_table(tables[1]))
        
        return '\n'.join(parts)

    @staticmethod
    def _render_toc(article: Dict[str, Any]) -> str:
        """Render table of contents with short labels (3-5 words max)."""
        items = []
        
        # Check if toc_dict is available (from Stage 6/Stage 2)
        toc_dict = article.get("toc") or article.get("toc_dict", {})
        
        for i in range(1, 10):
            # Handle both uppercase and lowercase keys
            title = article.get(f"section_{i:02d}_title") or article.get(f"section_{i:02d}_title", "")
            if title:
                anchor = f"toc_{i:02d}"
                
                # Use toc_dict label if available, otherwise generate short label
                toc_key = f"{i:02d}"  # "01", "02", etc.
                if toc_dict and toc_key in toc_dict:
                    display_title = toc_dict[toc_key]
                else:
                    # Strip HTML and create short TOC label (3-5 words max)
                    clean_title = HTMLRendererSimple._strip_html(title)
                    display_title = HTMLRendererSimple._create_short_toc_label(clean_title)
                
                items.append(f'<li><a href="#{anchor}">{HTMLRendererSimple._escape(display_title)}</a></li>')
        
        if not items:
            return ""
        
        # Join items with newline and indent (can't use backslash in f-string expression)
        items_str = '\n                '.join(items)
        return f"""<div class="toc">
            <h2>Table of Contents</h2>
            <ul>
                {items_str}
            </ul>
        </div>"""
    
    @staticmethod
    def _create_short_toc_label(title: str, max_words: int = 5) -> str:
        """
        Create a short TOC label from a full title (3-5 words max).
        
        Args:
            title: Full section title
            max_words: Maximum number of words (default: 5)
            
        Returns:
            Short label for TOC
        """
        import re
        
        # Remove common prefixes that add length without meaning
        prefixes_to_remove = [
            r'^What is\s+',
            r'^How does\s+',
            r'^Why does\s+',
            r'^When should\s+',
            r'^Where can\s+',
        ]
        
        cleaned = title
        for pattern in prefixes_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Split into words
        words = cleaned.split()
        
        # Take first max_words words
        if len(words) <= max_words:
            return cleaned
        
        # Take first max_words words and add ellipsis
        short_words = words[:max_words]
        return ' '.join(short_words) + '...'

    @staticmethod
    def _render_citations(sources: str) -> str:
        """
        Render citations section - NO STRING MANIPULATION.
        
        Stage 4 should output properly formatted HTML citations.
        This renderer just displays them as-is.
        """
        if not sources or not sources.strip():
            return ""
        
        # NO string manipulation - Stage 4 should have formatted citations as HTML
        # If sources is already HTML, render it directly
        # If sources is plain text, just escape and display
        if '<ol>' in sources or '<li>' in sources:
            # Already HTML formatted - render as-is
            return f"""<section class="citations">
            <h2>Sources</h2>
            {sources}
        </section>"""
        else:
            # Plain text - just escape and display (shouldn't happen if Stage 4 works correctly)
            escaped = HTMLRendererSimple._escape(sources)
            return f"""<section class="citations">
            <h2>Sources</h2>
            <div>{escaped}</div>
        </section>"""

    @staticmethod
    def _render_faq(faq_items: List[Dict[str, str]]) -> str:
        """Render FAQ section."""
        if not faq_items:
            return ""
        
        items = []
        for faq in faq_items:
            # Handle both dict and tuple formats
            if isinstance(faq, tuple):
                # Tuple format: (question, answer)
                q = faq[0] if len(faq) > 0 else ""
                a = faq[1] if len(faq) > 1 else ""
            elif isinstance(faq, dict):
                # Dict format: {"question": "...", "answer": "..."}
                q = faq.get("question", "")
                a = faq.get("answer", "")
            else:
                continue
            
            if q and a:
                items.append(f'<div class="faq-item"><h3>{HTMLRendererSimple._escape(str(q))}</h3><p>{str(a)}</p></div>')
        
        if not items:
            return ""
        
        return f"""<section class="faq">
            <h2>Frequently Asked Questions</h2>
            {''.join(items)}
        </section>"""

    @staticmethod
    def _render_paa(paa_items: List[Dict[str, str]]) -> str:
        """Render People Also Ask section."""
        if not paa_items:
            return ""
        
        items = []
        for paa in paa_items:
            # Handle both dict and tuple formats
            if isinstance(paa, tuple):
                # Tuple format: (question, answer)
                q = paa[0] if len(paa) > 0 else ""
                a = paa[1] if len(paa) > 1 else ""
            elif isinstance(paa, dict):
                # Dict format: {"question": "...", "answer": "..."}
                q = paa.get("question", "")
                a = paa.get("answer", "")
            else:
                continue
            
            if q and a:
                items.append(f'<div class="paa-item"><h3>{HTMLRendererSimple._escape(str(q))}</h3><p>{str(a)}</p></div>')
        
        if not items:
            return ""
        
        return f"""<section class="paa">
            <h2>People Also Ask</h2>
            {''.join(items)}
        </section>"""

    @staticmethod
    def _render_table(table: Dict[str, Any]) -> str:
        """Render comparison table."""
        title = table.get("title", "")
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        
        if not headers or not rows:
            return ""
        
        header_html = ''.join([f'<th>{h}</th>' for h in headers])
        rows_html = ''.join([
            '<tr>' + ''.join([f'<td>{cell}</td>' for cell in row]) + '</tr>'
            for row in rows
        ])
        
        return f"""
        {f'<h3>{title}</h3>' if title else ''}
        <table class="comparison-table">
            <thead><tr>{header_html}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>"""


    @staticmethod
    def _escape(text: str) -> str:
        """HTML escape text."""
        if not text:
            return ""
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )
    
    @staticmethod
    def _strip_html(text: str) -> str:
        """Strip HTML tags from text - for titles/headings. NO STRING MANIPULATION."""
        if not text:
            return ""
        
        # NO string manipulation - AI should have provided plain text titles
        # Just decode HTML entities if present
        import html
        try:
            clean = html.unescape(str(text))
        except:
            clean = str(text)
        
        return clean.strip()

    @staticmethod
    def _format_date(date_str: str) -> str:
        """Format date for display."""
        try:
            if '-' in date_str and len(date_str.split('-')[0]) == 4:
                dt = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d')
                return dt.strftime('%b %d, %Y')
        except (ValueError, IndexError):
            pass
        return date_str

