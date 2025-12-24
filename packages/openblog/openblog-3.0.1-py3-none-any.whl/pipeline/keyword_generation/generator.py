"""Main orchestrator for keyword generation"""

import logging
import os
import time
from typing import Optional, List, Dict
from datetime import datetime, UTC

from pipeline.integrations.seranking import SEORankingAPIClient
from pipeline.integrations.seranking.gap_analyzer_wrapper import GapAnalyzerWrapper
from .ai_generator import AIKeywordGenerator
from .scorer import KeywordScorer
from .models import (
    KeywordGenerationResult,
    KeywordGenerationStatistics,
    CompanyInfo,
    KeywordGenerationConfig,
    Keyword,
    KeywordSource,
)
from .exceptions import AIGenerationError, GapAnalysisError, ScoringError

logger = logging.getLogger(__name__)


class KeywordGeneratorV2:
    """
    Hybrid keyword generator combining:
    - 50% AI-generated keywords
    - 50% SERanking gap analysis keywords
    - AI scoring layer for all

    Workflow:
    1. Generate 40 AI keywords (seed + optional long-tail)
    2. Generate 40 gap analysis keywords (from competitors)
    3. Combine and deduplicate
    4. Re-score all 80+ with AI
    5. Filter and return top N
    """

    def __init__(
        self,
        google_api_key: Optional[str] = None,
        seranking_api_key: Optional[str] = None,
        api_timeout: float = 120.0,  # Increased from 60.0 for scoring batches
        api_rate_limit_delay: float = 0.5,
        max_batch_size: int = 25,  # Reduced from 50 to prevent timeouts
    ):
        """
        Initialize generator with API keys
        
        Args:
            google_api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            seranking_api_key: SE Ranking API key (defaults to SERANKING_API_KEY env var)
            api_timeout: API call timeout in seconds (default: 60.0)
            api_rate_limit_delay: Delay between API calls in seconds (default: 0.5)
            max_batch_size: Maximum keywords per scoring batch (default: 50)
        """
        logger.info("Initializing KeywordGeneratorV2")

        # Read from environment if not provided
        if google_api_key is None:
            google_api_key = os.getenv("GOOGLE_API_KEY")
        if seranking_api_key is None:
            seranking_api_key = os.getenv("SERANKING_API_KEY")

        self.ai_generator = AIKeywordGenerator(
            google_api_key, 
            rate_limit_delay=api_rate_limit_delay,
            api_timeout=api_timeout
        )
        # SE Ranking client (optional - gap analysis will be skipped if not available)
        if seranking_api_key:
            try:
                self.seranking_client = SEORankingAPIClient(seranking_api_key)
            except ValueError:
                logger.warning("SE Ranking API key invalid or missing - gap analysis will be disabled")
                self.seranking_client = None
        else:
            self.seranking_client = None
            logger.info("SE Ranking API key not provided - gap analysis will be disabled")
        self.scorer = KeywordScorer(
            google_api_key,
            rate_limit_delay=api_rate_limit_delay,
            api_timeout=api_timeout,
            max_batch_size=max_batch_size
        )

    async def generate(
        self,
        company_info: CompanyInfo,
        config: Optional[KeywordGenerationConfig] = None,
    ) -> KeywordGenerationResult:
        """
        Generate keywords using hybrid approach

        Args:
            company_info: Company information
            config: Generation configuration

        Returns:
            Complete keyword generation result
        """
        start_time = time.time()

        if config is None:
            config = KeywordGenerationConfig()

        logger.info(f"Starting keyword generation for {company_info.name}")

        # Step 1: Generate AI keywords (async parallel)
        ai_keywords = await self._generate_ai_keywords_async(company_info, config)
        logger.info(f"Generated {len(ai_keywords)} AI keywords")

        # Step 2: Generate gap analysis keywords (can be parallelized later)
        gap_keywords = []
        if config.enable_gap_analysis:
            gap_keywords = self._generate_gap_keywords(company_info, config)
            logger.info(f"Generated {len(gap_keywords)} gap keywords")
        else:
            logger.info("Gap analysis disabled")

        # Step 3: Combine and deduplicate
        all_keywords = self._merge_keywords(ai_keywords, gap_keywords)
        logger.info(f"Combined {len(all_keywords)} keywords after deduplication")

        # Step 4: Score all keywords (async parallel)
        scored_keywords = await self._score_keywords_async(all_keywords, company_info, config)

        # Step 5: Filter and sort
        final_keywords = self._filter_and_sort(scored_keywords, config)

        # Step 6: Create result
        processing_time = time.time() - start_time

        # Convert dicts to Keyword objects
        keyword_objects = []
        for kw_dict in final_keywords:
            try:
                # Convert source string to KeywordSource enum if needed
                if "source" in kw_dict and isinstance(kw_dict["source"], str):
                    try:
                        kw_dict["source"] = KeywordSource(kw_dict["source"])
                    except ValueError:
                        # If source string doesn't match enum, default to AI_GENERATED
                        kw_dict["source"] = KeywordSource.AI_GENERATED
                        logger.warning(f"Invalid source '{kw_dict.get('source')}', defaulting to AI_GENERATED")
                
                keyword_objects.append(Keyword(**kw_dict))
            except Exception as e:
                logger.warning(f"Failed to create Keyword from {kw_dict}: {e}")
                continue

        result = KeywordGenerationResult(
            keywords=keyword_objects,
            company_name=company_info.name,
            company_url=company_info.url,
            location=company_info.target_location,
            generation_method="hybrid",
            timestamp=datetime.now(UTC),
        )

        # Set primary keyword
        if result.keywords:
            result.primary_keyword = result.keywords[0]

        # Calculate statistics
        result.statistics = self._calculate_statistics(result, processing_time)

        logger.info(f"Keyword generation complete in {processing_time:.1f}s")
        return result

    async def _generate_ai_keywords_async(
        self,
        company_info: CompanyInfo,
        config: KeywordGenerationConfig,
    ) -> List[Dict]:
        """Generate AI keywords (async with parallel batches)"""
        logger.info("Generating AI keywords (parallel)")

        try:
            keywords = await self.ai_generator.generate_seed_keywords_async(
                company_name=company_info.name,
                industry=company_info.industry,
                services=company_info.services,
                products=company_info.products,
                location=company_info.target_location,
                target_audience=company_info.target_audience,
                count=config.ai_keywords_count,
            )

            # Optional: Generate long-tail variants (can be parallelized later)
            if config.enable_long_tail_expansion and keywords:
                seed_terms = [kw["keyword"] for kw in keywords]
                longtail = self.ai_generator.generate_long_tail_variants(
                    seed_terms,
                    company_info.name,
                    config.long_tail_per_seed,
                )
                keywords.extend(longtail)

            # Deduplicate (use higher threshold to be less aggressive)
            keywords = self.ai_generator.deduplicate_keywords(keywords, similarity_threshold=0.95)

            return keywords

        except AIGenerationError as e:
            logger.error(f"AI generation error: {e}")
            if e.original_error:
                logger.debug(f"Original error: {e.original_error}", exc_info=True)
            return []  # Graceful degradation - return empty list
        except Exception as e:
            logger.error(f"Unexpected error generating AI keywords: {e}", exc_info=True)
            return []
    
    def _generate_ai_keywords(
        self,
        company_info: CompanyInfo,
        config: KeywordGenerationConfig,
    ) -> List[Dict]:
        """Generate AI keywords (sync fallback)"""
        import asyncio
        return asyncio.run(self._generate_ai_keywords_async(company_info, config))

    def _generate_gap_keywords(
        self,
        company_info: CompanyInfo,
        config: KeywordGenerationConfig,
    ) -> List[Dict]:
        """Generate gap analysis keywords"""
        # Check if SE Ranking client is available
        if not self.seranking_client:
            logger.info("SE Ranking client not available, skipping gap analysis")
            return []
        
        logger.info("Generating gap analysis keywords")

        try:
            # Test connection first
            if not self.seranking_client.test_connection():
                logger.warning("SE Ranking API connection failed, skipping gap analysis")
                return []

            # Extract domain
            domain = self.seranking_client.extract_domain(company_info.url)

            # Get competitors (manual or auto-detect)
            competitors = company_info.competitors if company_info.competitors else None

            # Analyze gaps
            gaps = self.seranking_client.analyze_content_gaps(
                domain=domain,
                competitors=competitors,
                source="us",
                max_competitors=config.max_competitors,
                filters={
                    "min_volume": config.gap_min_volume,
                    "max_volume": config.gap_max_volume,
                    "max_difficulty": config.gap_max_difficulty,
                    "max_competition": config.gap_max_competition,
                    "min_words": config.gap_min_words,
                },
            )

            # Convert gap keywords to standard format
            gap_keywords = GapAnalyzerWrapper.batch_convert_gaps(gaps)

            # Take top N by AEO score
            gap_keywords.sort(key=lambda kw: kw.get("aeo_score", 0), reverse=True)
            gap_keywords = gap_keywords[: config.gap_keywords_count]

            return gap_keywords

        except Exception as e:
            logger.error(f"Error generating gap keywords: {e}", exc_info=True)
            # Graceful degradation - continue without gap keywords
            return []

    def _merge_keywords(
        self,
        ai_keywords: List[Dict],
        gap_keywords: List[Dict],
    ) -> List[Dict]:
        """Merge and deduplicate keywords from both sources"""
        logger.info("Merging and deduplicating keywords")

        all_keywords = ai_keywords + gap_keywords

        # Deduplicate by keyword text
        seen = set()
        merged = []

        for kw in all_keywords:
            kw_text = kw.get("keyword", "").lower().strip()

            if kw_text not in seen:
                seen.add(kw_text)
                merged.append(kw)

        logger.info(f"Merged {len(all_keywords)} to {len(merged)} unique keywords")
        return merged

    async def _score_keywords_async(
        self,
        keywords: List[Dict],
        company_info: CompanyInfo,
        config: Optional[KeywordGenerationConfig] = None,
    ) -> List[Dict]:
        """Score all keywords with AI (async parallel)"""
        logger.info(f"Scoring {len(keywords)} keywords (parallel)")

        # Get batch size from config if available
        if config and hasattr(config, 'max_batch_size'):
            config_batch_size = config.max_batch_size
        else:
            config_batch_size = 50  # Default API-safe batch size
        batch_size = min(50, config_batch_size)
        
        return await self.scorer.score_keywords_async(
            keywords,
            company_name=company_info.name,
            company_description=company_info.description,
            services=company_info.services,
            products=company_info.products,
            target_audience=company_info.target_audience,
            batch_size=batch_size,
        )
    
    def _score_keywords(
        self,
        keywords: List[Dict],
        company_info: CompanyInfo,
        config: Optional[KeywordGenerationConfig] = None,
    ) -> List[Dict]:
        """Score all keywords with AI (sync fallback)"""
        import asyncio
        return asyncio.run(self._score_keywords_async(keywords, company_info, config))

    def _filter_and_sort(
        self,
        keywords: List[Dict],
        config: KeywordGenerationConfig,
    ) -> List[Dict]:
        """Filter by score and sort"""
        logger.info(f"Filtering keywords (min score: {config.min_score}, target: {config.target_count})")

        if not keywords:
            logger.warning("No keywords to filter")
            return []

        # Debug: log keyword sources before filtering
        if keywords:
            logger.debug(f"Sample keyword structure: {list(keywords[0].keys())}")
            logger.debug(f"Sample keyword score: {keywords[0].get('score', 'MISSING')}")
            sources = {}
            for kw in keywords:
                source = kw.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            logger.debug(f"Keywords by source before filtering: {sources}")

        # Filter by score and limit to target count
        filtered = KeywordScorer.filter_by_score(
            keywords,
            min_score=config.min_score,
            max_keywords=config.target_count,  # Limit to target count after filtering
        )

        # Debug: log keyword sources after filtering
        if filtered:
            sources_after = {}
            for kw in filtered:
                source = kw.get('source', 'unknown')
                sources_after[source] = sources_after.get(source, 0) + 1
            logger.debug(f"Keywords by source after filtering: {sources_after}")

        logger.info(f"Final keyword count: {len(filtered)} (from {len(keywords)} input, target: {config.target_count})")
        return filtered

    @staticmethod
    def _calculate_statistics(
        result: KeywordGenerationResult,
        processing_time: float,
    ) -> KeywordGenerationStatistics:
        """Calculate generation statistics"""
        if not result.keywords:
            return KeywordGenerationStatistics()

        # Count sources (handle both enum and string comparison)
        ai_count = sum(1 for kw in result.keywords if (
            kw.source == KeywordSource.AI_GENERATED or 
            kw.source == KeywordSource.AI_GENERATED.value or
            (isinstance(kw.source, str) and kw.source == "ai_generated")
        ))
        gap_count = sum(1 for kw in result.keywords if (
            kw.source == KeywordSource.GAP_ANALYSIS or 
            kw.source == KeywordSource.GAP_ANALYSIS.value or
            (isinstance(kw.source, str) and kw.source == "gap_analysis")
        ))

        # Calculate averages
        scores = [kw.score for kw in result.keywords if kw.score]
        aeo_scores = [kw.aeo_score for kw in result.keywords if kw.aeo_score]
        volumes = [kw.volume for kw in result.keywords if kw.volume]
        difficulties = [kw.difficulty for kw in result.keywords if kw.difficulty]

        # Intent breakdown
        intent_breakdown = {}
        for kw in result.keywords:
            intent = kw.intent.value if hasattr(kw.intent, "value") else str(kw.intent)
            intent_breakdown[intent] = intent_breakdown.get(intent, 0) + 1

        # AEO features
        with_aeo = sum(1 for kw in result.keywords if kw.has_aeo_features)
        questions = sum(1 for kw in result.keywords if kw.is_question)

        return KeywordGenerationStatistics(
            total_keywords=len(result.keywords),
            ai_keywords=ai_count,
            gap_keywords=gap_count,
            avg_score=sum(scores) / len(scores) if scores else 0,
            avg_aeo_score=sum(aeo_scores) / len(aeo_scores) if aeo_scores else None,
            avg_volume=int(sum(volumes) / len(volumes)) if volumes else None,
            avg_difficulty=sum(difficulties) / len(difficulties) if difficulties else None,
            intent_breakdown=intent_breakdown,
            with_aeo_features=with_aeo,
            question_keywords=questions,
            processing_time_seconds=processing_time,
        )
