"""
Quick test script to verify Twitter API connectivity
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

print(f"Bearer token loaded: {bearer_token[:20]}..." if bearer_token else "NO TOKEN FOUND")
print(f"Token length: {len(bearer_token)}" if bearer_token else "")

if not bearer_token:
    print("\n❌ TWITTER_BEARER_TOKEN not found in .env file")
    exit(1)

# Test API connectivity
url = "https://api.twitter.com/2/tweets/search/recent"
headers = {
    "Authorization": f"Bearer {bearer_token}"
}
params = {
    "query": "Elon Musk",
    "max_results": 10,
    "tweet.fields": "author_id,created_at,text",
}

print(f"\n🔍 Testing Twitter API with query: 'Elon Musk'")
print(f"URL: {url}")

try:
    response = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"\n📊 Response Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        tweets = data.get('data', [])
        print(f"\n✅ SUCCESS! Found {len(tweets)} tweets")
        if tweets:
            print(f"\nSample tweet:")
            print(f"  Text: {tweets[0].get('text', 'N/A')[:100]}...")
    else:
        print(f"\n❌ ERROR!")
        print(f"Response Body:\n{response.text}")
        
except Exception as e:
    print(f"\n❌ Exception: {type(e).__name__}: {e}")
