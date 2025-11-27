import requests

try:
    response = requests.get('http://127.0.0.1:5000/static/wines.json')
    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.content)}")
    print(f"First 100 chars: {response.text[:100]}")
except Exception as e:
    print(f"Error: {e}")
