import requests

BASE_URL = "http://127.0.0.1:5000"

# Test the home endpoint
response = requests.get(BASE_URL + "/")
print("Home Endpoint:", response.text)

# Test the risk assessment
risk_data = {
    "answers": {
        "age": "20-40",
        "income": "50000+ USD",
        "horizon": "5+ years",
        "amount": "50K+ USD"
    }
}
response = requests.post(BASE_URL + "/risk", json=risk_data)
print("Risk Assessment:", response.json())

# Test the fetch stock data endpoint
response = requests.get(BASE_URL + "/fetch")
print("Fetch Data:", response.json())

# Test the recommend endpoint
recommend_data = {
    "risk_level": "Medium",
    "diversify": True
}
response = requests.post(BASE_URL + "/recommend", json=recommend_data)
print("Recommendations:", response.json())
