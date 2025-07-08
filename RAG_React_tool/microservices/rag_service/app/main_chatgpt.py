# rag-tool/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from RAG_tool.rag_chain import RAGPipeline
from database.chroma_db.rag_setup import RAGSetup

app = FastAPI()

class QueryInput(BaseModel):
    question: str

# Initialize vector store and chain
rag_setup = RAGSetup()
rag_setup.load_existing_vectorstore()
retriever = rag_setup.vectorstore.as_retriever()
rag_chain = RAGPipeline().create_rag_chain(retriever)

@app.post("/search")
async def rag_tool_search(input: QueryInput):
    try:
        result = rag_chain.invoke(input.question)
        return {"response": result}
    except Exception as e:
        return {"error": str(e)}
