"""
FAR RAG API Client - Async HTTP client for the Federal Acquisition Regulations API

Bot-First monetization: Returns exact error strings for quota/payment issues
so AI agents can understand and communicate limits to users.
"""

import os
import json
import httpx

# RapidAPI configuration
RAPIDAPI_HOST = os.getenv(
    "RAPIDAPI_HOST",
    "far-rag-federal-acquisition-regulation-search.p.rapidapi.com"
)
RAPIDAPI_BASE_URL = f"https://{RAPIDAPI_HOST}"

# Default timeout for API requests (seconds)
DEFAULT_TIMEOUT = 30.0


async def query_far_backend(
    query: str,
    api_key: str,
    top_k: int = 5,
    timeout: float = DEFAULT_TIMEOUT
) -> str:
    """
    Query the FAR RAG API for relevant federal acquisition regulation clauses.
    
    Args:
        query: Natural language search query
        api_key: RapidAPI key for authentication and billing
        top_k: Number of results to return (1-20)
        timeout: Request timeout in seconds
        
    Returns:
        str: JSON string of clauses on success, or error message string on failure
    """
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "top_k": min(max(top_k, 1), 20)  # Clamp between 1-20
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{RAPIDAPI_BASE_URL}/search",
                json=payload,
                headers=headers
            )
            
            # === CRITICAL: Bot-friendly error handling ===
            
            if response.status_code == 200:
                # Success: Return raw JSON list as string
                return json.dumps(response.json(), indent=2)
            
            elif response.status_code == 429:
                # Quota exceeded - EXACT message for bots to understand
                return (
                    "Error: Quota Exceeded. Monthly free limit reached. "
                    "Please upgrade your RapidAPI plan to continue."
                )
            
            elif response.status_code in (402, 403):
                # Payment required
                return (
                    "Error: Payment Required. Your API subscription has expired "
                    "or requires payment. Please check your RapidAPI account."
                )
            
            elif response.status_code >= 500:
                return "Error: FAR RAG Service Unavailable. Please try again later."
            
            else:
                return f"Error: Unexpected API response (HTTP {response.status_code})"
                
    except httpx.TimeoutException:
        return "Error: Request timed out. The FAR service may be experiencing high load."
    
    except httpx.ConnectError:
        return "Error: Connection failed. Please check your network connection."
    
    except Exception as e:
        return f"Error: {str(e)}"
