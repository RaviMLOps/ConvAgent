from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os
import requests
from typing import List, Dict, Any

# Add project root to Python path (go up three levels from current file)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import from the root level modules
try:
    from RAG_tool.rag_chain import RAGPipeline
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Current sys.path: {sys.path}")
    raise

app = FastAPI()

# ChromaDB server configuration from environment variables (ConfigMap in K8s)
CHROMA_SERVER = os.getenv("CHROMA_SERVER_HOST", "http://localhost:8000")
CHROMA_QUERY_ENDPOINT = os.getenv("CHROMA_QUERY_ENDPOINT", f"{CHROMA_SERVER}/chroma/query")
CHROMA_STATUS_ENDPOINT = os.getenv("CHROMA_STATUS_ENDPOINT", f"{CHROMA_SERVER}/chroma/status")

print("FastAPI app initialized")

class QueryInput(BaseModel):
    question: str
    top_k: int = 3  # Number of chunks to retrieve

def query_chroma_server(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Query the ChromaDB server for relevant document chunks
    """
    try:
        response = requests.get(
            CHROMA_QUERY_ENDPOINT,
            params={"q": query, "top_k": top_k}
        )
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.RequestException as e:
        print(f"Error querying ChromaDB server: {str(e)}")
        return []

# Initialize RAG pipeline
try:
    print("Initializing RAG pipeline...")
    rag_chain = RAGPipeline()
    print("✓ RAG pipeline initialized successfully")
except Exception as e:
    print(f"✗ Error initializing RAG pipeline: {str(e)}")
    raise

@app.get("/chroma/status")
async def chroma_status():
    """Check if ChromaDB server is running"""
    try:
        response = requests.get(CHROMA_STATUS_ENDPOINT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"ChromaDB server error: {str(e)}")

@app.post("/search")
async def rag_tool_search(input: QueryInput):
    print(f"Received search query: {input.question}")

    try:
        # 1. First retrieve relevant chunks from ChromaDB
        print(f"Querying ChromaDB for relevant chunks...")
        chunks = query_chroma_server(input.question, input.top_k)

        if not chunks:
            return {"response": "No relevant information found in the knowledge base."}

        # 2. Format the context from chunks
        context = "\n\n".join([chunk.get("text", "") for chunk in chunks])

        # 3. Generate response using the RAG chain with the retrieved context
        print("Generating response with RAG...")
        result = rag_chain.invoke({
            "question": input.question,
            "context": context
        })

        print("✓ Response generated successfully")
        return {
            "response": result,
            "sources": chunks  # Include the source chunks for reference
        }

    except Exception as e:
        print(f"Error in rag_tool_search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    host = "127.0.0.1"  # Changed from 0.0.0.0 to 127.0.0.1 for local access
    port = 8002

    print("\n" + "="*50)
    print(f"Starting FastAPI server on http://{host}:{port}")
    print("Endpoints:")
    print(f"  - Status:   http://{host}:{port}/chroma/status")
    print(f"  - Search:   http://{host}:{port}/search (POST)")
    print("="*50 + "\n")

    uvicorn.run(app, host=host, port=port, log_level="info")
