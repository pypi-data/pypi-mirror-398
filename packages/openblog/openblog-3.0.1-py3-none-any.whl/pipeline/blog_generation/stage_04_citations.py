"""
Stage 4: Citations Validation and Formatting

Maps to v4.1 Phase 4, Steps 8-13: CitationSanitizer + Information Extractor + AI Agent3 + Formatting

Processes citations from the article:
1. Extract sources from structured_data.Sources field
2. Parse citation format [1], [2], etc.
3. Extract URLs and titles
4. Validate URLs (optional)
5. Format as HTML

Input:
  - ExecutionContext.structured_data (ArticleOutput with Sources field)

Output:
  - ExecutionContext.parallel_results['citations_html'] (HTML formatted citations)

The citations from Gemini come in format:
[1]: https://example.com – Description of source
[2]: https://example.org – Another source
...
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

from ..core import ExecutionContext, Stage
from ..models.citation import Citation, CitationList
from ..models.gemini_client import GeminiClient
from ..processors.url_validator import CitationURLValidator
from ..processors.ultimate_citation_validator import SmartCitationValidator, ValidationResult
from ..config import Config

logger = logging.getLogger(__name__)


class CitationsStage(Stage):
    """
    Stage 4: Citations Validation and Formatting.

    Handles:
    - Parsing sources from structured_data
    - Extracting URLs and titles
    - Creating Citation objects
    - Formatting as HTML
    - Validation (optional URL checks)
    
    Performance Notes:
    - Uses Gemini 3 Pro (gemini-3-pro-preview) for citation validation
    - Required for complex tool calling (web search + JSON output + validation)
    - Flash 2.5 cannot handle multi-tool workflows reliably
    """

    stage_num = 4
    stage_name = "Citations Validation & Formatting"

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize citations stage.
        
        Args:
            config: Configuration object (optional, loads from env if not provided)
        """
        self.config = config or Config()
        self.gemini_client = None  # Lazy initialization
        self.validator = None  # Lazy initialization
        self.ultimate_validator = None  # Ultimate citation validator

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 4: Process and format citations (sequential flow).

        NEW SEQUENTIAL FLOW:
        1. Extract URLs from Sources field (simple parsing)
        2. HTTP Status Check (parallel)
        3. Security Check (AI)
        4. Identify Issues
        5. Find Replacements (1 retry max)
        6. Update Body Citations (AI-based)
        7. Format Output

        Input from context:
        - structured_data: ArticleOutput with Sources field

        Output to context:
        - parallel_results['citations_html']: Formatted HTML
        - parallel_results['citations_list']: Updated CitationList
        - parallel_results['validated_citation_map']: Citation number -> URL mapping

        Args:
            context: ExecutionContext from Stage 3

        Returns:
            Updated context with parallel_results populated
        """
        try:
            logger.info(f"Stage 4: {self.stage_name}")

            # Check if citations are disabled (defensive null check)
            job_config = context.job_config if context.job_config else {}
            if job_config.get("citations_disabled", False):
                logger.info("Citations disabled via job_config")
                context.parallel_results["citations_html"] = ""
                return context

            # Validate input
            if not context.structured_data:
                logger.warning("No structured_data available for citations")
                context.parallel_results["citations_html"] = ""
                return context

            sources_text = context.structured_data.Sources or ""
            if not sources_text.strip():
                logger.warning("No sources found in structured_data")
                context.parallel_results["citations_html"] = ""
                return context

            logger.info(f"Processing sources ({len(sources_text)} chars)...")

            # ============================================================
            # STEP 1: Extract URLs (Simple Parsing)
            # ============================================================
            logger.info("📝 Step 1: Extracting citations from Sources field (AI-only)...")
            citation_list = await self._extract_citations_simple(sources_text)

            if not citation_list.citations:
                logger.warning("No valid citations extracted")
                context.parallel_results["citations_html"] = ""
                return context

            logger.info(f"✅ Extracted {citation_list.count()} citations")

            # ============================================================
            # STEP 2: HTTP Status Check (Parallel)
            # ============================================================
            logger.info("🔍 Step 2: Checking HTTP status for all URLs (parallel)...")
            status_map = await self._check_url_status_parallel(citation_list)

            # ============================================================
            # STEP 3: Security Check (AI)
            # ============================================================
            logger.info("🔒 Step 3: Checking citations for security risks (AI)...")
            security_map = await self._check_security_ai(citation_list)

            # ============================================================
            # STEP 3.5: Competitor Check
            # ============================================================
            logger.info("🏢 Step 3.5: Checking citations for competitor domains...")
            competitor_map = self._check_competitors(citation_list, context)

            # ============================================================
            # STEP 4: Identify Issues
            # ============================================================
            logger.info("📋 Step 4: Identifying citations needing replacement...")
            issues_list = self._identify_issues(citation_list, status_map, security_map, competitor_map)

            # ============================================================
            # STEP 5: Find Replacements (1 Retry Max)
            # ============================================================
            # Save original URLs before replacement (needed for body update)
            original_urls = {c.number: c.url for c in issues_list} if issues_list else {}

            if issues_list:
                logger.info("🔍 Step 5: Finding replacements for broken/risky citations...")
                citation_list, no_replacement_nums = await self._find_replacements(
                    citation_list, issues_list, context
                )
            else:
                logger.info("✅ Step 5: No citations need replacement")
                no_replacement_nums = []

            # Build URL replacement map: original_url → new_url (or None if no replacement)
            url_updates = {}
            for num, original_url in original_urls.items():
                if num in no_replacement_nums:
                    url_updates[original_url] = None  # No replacement, will be stripped
                else:
                    # Find the new URL for this citation
                    for c in citation_list.citations:
                        if c.number == num:
                            if c.url != original_url:
                                url_updates[original_url] = c.url  # Updated URL
                            break

            # ============================================================
            # STEP 6: Update Body Citations
            # ============================================================
            if url_updates:
                logger.info("🔗 Step 6: Updating body citations...")
                context = await self._update_body_citations(context, url_updates)
            else:
                logger.info("✅ Step 6: No body citations need updating")

            # ============================================================
            # STEP 7: Format Output
            # ============================================================
            logger.info("📄 Step 7: Formatting citations as HTML...")
            
            # Filter out citations with no replacement
            valid_citations = CitationList()
            valid_citations.citations = [
                citation for citation in citation_list.citations
                if citation.number not in no_replacement_nums
            ]
            
            citations_html = valid_citations.to_html_paragraph_list()
            logger.info(f"   HTML size: {len(citations_html)} chars")
            
            # Build validated citation map for in-body links
            validated_citation_map = {}
            validated_source_name_map = {}
            for citation in valid_citations.citations:
                validated_citation_map[citation.number] = citation.url
                title_words = citation.title.split() if citation.title else []
                if title_words:
                    source_name = title_words[0]
                    validated_source_name_map[source_name.lower()] = citation.url
            
            logger.info(f"   Validated citation map: {len(validated_citation_map)} entries")
            if validated_source_name_map:
                logger.info(f"   Validated source names: {list(validated_source_name_map.keys())[:5]}...")

            # Store in context
            context.parallel_results["citations_html"] = citations_html
            context.parallel_results["citations_count"] = valid_citations.count()
            context.parallel_results["citations_list"] = valid_citations
            context.parallel_results["validated_citation_map"] = validated_citation_map
            context.parallel_results["validated_source_name_map"] = validated_source_name_map

            return context
        
        except AttributeError as e:
            if "'NoneType' object has no attribute 'get'" in str(e):
                logger.error(f"❌ Stage 4 AttributeError: {e}")
                logger.error("   This usually means company_data, sitemap_data, or job_config is None")
                logger.error(f"   company_data: {context.company_data is not None if hasattr(context, 'company_data') else 'N/A'}")
                logger.error(f"   sitemap_data: {getattr(context, 'sitemap_data', None) is not None}")
                logger.error(f"   job_config: {context.job_config is not None if hasattr(context, 'job_config') else 'N/A'}")
                # Return empty citations HTML to allow pipeline to continue
                context.parallel_results["citations_html"] = ""
                context.parallel_results["citations_count"] = 0
                return context
            else:
                raise
        except Exception as e:
            logger.error(f"❌ Stage 4 unexpected error: {e}", exc_info=True)
            # Return empty citations HTML to allow pipeline to continue
            context.parallel_results["citations_html"] = ""
            context.parallel_results["citations_count"] = 0
            return context

    async def _validate_citation_urls(
        self,
        citation_list: CitationList,
        context: ExecutionContext,
    ) -> CitationList:
        """
        Validate citation URLs and find alternatives for invalid ones.
        
        Matches v4.1 Step 11: AI Agent3 behavior:
        - Validates each URL with HTTP HEAD
        - Finds alternatives for invalid URLs
        - Filters competitors/internal/forbidden domains
        - Maintains citation count
        
        Args:
            citation_list: List of citations to validate
            context: Execution context with company data
            
        Returns:
            Validated CitationList (same count as input)
        """
        logger.info(f"Validating {citation_list.count()} citation URLs...")
        
        # Initialize validator if needed
        if not self.validator:
            if not self.gemini_client:
                # Use Gemini 3 Pro for citation validation (tool calling required)
                # Use Gemini 3 Pro for web search + JSON + tool calling capabilities
                # 2.5 Flash cannot handle complex tool calling with JSON output reliably
                self.gemini_client = GeminiClient(model="gemini-3-pro-preview")
            self.validator = CitationURLValidator(
                gemini_client=self.gemini_client,
                max_attempts=self.config.max_validation_attempts,
                timeout=self.config.citation_validation_timeout,
            )
        
        # Get company data (with null check)
        if not context.company_data:
            logger.warning("No company_data available for citation validation")
            return citation_list
        company_url = context.company_data.get("company_url", "")
        competitors = context.company_data.get("company_competitors", [])
        language = context.language or "en"
        
        # Validate all citations
        try:
            validated_citations = await self.validator.validate_all_citations(
                citations=citation_list.citations,
                company_url=company_url,
                competitors=competitors,
                language=language,
            )
            
            # OPTIMIZATION: Skip post-validation to speed up (already validated during main validation)
            # Post-validation was adding ~30 seconds and catching minimal issues
            # If needed, can re-enable but it slows down the workflow significantly
            logger.info("Skipping post-validation (performance optimization)")
            final_valid_count = len(validated_citations)  # Assume all valid (they were validated above)
            valid_ratio = 1.0
            
            # DISABLED: Post-validation check (too slow)
            # Uncomment below if you want to re-enable double-checking
            # logger.info("Running post-validation check on all citations...")
            # final_valid_count = 0
            # post_validation_results = []
            # for citation in validated_citations:
            #     try:
            #         is_valid, final_url = await self.validator._check_url_status(citation.url)
            #         post_validation_results.append({'citation': citation, 'valid': is_valid, 'url': final_url})
            #         if is_valid:
            #             final_valid_count += 1
            #     except Exception as e:
            #         logger.error(f"Error in post-validation for [{citation.number}]: {e}")
            #         post_validation_results.append({'citation': citation, 'valid': False, 'url': citation.url})
            # valid_ratio = final_valid_count / len(validated_citations) if validated_citations else 0
            # logger.info(f"✅ Post-validation complete: {final_valid_count}/{len(validated_citations)} ({valid_ratio:.0%}) valid")
            
            # Quality threshold check: Require at least 75% valid URLs
            # OPTIMIZATION: Disabled for now (post-validation is disabled, so we can't measure accurately)
            # Can re-enable if post-validation is restored
            QUALITY_THRESHOLD = 0.75
            logger.info(f"✅ Citation validation complete: {len(validated_citations)} citations processed")
            
            # DISABLED: Quality threshold (requires post-validation)
            # if valid_ratio < QUALITY_THRESHOLD:
            #     logger.warning(f"⚠️  Citation quality below threshold: {valid_ratio:.0%} < {QUALITY_THRESHOLD:.0%}")
            # else:
            #     logger.info(f"✅ Citation quality acceptable: {valid_ratio:.0%} valid")
            
            # Create new CitationList with validated citations
            validated_list = CitationList()
            validated_list.citations = validated_citations
            
            return validated_list
            
        except Exception as e:
            logger.error(f"Error validating citations: {e}")
            logger.warning("Continuing with original citations")
            return citation_list

    def _enhance_with_grounding_urls(
        self, 
        citation_list: CitationList, 
        grounding_urls: List[Dict[str, str]]
    ) -> CitationList:
        """
        Enhance citations with SPECIFIC URLs from Gemini's Google Search grounding.
        
        GeminiClient resolves grounding URLs:
        - 'url': Real resolved URL (e.g., https://checkpoint.com/.../cloud-security/)
        - 'domain': Domain from title (e.g., "checkpoint.com")
        - 'proxy_url': Original vertex proxy URL (kept for reference)
        
        Strategy:
        1. For each citation, find a grounding URL where domain matches
        2. Replace the citation URL with the real resolved URL
        3. If multiple matches, prefer the one with most similar title
        
        Args:
            citation_list: CitationList with potentially generic URLs
            grounding_urls: List of {'url': str, 'domain': str, ...} from Gemini grounding
            
        Returns:
            Enhanced CitationList with real, validated source URLs
        """
        if not grounding_urls:
            return citation_list
        
        # Build domain -> specific URLs map
        # CRITICAL: Use TITLE as domain (not URL which is always vertexaisearch.cloud.google.com)
        domain_to_urls: Dict[str, List[Dict[str, str]]] = {}
        for grounding in grounding_urls:
            url = grounding.get('url', '')
            title = grounding.get('title', '')
            if not url or not title:
                continue
            # The title IS the domain (e.g., "sportingnews.com", "aljazeera.com")
            domain = title.lower().replace('www.', '')
            if domain not in domain_to_urls:
                domain_to_urls[domain] = []
            domain_to_urls[domain].append(grounding)
        
        logger.info(f"   Grounding URL domains (from titles): {', '.join(domain_to_urls.keys())}")
        
        enhanced_count = 0
        domain_only_count = 0
        
        for citation in citation_list.citations:
            # Extract domain from citation URL
            try:
                from urllib.parse import urlparse
                parsed = urlparse(citation.url)
                citation_domain = parsed.netloc.lower().replace('www.', '')
                # Check if URL is domain-only (path has <= 3 parts: /, maybe /path, maybe /path/item)
                path_parts = [p for p in parsed.path.split('/') if p]
                is_domain_only = len(path_parts) <= 1  # Domain-only if just "/" or "/single-item"
            except Exception:
                continue
            
            # Check if we have grounding URLs for this domain
            # The domain_to_urls keys are from grounding titles (e.g., "gartner.com")
            if citation_domain in domain_to_urls:
                specific_urls = domain_to_urls[citation_domain]
                
                if specific_urls:
                    # Find best match by title similarity
                    best_match = self._find_best_title_match(citation.title, specific_urls)
                    
                    # CRITICAL: Always enhance domain-only URLs, only enhance full URLs if significantly better
                    should_enhance = False
                    if is_domain_only:
                        # Domain-only URLs should ALWAYS be enhanced
                        should_enhance = True
                        domain_only_count += 1
                        logger.info(f"   🎯 Citation [{citation.number}] is domain-only - WILL ENHANCE")
                    elif best_match and best_match['url'] != citation.url:
                        # Full URLs: only enhance if grounding URL is significantly better (longer path = more specific)
                        grounding_path_parts = [p for p in urlparse(best_match['url']).path.split('/') if p]
                        if len(grounding_path_parts) > len(path_parts) + 1:  # Significantly more specific
                            should_enhance = True
                            logger.info(f"   📎 Citation [{citation.number}] full URL - enhancing to more specific URL")
                        else:
                            logger.debug(f"   ⏭️  Citation [{citation.number}] already has good full URL - skipping")
                    
                    if should_enhance and best_match:
                        old_url = citation.url
                        citation.url = best_match['url']
                        enhanced_count += 1
                        logger.info(f"   ✅ Citation [{citation.number}] enhanced:")
                        logger.info(f"      OLD: {old_url}")
                        logger.info(f"      NEW: {citation.url[:80]}...")
        
        if enhanced_count > 0:
            logger.info(f"✅ Enhanced {enhanced_count} citations with specific URLs")
            if domain_only_count > 0:
                logger.info(f"   📊 {domain_only_count} domain-only URLs converted to full URLs")
        else:
            logger.info("   No URLs needed enhancement")
        
        return citation_list
    
    def _find_best_title_match(
        self, 
        citation_title: str, 
        grounding_urls: List[Dict[str, str]]
    ) -> Optional[Dict[str, str]]:
        """Find the grounding URL with the most similar title."""
        if not grounding_urls:
            return None
        
        if len(grounding_urls) == 1:
            return grounding_urls[0]
        
        # Simple word overlap scoring
        citation_words = set(citation_title.lower().split())
        
        best_match = grounding_urls[0]
        best_score = 0
        
        for grounding in grounding_urls:
            title = grounding.get('title', '')
            grounding_words = set(title.lower().split())
            overlap = len(citation_words & grounding_words)
            if overlap > best_score:
                best_score = overlap
                best_match = grounding
        
        return best_match

    async def _extract_citations_simple(self, sources_text: str) -> CitationList:
        """
        Extract citations from Sources field using AI-only parsing (no regex).
        
        Format: [1]: Title – URL
        Example: [1]: IBM Cost of a Data Breach Report 2024 – https://www.ibm.com/reports/data-breach
        
        Args:
            sources_text: Raw sources from structured_data
            
        Returns:
            CitationList with extracted citations
        """
        citation_list = CitationList()
        
        if not sources_text or not sources_text.strip():
            return citation_list
        
        logger.info("📝 Extracting citations from Sources field (AI-only parsing)")
        
        # Initialize Gemini client if needed
        if not self.gemini_client:
            self.gemini_client = GeminiClient()
        
        prompt = f"""Extract all citations from the Sources field below. Parse each citation and return structured JSON.

Sources field format: [number]: Title – URL
Example: [1]: IBM Cost of a Data Breach Report 2024 – https://www.ibm.com/reports/data-breach

CRITICAL REQUIREMENTS:
1. Extract ALL citations from the text
2. Parse citation number, title, and URL correctly
3. Handle both em dash (—) and regular dash (-) as separators
4. Validate URLs start with http:// or https://
5. Return ONLY valid citations (skip any malformed entries)

Sources field text:
{sources_text}

Return a JSON object with a "citations" array. Each citation must have:
- number: integer (citation number)
- title: string (citation title)
- url: string (full URL starting with http:// or https://)
"""
        
        try:
            from google.genai import types
            
            response_schema = types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "citations": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "number": types.Schema(
                                    type=types.Type.INTEGER,
                                    description="Citation number (e.g., 1, 2, 3)"
                                ),
                                "title": types.Schema(
                                    type=types.Type.STRING,
                                    description="Citation title (8-15 words)"
                                ),
                                "url": types.Schema(
                                    type=types.Type.STRING,
                                    description="Full URL starting with http:// or https://"
                                )
                            }
                        )
                    )
                },
                required=["citations"]
            )
            
            response = await self.gemini_client.generate_content(
                prompt=prompt,
                response_schema=response_schema,
                enable_tools=False
            )
            
            if not response:
                logger.warning("⚠️ AI parsing returned no response")
                return citation_list
            
            import json
            parsed = json.loads(response)
            citations_data = parsed.get('citations', [])
            
            for cit_data in citations_data:
                try:
                    citation = Citation(
                        number=cit_data.get('number'),
                        url=cit_data.get('url', '').strip(),
                        title=cit_data.get('title', '').strip(),
                        meta_description=""  # Will be populated later if needed
                    )
                    citation_list.citations.append(citation)
                except Exception as e:
                    logger.warning(f"   ⚠️ Could not create citation from AI response: {e}")
                    continue
            
            # Resolve any proxy URLs (vertexaisearch.cloud.google.com redirects)
            citation_list = self._resolve_proxy_urls(citation_list)
            
            # Extract metadata (meta titles and descriptions) for all citations
            citation_list = await self._extract_metadata_for_citations(citation_list)
            
            logger.info(f"✅ Extracted {len(citation_list.citations)} citations (AI-only)")
            
        except Exception as e:
            logger.error(f"❌ AI citation extraction failed: {e}")
            logger.warning("   Returning empty citation list")
            return citation_list
        
        return citation_list
    
    async def _extract_metadata_for_citations(self, citation_list: CitationList) -> CitationList:
        """
        Extract meta titles and descriptions for all citations using parallel HTTP requests.
        
        This enhances citations with proper source metadata so they appear as
        "IBM Cost of a Data Breach Report 2024" instead of just "ibm.com" in exports.
        
        Args:
            citation_list: CitationList with extracted citations
            
        Returns:
            CitationList with enhanced metadata (meta_description field populated)
        """
        if not citation_list.citations:
            return citation_list
            
        logger.info(f"📝 Extracting metadata for {len(citation_list.citations)} citations...")
        
        import asyncio
        import aiohttp
        from bs4 import BeautifulSoup
        
        async def fetch_metadata(session: aiohttp.ClientSession, citation: Citation):
            """Fetch metadata for a single citation."""
            try:
                async with session.get(
                    citation.url, 
                    timeout=aiohttp.ClientTimeout(total=8),
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; OpenBlog/1.0)'}
                ) as response:
                    if response.status != 200:
                        logger.warning(f"   ⚠️  Citation [{citation.number}] HTTP {response.status}: {citation.url}")
                        return citation
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract meta title (prefer og:title, then <title>, then current title)
                    meta_title = None
                    og_title = soup.find('meta', attrs={'property': 'og:title'})
                    if og_title and og_title.get('content'):
                        meta_title = og_title['content'].strip()
                    
                    if not meta_title:
                        title_tag = soup.find('title')
                        if title_tag and title_tag.text:
                            meta_title = title_tag.text.strip()
                    
                    # Extract meta description (prefer og:description, then meta description)
                    meta_description = None
                    og_desc = soup.find('meta', attrs={'property': 'og:description'})
                    if og_desc and og_desc.get('content'):
                        meta_description = og_desc['content'].strip()
                    
                    if not meta_description:
                        desc_tag = soup.find('meta', attrs={'name': 'description'})
                        if desc_tag and desc_tag.get('content'):
                            meta_description = desc_tag['content'].strip()
                    
                    # Update citation with metadata
                    if meta_title and len(meta_title) > 10:  # Only use if substantial
                        citation.title = meta_title[:150]  # Limit length
                        logger.debug(f"   📝 Citation [{citation.number}] title updated: {citation.title[:50]}...")
                    
                    if meta_description and len(meta_description) > 20:
                        citation.meta_description = meta_description[:300]  # Limit length
                        logger.debug(f"   📝 Citation [{citation.number}] description: {citation.meta_description[:50]}...")
                    
                    return citation
                    
            except asyncio.TimeoutError:
                logger.warning(f"   ⚠️  Citation [{citation.number}] timeout: {citation.url}")
            except Exception as e:
                logger.warning(f"   ⚠️  Citation [{citation.number}] metadata error: {e}")
            
            return citation
        
        # Process all citations in parallel
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_metadata(session, citation) for citation in citation_list.citations]
            updated_citations = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update citation list with results
        enhanced_count = 0
        for i, result in enumerate(updated_citations):
            if isinstance(result, Citation):
                citation_list.citations[i] = result
                if result.meta_description:
                    enhanced_count += 1
            # If exception, keep original citation
        
        logger.info(f"✅ Enhanced {enhanced_count}/{len(citation_list.citations)} citations with metadata")
        return citation_list
    
    def _resolve_proxy_urls(self, citation_list: CitationList) -> CitationList:
        """
        Resolve Gemini grounding proxy URLs to real destination URLs.
        
        Gemini sometimes includes proxy URLs directly in the Sources field:
        https://vertexaisearch.cloud.google.com/grounding-api-redirect/...
        
        These redirect (302) to the actual source. We follow the redirect
        to get clean, real URLs for citations.
        """
        import requests
        
        resolved_count = 0
        for citation in citation_list.citations:
            if 'vertexaisearch.cloud.google.com' in citation.url:
                try:
                    resp = requests.head(citation.url, allow_redirects=False, timeout=5)
                    if resp.status_code in (301, 302, 303, 307, 308):
                        real_url = resp.headers.get('Location', citation.url)
                        logger.info(f"   📎 Resolved proxy URL [{citation.number}]: {real_url}")
                        citation.url = real_url
                        resolved_count += 1
                except Exception as e:
                    logger.warning(f"   Failed to resolve proxy URL [{citation.number}]: {e}")
        
        if resolved_count > 0:
            logger.info(f"✅ Resolved {resolved_count} proxy URLs to real URLs")
        
        return citation_list
    
    async def _check_url_status_parallel(self, citation_list: CitationList) -> Dict[int, str]:
        """
        Check HTTP status of all citation URLs in parallel.
        
        Args:
            citation_list: CitationList with citations to check
            
        Returns:
            Dict mapping citation number to status: 'valid' | 'broken' | 'unknown'
        """
        import asyncio
        import requests
        from concurrent.futures import ThreadPoolExecutor
        
        def check_single_url_sync(citation: Citation) -> Tuple[int, str]:
            """Check a single URL synchronously and return (number, status)."""
            try:
                response = requests.head(
                    citation.url,
                    timeout=5,
                    allow_redirects=True,
                    headers={'User-Agent': 'OpenBlog Citation Validator'}
                )
                
                # Some servers block HEAD, try GET
                if response.status_code == 405:
                    response = requests.get(
                        citation.url,
                        timeout=5,
                        allow_redirects=True,
                        headers={'User-Agent': 'OpenBlog Citation Validator'}
                    )
                
                if 200 <= response.status_code < 400:
                    return (citation.number, 'valid')
                elif response.status_code in (404, 500, 503, 504):
                    return (citation.number, 'broken')
                else:
                    return (citation.number, 'unknown')
                    
            except requests.exceptions.Timeout:
                return (citation.number, 'broken')
            except requests.exceptions.ConnectionError:
                return (citation.number, 'broken')
            except Exception as e:
                logger.debug(f"   ⚠️ Citation [{citation.number}]: HTTP check failed - {e}")
                return (citation.number, 'unknown')
        
        logger.info(f"🔍 Checking HTTP status for {len(citation_list.citations)} URLs (parallel)...")
        
        # Run all checks in parallel using thread pool executor
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=10) as executor:
            tasks = [
                loop.run_in_executor(executor, check_single_url_sync, citation)
                for citation in citation_list.citations
            ]
            results = await asyncio.gather(*tasks)
        
        # Build status map
        status_map = {}
        valid_count = 0
        broken_count = 0
        
        for citation_num, status in results:
            status_map[citation_num] = status
            if status == 'valid':
                valid_count += 1
            elif status == 'broken':
                broken_count += 1
        
        logger.info(f"   ✅ HTTP status check complete: {valid_count} valid, {broken_count} broken, {len(citation_list.citations) - valid_count - broken_count} unknown")
        
        return status_map
    
    async def _check_security_ai(self, citation_list: CitationList) -> Dict[int, bool]:
        """
        Use AI (Gemini) to check citations for spam/malicious content.
        
        Args:
            citation_list: CitationList with citations to check
            
        Returns:
            Dict mapping citation number to is_security_risk (True = security risk, False = safe)
        """
        if not citation_list.citations:
            return {}
        
        # Initialize Gemini client if needed
        if not self.gemini_client:
            self.gemini_client = GeminiClient()
        
        logger.info(f"🔒 Checking {len(citation_list.citations)} citations for security risks (AI)...")
        
        # Build list of URLs and titles for analysis
        citations_text = ""
        for citation in citation_list.citations:
            citations_text += f"[{citation.number}]: {citation.url} - {citation.title}\n"
        
        prompt = f"""Analyze these citation URLs for security risks, spam, malicious content, phishing, or low-quality sources.

Citations:
{citations_text}

For each citation, determine if it's a security risk:
- Spam websites
- Malicious/phishing domains
- Low-quality or suspicious sources
- Known bad domains

Return JSON with this structure:
{{
  "security_risks": [
    {{"number": 1, "is_risk": true, "reason": "spam domain"}},
    {{"number": 2, "is_risk": false, "reason": "legitimate source"}}
  ]
}}

Only mark as security risk if you're confident it's spam/malicious. Legitimate sources should be marked as false.
"""
        
        try:
            from google.genai import types
            security_schema = types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "security_risks": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "number": types.Schema(type=types.Type.INTEGER),
                                "is_risk": types.Schema(type=types.Type.BOOLEAN),
                                "reason": types.Schema(type=types.Type.STRING)
                            },
                            required=["number", "is_risk", "reason"]
                        )
                    )
                },
                required=["security_risks"]
            )
            
            response = await self.gemini_client.generate_content(
                prompt=prompt,
                response_schema=security_schema,
                enable_tools=False
            )
            
            if response:
                import json
                parsed = json.loads(response)
                security_map = {}
                risk_count = 0
                
                for risk_info in parsed.get('security_risks', []):
                    citation_num = risk_info.get('number')
                    is_risk = risk_info.get('is_risk', False)
                    reason = risk_info.get('reason', '')
                    
                    security_map[citation_num] = is_risk
                    if is_risk:
                        risk_count += 1
                        logger.warning(f"   ⚠️ Citation [{citation_num}]: Security risk - {reason}")
                
                logger.info(f"   ✅ Security check complete: {risk_count} security risks found")
                return security_map
            else:
                logger.warning("⚠️ Security check returned no response")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Security check failed: {e}")
            logger.warning("   Continuing without security check")
            return {}
    
    def _check_competitors(
        self,
        citation_list: CitationList,
        context: ExecutionContext
    ) -> Dict[int, bool]:
        """
        Check if any citation URLs are from competitor domains.

        Args:
            citation_list: CitationList with citations to check
            context: Execution context with company data

        Returns:
            Dict mapping citation number to is_competitor (True = competitor domain)
        """
        competitor_map = {}

        # Get competitors from company_data
        if not context.company_data:
            logger.warning("No company_data available for competitor check")
            return competitor_map

        competitors = context.company_data.get("company_competitors", [])
        if not competitors:
            logger.info("   No competitors defined - skipping competitor check")
            return competitor_map

        # Normalize competitor list (handle comma-separated strings)
        normalized_competitors = []
        for comp in competitors:
            if not comp or not isinstance(comp, str):
                continue
            if "," in comp:
                normalized_competitors.extend([c.strip().lower() for c in comp.split(",") if c.strip()])
            else:
                normalized_competitors.append(comp.strip().lower())

        if not normalized_competitors:
            return competitor_map

        logger.info(f"   Checking against {len(normalized_competitors)} competitors: {normalized_competitors[:5]}...")

        from urllib.parse import urlparse

        competitor_count = 0
        for citation in citation_list.citations:
            try:
                parsed = urlparse(citation.url)
                host = parsed.netloc.lower().replace("www.", "")

                # Check if host matches any competitor
                is_competitor = False
                matched_competitor = None
                for comp in normalized_competitors:
                    # Clean competitor name (might be just company name, not domain)
                    comp_clean = comp.replace("www.", "").replace("https://", "").replace("http://", "").strip("/")

                    # Check for exact match or subdomain
                    if host == comp_clean or host.endswith(f".{comp_clean}"):
                        is_competitor = True
                        matched_competitor = comp
                        break

                    # Check if competitor name is in the domain (e.g., "rewardful" in "rewardful.com")
                    if comp_clean in host:
                        is_competitor = True
                        matched_competitor = comp
                        break

                competitor_map[citation.number] = is_competitor
                if is_competitor:
                    competitor_count += 1
                    logger.warning(f"   ⚠️ Citation [{citation.number}]: Competitor domain detected - {host} (matched: {matched_competitor})")

            except Exception as e:
                logger.debug(f"   Error checking competitor for citation [{citation.number}]: {e}")
                competitor_map[citation.number] = False

        logger.info(f"   ✅ Competitor check complete: {competitor_count} competitor citations found")
        return competitor_map

    def _identify_issues(
        self,
        citation_list: CitationList,
        status_map: Dict[int, str],
        security_map: Dict[int, bool],
        competitor_map: Optional[Dict[int, bool]] = None
    ) -> List[Citation]:
        """
        Identify citations that need replacement based on HTTP status, security, and competitor checks.

        Args:
            citation_list: CitationList with all citations
            status_map: Dict mapping citation number to HTTP status ('valid' | 'broken' | 'unknown')
            security_map: Dict mapping citation number to is_security_risk (True/False)
            competitor_map: Dict mapping citation number to is_competitor (True/False)

        Returns:
            List of Citation objects that need replacement
        """
        issues = []

        for citation in citation_list.citations:
            needs_replacement = False
            reason = []

            # Check HTTP status
            status = status_map.get(citation.number, 'unknown')
            if status == 'broken':
                needs_replacement = True
                reason.append('broken URL (404/500/timeout)')

            # Check security risk
            is_security_risk = security_map.get(citation.number, False)
            if is_security_risk:
                needs_replacement = True
                reason.append('security risk (spam/malicious)')

            # Check competitor domain
            if competitor_map:
                is_competitor = competitor_map.get(citation.number, False)
                if is_competitor:
                    needs_replacement = True
                    reason.append('competitor domain')

            # Check if domain-only (path has <= 1 part)
            from urllib.parse import urlparse
            try:
                parsed = urlparse(citation.url)
                path_parts = [p for p in parsed.path.split('/') if p]
                if len(path_parts) <= 1:
                    needs_replacement = True
                    reason.append('domain-only URL')
            except Exception:
                pass

            if needs_replacement:
                issues.append(citation)
                logger.debug(f"   ⚠️ Citation [{citation.number}] needs replacement: {', '.join(reason)}")

        logger.info(f"📋 Identified {len(issues)} citations needing replacement")
        return issues
    
    async def _find_replacements(
        self,
        citation_list: CitationList,
        issues_list: List[Citation],
        context: ExecutionContext
    ) -> Tuple[CitationList, List[int]]:
        """
        Find replacement URLs for broken/security-risk citations (1 retry max).
        
        Args:
            citation_list: Original CitationList
            issues_list: List of citations needing replacement
            context: Execution context
            
        Returns:
            Tuple of (updated CitationList, list of citation numbers with no replacement found)
        """
        if not issues_list:
            return citation_list, []
        
        # Initialize Gemini client if needed
        if not self.gemini_client:
            self.gemini_client = GeminiClient()
        
        logger.info(f"🔍 Finding replacements for {len(issues_list)} citations (1 retry max)...")
        
        updated_list = CitationList()
        updated_list.citations = citation_list.citations.copy()
        no_replacement_nums = []
        
        for citation in issues_list:
            # Try to find alternative URL using Gemini web search
            alternative_url = await self._find_alternative_url(citation, context)
            
            if alternative_url:
                # Validate replacement URL
                status = await self._validate_replacement_url(alternative_url)
                if status == 'valid':
                    # Update citation URL
                    for updated_citation in updated_list.citations:
                        if updated_citation.number == citation.number:
                            logger.info(f"   ✅ Citation [{citation.number}]: Replaced {citation.url[:60]}... → {alternative_url[:60]}...")
                            updated_citation.url = alternative_url
                            break
                else:
                    # Replacement URL also broken - mark as no replacement
                    logger.warning(f"   ⚠️ Citation [{citation.number}]: Replacement URL also broken")
                    no_replacement_nums.append(citation.number)
            else:
                # No alternative found - mark as no replacement
                logger.warning(f"   ⚠️ Citation [{citation.number}]: No replacement found")
                no_replacement_nums.append(citation.number)
        
        if no_replacement_nums:
            logger.warning(f"❌ {len(no_replacement_nums)} citations have no replacement: {no_replacement_nums}")
        else:
            logger.info(f"✅ All {len(issues_list)} citations replaced successfully")
        
        return updated_list, no_replacement_nums
    
    async def _find_alternative_url(self, citation: Citation, context: ExecutionContext) -> Optional[str]:
        """
        Use Gemini web search to find alternative URL for a broken citation (AI-only, no regex).

        Args:
            citation: Citation needing replacement
            context: Execution context

        Returns:
            Alternative URL if found, None otherwise
        """
        # Get competitors to avoid in search
        competitors = []
        if context.company_data:
            comp_data = context.company_data.get("company_competitors", [])
            for comp in comp_data:
                if comp and isinstance(comp, str):
                    if "," in comp:
                        competitors.extend([c.strip() for c in comp.split(",") if c.strip()])
                    else:
                        competitors.append(comp.strip())

        competitors_str = ", ".join(competitors[:10]) if competitors else "none"

        prompt = f"""Find a high-quality alternative source for this broken citation.

Original Citation:
Title: {citation.title}
Original URL: {citation.url} (broken - 404/500/timeout or security risk)

REQUIREMENTS:
1. Search for authoritative sources (.edu, .gov, .org, major publications)
2. Avoid blogs, personal websites, or low-quality sources
3. Prefer recent sources (2020+) unless historical context needed
4. Return the URL of the best alternative source in the "url" field
5. If no good alternative exists, set "url" to null
6. NEVER use URLs from these competitor domains: {competitors_str}

Search for: {citation.title}
"""
        
        try:
            # Simple prompt asking for JSON response
            json_prompt = prompt + """

RESPOND WITH ONLY A JSON OBJECT:
{"url": "https://example.com/article", "reason": "why this source"}
OR if no good source found:
{"url": null, "reason": "why no source"}
"""

            response = await self.gemini_client.generate_content(
                prompt=json_prompt,
                enable_tools=True  # Enable Google Search grounding
            )

            if not response:
                return None

            # Parse JSON response
            import json
            # Clean response - find JSON object
            response_text = response.strip()
            if '{' in response_text:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                response_text = response_text[start:end]

            parsed = json.loads(response_text)
            url = parsed.get('url')
            
            if url and url.strip() and url.lower() != 'null':
                # Validate URL format (simple check, no regex)
                if url.startswith(('http://', 'https://')):
                    # Double-check replacement URL is not from a competitor
                    from urllib.parse import urlparse
                    parsed = urlparse(url.strip())
                    host = parsed.netloc.lower().replace("www.", "")

                    is_competitor = False
                    for comp in competitors:
                        comp_clean = comp.lower().replace("www.", "").replace("https://", "").replace("http://", "").strip("/")
                        if host == comp_clean or host.endswith(f".{comp_clean}") or comp_clean in host:
                            is_competitor = True
                            logger.warning(f"   ⚠️ Replacement URL {url[:60]}... is from competitor {comp} - rejecting")
                            break

                    if not is_competitor:
                        return url.strip()
                    # If competitor, fall through to try grounding URLs
            
            # Fallback: Check grounding URLs from Gemini search (from current response)
            # Note: Gemini's grounding URLs are automatically included in the response
            # We rely on Gemini's structured output above, but if that fails, we check context
            grounding_urls = getattr(context, 'grounding_urls', [])
            if grounding_urls:
                # Use first grounding URL as fallback
                for grounding in grounding_urls[:1]:
                    url = grounding.get('url', '')
                    if url and url.startswith(('http://', 'https://')):
                        logger.debug(f"   Using grounding URL as alternative: {url[:60]}...")
                        return url
            
            return None
            
        except Exception as e:
            logger.warning(f"   Alternative search failed for citation [{citation.number}]: {e}")
            return None
    
    async def _validate_replacement_url(self, url: str) -> str:
        """
        Validate a replacement URL with HTTP check.
        
        Args:
            url: URL to validate
            
        Returns:
            'valid' | 'broken' | 'unknown'
        """
        import requests
        
        try:
            response = requests.head(
                url,
                timeout=5,
                allow_redirects=True,
                headers={'User-Agent': 'OpenBlog Citation Validator'}
            )
            
            if response.status_code == 405:
                response = requests.get(url, timeout=5, allow_redirects=True)
            
            if 200 <= response.status_code < 400:
                return 'valid'
            else:
                return 'broken'
        except Exception:
            return 'broken'
    
    async def _update_body_citations(
        self,
        context: ExecutionContext,
        url_updates: Dict[str, Optional[str]]
    ) -> ExecutionContext:
        """
        Update body citations: replace broken URLs or strip to plain text.

        Uses BeautifulSoup for reliable HTML parsing:
        - Find all <a class="citation" href="..."> tags
        - If href has replacement → update href to new URL
        - If href has no replacement (None) → unwrap (keep text, remove link)

        Args:
            context: Execution context with structured_data
            url_updates: Map of original_url → new_url (or None to strip)

        Returns:
            Updated context with body citations fixed
        """
        if not context.structured_data:
            return context

        if not url_updates:
            return context

        from bs4 import BeautifulSoup

        # Separate URLs to update vs strip
        urls_to_update = {k: v for k, v in url_updates.items() if v is not None}
        urls_to_strip = {k for k, v in url_updates.items() if v is None}

        logger.info(f"   URLs to update: {len(urls_to_update)}, URLs to strip: {len(urls_to_strip)}")

        # Fields to update
        fields_to_update = [
            'Intro', 'Direct_Answer',
            'section_01_content', 'section_02_content', 'section_03_content',
            'section_04_content', 'section_05_content', 'section_06_content',
            'section_07_content', 'section_08_content', 'section_09_content'
        ]

        article_dict = context.structured_data.model_dump()
        updated_count = 0
        replaced_count = 0
        stripped_count = 0

        for field_name in fields_to_update:
            content = article_dict.get(field_name, '')
            if not content or not isinstance(content, str):
                continue

            # Skip if no citation tags
            if 'class="citation"' not in content and "class='citation'" not in content:
                continue

            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            modified = False

            # Find all citation links
            for link in soup.find_all('a', class_='citation'):
                href = link.get('href', '')
                if not href:
                    continue

                # Check if this URL should be updated
                if href in urls_to_update:
                    new_url = urls_to_update[href]
                    link['href'] = new_url
                    modified = True
                    replaced_count += 1
                    logger.debug(f"   Replaced URL in {field_name}: {href[:40]}... → {new_url[:40]}...")

                # Check if this URL should be stripped
                elif href in urls_to_strip:
                    # Unwrap: keep text, remove link
                    link.unwrap()
                    modified = True
                    stripped_count += 1
                    logger.debug(f"   Stripped broken citation in {field_name}: {href[:50]}...")

            if modified:
                article_dict[field_name] = str(soup)
                updated_count += 1

        if updated_count > 0:
            logger.info(f"✅ Updated {updated_count} fields: {replaced_count} URLs replaced, {stripped_count} citations stripped")
            # Update structured_data
            from ..models.output_schema import ArticleOutput
            context.structured_data = ArticleOutput(**article_dict)
        else:
            logger.debug("   No body citations needed updating")

        return context

    async def _validate_citations_ultimate(
        self,
        citation_list: CitationList,
        context: ExecutionContext
    ) -> CitationList:
        """
        Ultimate citation validation using the enhanced validator.
        
        Combines:
        - DOI validation via CrossRef API
        - URL status validation with caching
        - Alternative URL search for invalid URLs
        - Metadata quality analysis
        - Author sanity checks
        
        Args:
            citation_list: Citations to validate
            context: Execution context with company data
            
        Returns:
            CitationList with validated and enhanced citations
        """
        if not citation_list.citations:
            return citation_list
        
        # Initialize ultimate validator
        if not self.ultimate_validator:
            if not self.gemini_client:
                self.gemini_client = GeminiClient()
            self.ultimate_validator = SmartCitationValidator(
                gemini_client=self.gemini_client,
                timeout=8.0
            )
        
        # Convert citations to dict format for validation
        citations_for_validation = []
        for citation in citation_list.citations:
            citation_dict = {
                'url': citation.url,
                'title': citation.title,
                'authors': [],  # Isaac Security doesn't parse authors yet
                'doi': '',  # Could be extracted from URL if needed
                'year': 0   # Could be extracted from content if needed
            }
            citations_for_validation.append(citation_dict)
        
        # Extract company and competitor information
        if not context.company_data:
            logger.warning("No company_data available for ultimate citation validation")
            return citation_list
        company_url = context.company_data.get("company_url", "")
        # Fix: Handle case where sitemap_data exists but is None
        sitemap_data = getattr(context, 'sitemap_data', None) or {}
        competitors = sitemap_data.get("competitors", []) if isinstance(sitemap_data, dict) else []
        language = context.language or "en"
        
        # Validate all citations
        try:
            validation_results = await self.ultimate_validator.validate_citations_simple(
                citations_for_validation,
                company_url=company_url,
                competitors=competitors
            )
            
            # Create new citation list with validated URLs
            validated_list = CitationList()
            
            for i, (original_citation, validation_result) in enumerate(zip(citation_list.citations, validation_results)):
                if validation_result.is_valid:
                    # Use validated URL and title
                    enhanced_citation = Citation(
                        number=original_citation.number,
                        url=validation_result.url,
                        title=validation_result.title or original_citation.title
                    )
                    validated_list.citations.append(enhanced_citation)
                    
                    # Log validation result
                    validation_type = validation_result.validation_type
                    if validation_type == 'original_url':
                        logger.info(f"✅ Citation [{enhanced_citation.number}]: Original URL validated")
                    elif validation_type == 'alternative_found':
                        logger.info(f"🔄 Citation [{enhanced_citation.number}]: Alternative URL found")
                        logger.info(f"   Original: {original_citation.url}")
                        logger.info(f"   Enhanced: {enhanced_citation.url}")
                    elif validation_type == 'doi_verified':
                        logger.info(f"📚 Citation [{enhanced_citation.number}]: DOI verified")
                    
                    if validation_result.issues:
                        for issue in validation_result.issues:
                            logger.warning(f"   ⚠️  {issue}")
                            
                else:
                    # Citation failed validation - check if we should keep it
                    # Filter out if:
                    # 1. Spam/malicious/phishing
                    # 2. HTTP errors (404, 500, etc.) with no alternative found
                    # 3. No valid URL found
                    should_filter = False
                    has_http_error = False
                    has_alternative_attempt = False
                    
                    for issue in validation_result.issues:
                        issue_lower = issue.lower()
                        # Security concerns - always filter
                        if any(keyword in issue_lower for keyword in ['spam', 'malicious', 'phishing']):
                            should_filter = True
                            break
                        # HTTP errors (404, 500, etc.)
                        if 'http' in issue_lower and any(code in issue for code in ['403', '404', '500', '503', '504']):
                            has_http_error = True
                        # Check if alternative was attempted
                        if 'alternative' in issue_lower or 'no alternative' in issue_lower:
                            has_alternative_attempt = True
                    
                    # Filter out if HTTP error AND no alternative found
                    if has_http_error and ('no alternative source found' in ' '.join(validation_result.issues).lower()):
                        should_filter = True
                    
                    # Filter out if no valid URL found
                    if 'no valid url found' in ' '.join(validation_result.issues).lower():
                        should_filter = True
                    
                    if should_filter:
                        logger.warning(f"❌ Filtering out Citation [{original_citation.number}]: Validation failed")
                        for issue in validation_result.issues:
                            logger.warning(f"   ⚠️  {issue}")
                        # Don't add to validated_list - citation is removed
                    else:
                        # Only keep if it's a minor issue (metadata quality, etc.) but URL is valid
                        logger.warning(f"⚠️ Keeping Citation [{original_citation.number}] with minor issues:")
                        for issue in validation_result.issues:
                            logger.warning(f"   ⚠️  {issue}")
                        validated_list.citations.append(original_citation)
            
            # Renumber citations
            for i, citation in enumerate(validated_list.citations, 1):
                citation.number = i
            
            logger.info(f"🔍 Ultimate validation complete: {len(validated_list.citations)} citations processed")
            
            return validated_list
            
        except Exception as e:
            logger.error(f"Ultimate citation validation failed: {e}")
            # Return original citations on failure
            return citation_list
    
    def __repr__(self) -> str:
        """String representation."""
        return f"CitationsStage(stage_num={self.stage_num})"
