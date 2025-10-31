# modules/google_search.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def perform_google_search(query, num_results=3):
    api_key = os.getenv("SERPAPI_API_KEY")
    
    if not api_key or api_key.startswith("9e448"):
        return ["🔒 Invalid SERPAPI key - please update your .env file with a valid key"]
    
    try:
        params = {
            "q": query,
            "engine": "google",
            "api_key": api_key,
            "num": num_results
        }
        response = requests.get(
            "https://serpapi.com/search",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        results = []
        for item in response.json().get("organic_results", [])[:num_results]:
            title = item.get("title", "No title")
            snippet = item.get("snippet", "No description available")
            results.append(f"{title}: {snippet}")
        
        return results if results else ["No results found"]
        
    except Exception as e:
        return [f"⚠️ Search error: {str(e)}"]