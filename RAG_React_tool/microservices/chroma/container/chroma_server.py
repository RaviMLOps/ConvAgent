from fastapi import FastAPI
from rag_setup import RAGSetup
from config import Config
from fastapi import Query

app = FastAPI()

rag = RAGSetup()
vectorstore_loaded = rag.load_existing_vectorstore()

# Automatically create the vectorstore if missing
if not vectorstore_loaded:
    rag.setup_vectorstore(force_recreate=True)
    vectorstore_loaded = True

@app.get("/chroma/status")
def status():
    return {"status": "ChromaDB is running", "vectorstore_loaded": vectorstore_loaded}

@app.get("/chroma/docs")
def docs():
    if not rag.vectorstore:
        return {"docs": []}
    try:
        items = rag.vectorstore._collection.get(include=['metadatas', 'documents'], limit=5)
        return {"docs": items}
    except Exception as e:
        return {"error": str(e)}

@app.post("/chroma/reindex")
def reindex():
    try:
        rag.setup_vectorstore(force_recreate=True)
        global vectorstore_loaded
        vectorstore_loaded = True
        return {"status": "Reindexed"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/chroma/query")
def chroma_query(q: str = Query(..., description="Question to query RAG")):
    """
    Query the RAG vectorstore and return relevant answer(s).
    """
    if not rag.vectorstore:
        return {"error": "RAG vectorstore not loaded"}
    try:
        # This assumes you have a query() method in your RAG pipeline
        # that takes a question and returns an answer (or relevant docs).
        answer = rag.query(q)  # Adapt as needed to your pipeline
        return {"answer": answer}
    except Exception as e:
        return {"error": str(e)}