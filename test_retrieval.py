import requests
import json

API_URL = "http://localhost:8000/retrieve/"

def test_retrieval():
    # Search for something likely in the ingested docs
    query = "Operating Procedure"
    
    print(f"Testing retrieval for query: '{query}'")
    
    try:
        response = requests.post(API_URL, params={"query": query, "top_k": 3})
        
        if response.status_code == 200:
            results = response.json()
            print(json.dumps(results, indent=2))
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_retrieval()
