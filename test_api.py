import requests

token = "14febdd1820f1a4aa11e1bf920cd3a38950b77a5"
url = f"https://api.tiingo.com/tiingo/daily/SPY/prices?startDate=2022-01-01&token={token}"

print("Testing Tiingo API...")
response = requests.get(url)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Rows received: {len(data)}")
    if len(data) > 0:
        latest = data[-1]
        print(f"Latest date: {latest['date']}")
        print(f"Latest close: ${latest['close']:.2f}")
        print("API is working!")
else:
    print(f"Error: {response.text}")