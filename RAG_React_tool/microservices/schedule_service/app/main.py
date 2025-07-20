# sql-tool/main.py
import sys
from pathlib import Path

from dotenv import load_dotenv  
load_dotenv()

# Add the project root to Python path
project_root = str(Path(__file__).resolve().parents[4])
sys.path.append(project_root)

from fastapi import FastAPI
from pydantic import BaseModel
from RAG_React_tool.Schedule_tool.schedule_sql_tool import get_schedule_sql_tool

app = FastAPI()

schedule_sql_tool_func = get_schedule_sql_tool()["func"]

class QueryInput(BaseModel):
    question: str

@app.post("/query")
async def schedule_sql_tool_query(input: QueryInput):
    try:
        response = schedule_sql_tool_func(input.question)
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)