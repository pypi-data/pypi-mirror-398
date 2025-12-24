# ABOUTME: Unified search tool executor with Google Search + Serper.dev fallback support
# ABOUTME: Handles search operations with automatic fallback when Google Search quota is exhausted

import logging
import os
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class SearchToolExecutor:
    """Unified search tool executor with fallback support.
    
    Primary: Google Search (free, built into Gemini)
    Fallback: Serper.dev (paid API)
    """

    def __init__(self):
        """Initialize search executor with Serper.dev fallback."""
        self.serper_provider = None
        
        # Initialize Serper.dev provider if API key available
        try:
            from .serper_provider import SerperProvider
            
            api_key = os.getenv("SERPER_API_KEY")
            
            if api_key:
                self.serper_provider = SerperProvider(api_key)
                logger.info("✅ Serper.dev fallback initialized")
            else:
                logger.warning("⚠️  Serper.dev API key not found - fallback disabled")
        except ImportError:
            logger.warning("⚠️  Serper.dev provider not available")

    async def execute_search_with_fallback(
        self, 
        query: str, 
        primary_error: Optional[Exception] = None,
        max_results: int = 5,
        country: str = "us",
        language: str = "en"
    ) -> str:
        """Execute search with Serper.dev fallback when Google Search fails.

        Args:
            query: Search query string
            primary_error: Error from primary Google Search (if any)
            max_results: Maximum number of results to return
            country: Country code for localization
            language: Language code

        Returns:
            Formatted search results string for LLM consumption
        """
        # Check if we should use fallback
        should_use_fallback = False
        
        if primary_error:
            error_str = str(primary_error).lower()
            quota_exhausted = any(keyword in error_str for keyword in [
                "rate limit", "quota", "resource_exhausted", "429", 
                "too many requests", "usage limit", "billing"
            ])
            
            if quota_exhausted:
                should_use_fallback = True
                logger.warning(f"🚨 Google Search quota exhausted, activating Serper.dev fallback")

        if should_use_fallback and self.serper_provider:
            return await self._execute_serper_search(
                query, max_results, country, language
            )
        elif primary_error:
            # No fallback available or error is not quota-related
            logger.error(f"❌ Search failed and no fallback available: {primary_error}")
            return f"Search failed: {str(primary_error)}"
        else:
            # This shouldn't happen - we're only called when there's an error
            logger.warning("⚠️  SearchToolExecutor called without error")
            return f"Search unavailable for: {query}"

    async def _execute_serper_search(
        self, 
        query: str, 
        max_results: int,
        country: str,
        language: str
    ) -> str:
        """Execute search using Serper.dev provider.

        Args:
            query: Search query string
            max_results: Maximum number of results
            country: Country code
            language: Language code

        Returns:
            Formatted search results string
        """
        try:
            logger.info(f"🔍 Executing Serper.dev search: '{query}' ({country}, {language})")
            
            response = await self.serper_provider.search(
                query=query,
                num_results=max_results * 2,  # Get more results, format fewer
                language=language,
                country=country
            )

            if not response.get("success"):
                error_msg = f"Serper.dev search failed: {response.get('error', 'Unknown error')}"
                logger.error(f"❌ {error_msg}")
                return error_msg

            # Format results for LLM consumption
            formatted_results = self.serper_provider.format_for_llm(
                response, max_results=max_results
            )

            # Log success metrics
            logger.info(
                f"✅ Serper.dev fallback successful: {len(response.get('results', []))} results"
            )
            
            return formatted_results

        except Exception as e:
            error_msg = f"Serper.dev fallback error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return error_msg

    def is_fallback_available(self) -> bool:
        """Check if Serper.dev fallback is available."""
        return self.serper_provider is not None and self.serper_provider.is_configured()

    def get_fallback_info(self) -> Dict[str, Any]:
        """Get information about fallback configuration."""
        if not self.serper_provider:
            return {
                "available": False,
                "reason": "Serper.dev provider not initialized"
            }

        if not self.serper_provider.is_configured():
            return {
                "available": False,
                "reason": "Serper.dev API key not configured"
            }

        return {
            "available": True,
            "provider": self.serper_provider.name,
            "api_key_set": bool(self.serper_provider.api_key)
        }


# Global instance for reuse across requests
_search_executor = None


def get_search_executor() -> SearchToolExecutor:
    """Get global search executor instance."""
    global _search_executor
    if _search_executor is None:
        _search_executor = SearchToolExecutor()
    return _search_executor


