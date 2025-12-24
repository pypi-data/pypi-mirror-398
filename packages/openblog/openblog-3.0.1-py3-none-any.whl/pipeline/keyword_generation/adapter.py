"""Adapter to integrate Keyword Generation V2 with blog-writer system"""

import asyncio
import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse

from .generator import KeywordGeneratorV2
from .models import CompanyInfo, KeywordGenerationConfig, KeywordGenerationResult

logger = logging.getLogger(__name__)


class KeywordV2Adapter:
    """
    Adapter to convert Keyword Generation V2 output to blog-writer format
    
    Bridges async V2 interface with sync blog-writer interface
    """
    
    def __init__(self, google_api_key: Optional[str] = None, seranking_api_key: Optional[str] = None):
        """
        Initialize adapter
        
        Args:
            google_api_key: Google API key (uses GOOGLE_API_KEY env var if not provided)
            seranking_api_key: SE Ranking API key (uses SERANKING_API_KEY env var if not provided)
        """
        self.generator = KeywordGeneratorV2(google_api_key, seranking_api_key)
    
    def generate_for_blog_writer(
        self,
        company_name: str,
        domain: str,
        location: Optional[str] = None,
        keyword_count: int = 80,
        cluster_count: int = 6,
        min_score: int = 40,
        **kwargs
    ) -> Dict:
        """
        Generate keywords in blog-writer format (sync wrapper)
        
        Validates inputs before processing.
        
        Args:
            company_name: Company name (required, max 200 chars)
            domain: Company website domain (required, must be valid format)
            location: Company location/country (optional)
            keyword_count: Target number of keywords (1-500, default: 80)
            cluster_count: Number of clusters to create (1-20, default: 6)
            min_score: Minimum keyword score threshold (0-100, default: 40)
            **kwargs: Additional arguments (ignored for compatibility)
        
        Returns:
            Dict matching KeywordResearchOutput schema
        """
        # Validate inputs
        if not isinstance(company_name, str) or not company_name.strip():
            raise ValueError("company_name must be a non-empty string")
        
        if not isinstance(domain, str) or not domain.strip():
            raise ValueError("domain must be a non-empty string")
        
        if not isinstance(keyword_count, int) or keyword_count < 1 or keyword_count > 500:
            raise ValueError("keyword_count must be between 1 and 500")
        
        if not isinstance(cluster_count, int) or cluster_count < 1 or cluster_count > 20:
            raise ValueError("cluster_count must be between 1 and 20")
        
        if not isinstance(min_score, int) or min_score < 0 or min_score > 100:
            raise ValueError("min_score must be between 0 and 100")
        """
        Generate keywords in blog-writer format (sync wrapper)
        
        This method matches the signature of KeywordResearchGenerator.generate_keyword_research()
        but uses Keyword Generation V2 internally.
        
        Args:
            company_name: Company name
            domain: Company website domain
            location: Company location/country
            keyword_count: Target number of keywords
            cluster_count: Number of clusters to create (used for simple clustering)
            min_score: Minimum keyword score threshold
            **kwargs: Additional arguments (ignored for compatibility)
        
        Returns:
            Dict matching KeywordResearchOutput schema:
            {
                "company_info": {...},
                "keywords": [{"keyword": str, "score": int, "cluster": str, "intent": str, ...}],
                "clusters": [str, ...],
                "clusters_with_keywords": {cluster_name: [keywords...]},
                "statistics": {...}
            }
        
        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If called from async context (use generate_for_blog_writer_async instead)
        """
        # Use asyncio.run() for sync contexts - handles event loop correctly
        # This works whether called from sync or async contexts
        try:
            # Check if we're already in an async context
            loop = asyncio.get_running_loop()
            # If we're in an async context, we can't use run_until_complete
            # User should use generate_for_blog_writer_async instead
            raise RuntimeError(
                "Cannot call generate_for_blog_writer() from async context. "
                "Use generate_for_blog_writer_async() instead or await the async method directly."
            )
        except RuntimeError as e:
            # Check if this is our error (raised by get_running_loop check)
            # get_running_loop() raises RuntimeError("no running event loop") if no loop
            # We raise RuntimeError("Cannot call...") if loop exists
            error_msg = str(e)
            if "async context" in error_msg or "Cannot call" in error_msg:
                raise  # Re-raise our custom error
            # No running loop - safe to use asyncio.run()
            # This handles the RuntimeError("no running event loop") case
            return asyncio.run(
                self._generate_async(
                    company_name=company_name,
                    domain=domain,
                    location=location,
                    keyword_count=keyword_count,
                    cluster_count=cluster_count,
                    min_score=min_score,
                )
            )
    
    async def generate_for_blog_writer_async(
        self,
        company_name: str,
        domain: str,
        location: Optional[str] = None,
        keyword_count: int = 80,
        cluster_count: int = 6,
        min_score: int = 40,
    ) -> Dict:
        """
        Generate keywords in blog-writer format (async version)
        
        Use this method when calling from async contexts (FastAPI, etc.)
        
        Args:
            company_name: Company name (required, max 200 chars)
            domain: Company website domain (required, must be valid format)
            location: Company location/country (optional)
            keyword_count: Target number of keywords (1-500, default: 80)
            cluster_count: Number of clusters to create (1-20, default: 6)
            min_score: Minimum keyword score threshold (0-100, default: 40)
        
        Returns:
            Dict matching KeywordResearchOutput schema
        
        Raises:
            ValueError: If inputs are invalid
        """
        # Validate inputs (same as sync version)
        if not isinstance(company_name, str) or not company_name.strip():
            raise ValueError("company_name must be a non-empty string")
        
        if not isinstance(domain, str) or not domain.strip():
            raise ValueError("domain must be a non-empty string")
        
        if not isinstance(keyword_count, int) or keyword_count < 1 or keyword_count > 500:
            raise ValueError("keyword_count must be between 1 and 500")
        
        if not isinstance(cluster_count, int) or cluster_count < 1 or cluster_count > 20:
            raise ValueError("cluster_count must be between 1 and 20")
        
        if not isinstance(min_score, int) or min_score < 0 or min_score > 100:
            raise ValueError("min_score must be between 0 and 100")
        
        return await self._generate_async(
            company_name=company_name,
            domain=domain,
            location=location,
            keyword_count=keyword_count,
            cluster_count=cluster_count,
            min_score=min_score,
        )
    
    async def _generate_async(
        self,
        company_name: str,
        domain: str,
        location: Optional[str] = None,
        keyword_count: int = 80,
        cluster_count: int = 6,
        min_score: int = 40,
    ) -> Dict:
        """Async generation method"""
        
        # Validate and sanitize inputs
        if not company_name or not company_name.strip():
            raise ValueError("company_name cannot be empty")
        
        if not domain or not domain.strip():
            raise ValueError("domain cannot be empty")
        
        # Sanitize company name (remove dangerous characters)
        company_name = company_name.strip()[:200]  # Limit length
        
        # Extract domain from URL if needed
        domain = domain.strip()
        if not domain:
            raise ValueError("domain cannot be empty")
        
        # Handle URL parsing edge cases
        if domain.startswith('http://') or domain.startswith('https://'):
            parsed_url = urlparse(domain)
            clean_domain = parsed_url.netloc or parsed_url.path.split('/')[0]
        else:
            # Simple domain format - remove path and port if present
            clean_domain = domain.split('/')[0].split(':')[0]
        
        # Validate domain format (basic check - must have at least one dot)
        if not clean_domain:
            raise ValueError("domain cannot be empty after parsing")
        
        if '.' not in clean_domain:
            raise ValueError(f"Invalid domain format: '{clean_domain}' (must contain at least one dot)")
        
        # Limit domain length (RFC 1035 max domain length is 253 chars)
        if len(clean_domain) > 253:
            raise ValueError(f"Domain too long: {len(clean_domain)} characters (max 253)")
        
        clean_domain = clean_domain[:253]
        
        # Convert to CompanyInfo
        company = CompanyInfo(
            name=company_name,
            url=clean_domain,
            target_location=location,
        )
        
        # Configure generation
        # Generate ~3x target count to account for:
        # 1. Filtering losses (min_score threshold)
        # 2. AI model not always generating exact requested count
        # Target count is AFTER filtering, so we need more raw keywords
        generation_multiplier = 2.5  # Balance between getting enough keywords and API efficiency
        ai_count = int(keyword_count * generation_multiplier // 2)
        gap_count = int(keyword_count * generation_multiplier // 2)
        
        config = KeywordGenerationConfig(
            target_count=keyword_count,  # This is the final target AFTER filtering
            ai_keywords_count=ai_count,  # Generate 2x to account for filtering
            gap_keywords_count=gap_count,  # Generate 2x to account for filtering
            min_score=min_score,
            enable_clustering=False,  # We'll do simple clustering ourselves
            enable_long_tail_expansion=True,  # Enable long-tail variants for more keywords
            long_tail_per_seed=2,  # Generate 2 long-tail variants per seed keyword
        )
        
        # Generate keywords
        try:
            result = await self.generator.generate(company, config)
        except Exception as e:
            logger.error(f"Keyword generation failed: {e}", exc_info=True)
            # Return empty result on failure
            return self._empty_result(company_name, clean_domain, location)
        
        # Convert to blog-writer format
        return self._convert_to_blog_writer_format(result, company_name, clean_domain, location, cluster_count)
    
    def _convert_to_blog_writer_format(
        self,
        result: KeywordGenerationResult,
        company_name: str,
        domain: str,
        location: Optional[str],
        cluster_count: int,
    ) -> Dict:
        """Convert V2 result to blog-writer format"""
        
        # Simple clustering by intent (can be enhanced later)
        clusters = self._create_simple_clusters(result.keywords, cluster_count)
        
        # Convert keywords to KeywordItem format
        keyword_items = []
        clusters_with_keywords = {}
        
        for kw in result.keywords:
            # Assign cluster based on intent
            cluster_name = self._assign_cluster(kw, clusters)
            
            # Get source value (ai_generated or gap_analysis)
            source_value = kw.source.value if hasattr(kw.source, 'value') else str(kw.source).lower()
            
            keyword_item = {
                "keyword": kw.keyword,
                "score": kw.score,
                "cluster": cluster_name,
                "intent": kw.intent.value.title() if hasattr(kw.intent, 'value') else str(kw.intent).title(),
                "source": source_value,  # Add source label
                "search_volume": kw.volume,
                "difficulty": kw.difficulty,
                "trend": None,  # V2 doesn't provide trend data
            }
            keyword_items.append(keyword_item)
            
            # Add to cluster grouping
            if cluster_name not in clusters_with_keywords:
                clusters_with_keywords[cluster_name] = []
            clusters_with_keywords[cluster_name].append({
                "keyword": kw.keyword,
                "score": kw.score,
                "intent": keyword_item["intent"],
                "source": source_value,  # Include source in cluster grouping too
            })
        
        # Create company_info dict
        company_info = {
            "company_name": company_name,
            "domain": domain,
            "description": None,  # V2 doesn't research company description
            "location": location,
        }
        
        # Create statistics dict
        statistics = {
            "total_keywords": result.statistics.total_keywords,
            "ai_keywords": result.statistics.ai_keywords,
            "gap_keywords": result.statistics.gap_keywords,
            "scored_keywords": result.statistics.total_keywords,
            "filtered_keywords": len([k for k in result.keywords if k.score >= result.statistics.avg_score]),
            "clusters_count": len(clusters),
            "average_cpc": "unknown",  # V2 doesn't provide CPC
            "processing_time_seconds": result.statistics.processing_time_seconds,
        }
        
        return {
            "company_info": company_info,
            "keywords": keyword_items,
            "clusters": clusters,
            "clusters_with_keywords": clusters_with_keywords,
            "statistics": statistics,
        }
    
    def _create_simple_clusters(self, keywords: List, cluster_count: int) -> List[str]:
        """Create simple clusters based on intent"""
        
        # Count intents
        intent_counts = {}
        for kw in keywords:
            intent = kw.intent.value if hasattr(kw.intent, 'value') else str(kw.intent)
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        # Sort by frequency
        sorted_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Create cluster names
        cluster_names = []
        intent_to_cluster = {
            "question": "Questions & How-To",
            "informational": "Informational Content",
            "commercial": "Commercial Intent",
            "transactional": "Transactional Keywords",
            "navigational": "Brand & Navigation",
        }
        
        for intent, count in sorted_intents[:cluster_count]:
            cluster_name = intent_to_cluster.get(intent, intent.title())
            if cluster_name not in cluster_names:
                cluster_names.append(cluster_name)
        
        # Fill remaining slots with generic names
        generic_names = ["General Topics", "Related Keywords", "Additional Terms"]
        for name in generic_names:
            if len(cluster_names) < cluster_count and name not in cluster_names:
                cluster_names.append(name)
        
        return cluster_names[:cluster_count]
    
    def _assign_cluster(self, keyword, clusters: List[str]) -> str:
        """Assign keyword to a cluster"""
        
        intent = keyword.intent.value if hasattr(keyword.intent, 'value') else str(keyword.intent)
        
        intent_to_cluster = {
            "question": "Questions & How-To",
            "informational": "Informational Content",
            "commercial": "Commercial Intent",
            "transactional": "Transactional Keywords",
            "navigational": "Brand & Navigation",
        }
        
        preferred_cluster = intent_to_cluster.get(intent, "General Topics")
        
        # Return preferred cluster if it exists, otherwise first cluster
        if preferred_cluster in clusters:
            return preferred_cluster
        return clusters[0] if clusters else "General Topics"
    
    def _empty_result(self, company_name: str, domain: str, location: Optional[str]) -> Dict:
        """Return empty result on failure"""
        return {
            "company_info": {
                "company_name": company_name,
                "domain": domain,
                "description": None,
                "location": location,
            },
            "keywords": [],
            "clusters": [],
            "clusters_with_keywords": {},
            "statistics": {
                "total_keywords": 0,
                "scored_keywords": 0,
                "filtered_keywords": 0,
                "clusters_count": 0,
                "average_cpc": "unknown",
                "processing_time_seconds": 0,
            },
        }

