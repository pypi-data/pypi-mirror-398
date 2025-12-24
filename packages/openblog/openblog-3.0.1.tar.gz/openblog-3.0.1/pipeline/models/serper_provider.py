"""
Serper.dev Search Provider

Uses Serper.dev API for Google Search fallback.
Simpler than DataForSEO, faster, more reliable.

API: https://serper.dev/api/search
Cost: Check Serper Dev pricing
"""

import logging
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)


@dataclass
class SerperSearchResult:
    """Serper Dev search result."""
    title: str
    link: str
    snippet: str
    position: int = 0


class SerperProvider:
    """Serper.dev provider for Google Search fallback.
    
    Provides search results including:
    - Organic results
    - Featured snippets
    - People Also Ask
    - Related searches
    
    Simpler and faster than DataForSEO.
    """
    
    API_URL = "https://google.serper.dev/search"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Serper.dev provider.
        
        Args:
            api_key: Serper Dev API key (defaults to env var SERPER_API_KEY)
        """
        self.name = "serper"
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        
        if not self.api_key:
            logger.warning("⚠️  Serper Dev API key not found - search fallback disabled")
        else:
            logger.info("✅ Serper Dev search provider initialized")
    
    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        return bool(self.api_key)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers."""
        return {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        language: str = "en",
        country: str = "us"
    ) -> Dict[str, Any]:
        """Execute search using Serper.dev.
        
        Args:
            query: Search query string
            num_results: Number of results to return
            language: Language code (e.g., "en")
            country: Country code (e.g., "us")
            
        Returns:
            Dict with search results and metadata
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Serper Dev not configured",
                "results": []
            }
        
        logger.info(f"🔍 Executing Serper.dev search: '{query}' ({country}, {language})")
        
        payload = {
            "q": query,
            "num": min(num_results, 100),  # Serper Dev max is 100
        }
        
        # Add location if provided
        if country:
            payload["gl"] = country  # Google location
        if language:
            payload["hl"] = language  # Google language
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.API_URL,
                    json=payload,
                    headers=self._get_headers(),
                )
                
                if response.status_code != 200:
                    error_msg = f"Serper Dev API error: HTTP {response.status_code}"
                    logger.error(f"❌ {error_msg}")
                    logger.debug(f"Response: {response.text[:200]}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "results": []
                    }
                
                data = response.json()
                results = self._parse_results(data)
                
                logger.info(f"✅ Serper.dev search successful: {len(results)} results")
                return {
                    "success": True,
                    "results": results,
                    "organic": data.get("organic", []),
                    "answerBox": data.get("answerBox"),
                    "peopleAlsoAsk": data.get("peopleAlsoAsk", []),
                    "relatedSearches": data.get("relatedSearches", [])
                }
                
        except Exception as e:
            error_msg = f"Serper.dev search error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "results": []
            }
    
    def _parse_results(self, data: Dict[str, Any]) -> List[SerperSearchResult]:
        """Parse Serper.dev API response."""
        results = []
        
        # Serper Dev structure: data["organic"] contains organic results
        organic_results = data.get("organic", [])
        
        for idx, item in enumerate(organic_results, 1):
            results.append(SerperSearchResult(
                title=item.get("title", ""),
                link=item.get("link", ""),
                snippet=item.get("snippet", ""),
                position=idx
            ))
        
        return results
    
    def format_for_llm(self, response: Dict[str, Any], max_results: int = 5) -> str:
        """Format search results for LLM consumption.
        
        Args:
            response: Response dict from search()
            max_results: Maximum number of results to format
            
        Returns:
            Formatted string for LLM
        """
        if not response.get("success"):
            return f"Search failed: {response.get('error', 'Unknown error')}"
        
        results = response.get("results", [])[:max_results]
        
        if not results:
            return "No search results found"
        
        formatted_lines = ["## Web Research Results (from Serper.dev)\n"]
        
        for result in results:
            formatted_lines.append(
                f"{result.position}. **{result.title}**\n"
                f"   URL: {result.link}\n"
                f"   {result.snippet}\n"
            )
        
        # Add answer box if available
        answer_box = response.get("answerBox")
        if answer_box:
            formatted_lines.append("\n## Featured Answer\n")
            if answer_box.get("answer"):
                formatted_lines.append(f"{answer_box.get('answer')}\n")
            if answer_box.get("link"):
                formatted_lines.append(f"Source: {answer_box.get('link')}\n")
        
        return "\n".join(formatted_lines)

