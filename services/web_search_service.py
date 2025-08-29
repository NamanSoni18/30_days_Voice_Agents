from tavily import TavilyClient
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class WebSearchService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = TavilyClient(api_key=api_key)
        logger.info("🔍 Web Search Service initialized with Tavily")
    
    async def search_web(self, query: str, max_results: int = 3) -> List[Dict]:
        """
        Search the web using Tavily API and return top results
        """
        try:
            logger.info(f"🔍 Searching web for: '{query}' (max_results: {max_results})")
            
            # Use Tavily search API
            response = self.client.search(
                query=query,
                search_depth="basic",  # Can be "basic" or "advanced"
                max_results=max_results,
                include_answer=False,  # We don't want the AI-generated answer
                include_raw_content=False  # We don't need raw content
            )
            
            search_results = []
            
            if "results" in response and response["results"]:
                for result in response["results"]:
                    title = result.get("title", "")
                    content = result.get("content", "")
                    url = result.get("url", "")
                    
                    # Filter out results with very short or empty content
                    if content and len(content.strip()) > 20:
                        search_results.append({
                            "title": title,
                            "snippet": content,
                            "url": url
                        })
                
                logger.info(f"[SUCCESS] Found {len(search_results)} relevant web search results")
            else:
                logger.warning("⚠️ No search results found")
            
            return search_results
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Web search error for '{query}': {error_msg}")
            
            # Check for specific error types
            if "quota" in error_msg.lower() or "429" in error_msg:
                raise Exception("Web search API quota exceeded. Please check your Tavily billing and rate limits.")
            elif "403" in error_msg or "unauthorized" in error_msg.lower():
                raise Exception("Web search API authentication failed. Please check your Tavily API key.")
            elif "404" in error_msg or "not found" in error_msg.lower():
                raise Exception("Web search API endpoint not found. Please check the Tavily service status.")
            else:
                raise Exception(f"Web search failed: {error_msg}")
    
    def format_search_results_for_llm(self, search_results: List[Dict], show_urls: bool = False) -> str:
        """
        Format search results for inclusion in LLM prompt
        """
        if not search_results:
            return "No web search results found."
        
        formatted_results = "\n\nWeb Search Results:\n"
        for i, result in enumerate(search_results, 1):
            formatted_results += f"\n{i}. **{result.get('title', 'No title')}**\n"
            if show_urls:
                formatted_results += f"   URL: {result.get('url', 'No URL')}\n"
            formatted_results += f"   Content: {result.get('snippet', 'No content available')}\n"
        
        return formatted_results
    
    def is_configured(self) -> bool:
        """Check if web search service is properly configured"""
        return bool(self.api_key and self.client)
