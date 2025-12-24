"""AI-based keyword generation using Gemini"""

import json
import logging
import time
import threading
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, UTC

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
except ImportError:
    genai = None
    GenerationConfig = None

from .models import Keyword, KeywordSource, IntentType
from .exceptions import AIGenerationError

logger = logging.getLogger(__name__)


class AIKeywordGenerator:
    """
    Generate keywords using Gemini AI

    Generates:
    - Initial seed keywords (100% AI)
    - Optional long-tail expansions (2-3 per seed)
    """

    def __init__(self, api_key: Optional[str] = None, rate_limit_delay: float = 0.5, api_timeout: float = 60.0):
        """
        Initialize AI generator

        Args:
            api_key: Google API key (uses GOOGLE_API_KEY env var if not provided)
            rate_limit_delay: Delay between API calls in seconds (default: 0.5)
            api_timeout: API call timeout in seconds (default: 60.0)
        """
        if genai is None:
            raise ImportError("google-generativeai not installed. Install with: pip install google-generativeai")

        import os
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError(
                "Google API key not found. "
                "Set GOOGLE_API_KEY environment variable."
            )

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-3-pro-preview")
        self.max_retries = 3
        self.retry_delay = 1.0  # Initial delay in seconds
        
        # Rate limiting and timeout
        self._last_api_call_time = 0.0
        self._rate_limit_delay = rate_limit_delay
        self._api_timeout = api_timeout
        self._rate_limit_lock = threading.Lock()  # Thread-safe rate limiting

    def generate_seed_keywords(
        self,
        company_name: str,
        industry: Optional[str] = None,
        services: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        location: Optional[str] = None,
        target_audience: Optional[str] = None,
        count: int = 40,
    ) -> List[Dict]:
        """
        Generate seed keywords using AI

        Args:
            company_name: Company name
            industry: Industry category
            services: List of services
            products: List of products
            location: Target location
            target_audience: Target audience description
            count: Number of keywords to generate

        Returns:
            List of keyword dictionaries
        """
        logger.info(f"Generating {count} seed keywords for {company_name}")

        # Build company context
        context_parts = [f"Company: {company_name}"]

        if industry:
            context_parts.append(f"Industry: {industry}")
        if services:
            context_parts.append(f"Services: {', '.join(services)}")
        if products:
            context_parts.append(f"Products: {', '.join(products)}")
        if location:
            context_parts.append(f"Location: {location}")
        if target_audience:
            context_parts.append(f"Target Audience: {target_audience}")

        company_context = "\n".join(context_parts)

        # Create prompt with AEO pattern prioritization
        # Target ~40-50% AEO patterns, rest regular keywords
        aeo_count = max(1, int(count * 0.45))  # ~45% AEO patterns
        regular_count = count - aeo_count
        
        # Create JSON schema for structured output
        # Note: Gemini's response_schema doesn't support minItems/maxItems, so we rely on prompt clarity
        keyword_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "The keyword term (1-7 words)"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["short-tail", "long-tail"],
                        "description": "Keyword type: 'short-tail' (1-2 words) or 'long-tail' (3+ words)"
                    },
                    "intent": {
                        "type": "string",
                        "enum": ["informational", "commercial", "transactional", "question"],
                        "description": "Search intent type"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Brief explanation why this keyword is relevant"
                    },
                    "has_aeo_features": {
                        "type": "boolean",
                        "description": "True if the keyword is AEO-optimized (question-based, comparison, best-of lists)"
                    }
                },
                "required": ["keyword", "type", "intent", "notes", "has_aeo_features"]
            }
        }
        
        prompt = f"""Generate exactly {count} relevant keywords for this company.

{company_context}

CRITICAL REQUIREMENT: You MUST return exactly {count} keywords in the JSON array. No more, no less. Count them carefully.

The JSON array must contain exactly {count} objects. Each object must have: keyword, type, intent, notes, has_aeo_features.

HIGH PRIORITY - AEO-Optimizing Patterns (~{aeo_count} keywords):
Generate keywords following these Answer Engine Optimization (AEO) patterns that work well for featured snippets:
1. "Best [PRODUCT/SERVICE] for [SPECIFIC ICP] in [REGION]"
   Example: "Best AI consulting for SaaS companies in Germany"
2. "Top rated [PRODUCT CATEGORY] providers for [USE CASE]"
   Example: "Top rated cloud storage providers for GDPR-compliant data archiving"
3. "Which [PRODUCT] is the best alternative to [COMPETITOR]?"
   Example: "Best alternative to traditional consulting for AI strategy"
4. "What is the most reliable [PRODUCT] for [PROBLEM]?"
   Example: "Most reliable AI solutions for business process automation"
5. "Best [PRODUCT] with strong [FEATURE] in [REGION]"
   Example: "Best AI consulting with strong data analytics in DACH"
6. "Who are the leading providers of [NICHE CATEGORY]?"
   Example: "Leading providers of AI-powered business transformation"
7. "Best [SERVICE] for companies in [INDUSTRY] facing [PAIN POINT]"
   Example: "Best AI consulting for tech companies facing scaling challenges"
8. "Which [CATEGORY] vendors support [STANDARD/COMPLIANCE]?"
   Example: "Which AI consulting firms support GDPR compliance"
9. "Best [PRODUCT TYPE] for teams with [SPECIFIC WORKFLOW]"
   Example: "Best AI tools for teams managing multi-channel operations"
10. "Who offers the highest performance [PRODUCT] for [REGION] users?"
    Example: "Fastest AI solutions for European customers"
11. "Best budget-friendly [PRODUCT] that still offers [FEATURE]"
    Example: "Best budget-friendly AI consulting that still offers enterprise features"
12. "Top [PRODUCT CATEGORY] tools recommended for [ICP] in [YEAR]"
    Example: "Top AI consulting services recommended for startups in 2025"
13. "Best [SERVICE PROVIDER] for companies scaling to [REGION]"
    Example: "Best AI consulting for SaaS companies expanding into Europe"
14. "Which [CATEGORY] solution has the strongest [FEATURE] compared to [COMPETITOR]?"
    Example: "Which AI consulting has stronger data analytics than traditional firms"
15. "What is the best [PRODUCT] if I need [VERY SPECIFIC REQUIREMENT]?"
    Example: "Best AI consulting if I need rapid digital transformation"

REGULAR KEYWORDS (~{regular_count} keywords):
- Each keyword should be 1-7 words long
- Focus on business-relevant, high-intent keywords
- Mix of short-tail and long-tail keywords
- Include question-based keywords where relevant
- Avoid brand names and competitor names

Return exactly {count} keywords in the specified JSON format."""

        # Split into batches if count is large to avoid truncation
        # Generate in batches of 10 to ensure complete responses (smaller = more reliable)
        batch_size = 10
        all_keywords = []
        
        if count <= batch_size:
            # Single batch
            batches = [(count, aeo_count, regular_count)]
        else:
            # Multiple batches
            num_batches = (count + batch_size - 1) // batch_size
            batches = []
            remaining_aeo = aeo_count
            remaining_regular = regular_count
            
            for i in range(num_batches):
                batch_count = min(batch_size, count - len(all_keywords))
                batch_aeo = max(0, min(remaining_aeo, int(batch_count * 0.45)))
                batch_regular = batch_count - batch_aeo
                batches.append((batch_count, batch_aeo, batch_regular))
                remaining_aeo -= batch_aeo
                remaining_regular -= batch_regular
        
        logger.info(f"Generating {count} keywords in {len(batches)} batch(es)")
        
        # Generate batches sequentially (will be parallelized in async version)
        for batch_num, (batch_count, batch_aeo, batch_regular) in enumerate(batches, 1):
            logger.info(f"Batch {batch_num}/{len(batches)}: Generating {batch_count} keywords ({batch_aeo} AEO, {batch_regular} regular)")
            
            # Create batch-specific prompt (shorter to avoid truncation)
            batch_prompt = f"""Generate exactly {batch_count} keywords for this company.

{company_context}

Return exactly {batch_count} keywords as JSON array. Each object: keyword (string), type ("short-tail" or "long-tail"), intent ("informational", "commercial", "transactional", "question"), notes (string), has_aeo_features (boolean).

AEO patterns (~{batch_aeo}): "Best [PRODUCT] for [ICP]", "Which [PRODUCT] vendors support [STANDARD]?"
Regular (~{batch_regular}): Business keywords, 1-7 words."""

            # Retry logic with exponential backoff
            batch_keywords = []
            for attempt in range(self.max_retries):
                try:
                    self._rate_limit()
                    
                    # Use structured output
                    try:
                        config = GenerationConfig(
                            temperature=0.7,
                            response_mime_type="application/json",
                            response_schema=keyword_schema,
                            max_output_tokens=4096,  # Smaller batches = smaller token limit needed
                        )
                        response = self.model.generate_content(batch_prompt, generation_config=config)
                        response_text = response.text.strip()
                        keywords_data = json.loads(response_text)
                        
                        if isinstance(keywords_data, list):
                            logger.info(f"✅ Batch {batch_num}: Got {len(keywords_data)} keywords")
                            batch_keywords = keywords_data
                            break
                        else:
                            raise ValueError(f"Expected list, got {type(keywords_data)}")
                            
                    except Exception as e:
                        logger.warning(f"Batch {batch_num} structured output failed: {e}, trying fallback")
                        # Fallback
                        config = GenerationConfig(temperature=0.7, max_output_tokens=4096)
                        response = self.model.generate_content(batch_prompt, generation_config=config)
                        response_text = response.text.strip()
                        keywords_data = self._parse_json_response(response_text)
                        if keywords_data and isinstance(keywords_data, list):
                            logger.info(f"✅ Batch {batch_num} fallback: Got {len(keywords_data)} keywords")
                            batch_keywords = keywords_data
                            break
                        raise
                        
                except Exception as e:
                    logger.warning(f"Batch {batch_num} attempt {attempt + 1} failed: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))
                    else:
                        logger.error(f"Batch {batch_num} failed after {self.max_retries} attempts")
            
            # Convert batch keywords to dict format
            for kw_data in batch_keywords:
                if isinstance(kw_data, dict):
                    kw_dict = {
                        "keyword": kw_data.get("keyword", "").strip(),
                        "score": 0,
                        "source": KeywordSource.AI_GENERATED.value,
                        "intent": kw_data.get("intent", "informational").lower(),
                        "word_count": len(kw_data.get("keyword", "").split()),
                        "is_question": kw_data.get("intent", "").lower() == "question",
                        "notes": kw_data.get("notes", ""),
                        "created_at": datetime.now(UTC),
                        "updated_at": datetime.now(UTC),
                    }
                    if kw_dict["keyword"]:
                        all_keywords.append(kw_dict)
        
        logger.info(f"Generated {len(all_keywords)} total seed keywords (requested {count})")
        
        # Trim to exact count if needed
        if len(all_keywords) > count:
            all_keywords = all_keywords[:count]
        
        return all_keywords
    
    async def generate_seed_keywords_async(
        self,
        company_name: str,
        industry: Optional[str] = None,
        services: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        location: Optional[str] = None,
        target_audience: Optional[str] = None,
        count: int = 40,
    ) -> List[Dict]:
        """
        Async version with parallel batch processing
        """
        # Build company context
        context_parts = [f"Company: {company_name}"]
        if industry:
            context_parts.append(f"Industry: {industry}")
        if services:
            context_parts.append(f"Services: {', '.join(services)}")
        if products:
            context_parts.append(f"Products: {', '.join(products)}")
        if location:
            context_parts.append(f"Location: {location}")
        if target_audience:
            context_parts.append(f"Target Audience: {target_audience}")

        company_context = "\n".join(context_parts)

        # Create prompt with AEO pattern prioritization
        aeo_count = max(1, int(count * 0.45))
        regular_count = count - aeo_count
        
        # Create JSON schema
        keyword_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "The keyword term (1-7 words)"},
                    "type": {"type": "string", "enum": ["short-tail", "long-tail"]},
                    "intent": {"type": "string", "enum": ["informational", "commercial", "transactional", "question"]},
                    "notes": {"type": "string", "description": "Brief explanation"},
                    "has_aeo_features": {"type": "boolean", "description": "True if AEO-optimized"}
                },
                "required": ["keyword", "type", "intent", "notes", "has_aeo_features"]
            }
        }
        
        # Split into batches (reduced size for better reliability)
        batch_size = 8  # Reduced from 10 for better reliability
        if count <= batch_size:
            batches = [(count, aeo_count, regular_count)]
        else:
            num_batches = (count + batch_size - 1) // batch_size
            batches = []
            remaining_aeo = aeo_count
            remaining_regular = regular_count
            remaining_count = count
            
            for i in range(num_batches):
                # Calculate batch count properly
                batch_count = min(batch_size, remaining_count)
                batch_aeo = max(0, min(remaining_aeo, int(batch_count * 0.45)))
                batch_regular = batch_count - batch_aeo
                batches.append((batch_count, batch_aeo, batch_regular))
                remaining_aeo -= batch_aeo
                remaining_regular -= batch_regular
                remaining_count -= batch_count
        
        logger.info(f"🔵 Creating {len(batches)} parallel batches for {count} keywords")
        for batch_num, (batch_count, batch_aeo, batch_regular) in enumerate(batches, 1):
            logger.info(f"  Batch {batch_num}: {batch_count} keywords ({batch_aeo} AEO, {batch_regular} regular)")
        
        # Generate batches in parallel
        logger.info(f"🚀 Starting parallel execution of {len(batches)} batches...")
        batch_tasks = [
            self._generate_batch_async(
                batch_num, batch_count, batch_aeo, batch_regular,
                company_context, keyword_schema
            )
            for batch_num, (batch_count, batch_aeo, batch_regular) in enumerate(batches, 1)
        ]
        
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        logger.info(f"✅ All {len(batches)} batches completed (gathered results)")
        
        # Combine results with detailed logging
        all_keywords = []
        successful_batches = 0
        failed_batches = 0
        
        for batch_num, result in enumerate(batch_results, 1):
            if isinstance(result, Exception):
                failed_batches += 1
                logger.error(f"❌ Batch {batch_num} failed with exception: {type(result).__name__}: {result}", exc_info=result)
                continue
            if isinstance(result, list):
                if result:
                    successful_batches += 1
                    all_keywords.extend(result)
                    logger.info(f"✅ Batch {batch_num} contributed {len(result)} keywords")
                else:
                    failed_batches += 1
                    logger.warning(f"⚠️  Batch {batch_num} returned empty list")
            else:
                failed_batches += 1
                logger.error(f"❌ Batch {batch_num} returned unexpected type: {type(result)}")
        
        logger.info(f"Batch summary: {successful_batches} succeeded, {failed_batches} failed, {len(all_keywords)} total keywords (requested {count})")
        
        if len(all_keywords) > count:
            all_keywords = all_keywords[:count]
        
        return all_keywords
    
    async def _generate_batch_async(
        self,
        batch_num: int,
        batch_count: int,
        batch_aeo: int,
        batch_regular: int,
        company_context: str,
        keyword_schema: Dict,
    ) -> List[Dict]:
        """Generate a single batch asynchronously"""
        batch_prompt = f"""Generate exactly {batch_count} keywords for this company.

{company_context}

Return exactly {batch_count} keywords as JSON array. Each object: keyword (string), type ("short-tail" or "long-tail"), intent ("informational", "commercial", "transactional", "question"), notes (string), has_aeo_features (boolean).

AEO patterns (~{batch_aeo}): "Best [PRODUCT] for [ICP]", "Which [PRODUCT] vendors support [STANDARD]?"
Regular (~{batch_regular}): Business keywords, 1-7 words."""

        for attempt in range(self.max_retries):
            try:
                # Rate limit (async-safe) - reduced for parallel batches
                await asyncio.sleep(0.1)  # Reduced from 0.5s for parallel processing
                
                # Use regular generation (skip structured output for speed)
                config = GenerationConfig(temperature=0.7, max_output_tokens=4096)
                
                # Run synchronous API call in thread pool for true concurrency
                # Use get_running_loop() with fallback for better compatibility
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No running loop, create new one (shouldn't happen in async context)
                    loop = asyncio.get_event_loop()
                
                # Wrap executor call with timeout
                executor_call = lambda: self.model.generate_content(batch_prompt, generation_config=config)
                if self._api_timeout and self._api_timeout > 0:
                    response = await asyncio.wait_for(
                        loop.run_in_executor(None, executor_call),
                        timeout=self._api_timeout
                    )
                else:
                    response = await loop.run_in_executor(None, executor_call)
                
                response_text = response.text.strip()
                keywords_data = self._parse_json_response(response_text)

                if keywords_data and isinstance(keywords_data, list):
                    # Validate batch returned expected count
                    if len(keywords_data) < batch_count:
                        logger.warning(f"⚠️  Batch {batch_num}: Got {len(keywords_data)} keywords, requested {batch_count}")
                    else:
                        logger.info(f"✅ Batch {batch_num}: Got {len(keywords_data)} keywords (requested {batch_count})")
                    
                    # Convert to dict format
                    result = []
                    for kw_data in keywords_data:
                        if isinstance(kw_data, dict):
                            kw_dict = {
                                "keyword": kw_data.get("keyword", "").strip(),
                                "score": 0,
                                "source": KeywordSource.AI_GENERATED.value,
                                "intent": kw_data.get("intent", "informational").lower(),
                                "word_count": len(kw_data.get("keyword", "").split()),
                                "is_question": kw_data.get("intent", "").lower() == "question",
                                "notes": kw_data.get("notes", ""),
                                "created_at": datetime.now(UTC),
                                "updated_at": datetime.now(UTC),
                            }
                            if kw_dict["keyword"]:
                                result.append(kw_dict)
                    
                    # Return even if fewer than requested (partial success)
                    if result:
                        return result
                    else:
                        raise ValueError(f"Batch {batch_num} returned empty result")
                else:
                    raise ValueError(f"Failed to parse keywords from batch {batch_num}: got {type(keywords_data)}")
                    
            except asyncio.TimeoutError:
                logger.warning(f"Batch {batch_num} attempt {attempt + 1}/{self.max_retries} timed out after {self._api_timeout}s")
                if attempt < self.max_retries - 1:
                    retry_delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"⏳ Retrying batch {batch_num} in {retry_delay:.1f}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"❌ Batch {batch_num} timed out after {self.max_retries} attempts")
            except Exception as e:
                logger.warning(f"Batch {batch_num} attempt {attempt + 1}/{self.max_retries} failed: {type(e).__name__}: {e}")
                if attempt < self.max_retries - 1:
                    retry_delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"⏳ Retrying batch {batch_num} in {retry_delay:.1f}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"❌ Batch {batch_num} failed after {self.max_retries} attempts: {e}", exc_info=True)
        
        # Return empty list if all retries failed
        logger.error(f"🔴 Batch {batch_num} returning empty result after all retries")
        return []

    def generate_long_tail_variants(
        self,
        seed_keywords: List[str],
        company_name: str,
        variants_per_seed: int = 2,
    ) -> List[Dict]:
        """
        Generate long-tail variants of seed keywords

        Args:
            seed_keywords: List of seed keyword terms
            company_name: Company name for context
            variants_per_seed: Number of variants per seed (2-3)

        Returns:
            List of long-tail keyword dictionaries
        """
        if not seed_keywords:
            return []

        # Take top 10 seeds to avoid too many API calls
        seeds_to_expand = seed_keywords[:10]

        logger.info(f"Generating {len(seeds_to_expand) * variants_per_seed} long-tail variants")

        all_variants = []

        for seed in seeds_to_expand:
            variants = self._generate_variants_for_seed(seed, company_name, variants_per_seed)
            all_variants.extend(variants)

        logger.info(f"Generated {len(all_variants)} long-tail variants")
        return all_variants

    def _generate_variants_for_seed(
        self,
        seed: str,
        company_name: str,
        count: int = 2,
    ) -> List[Dict]:
        """Generate variants for a single seed keyword"""

        prompt = f"""Generate {count} long-tail keyword variations of this seed:

Seed: "{seed}"
Company: {company_name}

Requirements:
- Each variant should be 3-8 words long
- Focus on conversational, long-tail variations
- Include question formats (how to, what is, why do, etc.)
- Make them specific and intent-driven
- Maintain relevance to the seed keyword
- Format: Return as JSON array with fields:
  - keyword: the variation
  - question_based: true if it's a question format
  - intent: 'informational', 'commercial', 'question', etc.

Response ONLY with valid JSON."""

        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Enforce rate limiting before API call
                self._rate_limit()
                
                config = GenerationConfig(temperature=0.7)
                response = self.model.generate_content(prompt, generation_config=config)
                response_text = response.text.strip()

                variants_data = self._parse_json_response(response_text)

                variants = []
                for var_data in variants_data:
                    kw_dict = {
                        "keyword": var_data.get("keyword", "").strip(),
                        "score": 0,
                        "source": KeywordSource.AI_GENERATED.value,
                        "intent": var_data.get("intent", "informational"),
                        "word_count": len(var_data.get("keyword", "").split()),
                        "is_question": var_data.get("question_based", False),
                        "created_at": datetime.now(UTC),
                        "updated_at": datetime.now(UTC),
                    }

                    if kw_dict["keyword"]:
                        variants.append(kw_dict)

                return variants

            except Exception as e:
                last_error = e
                logger.warning(f"Error generating variants for '{seed}' (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    logger.error(f"Failed to generate variants after {self.max_retries} attempts")
                    # Return empty list on failure (graceful degradation)
                    return []
        
        return []

    def _rate_limit(self):
        """Enforce rate limiting between API calls (thread-safe)"""
        with self._rate_limit_lock:
            current_time = time.time()
            time_since_last_call = current_time - self._last_api_call_time
            
            if time_since_last_call < self._rate_limit_delay:
                sleep_time = self._rate_limit_delay - time_since_last_call
                time.sleep(sleep_time)
            
            self._last_api_call_time = time.time()

    @staticmethod
    def _parse_json_response(response_text: str) -> Optional[List[Dict]]:
        """
        Parse JSON response from model

        Handles cases where model wraps JSON in markdown code blocks
        """
        try:
            # Try direct parsing first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try extracting from markdown code block
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                return None

            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON: {json_str}")
                return None

    def deduplicate_keywords(
        self,
        keywords: List[Dict],
        similarity_threshold: float = 0.85,
    ) -> List[Dict]:
        """
        Remove duplicate or near-duplicate keywords

        Uses simple string similarity comparison

        Args:
            keywords: List of keywords
            similarity_threshold: Threshold for considering duplicates (0-1)

        Returns:
            Deduplicated list
        """
        if not keywords:
            return []

        seen = set()
        deduplicated = []

        for kw in keywords:
            keyword_text = kw.get("keyword", "").lower().strip()

            # Check exact duplicates
            if keyword_text in seen:
                continue

            # Check near-duplicates
            is_duplicate = False
            for seen_kw in seen:
                if self._string_similarity(keyword_text, seen_kw) >= similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen.add(keyword_text)
                deduplicated.append(kw)

        logger.info(f"Deduplicated {len(keywords)} to {len(deduplicated)} keywords")
        return deduplicated

    @staticmethod
    def _string_similarity(s1: str, s2: str) -> float:
        """
        Calculate similarity between two keyword strings
        Uses word-based comparison for better accuracy
        """
        if s1 == s2:
            return 1.0

        # Split into words and normalize
        words1 = set(s1.lower().split())
        words2 = set(s2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity (intersection over union)
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
