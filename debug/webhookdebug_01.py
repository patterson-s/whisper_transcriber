import requests
webhook_url = "https://discordapp.com/api/webhooks/1374483126415261826/GuVwTpHAGx50T2U62yW0Sl2ihd80zMX5fZIUhiW8onvyysbifLWlLyDt3UZ-rP_8vM72"
response = requests.post(webhook_url, json={"content": "Test message"})
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")