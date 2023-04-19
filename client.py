import requests

try:
    response = requests.get('http://localhost:54789/example', timeout=5)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"Request error: {str(e)}")
else:
    print(f"Status code: {response.status_code}")
    print(f"Response JSON: {response.json()}")
