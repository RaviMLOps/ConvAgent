from fastapi import FastAPI
from chromadb import PersistentClient

app = FastAPI()

client = PersistentClient(path="/app/chroma-data")

@app.get("/status")
def health_check():
    return {"status": "ChromaDB is running"}

