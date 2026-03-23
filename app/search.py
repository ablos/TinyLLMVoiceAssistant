import httpx
from app.config import config

async def search(query: str, categories: str = "general") -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{config.searxng.url}/search",
            params={"q": query, "format": "json", "categories": categories},
        )
        resp.raise_for_status()
        data = resp.json()
        
    results = data.get("results", [])[:5]
    
    if not results:
        return "No results found."
    
    # Format results for LLM
    formatted = "\n\n".join(
        f"Title: {r.get('title', '')}\nSnippet: {r.get('content', '')}"
        for r in results
    )
    
    return formatted