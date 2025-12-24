"""
Gemini Embeddings Client - Semantic Similarity Support

Simple client for generating text embeddings using Google's Gemini API.
Used by the hybrid similarity checker for semantic duplicate detection.

Features:
- Text embedding generation using Gemini models
- In-memory caching for batch sessions
- Error handling and retry logic
- Rate limiting support
- Token usage tracking

Usage:
    client = GeminiEmbeddingClient(api_key="your-key")
    embedding = client.embed_text("Your content here")
    similarity = client.compare_texts(text1, text2)
"""

import hashlib
import logging
import time
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingCacheEntry:
    """Cache entry for embeddings with metadata."""
    embedding: List[float]
    text_hash: str
    created_at: float
    token_count: int


class GeminiEmbeddingClient:
    """
    Gemini API client for text embeddings.
    
    Provides semantic similarity analysis for the hybrid similarity checker.
    """
    
    def __init__(self, api_key: str, model: str = "text-embedding-004", cache_ttl: int = 3600):
        """
        Initialize Gemini embedding client.
        
        Args:
            api_key: Google API key for Gemini
            model: Embedding model to use
            cache_ttl: Cache time-to-live in seconds (1 hour default)
        """
        self.api_key = api_key
        self.model = model
        self.cache_ttl = cache_ttl
        
        # In-memory cache for batch sessions
        self._cache: Dict[str, EmbeddingCacheEntry] = {}
        
        # Performance tracking
        self._requests_made = 0
        self._cache_hits = 0
        self._total_tokens = 0
        self._api_errors = 0
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
        
        logger.info(f"✅ Gemini embedding client initialized (model: {model})")
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text with caching.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        if not text or not text.strip():
            return None
        
        # Check cache first
        text_hash = self._hash_text(text)
        cached = self._get_cached_embedding(text_hash)
        if cached:
            self._cache_hits += 1
            return cached.embedding
        
        # Rate limiting
        self._enforce_rate_limit()
        
        try:
            # Generate embedding via API
            embedding = self._call_gemini_api(text)
            if embedding:
                # Cache the result
                self._cache_embedding(text_hash, embedding, text)
                self._requests_made += 1
                return embedding
        except Exception as e:
            self._api_errors += 1
            logger.error(f"Embedding generation failed: {e}")
        
        return None
    
    def compare_texts(self, text1: str, text2: str) -> float:
        """
        Compare semantic similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Cosine similarity (0.0 to 1.0)
        """
        emb1 = self.embed_text(text1)
        emb2 = self.embed_text(text2)
        
        if emb1 and emb2:
            return self._cosine_similarity(emb1, emb2)
        
        return 0.0
    
    def _call_gemini_api(self, text: str) -> Optional[List[float]]:
        """
        Call Gemini API to generate embedding using google-generativeai package.
        
        Requires: pip install google-generativeai
        """
        try:
            # Import Google AI SDK
            try:
                import google.generativeai as genai
            except ImportError:
                logger.warning("google-generativeai package not installed. Install with: pip install google-generativeai")
                return None
            
            # Configure API key
            genai.configure(api_key=self.api_key)
            
            # Generate embedding
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="semantic_similarity"
            )
            
            # Extract embedding vector
            embedding = result.get('embedding')
            if embedding and isinstance(embedding, list):
                logger.debug(f"Generated {len(embedding)}D embedding for {len(text)} chars")
                return embedding
            else:
                logger.error(f"Invalid embedding format received: {type(embedding)}")
                return None
            
        except ImportError as e:
            logger.error(f"google-generativeai package not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return None
    
    def _hash_text(self, text: str) -> str:
        """Generate consistent hash for text caching."""
        # Normalize text for consistent hashing
        normalized = text.strip().lower()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]
    
    def _get_cached_embedding(self, text_hash: str) -> Optional[EmbeddingCacheEntry]:
        """Get cached embedding if available and not expired."""
        if text_hash in self._cache:
            entry = self._cache[text_hash]
            # Check if expired
            if time.time() - entry.created_at < self.cache_ttl:
                return entry
            else:
                # Remove expired entry
                del self._cache[text_hash]
        return None
    
    def _cache_embedding(self, text_hash: str, embedding: List[float], text: str):
        """Cache embedding with metadata."""
        token_count = self._estimate_tokens(text)
        entry = EmbeddingCacheEntry(
            embedding=embedding,
            text_hash=text_hash,
            created_at=time.time(),
            token_count=token_count
        )
        self._cache[text_hash] = entry
        self._total_tokens += token_count
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation for tracking."""
        # Simple approximation: ~4 characters per token
        return len(text) // 4
    
    def _enforce_rate_limit(self):
        """Simple rate limiting to avoid API throttling."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors."""
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
    
    def get_stats(self) -> Dict:
        """Get client performance statistics."""
        cache_hit_rate = (self._cache_hits / max(self._requests_made + self._cache_hits, 1)) * 100
        
        return {
            "requests_made": self._requests_made,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "total_tokens": self._total_tokens,
            "api_errors": self._api_errors,
            "cached_embeddings": len(self._cache),
            "cache_memory_mb": self._estimate_cache_size()
        }
    
    def _estimate_cache_size(self) -> float:
        """Estimate cache memory usage in MB."""
        if not self._cache:
            return 0.0
        
        # Rough estimation: each float is 8 bytes, plus overhead
        total_floats = sum(len(entry.embedding) for entry in self._cache.values() if entry.embedding)
        bytes_used = total_floats * 8 + len(self._cache) * 100  # Overhead per entry
        return bytes_used / (1024 * 1024)
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self._cache.clear()
        logger.info("Embedding cache cleared")
    
    def cleanup_expired(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time - entry.created_at >= self.cache_ttl
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


# ========== CONVENIENCE FUNCTIONS ==========

def create_gemini_client(api_key: str, model: str = "text-embedding-004") -> GeminiEmbeddingClient:
    """Create a new Gemini embedding client."""
    return GeminiEmbeddingClient(api_key=api_key, model=model)


def calculate_semantic_similarity(text1: str, text2: str, client: GeminiEmbeddingClient) -> float:
    """Quick semantic similarity calculation between two texts."""
    return client.compare_texts(text1, text2)