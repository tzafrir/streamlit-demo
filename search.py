"""
A module for performing web searches using the Brave Search API.

This module provides functionality to search the web using Brave's search engine,
which offers privacy-focused web search capabilities.

Required Environment Variables:
    - BRAVE_API_KEY: API key for accessing Brave Search API
"""

import requests
import os

def search_brave(query):
    """
    Perform a web search using the Brave Search API.
    
    Args:
        query (str): The search query string to be executed
        
    Returns:
        str: JSON response text containing search results, including titles, 
             descriptions, and URLs of the top 5 search results
        
    Note:
        The function includes debug print statements for monitoring API responses
        and troubleshooting.
    """
    url = f'https://api.search.brave.com/res/v1/web/search?q={query}&count=5'
    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'X-Subscription-Token': os.getenv("BRAVE_API_KEY")
    }
    
    response = requests.get(url, headers=headers)
    print(f"Debug: Response status code: {response.status_code}")
    print(f"Debug: Response text: {response.text}")
    
    return response.text

