# react-agent/main.py
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import httpx
import os
import json
from typing import Dict, Any
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.chat_models import ChatOpenAI
from langchain import hub
import os
import sys

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# from config import Config

app = FastAPI()

# Service URLs from config
SQL_TOOL_URL = os.getenv("SQL_TOOL_URL", "http://localhost:8001/query")
RAG_TOOL_URL = os.getenv("RAG_TOOL_URL", "http://localhost:8002/search")
SCHEDULE_SERVICE_URL = os.getenv("SCHEDULE_SERVICE_URL", "http://localhost:8003/query")

# ---- LangChain ReAct Agent Setup ---- #
llm = ChatOpenAI(model_name="gpt-4", temperature=0)
prompt = hub.pull("hwchase17/react")

async def sql_tool_fn(input: str) -> str:
    """Handle flight reservation related queries"""
    async with httpx.AsyncClient() as client:
        response = await client.post(SQL_TOOL_URL, json={"question": input})
        return response.json().get("response", "[SQL Tool Error]")

async def rag_tool_fn(input: str) -> str:
    """Handle general knowledge and policy queries"""
    async with httpx.AsyncClient() as client:
        response = await client.post(RAG_TOOL_URL, json={"question": input})
        return response.json().get("response", "[RAG Tool Error]")

async def schedule_tool_fn(input: str) -> str:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SCHEDULE_SERVICE_URL,
                json={"question": input}
            )

            if response.status_code != 200:
                return f"[Schedule Service Error] {response.text}"

            return json.dumps(response.json(), indent=2)

    except Exception as e:
        return f"[Schedule Tool Error] {str(e)}"

# Tools wrapped in LangChain Tool interface
tools = [
    Tool(
        name="CancelTool",
        func=sql_tool_fn,
        coroutine=sql_tool_fn,
        description="Useful for flight reservation queries like bookings, cancellations, status, and refunds."
    ),
    Tool(
        name="PolicyTool",
        func=rag_tool_fn,
        coroutine=rag_tool_fn,
        description="Useful for airline policy questions, general queries, and information about baggage, check-in, and other policies."
    ),
    Tool(
        name="ScheduleTool",
        func=schedule_tool_fn,
        coroutine=schedule_tool_fn,
        description="""Useful for checking flight schedules, availability, and timings. 
        Example inputs: 
        - 'Show flights from Delhi to Mumbai'
        - 'What are the available flights from Bangalore to Delhi tomorrow?'
        - 'Is there a morning flight from Mumbai to Delhi?'"""
    )
]

agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

class QueryInput(BaseModel):
    question: str

@app.post("/react-agent")
async def react_agent(input: QueryInput):
    try:
        result = await agent_executor.ainvoke({"input": input.question})
        return {"answer": result.get("output")}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)