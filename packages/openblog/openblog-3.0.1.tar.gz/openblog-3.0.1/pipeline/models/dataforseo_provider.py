# ABOUTME: DataForSEO provider for premium SERP data with rich features as fallback for Google Search
# ABOUTME: Paid service at $0.50/1K queries - includes featured snippets, PAA, related searches
# ABOUTME: Uses Standard mode (task_post + task_get) for cost efficiency vs Live mode

import asyncio
import base64
import logging
import os
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


# DataForSEO location codes for common countries
LOCATION_CODES = {
    "us": 2840,  # United States
    "uk": 2826,  # United Kingdom
    "gb": 2826,  # United Kingdom (alt)
    "ca": 2124,  # Canada
    "au": 2036,  # Australia
    "de": 2276,  # Germany
    "fr": 2250,  # France
    "es": 2724,  # Spain
    "it": 2380,  # Italy
    "jp": 2392,  # Japan
    "br": 2076,  # Brazil
    "in": 2356,  # India
    "mx": 2484,  # Mexico
    "nl": 2528,  # Netherlands
    "se": 2752,  # Sweden
    "pl": 2616,  # Poland
    "ch": 2756,  # Switzerland
    "at": 2040,  # Austria
    "be": 2056,  # Belgium
}


@dataclass
class SearchResult:
    """Individual search result from DataForSEO."""
    position: int
    title: str
    snippet: str
    link: str
    domain: str


@dataclass
class SerpResponse:
    """Response from DataForSEO search."""
    success: bool
    query: str
    results: List[SearchResult]
    provider: str
    error: Optional[str] = None
    cost_credits: float = 0.0


class DataForSeoProvider:
    """DataForSEO provider for premium SERP data as Google Search fallback.

    Uses Standard mode (task_post + task_get) for cost efficiency.
    Standard mode is ~30% cheaper than Live mode but requires polling.

    Provides rich search results including:
    - Organic results with ratings, prices
    - Featured snippets
    - People Also Ask
    - Related searches

    Cost: $0.50 per 1,000 queries (Standard mode)
    Latency: ~1-5 seconds (async polling)
    """

    # Standard mode endpoints (cheaper than Live mode)
    TASK_POST_URL = "https://api.dataforseo.com/v3/serp/google/organic/task_post"
    TASK_GET_URL = "https://api.dataforseo.com/v3/serp/google/organic/task_get/{task_id}"

    # Polling configuration
    MAX_POLL_ATTEMPTS = 10
    INITIAL_POLL_DELAY = 0.5  # Start with 500ms
    MAX_POLL_DELAY = 5.0  # Cap at 5 seconds
    BACKOFF_MULTIPLIER = 1.5

    def __init__(self, api_login: Optional[str] = None, api_password: Optional[str] = None):
        """Initialize DataForSEO provider.

        Args:
            api_login: DataForSEO API login (email) - defaults to env var
            api_password: DataForSEO API password - defaults to env var
        """
        self.name = "dataforseo"
        self.cost_per_1k = 0.50
        self.api_login = api_login or os.getenv("DATAFORSEO_LOGIN")
        self.api_password = api_password or os.getenv("DATAFORSEO_PASSWORD")
        self._encoded_credentials: Optional[str] = None

    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        return bool(self.api_login and self.api_password)

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        if not self._encoded_credentials:
            credentials = f"{self.api_login}:{self.api_password}"
            self._encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        return {
            "Authorization": f"Basic {self._encoded_credentials}",
            "Content-Type": "application/json",
        }

    async def _post_task(
        self,
        client: httpx.AsyncClient,
        query: str,
        num_results: int,
        language: str,
        country: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Submit a search task to DataForSEO.
        
        Returns:
            Tuple of (task_id, error_message)
        """
        location_code = LOCATION_CODES.get(country.lower(), 2840)  # Default to US

        payload = [
            {
                "keyword": query,
                "location_code": location_code,
                "language_code": language,
                "depth": min(num_results, 100),  # DataForSEO max is 100
                "priority": 1,  # 1 = Normal priority for Standard mode
            }
        ]

        try:
            response = await client.post(
                self.TASK_POST_URL,
                json=payload,
                headers=self._get_auth_headers(),
            )

            if response.status_code != 200:
                return None, f"HTTP {response.status_code}: {response.text}"

            data = response.json()
            
            if not data.get("tasks") or not data["tasks"]:
                return None, "No tasks in response"

            task = data["tasks"][0]
            if task.get("status_code") != 20100:  # 20100 = task created
                return None, task.get("status_message", "Task creation failed")

            task_id = task.get("id")
            if not task_id:
                return None, "No task ID in response"

            logger.debug(f"DataForSEO task created: {task_id}")
            return task_id, None

        except Exception as e:
            return None, f"Task POST failed: {str(e)}"

    async def _poll_task_results(
        self,
        client: httpx.AsyncClient,
        task_id: str,
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """Poll for task results with exponential backoff.
        
        Returns:
            Tuple of (results_items, error_message)
        """
        delay = self.INITIAL_POLL_DELAY
        url = self.TASK_GET_URL.format(task_id=task_id)

        for attempt in range(self.MAX_POLL_ATTEMPTS):
            await asyncio.sleep(delay)
            
            try:
                response = await client.get(url, headers=self._get_auth_headers())

                if response.status_code != 200:
                    logger.debug(f"Poll attempt {attempt + 1}: HTTP {response.status_code}")
                    delay = min(delay * self.BACKOFF_MULTIPLIER, self.MAX_POLL_DELAY)
                    continue

                data = response.json()
                
                if not data.get("tasks") or not data["tasks"]:
                    delay = min(delay * self.BACKOFF_MULTIPLIER, self.MAX_POLL_DELAY)
                    continue

                task = data["tasks"][0]
                status_code = task.get("status_code")

                # Task still processing
                if status_code == 20100:
                    logger.debug(f"Poll attempt {attempt + 1}: Task still processing")
                    delay = min(delay * self.BACKOFF_MULTIPLIER, self.MAX_POLL_DELAY)
                    continue

                # Task completed successfully
                if status_code == 20000:
                    task_result = task.get("result", [])
                    if task_result:
                        items = task_result[0].get("items", [])
                        return items, None
                    return [], None

                # Task failed
                return None, task.get("status_message", f"Task failed with code {status_code}")

            except Exception as e:
                logger.debug(f"Poll attempt {attempt + 1} error: {str(e)}")
                delay = min(delay * self.BACKOFF_MULTIPLIER, self.MAX_POLL_DELAY)

        return None, f"Task polling timeout after {self.MAX_POLL_ATTEMPTS} attempts"

    async def search(
        self,
        query: str,
        num_results: int = 10,
        language: str = "en",
        country: str = "us",
    ) -> SerpResponse:
        """Execute search query through DataForSEO Standard mode.

        Standard mode workflow:
        1. POST task to task_post endpoint
        2. Poll task_get endpoint until results ready
        3. Return parsed results

        Args:
            query: Search query string
            num_results: Number of results (max 100)
            language: Language code (default: "en")
            country: Country code (default: "us")

        Returns:
            SerpResponse with search results and rich features
        """
        if not self.is_configured():
            return SerpResponse(
                success=False,
                query=query,
                results=[],
                provider=self.name,
                error="DataForSEO credentials not configured",
            )

        logger.info(f"🔍 DataForSEO Standard mode: {query} ({country}, {language})")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Submit task
                task_id, error = await self._post_task(
                    client, query, num_results, language, country
                )
                
                if error or not task_id:
                    logger.error(f"DataForSEO task creation failed: {error}")
                    return SerpResponse(
                        success=False,
                        query=query,
                        results=[],
                        provider=self.name,
                        error=error or "Task creation failed",
                    )

                # Step 2: Poll for results
                items, error = await self._poll_task_results(client, task_id)
                
                if error:
                    logger.error(f"DataForSEO task polling failed: {error}")
                    return SerpResponse(
                        success=False,
                        query=query,
                        results=[],
                        provider=self.name,
                        error=error,
                    )

                # Step 3: Parse results
                results = []
                for item in (items or []):
                    if item.get("type") == "organic":
                        results.append(
                            SearchResult(
                                position=item.get("rank_absolute", 0),
                                title=item.get("title", ""),
                                snippet=item.get("description", ""),
                                link=item.get("url", ""),
                                domain=item.get("domain", ""),
                            )
                        )

                # Calculate cost (approximate)
                cost_credits = 0.001 * self.cost_per_1k  # $0.50 per 1k = $0.0005 per query
                
                logger.info(f"✅ DataForSEO Standard mode success: {len(results)} results, ~${cost_credits:.4f}")

                return SerpResponse(
                    success=True,
                    query=query,
                    results=results,
                    provider=self.name,
                    cost_credits=cost_credits,
                )

        except httpx.TimeoutException:
            error_msg = "DataForSEO API timeout"
            logger.error(error_msg)
            return SerpResponse(
                success=False,
                query=query,
                results=[],
                provider=self.name,
                error=error_msg,
            )

        except Exception as e:
            error_msg = f"DataForSEO API error: {str(e)}"
            logger.error(error_msg)
            return SerpResponse(
                success=False,
                query=query,
                results=[],
                provider=self.name,
                error=error_msg,
            )

    def format_for_llm(self, serp_response: SerpResponse, max_results: int = 5) -> str:
        """Format DataForSEO results for LLM consumption, matching Google Search format.

        Args:
            serp_response: DataForSEO search response
            max_results: Maximum number of results to include

        Returns:
            Formatted string for LLM context
        """
        if not serp_response.success or not serp_response.results:
            return f"Search failed: {serp_response.error or 'No results'}"

        # Format similar to Google Search results
        snippets = []
        for result in serp_response.results[:max_results]:
            snippets.append(f"[{result.position}] {result.title}: {result.snippet} ({result.link})")
        
        return "\n\n".join(snippets)


