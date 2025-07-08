# react-agent/main.py
from fastapi import FastAPI, Request
from pydantic import BaseModel
import httpx
import os
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.chat_models import ChatOpenAI
from langchain import hub

app = FastAPI()

SQL_TOOL_URL = os.getenv("SQL_TOOL_URL", "http://localhost:8001/query")
RAG_TOOL_URL = os.getenv("RAG_TOOL_URL", "http://localhost:8002/search")

# ---- LangChain ReAct Agent Setup ---- #
llm = ChatOpenAI(model_name="gpt-4", temperature=0)
prompt = hub.pull("hwchase17/react")

async def sql_tool_fn(input: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(SQL_TOOL_URL, json={"question": input})
        return response.json().get("response", "[SQL Tool Error]")

async def rag_tool_fn(input: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(RAG_TOOL_URL, json={"question": input})
        return response.json().get("response", "[RAG Tool Error]")

# Tools wrapped in LangChain Tool interface
tools = [
    Tool(
        name="SQLTool",
        func=lambda x: sql_tool_fn(x),
        description="Useful for flight reservation queries like cancellations, status, and refund."
    ),
    Tool(
        name="RAGTool",
        func=lambda x: rag_tool_fn(x),
        description="Useful for airline policy questions and general queries."
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
