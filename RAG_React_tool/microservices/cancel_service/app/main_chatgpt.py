# sql-tool/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from RAG_React_tool.Cancel_tool.sql_tool import get_sql_tool

app = FastAPI()

sql_tool_func = get_sql_tool()["func"]

class QueryInput(BaseModel):
    question: str

@app.post("/query")
async def sql_tool_query(input: QueryInput):
    try:
        response = sql_tool_func(input.question)
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}
