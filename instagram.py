import requests

def get_instagram_profile_json(username):
    url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200 and response.headers['Content-Type'] == 'application/json':
        return response.json()
    else:
        print("Failed to retrieve JSON data")
        print("Response status code:", response.status_code)
        print("Response headers:", response.headers)
        print("Response content:", response.text)
        return None

username = "sephora"
profile_data = get_instagram_profile_json(username)

if profile_data:
    print(profile_data)
else:
    print("Failed to retrieve data")
