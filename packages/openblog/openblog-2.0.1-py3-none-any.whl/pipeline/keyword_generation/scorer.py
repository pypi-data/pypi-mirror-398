"""AI-based keyword scoring using Gemini"""

import json
import logging
import time
import threading
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime, UTC

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
except ImportError:
    genai = None
    GenerationConfig = None

from .exceptions import ScoringError

logger = logging.getLogger(__name__)


class KeywordScorer:
    """
    Score keywords using AI based on company fit and AEO potential

    Scoring factors:
    - Company fit (~50 points):
      - Product/Service coverage
      - ICP/Use-case fit
      - Geo/Language fit
      - Positioning/Price image
      - Integration/Partners
    - AEO potential (~35 points):
      - Question format suitability
      - Featured snippet potential
      - Conversational phrasing
    - Compliance (~15 points):
      - Brand safety
      - Legal compliance
    """

    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = 0.5, api_timeout: float = 120.0, max_batch_size: int = 25):
        """
        Initialize scorer
        
        Args:
            api_key: Google API key (uses GOOGLE_API_KEY env var if not provided)
            rate_limit_delay: Delay between API calls in seconds (default: 0.5)
            api_timeout: API call timeout in seconds (default: 60.0)
            max_batch_size: Maximum keywords per batch (default: 50)
        """
        if genai is None:
            raise ImportError("google-generativeai not installed")

        import os
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError("Google API key not found")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-3-pro-preview")
        self.max_retries = 3
        self.retry_delay = 1.0  # Initial delay in seconds
        
        # Rate limiting, timeout, and batch size
        self._last_api_call_time = 0.0
        self._rate_limit_delay = rate_limit_delay
        self._api_timeout = api_timeout
        self._max_batch_size = max_batch_size
        self._rate_limit_lock = threading.Lock()  # Thread-safe rate limiting

    def score_keywords(
        self,
        keywords: List[Dict],
        company_name: str,
        company_description: Optional[str] = None,
        services: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        target_audience: Optional[str] = None,
        batch_size: int = 50,
    ) -> List[Dict]:
        """
        Score keywords based on company fit

        Args:
            keywords: List of keyword dictionaries
            company_name: Company name
            company_description: Company description
            services: List of services
            products: List of products
            target_audience: Target audience
            batch_size: Keywords per API call (50 is safe limit)

        Returns:
            Keywords with scores added
        """
        if not keywords:
            return []

        logger.info(f"Scoring {len(keywords)} keywords for {company_name}")

        # Score in batches (respect max_batch_size)
        scored = []
        effective_batch_size = min(batch_size, self._max_batch_size)
        for i in range(0, len(keywords), effective_batch_size):
            batch = keywords[i:i + effective_batch_size]
            batch_scores = self._score_batch(
                batch,
                company_name,
                company_description,
                services,
                products,
                target_audience,
            )
            scored.extend(batch_scores)

        # Sort by score
        scored.sort(key=lambda kw: kw.get("score", 0), reverse=True)

        logger.info(f"Scored {len(scored)} keywords")
        return scored
    
    async def score_keywords_async(
        self,
        keywords: List[Dict],
        company_name: str,
        company_description: Optional[str] = None,
        services: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        target_audience: Optional[str] = None,
        batch_size: int = 50,
    ) -> List[Dict]:
        """
        Async version with parallel batch scoring
        """
        if not keywords:
            return []

        logger.info(f"Scoring {len(keywords)} keywords for {company_name} (parallel)")

        # Split into batches
        effective_batch_size = min(batch_size, self._max_batch_size)
        batches = [
            keywords[i:i + effective_batch_size]
            for i in range(0, len(keywords), effective_batch_size)
        ]
        
        logger.info(f"Scoring {len(keywords)} keywords in {len(batches)} parallel batches")
        
        # Score batches in parallel
        batch_tasks = [
            self._score_batch_async(
                batch,
                company_name,
                company_description,
                services,
                products,
                target_audience,
            )
            for batch in batches
        ]
        
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Combine results with detailed logging
        scored = []
        successful_batches = 0
        failed_batches = 0
        
        for batch_num, result in enumerate(batch_results, 1):
            if isinstance(result, Exception):
                failed_batches += 1
                logger.error(f"❌ Scoring batch {batch_num} failed: {type(result).__name__}: {result}")
                # NO FALLBACK - Retry the entire batch
                # Extract keywords for this batch and retry
                batch_start = (batch_num - 1) * effective_batch_size
                batch_end = min(batch_start + effective_batch_size, len(keywords))
                batch_keywords = keywords[batch_start:batch_end]
                
                # Retry this batch with exponential backoff
                retry_success = False
                for retry_attempt in range(self.max_retries):
                    try:
                        logger.info(f"🔄 Retrying scoring batch {batch_num} (attempt {retry_attempt + 1}/{self.max_retries})")
                        await asyncio.sleep(2 ** retry_attempt)  # Exponential backoff
                        retry_result = await self._score_batch_async(
                            batch_keywords,
                            company_name,
                            company_description,
                            services,
                            products,
                            target_audience,
                        )
                        if retry_result:
                            scored.extend(retry_result)
                            retry_success = True
                            logger.info(f"✅ Retry successful for batch {batch_num}")
                            break
                    except Exception as retry_error:
                        logger.warning(f"Retry attempt {retry_attempt + 1} failed: {retry_error}")
                
                if not retry_success:
                    logger.error(f"❌ Batch {batch_num} failed after all retries - keywords will be excluded")
                    # Keywords without scores are excluded (no default scores)
            elif isinstance(result, list):
                if result:
                    successful_batches += 1
                    scored.extend(result)
                    logger.info(f"✅ Scoring batch {batch_num} scored {len(result)} keywords")
                else:
                    failed_batches += 1
                    logger.warning(f"⚠️  Scoring batch {batch_num} returned empty list")
            else:
                failed_batches += 1
                logger.error(f"❌ Scoring batch {batch_num} returned unexpected type: {type(result)}")
        
        logger.info(f"Scoring summary: {successful_batches} succeeded, {failed_batches} failed, {len(scored)} total scored")
        
        # Sort by score
        scored.sort(key=lambda kw: kw.get("score", 0), reverse=True)

        logger.info(f"Scored {len(scored)} keywords")
        return scored
    
    async def _score_batch_async(
        self,
        keywords: List[Dict],
        company_name: str,
        company_description: Optional[str],
        services: Optional[List[str]],
        products: Optional[List[str]],
        target_audience: Optional[str],
    ) -> List[Dict]:
        """Score a batch of keywords asynchronously"""
        # Build company context (same as sync version)
        context_parts = [f"Company: {company_name}"]
        if company_description:
            context_parts.append(f"Description: {company_description}")
        if services:
            context_parts.append(f"Services: {', '.join(services)}")
        if products:
            context_parts.append(f"Products: {', '.join(products)}")
        if target_audience:
            context_parts.append(f"Target Audience: {target_audience}")

        company_context = "\n".join(context_parts)
        keywords_text = "\n".join([f"- {kw['keyword']}" for kw in keywords])

        # Create scoring prompt (same as sync version)
        prompt = f"""Score these keywords for {company_name} on a 1-100 scale.

{company_context}

Keywords to score:
{keywords_text}

Scoring Criteria (Total 100 points):
A) Product/Service Coverage (0-20 points)
B) ICP/Use-Case Fit (0-15 points)
C) Search Intent Match (0-15 points)
D) AEO Potential (0-20 points)
E) Competition Level (0-15 points)
F) Business Value (0-15 points)

Return JSON array with objects: {{"keyword": "...", "score": 0-100, "reasoning": "..."}}"""

        for attempt in range(self.max_retries):
            try:
                # Rate limit (async-safe) - reduced for parallel batches
                await asyncio.sleep(0.1)  # Reduced from 0.5s for parallel processing
                
                config = GenerationConfig(temperature=0.3)
                
                # Run synchronous API call in thread pool for true concurrency
                # Use get_running_loop() with fallback for better compatibility
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No running loop, create new one (shouldn't happen in async context)
                    loop = asyncio.get_event_loop()
                
                # Wrap executor call with timeout
                executor_call = lambda: self.model.generate_content(prompt, generation_config=config)
                if self._api_timeout and self._api_timeout > 0:
                    response = await asyncio.wait_for(
                        loop.run_in_executor(None, executor_call),
                        timeout=self._api_timeout
                    )
                else:
                    response = await loop.run_in_executor(None, executor_call)
                
                response_text = response.text.strip()
                scores_data = self._parse_json_response(response_text)
                
                if scores_data and isinstance(scores_data, list):
                    # Map scores back to keywords
                    scored = []
                    score_map = {item.get("keyword", ""): item.get("score") for item in scores_data if isinstance(item, dict) and item.get("score") is not None}
                    
                    for kw in keywords:
                        kw_copy = dict(kw)
                        keyword_text = kw.get("keyword", "")
                        # Only use score if found in response, otherwise skip keyword
                        if keyword_text in score_map:
                            kw_copy["score"] = score_map[keyword_text]
                            scored.append(kw_copy)
                        else:
                            logger.warning(f"Keyword '{keyword_text}' not found in scoring response - excluding")
                    
                    return scored
                else:
                    raise ValueError("Failed to parse scores")
                    
            except asyncio.TimeoutError:
                logger.warning(f"Scoring attempt {attempt + 1}/{self.max_retries} timed out after {self._api_timeout}s")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue  # Retry
                else:
                    logger.error(f"Scoring timed out after {self.max_retries} attempts - raising exception")
                    raise ScoringError(f"Scoring batch timed out after {self.max_retries} attempts")
            except Exception as e:
                logger.warning(f"Scoring attempt {attempt + 1}/{self.max_retries} failed: {type(e).__name__}: {e}")
                if attempt < self.max_retries - 1:
                    retry_delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying scoring in {retry_delay:.1f}s...")
                    await asyncio.sleep(retry_delay)
                    continue  # Retry
                else:
                    logger.error(f"Scoring failed after {self.max_retries} attempts - raising exception")
                    import traceback
                    logger.debug(f"Scoring failure traceback:\n{traceback.format_exc()}")
                    raise ScoringError(f"Scoring batch failed after {self.max_retries} attempts: {e}") from e
        
        # Should never reach here, but just in case
        raise ScoringError("Scoring failed - all retries exhausted")

    def _score_batch(
        self,
        keywords: List[Dict],
        company_name: str,
        company_description: Optional[str],
        services: Optional[List[str]],
        products: Optional[List[str]],
        target_audience: Optional[str],
    ) -> List[Dict]:
        """Score a batch of keywords"""

        # Build company context
        context_parts = [f"Company: {company_name}"]

        if company_description:
            context_parts.append(f"Description: {company_description}")
        if services:
            context_parts.append(f"Services: {', '.join(services)}")
        if products:
            context_parts.append(f"Products: {', '.join(products)}")
        if target_audience:
            context_parts.append(f"Target Audience: {target_audience}")

        company_context = "\n".join(context_parts)

        # Build keyword list
        keywords_text = "\n".join([f"- {kw['keyword']}" for kw in keywords])

        # Create scoring prompt
        prompt = f"""Score these keywords for {company_name} on a 1-100 scale.

{company_context}

Keywords to score:
{keywords_text}

Scoring Criteria (Total 100 points):

A) Product/Service Coverage (0-20 points):
   - How directly does this keyword relate to the company's core offerings?
   - Is this a primary, secondary, or tangential keyword?

B) ICP/Use-Case Fit (0-15 points):
   - How relevant is this keyword to the target audience?
   - Does it match common use cases?

C) Geo/Language Fit (0-5 points):
   - Is this keyword relevant to the target location/language?

D) Positioning/Price Image (0-5 points):
   - Does this keyword match the company's market positioning?
   - Any premium/budget/enterprise alignment?

E) Integration/Partners (0-5 points):
   - Does this keyword relate to integrations or partner ecosystems?

F) AEO Potential (0-25 points):
   - How likely is this to appear in AI-generated answers?
   - Does it have question format potential?
   - Does it support featured snippets?
   - Is it conversational and natural?

G) Brand/Legal Safety (0 to -15 points):
   - Any brand safety concerns?
   - Any compliance/legal red flags?
   - Apply penalties only if there are issues

Return a JSON array with format:
[
  {{
    "keyword": "exact keyword from list",
    "score": 1-100,
    "reasoning": "brief explanation of score"
  }}
]

Response ONLY with valid JSON, no other text."""

        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Enforce rate limiting before API call
                self._rate_limit()
                
                config = GenerationConfig(temperature=0.3)
                response = self.model.generate_content(prompt, generation_config=config)
                response_text = response.text.strip()

                # Parse response
                scores_data = self._parse_json_response(response_text)

                if not scores_data:
                    logger.warning("Failed to parse scores, retrying...")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    logger.error("Failed to parse scores after retries - raising exception")
                    raise ScoringError("Failed to parse scores after all retries")

                # Map scores back to keywords - only include keywords with valid scores
                score_map = {item["keyword"]: item["score"] for item in scores_data if isinstance(item, dict) and item.get("score") is not None}

                scored_keywords = []
                for kw in keywords:
                    keyword_text = kw.get("keyword", "")
                    if keyword_text in score_map:
                        kw_copy = kw.copy()
                        kw_copy["score"] = score_map[keyword_text]
                        scored_keywords.append(kw_copy)
                    else:
                        logger.warning(f"Keyword '{keyword_text}' not found in scoring response - excluding")

                if not scored_keywords:
                    raise ScoringError(f"No keywords were successfully scored from batch")
                
                return scored_keywords

            except Exception as e:
                last_error = e
                logger.warning(f"Error scoring batch (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Failed to score keywords after {self.max_retries} attempts - raising exception")
                    raise ScoringError(f"Scoring batch failed after {self.max_retries} attempts: {e}") from e
        
        # Should never reach here, but just in case
        raise ScoringError("Scoring failed - all retries exhausted")

    def _rate_limit(self):
        """Enforce rate limiting between API calls (thread-safe)"""
        with self._rate_limit_lock:
            current_time = time.time()
            time_since_last_call = current_time - self._last_api_call_time
            
            if time_since_last_call < self._rate_limit_delay:
                sleep_time = self._rate_limit_delay - time_since_last_call
                time.sleep(sleep_time)
            
            self._last_api_call_time = time.time()

    # Removed _default_score_batch - no default scores allowed
    # All keywords must be scored by AI with retries until success
    # This ensures consistency with async flow which raises ScoringError on failure

    @staticmethod
    def _parse_json_response(response_text: str) -> Optional[List[Dict]]:
        """Parse JSON response"""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                return None

            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response")
                return None

    @staticmethod
    def filter_by_score(
        keywords: List[Dict],
        min_score: int = 40,
        max_keywords: Optional[int] = None,
    ) -> List[Dict]:
        """Filter keywords by score"""
        filtered = [kw for kw in keywords if kw.get("score", 0) >= min_score]

        if max_keywords:
            filtered = filtered[:max_keywords]

        logger.info(f"Filtered to {len(filtered)} keywords (min score: {min_score})")
        return filtered
