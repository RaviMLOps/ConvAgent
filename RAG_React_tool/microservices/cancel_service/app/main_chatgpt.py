# sql-tool/main.py
from fastapi import FastAPI
from pydantic import BaseModel

import os
import sys

try:
    from RAG_React_tool.Cancel_tool.sql_tool import get_sql_tool
except:
    print((os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
    sys.path.append((os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
    from Cancel_tool.sql_tool import get_sql_tool

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)