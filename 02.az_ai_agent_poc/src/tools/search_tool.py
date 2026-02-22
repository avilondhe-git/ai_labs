"""
Web Search Tool using Tavily API
Purpose: Enable agent to search the web for information
"""

from typing import Dict, List
import os
from tavily import TavilyClient
from config.config import settings
from config.logger import app_logger as logger


class SearchTool:
    """
    Web search tool powered by Tavily API
    
    WHY: Tavily provides:
         - Answer-focused search results
         - Real-time information
         - Free tier (1000 searches/month)
         - Snippet extraction
    """
    
    def __init__(self):
        """Initialize Tavily client"""
        
        if not settings.tavily_api_key:
            logger.warning("⚠️  Tavily API key not set. Search tool disabled.")
            self.client = None
        else:
            self.client = TavilyClient(api_key=settings.tavily_api_key)
            logger.info("SearchTool initialized")
    
    def search(self, query: str, max_results: int = 5) -> Dict:
        """
        Search the web for information
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            Dictionary with search results
        """
        
        if not self.client:
            return {
                "success": False,
                "error": "Search tool not configured (missing API key)",
                "results": []
            }
        
        try:
            # WHY: Tavily's search method returns answer + sources
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="basic"  # WHY: 'basic' is faster and cheaper
            )
            
            # Format results
            results = []
            for result in response.get("results", []):
                results.append({
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "content": result.get("content"),
                    "score": result.get("score")
                })
            
            logger.info(f"Search completed: {len(results)} results for '{query}'")
            
            return {
                "success": True,
                "query": query,
                "answer": response.get("answer", ""),  # WHY: Tavily provides direct answer
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def get_tool_definition(self) -> Dict:
        """
        Get tool definition for Semantic Kernel
        
        WHY: Semantic Kernel needs tool descriptions in specific format
        """
        return {
            "name": "search_web",
            "description": "Search the web for current information. Use this when you need up-to-date facts, news, or answers that you don't have in your training data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }


# ====================
# USAGE EXAMPLE
# ====================
if __name__ == "__main__":
    print("\n🔍 Testing Search Tool...")
    
    # Set API key for testing (get free key from https://tavily.com)
    # os.environ["TAVILY_API_KEY"] = "your_key_here"
    
    tool = SearchTool()
    
    # Test search
    query = "Latest developments in AI agents 2025"
    print(f"\nQuery: {query}")
    
    result = tool.search(query, max_results=3)
    
    if result["success"]:
        print(f"\n✓ Search successful")
        print(f"Answer: {result.get('answer', 'N/A')}")
        print(f"\nTop Results:")
        for i, res in enumerate(result["results"], 1):
            print(f"{i}. {res['title']}")
            print(f"   URL: {res['url']}")
            print(f"   Snippet: {res['content'][:150]}...")
            print()
    else:
        print(f"✗ Search failed: {result['error']}")
