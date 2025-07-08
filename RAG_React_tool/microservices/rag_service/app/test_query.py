import requests
import json
from typing import Dict, Any
import argparse

# Default API URL (update if your service is running on a different port/URL)
BASE_URL = "http://localhost:8000"

def test_query(query: str, pretty: bool = False) -> Dict[str, Any]:
    """
    Send a test query to the RAG service.
    
    Args:
        query: The question to ask
        pretty: Whether to pretty-print the response
        
    Returns:
        The JSON response from the API
    """
    print("\n=== Test Query ===")
    print(f"Query: {query}")
    url = f"{BASE_URL}/query"
    headers = {"Content-Type": "application/json"}
    payload = {"query": query}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        print("inside test_query() - reached here")
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        result = response.json()
        print("result(before if statement):", result)
        
        if pretty:
            print("\n=== Response ===")
            print(f"Query: {query}")
            print("\nAnswer:")
            print(result.get("answer", "No answer provided"))
            
            if "sources" in result and result["sources"]:
                print("\nSources:")
                for i, source in enumerate(result["sources"], 1):
                    print(f"\nSource {i}:")
                    print(f"Content: {source.get('content', 'No content')[:200]}...")
                    if "metadata" in source:
                        print(f"Metadata: {source['metadata']}")
        else:
            print(json.dumps(result, indent=2))
            
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        return {}

def interactive_mode():
    """Run in interactive mode to test multiple queries."""
    print("RAG Service Tester - Interactive Mode")
    print("Type 'exit' or 'quit' to end the session")
    print("-" * 50)
    
    while True:
        try:
            query = input("\nEnter your question: ").strip()
            if query.lower() in ('exit', 'quit'):
                break
                
            if not query:
                print("Please enter a valid question.")
                continue
                
            test_query(query, pretty=True)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the RAG service API")
    parser.add_argument("--query", type=str, help="The question to ask")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Run in interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive:
        print("Interactive mode enabled")
        interactive_mode()
    elif args.query:
        print("Query mode enabled")
        test_query(args.query, pretty=True)
    else:
        print("Default test query enabled")
        # Default test query
        test_query("What is baggage allowance policy of kohinoor airlines", pretty=True)
