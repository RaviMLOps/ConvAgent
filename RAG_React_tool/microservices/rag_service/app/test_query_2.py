import requests
import json
import sys

# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)

# Default API URL
BASE_URL = "http://localhost:8002"  # Default port for main_chatgpt.py
SEARCH_ENDPOINT = f"{BASE_URL}/search"

def test_query(question: str, top_k: int = 3):
    """Simple test function to query the RAG service with detailed logging"""
    print(f"\n=== Testing Query ===")
    print(f"Question: {question}")
    
    # Prepare the request
    headers = {"Content-Type": "application/json"}
    payload = {"question": question, "top_k": top_k}
    
    logging.info(f"Sending request to {SEARCH_ENDPOINT}")
    logging.debug(f"Request payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Make the request
        response = requests.post(SEARCH_ENDPOINT, headers=headers, json=payload)
        logging.info(f"Response status: {response.status_code}")
        
        # Check for HTTP errors
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        logging.debug(f"Raw response: {json.dumps(result, indent=2)}")
        
        # Print the response in a simple format
        print("\n=== Response ===")
        print(f"Status: {response.status_code}")
        
        if "response" in result:
            print(f"\nAnswer: {result['response']}")
        
        if "sources" in result and result["sources"]:
            print(f"\nFound {len(result['sources'])} relevant chunks:")
            for i, chunk in enumerate(result['sources'], 1):
                text = chunk.get('text', chunk.get('content', str(chunk)))
                print(f"\nChunk {i}:")
                print(text[:300] + ("..." if len(text) > 300 else ""))
        else:
            print("\nNo relevant chunks found.")
        
        return result
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"Response status: {e.response.status_code}")
            logging.error(f"Response content: {e.response.text}")
        print(f"\nError: {str(e)}")
        return None

def interactive_mode():
    """Simple interactive mode for testing"""
    print("\n=== Interactive Mode ===")
    print("Enter your question or 'exit' to quit")
    
    while True:
        try:
            question = input("\nQuestion: ").strip()
            if not question:
                continue
                
            if question.lower() in ('exit', 'quit'):
                break
                
            test_query(question)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the RAG service API")
    parser.add_argument("--query", "-q", type=str, help="Question to ask")
    parser.add_argument("--interactive", "-i", action="store_true", 
                      help="Run in interactive mode")
    parser.add_argument("--debug", "-d", action="store_true",
                      help="Enable debug logging")
    parser.add_argument("--url", type=str, default=BASE_URL,
                      help=f"Base URL of the API (default: {BASE_URL})")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    # Update base URL if provided
    if args.url != BASE_URL:
        BASE_URL = args.url.rstrip('/')
    
    # Run in the appropriate mode
    if args.interactive or not args.query:
        interactive_mode()
    else:
        test_query(args.query)
