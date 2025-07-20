# test_code.py
import requests

BASE_URL = "http://localhost:8000"

sample_queries = [
    "Show me the status of my flight with PNR number AB1234",
    "Cancel my reservation for PNR number CD5678",
    "What is the refund status for PNR EF9012?",
    "List all bookings made by passenger named Rajiv Kumar"
]

def test_react_agent_tool():
    for query in sample_queries:
        print(f"\nTesting query: {query}")
        try:
            response = requests.post(f"{BASE_URL}/react-agent", json={"question": query})
            if response.ok:
                print("Response:")
                print(response.json().get("response", "[No output]"))
            else:
                print(f"Error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    test_react_agent_tool()
