import requests
import os

def search_brave(query):
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

