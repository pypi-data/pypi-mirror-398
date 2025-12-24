"""
Hybrid Batch Similarity Checker - Character Shingles + Semantic Embeddings

Enhanced similarity checker combining character-level and semantic analysis for batch blog generation.
Supports both dependency-free mode (character shingles only) and enhanced mode (+ Gemini embeddings).

Detects content cannibalization within a batch session:
- Keyword cannibalization
- Content overlap using character shingles (language-agnostic)  
- Semantic similarity using Gemini embeddings (optional)
- Title/heading similarity
- FAQ duplication

Design:
- In-memory only (session scope)
- Optional Gemini embeddings for semantic similarity
- Language-agnostic character shingles as fallback
- Fast Jaccard + cosine similarity
- Hybrid scoring combines both approaches
- Content regeneration workflow when similarity too high

Usage:
    # Zero-dependency mode
    checker = HybridSimilarityChecker()
    
    # Enhanced mode with semantic analysis
    from pipeline.utils.gemini_embeddings import GeminiEmbeddingClient
    client = GeminiEmbeddingClient(api_key="your-key")
    checker = HybridSimilarityChecker(embedding_client=client)
    
    # During batch generation with regeneration
    for topic in batch_topics:
        if checker.is_duplicate_keyword(topic):
            print(f"Skip: {topic} already covered")
            continue
            
        article = generate_article(topic)
        
        report = checker.check_content_similarity(article)
        if report.is_too_similar:
            if checker.enable_regeneration:
                print(f"Regenerating due to similarity: {report.similarity_score:.1f}%")
                # Trigger content regeneration
                continue
            else:
                print(f"Warning: Similar to {report.similar_article}")
        
        # Store for next comparisons
        checker.add_article(article)
"""

import re
import hashlib
import math
import asyncio
from typing import Dict, List, Set, Optional, Tuple, NamedTuple, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class SimilarityResult(NamedTuple):
    """Hybrid similarity check result with detailed analysis."""
    is_too_similar: bool
    similarity_score: float  # 0-100 (hybrid score)
    similar_article: Optional[str] = None
    issues: List[str] = None
    shingle_score: Optional[float] = None  # Character shingle similarity
    semantic_score: Optional[float] = None  # Semantic embedding similarity (0.0-1.0)
    analysis_mode: str = "shingles_only"  # "shingles_only", "hybrid"
    regeneration_needed: bool = False  # Whether content should be regenerated


@dataclass
class ArticleSummary:
    """Lightweight article summary for in-memory comparison with optional embeddings."""
    slug: str
    keyword: str
    title: str
    headings: List[str]
    content_shingles: Set[str]  # Character-level shingles
    faq_questions: List[str]
    intro_hash: str
    content_embedding: Optional[List[float]] = None  # Semantic embedding vector
    embedding_text: Optional[str] = None  # Text used for embedding generation
    
    def __post_init__(self):
        """Ensure lists are not None."""
        self.headings = self.headings or []
        self.faq_questions = self.faq_questions or []
        self.content_shingles = self.content_shingles or set()


class HybridSimilarityChecker:
    """
    Hybrid in-memory similarity checker for batch sessions.
    
    Combines character shingles with optional semantic embeddings
    for comprehensive duplicate detection in 5-20 article batches.
    """
    
    # Similarity thresholds
    DUPLICATE_THRESHOLD = 70.0    # 70%+ = too similar, skip/regenerate
    WARNING_THRESHOLD = 50.0      # 50%+ = warn but proceed
    SEMANTIC_THRESHOLD = 0.85     # Cosine similarity for semantic duplicates
    
    # Shingle configuration
    SHINGLE_SIZE = 5              # 5-character shingles
    MIN_CONTENT_LENGTH = 100      # Minimum content length to check
    
    def __init__(self, embedding_client=None, enable_regeneration=True, similarity_threshold=None):
        """
        Initialize hybrid similarity checker.
        
        Args:
            embedding_client: Optional Gemini embedding client for semantic analysis
            enable_regeneration: Whether to enable content regeneration on high similarity
            similarity_threshold: Custom similarity threshold (default: 70.0%)
        """
        self.articles: Dict[str, ArticleSummary] = {}  # slug -> summary
        self.keywords: Set[str] = set()  # normalized keywords
        self._slug_counter = 0
        
        # Use custom threshold if provided, otherwise use default
        if similarity_threshold is not None:
            self.DUPLICATE_THRESHOLD = float(similarity_threshold)
        # Keep WARNING_THRESHOLD relative to DUPLICATE_THRESHOLD
        self.WARNING_THRESHOLD = max(self.DUPLICATE_THRESHOLD - 20.0, 30.0)
        
        # Embedding support
        self.embedding_client = embedding_client
        self.semantic_mode = embedding_client is not None
        self.enable_regeneration = enable_regeneration
        
        # Performance tracking
        self._embedding_cache_hits = 0
        self._embedding_requests = 0
        
        if self.semantic_mode:
            logger.info("✅ Hybrid similarity checker initialized (character shingles + semantic embeddings)")
        else:
            logger.info("✅ Basic similarity checker initialized (character shingles only)")
    
    # ========== KEYWORD CHECKING ==========
    
    def is_duplicate_keyword(self, keyword: str) -> bool:
        """
        Quick check if keyword already exists in batch.
        
        Args:
            keyword: Target keyword to check
            
        Returns:
            True if keyword already used
        """
        normalized = self._normalize_text(keyword)
        return normalized in self.keywords
    
    def get_similar_keywords(self, keyword: str, threshold: float = 0.8) -> List[str]:
        """
        Find similar keywords already in batch.
        
        Args:
            keyword: Keyword to check
            threshold: Similarity threshold (0.8 = 80% word overlap)
            
        Returns:
            List of similar keywords found
        """
        normalized = self._normalize_text(keyword)
        keyword_words = set(normalized.split())
        
        similar = []
        for existing_kw in self.keywords:
            existing_words = set(existing_kw.split())
            
            if keyword_words and existing_words:
                # Jaccard similarity on words
                overlap = len(keyword_words & existing_words)
                union = len(keyword_words | existing_words)
                similarity = overlap / union if union > 0 else 0
                
                if similarity >= threshold:
                    similar.append(existing_kw)
        
        return similar
    
    # ========== CONTENT CHECKING ==========
    
    def check_content_similarity(self, article: Dict, slug: str = None) -> SimilarityResult:
        """
        Check article content similarity against batch using hybrid approach.
        
        Args:
            article: Article dictionary
            slug: Optional slug (auto-generated if not provided)
            
        Returns:
            SimilarityResult with detailed hybrid analysis
        """
        if not self.articles:
            return SimilarityResult(
                False, 0.0, issues=[], 
                analysis_mode="hybrid" if self.semantic_mode else "shingles_only"
            )
        
        # Extract summary from new article
        new_summary = self._extract_summary(article, slug)
        
        # Compare against all existing articles
        best_match = None
        highest_score = 0.0
        all_issues = []
        best_shingle_score = 0.0
        best_semantic_score = None
        
        for existing_slug, existing_summary in self.articles.items():
            score, issues, shingle_score, semantic_score = self._compare_articles(new_summary, existing_summary)
            
            if score > highest_score:
                highest_score = score
                best_match = existing_slug
                all_issues = issues
                best_shingle_score = shingle_score
                best_semantic_score = semantic_score
        
        is_too_similar = highest_score >= self.DUPLICATE_THRESHOLD
        analysis_mode = "hybrid" if self.semantic_mode and new_summary.content_embedding else "shingles_only"
        regeneration_needed = is_too_similar and self.enable_regeneration
        
        return SimilarityResult(
            is_too_similar=is_too_similar,
            similarity_score=highest_score,
            similar_article=best_match,
            issues=all_issues,
            shingle_score=best_shingle_score,
            semantic_score=best_semantic_score,
            analysis_mode=analysis_mode,
            regeneration_needed=regeneration_needed
        )
    
    def add_article(self, article: Dict, slug: str = None) -> str:
        """
        Add article to batch memory for future comparisons.
        
        Args:
            article: Article dictionary
            slug: Optional slug
            
        Returns:
            Generated slug for the article
        """
        summary = self._extract_summary(article, slug)
        
        # Store article
        self.articles[summary.slug] = summary
        self.keywords.add(summary.keyword)
        
        logger.info(f"Added article '{summary.slug}' to batch memory ({len(self.articles)} total)")
        return summary.slug
    
    # ========== SUMMARY EXTRACTION ==========
    
    def _extract_summary(self, article: Dict, slug: str = None) -> ArticleSummary:
        """Extract lightweight summary with optional embedding generation."""
        
        # Generate slug
        if not slug:
            title = article.get("Headline") or article.get("headline", "")
            if title:
                slug = self._title_to_slug(title)
            else:
                self._slug_counter += 1
                slug = f"article-{self._slug_counter:03d}"
        
        # Extract and normalize keyword
        keyword = self._normalize_text(
            article.get("primary_keyword") or article.get("keyword", "")
        )
        
        # Extract and normalize title
        title = self._normalize_text(
            article.get("Meta_Title") or article.get("meta_title") or 
            article.get("Headline") or article.get("headline", "")
        )
        
        # Extract headings
        headings = self._extract_headings(article)
        
        # Extract content shingles
        content_text = self._extract_content(article)
        content_shingles = self._extract_shingles(content_text)
        
        # Extract FAQ questions
        faq_questions = self._extract_faq_questions(article)
        
        # Generate intro hash
        intro = article.get("Intro") or article.get("intro", "")
        intro_hash = hashlib.md5(
            self._normalize_text(intro[:300]).encode('utf-8')
        ).hexdigest()[:12]
        
        # Generate embedding if semantic mode enabled
        content_embedding = None
        embedding_text = None
        if self.semantic_mode and len(content_text) >= self.MIN_CONTENT_LENGTH:
            embedding_text = self._prepare_embedding_text(article, content_text)
            content_embedding = self._generate_embedding(embedding_text)
        
        return ArticleSummary(
            slug=slug,
            keyword=keyword,
            title=title,
            headings=headings,
            content_shingles=content_shingles,
            faq_questions=faq_questions,
            intro_hash=intro_hash,
            content_embedding=content_embedding,
            embedding_text=embedding_text
        )
    
    def _extract_content(self, article: Dict) -> str:
        """Extract all content for analysis."""
        parts = []
        
        # Headline (weighted)
        headline = article.get("Headline") or article.get("headline", "")
        if headline:
            parts.extend([headline] * 2)  # Weight headlines
        
        # Intro
        intro = article.get("Intro") or article.get("intro", "")
        if intro:
            parts.append(intro)
        
        # Sections (try both formats)
        for i in range(1, 15):
            # Format 1: section_01_content
            content = article.get(f"section_{i:02d}_content", "")
            if not content:
                # Format 2: Section_01_Content
                content = article.get(f"Section_{i:02d}_Content", "")
            
            if content:
                parts.append(content)
        
        # Key takeaways
        for i in range(1, 6):
            takeaway = (
                article.get(f"key_takeaway_{i:02d}", "") or
                article.get(f"Key_Takeaway_{i:02d}", "")
            )
            if takeaway:
                parts.append(takeaway)
        
        return " ".join(parts)
    
    def _extract_headings(self, article: Dict) -> List[str]:
        """Extract and normalize headings."""
        headings = []
        
        # From ToC
        toc = article.get("table_of_contents") or article.get("ToC", [])
        if isinstance(toc, list):
            for item in toc:
                if isinstance(item, dict) and "title" in item:
                    heading = self._normalize_text(item["title"])
                    if heading:
                        headings.append(heading)
                elif isinstance(item, str):
                    heading = self._normalize_text(item)
                    if heading:
                        headings.append(heading)
        
        # From section headings
        for i in range(1, 15):
            heading = (
                article.get(f"section_{i:02d}_heading", "") or
                article.get(f"Section_{i:02d}_Heading", "")
            )
            if heading:
                normalized = self._normalize_text(heading)
                if normalized:
                    headings.append(normalized)
        
        return headings
    
    def _extract_faq_questions(self, article: Dict) -> List[str]:
        """Extract FAQ questions."""
        questions = []
        
        # Check different FAQ formats
        for key in ["FAQ", "faq", "PAA", "paa"]:
            faq_data = article.get(key, [])
            if isinstance(faq_data, list):
                for item in faq_data:
                    if isinstance(item, dict) and "question" in item:
                        q = self._normalize_text(item["question"])
                        if q:
                            questions.append(q)
        
        return questions
    
    # ========== EMBEDDING SUPPORT ==========
    
    def _prepare_embedding_text(self, article: Dict, content_text: str) -> str:
        """Prepare text for embedding generation (focus on key content)."""
        parts = []
        
        # Primary keyword (important for semantic similarity)
        keyword = article.get("primary_keyword", "")
        if keyword:
            parts.append(f"Topic: {keyword}")
        
        # Title/headline
        title = (article.get("Meta_Title") or article.get("Headline") or 
                article.get("headline") or "")
        if title:
            parts.append(f"Title: {title}")
        
        # Intro (most important for semantic analysis)
        intro = article.get("Intro") or article.get("intro", "")
        if intro:
            parts.append(f"Introduction: {intro}")
        
        # Key sections (limit to avoid token limits)
        sections_added = 0
        for i in range(1, 8):  # Limit to first 7 sections
            content = (article.get(f"section_{i:02d}_content", "") or
                      article.get(f"Section_{i:02d}_Content", ""))
            if content and sections_added < 3:  # Max 3 sections
                parts.append(content[:200])  # Limit section length
                sections_added += 1
        
        # Combine with reasonable length limit
        combined = " ".join(parts)
        return combined[:2000]  # Keep within reasonable token limits
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using Gemini API."""
        if not self.embedding_client or not text.strip():
            return None
        
        try:
            self._embedding_requests += 1
            # Run the async embedding generation in sync context
            loop = None
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # The embed_text method is synchronous, no need for complex async handling
            embedding = self.embedding_client.embed_text(text)
            
            logger.debug(f"Generated embedding for {len(text)} chars: {len(embedding) if embedding else 0} dims")
            return embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None
    
    # ========== TEXT PROCESSING ==========
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison (language-agnostic)."""
        if not text or not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        # Strip
        text = text.strip()
        
        return text
    
    def _extract_shingles(self, text: str) -> Set[str]:
        """
        Extract character-level shingles (k-grams).
        
        Language-agnostic approach using character overlaps.
        """
        text = self._normalize_text(text)
        
        if len(text) < self.SHINGLE_SIZE:
            return set()
        
        shingles = set()
        for i in range(len(text) - self.SHINGLE_SIZE + 1):
            shingle = text[i:i + self.SHINGLE_SIZE]
            # Use hash for memory efficiency
            shingle_hash = hashlib.md5(shingle.encode('utf-8')).hexdigest()[:8]
            shingles.add(shingle_hash)
        
        return shingles
    
    def _title_to_slug(self, title: str) -> str:
        """Convert title to URL-friendly slug."""
        slug = self._normalize_text(title)
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s]+', '-', slug)
        return slug[:50]  # Reasonable length limit
    
    # ========== SIMILARITY COMPARISON ==========
    
    def _compare_articles(self, new: ArticleSummary, existing: ArticleSummary) -> Tuple[float, List[str], float, Optional[float]]:
        """Compare two articles and return hybrid similarity score + detailed analysis."""
        issues = []
        
        # 1. Keyword match (critical)
        keyword_match = new.keyword == existing.keyword and new.keyword != ""
        if keyword_match:
            issues.append("CRITICAL: Same target keyword")
        
        # 2. Title similarity
        title_sim = self._jaccard_words(new.title, existing.title)
        if title_sim > 0.6:
            issues.append(f"High title similarity ({title_sim:.0%})")
        
        # 3. Intro hash match
        intro_match = new.intro_hash == existing.intro_hash and new.intro_hash != ""
        if intro_match:
            issues.append("Identical intro")
        
        # 4. Character-level content overlap
        content_sim = self._jaccard_similarity(new.content_shingles, existing.content_shingles)
        if content_sim > 0.15:  # 15% character overlap = significant
            issues.append(f"Character similarity ({content_sim:.0%})")
        
        # 5. Heading overlap
        heading_sim = self._list_similarity(new.headings, existing.headings)
        if heading_sim > 0.4:
            issues.append(f"Overlapping headings ({heading_sim:.0%})")
        
        # 6. FAQ overlap
        faq_sim = self._list_similarity(new.faq_questions, existing.faq_questions)
        if faq_sim > 0.5:
            issues.append(f"FAQ overlap ({faq_sim:.0%})")
        
        # 7. Semantic similarity (if embeddings available)
        semantic_sim = None
        if (self.semantic_mode and 
            new.content_embedding and existing.content_embedding):
            semantic_sim = self._cosine_similarity(new.content_embedding, existing.content_embedding)
            if semantic_sim > self.SEMANTIC_THRESHOLD:
                issues.append(f"HIGH semantic similarity ({semantic_sim:.1%})")
            elif semantic_sim > 0.75:
                issues.append(f"Moderate semantic similarity ({semantic_sim:.1%})")
        
        # Calculate character-based score (original logic)
        shingle_score = (
            (40 if keyword_match else 0) +      # Keyword match is critical
            (title_sim * 20) +                  # Title similarity important
            (content_sim * 25) +                # Content is most important
            (heading_sim * 10) +                # Heading structure matters
            (faq_sim * 5) +                     # FAQ less critical
            (5 if intro_match else 0)           # Intro bonus
        )
        shingle_score = min(shingle_score, 100)
        
        # Hybrid score combines character + semantic similarity
        if semantic_sim is not None:
            # Weight: 60% character analysis, 40% semantic similarity
            semantic_score_weighted = semantic_sim * 100  # Convert to 0-100 scale
            hybrid_score = (shingle_score * 0.6) + (semantic_score_weighted * 0.4)
            
            # Boost score if both methods detect high similarity
            if shingle_score > 50 and semantic_sim > 0.8:
                hybrid_score = min(hybrid_score * 1.2, 100)  # 20% boost for consensus
                issues.append("CONSENSUS: Both character and semantic analysis detect high similarity")
        else:
            hybrid_score = shingle_score
        
        return hybrid_score, issues, shingle_score, semantic_sim
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two embedding vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        # Dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """Jaccard similarity: |A ∩ B| / |A ∪ B|"""
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _jaccard_words(self, text1: str, text2: str) -> float:
        """Jaccard similarity on word level."""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        return self._jaccard_similarity(words1, words2)
    
    def _list_similarity(self, list1: List[str], list2: List[str]) -> float:
        """Calculate similarity between two lists of strings."""
        if not list1 or not list2:
            return 0.0
        
        matches = 0
        for item1 in list1:
            for item2 in list2:
                if self._jaccard_words(item1, item2) > 0.7:  # 70% word overlap
                    matches += 1
                    break
        
        return matches / len(list1) if list1 else 0.0
    
    # ========== BATCH MANAGEMENT ==========
    
    def get_batch_stats(self) -> Dict:
        """Get current batch statistics including embedding info."""
        total_shingles = sum(len(article.content_shingles) for article in self.articles.values())
        embeddings_count = sum(1 for article in self.articles.values() if article.content_embedding)
        embedding_dimensions = 0
        if embeddings_count > 0:
            first_embedding = next((a.content_embedding for a in self.articles.values() if a.content_embedding), None)
            embedding_dimensions = len(first_embedding) if first_embedding else 0
        
        return {
            "total_articles": len(self.articles),
            "total_keywords": len(self.keywords),
            "memory_usage_shingles": total_shingles,
            "semantic_mode": self.semantic_mode,
            "embeddings_stored": embeddings_count,
            "embedding_dimensions": embedding_dimensions,
            "embedding_cache_hits": self._embedding_cache_hits,
            "embedding_requests": self._embedding_requests,
            "regeneration_enabled": self.enable_regeneration,
            "articles": list(self.articles.keys())
        }
    
    def clear_batch(self):
        """Clear all articles from memory (start new batch)."""
        self.articles.clear()
        self.keywords.clear()
        self._slug_counter = 0
        self._embedding_cache_hits = 0
        self._embedding_requests = 0
        logger.info("Batch memory cleared")
    
    def remove_article(self, slug: str) -> bool:
        """Remove specific article from batch."""
        if slug in self.articles:
            article = self.articles[slug]
            del self.articles[slug]
            self.keywords.discard(article.keyword)
            logger.info(f"Removed article '{slug}' from batch")
            return True
        return False
    
    def list_articles(self) -> List[Dict[str, str]]:
        """List all articles in current batch with embedding status."""
        return [
            {
                "slug": article.slug,
                "keyword": article.keyword,
                "title": article.title[:80] + "..." if len(article.title) > 80 else article.title,
                "has_embedding": "yes" if article.content_embedding else "no"
            }
            for article in self.articles.values()
        ]


# ========== CONVENIENCE FUNCTIONS ==========

def check_batch_similarity_hybrid(article: Dict, checker: HybridSimilarityChecker) -> SimilarityResult:
    """Quick hybrid similarity check against current batch."""
    return checker.check_content_similarity(article)


def create_hybrid_checker(embedding_client=None, enable_regeneration=True) -> HybridSimilarityChecker:
    """Create new hybrid similarity checker with optional embedding support."""
    return HybridSimilarityChecker(embedding_client=embedding_client, enable_regeneration=enable_regeneration)