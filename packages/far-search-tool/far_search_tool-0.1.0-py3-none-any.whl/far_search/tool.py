"""
FAR Search Tool - LangChain integration for Federal Acquisition Regulations search
"""

from typing import Optional, Type, Any
import requests
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun

from far_search.exceptions import FARAPIError, FARRateLimitError


class FARSearchInput(BaseModel):
    """Input schema for FAR Search Tool"""
    query: str = Field(
        description="Natural language query to search Federal Acquisition Regulations. "
                    "Examples: 'small business set aside requirements', "
                    "'cybersecurity contract clauses', 'payment terms for government contracts'"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of relevant FAR clauses to return (1-20)"
    )


class FARSearchTool(BaseTool):
    """
    LangChain tool for semantic search over Federal Acquisition Regulations (FAR).
    
    The FAR is the primary set of rules governing federal government procurement
    in the United States. This tool enables AI agents to search for relevant
    regulations, clauses, and requirements.
    
    Usage:
        # Direct API (free, rate limited)
        tool = FARSearchTool()
        
        # With RapidAPI key (paid, higher limits)
        tool = FARSearchTool(rapidapi_key="your-key-here")
        
        # Use in agent
        result = tool.invoke({"query": "small business requirements"})
    """
    
    name: str = "far_search"
    description: str = (
        "Search Federal Acquisition Regulations (FAR) by semantic query. "
        "Use this tool when you need to find government contracting rules, "
        "procurement requirements, contract clauses, compliance obligations, "
        "or any regulations related to federal acquisition. "
        "Input should be a natural language question or topic."
    )
    args_schema: Type[BaseModel] = FARSearchInput
    return_direct: bool = False
    
    # Configuration
    rapidapi_key: Optional[str] = Field(default=None, exclude=True)
    base_url: str = Field(
        default="https://far-rag-api-production.up.railway.app",
        exclude=True
    )
    rapidapi_url: str = Field(
        default="https://far-rag-federal-acquisition-regulation-search.p.rapidapi.com",
        exclude=True
    )
    timeout: int = Field(default=30, exclude=True)
    max_retries: int = Field(default=2, exclude=True)
    
    def __init__(
        self,
        rapidapi_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 2,
        **kwargs
    ):
        """
        Initialize FAR Search Tool.
        
        Args:
            rapidapi_key: Optional RapidAPI key for paid tier with higher limits.
                         If not provided, uses free tier with rate limiting.
            base_url: Override the default API URL (for self-hosted instances).
            timeout: Request timeout in seconds.
            max_retries: Number of retries on transient failures.
        """
        super().__init__(**kwargs)
        self.rapidapi_key = rapidapi_key
        if base_url:
            self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
    
    def _run(
        self,
        query: str,
        top_k: int = 5,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Execute FAR search query.
        
        Args:
            query: Natural language search query
            top_k: Number of results to return
            run_manager: Optional callback manager
            
        Returns:
            Formatted string of relevant FAR clauses
        """
        results = self._search(query, top_k)
        return self._format_results(results)
    
    def _search(self, query: str, top_k: int = 5) -> list:
        """
        Make API request to FAR RAG service.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of clause dictionaries
        """
        # Determine which endpoint to use
        if self.rapidapi_key:
            url = f"{self.rapidapi_url}/search"
            headers = {
                "X-RapidAPI-Key": self.rapidapi_key,
                "X-RapidAPI-Host": "far-rag-federal-acquisition-regulation-search.p.rapidapi.com",
                "Content-Type": "application/json"
            }
        else:
            url = f"{self.base_url}/search"
            headers = {"Content-Type": "application/json"}
        
        payload = {
            "query": query,
            "top_k": min(top_k, 20)  # Cap at 20 for reasonable response size
        }
        
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 429:
                    raise FARRateLimitError()
                
                if response.status_code != 200:
                    raise FARAPIError(
                        f"API returned status {response.status_code}: {response.text}",
                        status_code=response.status_code
                    )
                
                return response.json()
                
            except requests.exceptions.Timeout:
                last_error = FARAPIError("Request timed out", status_code=408)
            except requests.exceptions.ConnectionError:
                last_error = FARAPIError("Connection failed", status_code=503)
            except FARRateLimitError:
                raise  # Don't retry rate limits
            except Exception as e:
                last_error = FARAPIError(str(e))
        
        raise last_error
    
    def _format_results(self, results: list) -> str:
        """
        Format API results for LLM consumption.
        
        Args:
            results: List of clause dictionaries
            
        Returns:
            Formatted string optimized for LLM context
        """
        if not results:
            return "No relevant FAR clauses found for this query."
        
        formatted_parts = [f"Found {len(results)} relevant FAR clauses:\n"]
        
        for i, clause in enumerate(results, 1):
            # Extract fields with fallbacks
            clause_id = clause.get("id", "Unknown")
            title = clause.get("title", "Untitled")
            source = clause.get("source", "")
            url = clause.get("url", "")
            text = clause.get("text", "")
            score = clause.get("similarity_score", 0)
            
            # Truncate text if too long
            if len(text) > 500:
                text = text[:500] + "..."
            
            formatted_parts.append(
                f"---\n"
                f"**{i}. {title}** (FAR {clause_id})\n"
                f"Relevance: {score:.1%}\n"
                f"Source: {source}\n"
                f"URL: {url}\n\n"
                f"{text}\n"
            )
        
        return "\n".join(formatted_parts)
    
    async def _arun(
        self,
        query: str,
        top_k: int = 5,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Async version of FAR search (falls back to sync for simplicity).
        """
        # For simplicity, use sync version. Can be upgraded to aiohttp if needed.
        return self._run(query, top_k, run_manager)

