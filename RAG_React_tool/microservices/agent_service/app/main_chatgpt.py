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
from config import Config

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
    """Handle flight schedule and availability queries"""
    try:
        # Parse the input to extract parameters
        params = parse_schedule_query(input)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SCHEDULE_SERVICE_URL,
                json=params.dict(exclude_none=True)
            )
            
            if response.status_code != 200:
                return f"[Schedule Service Error] {response.text}"
                
            data = response.json()
            if not data.get("flights"):
                return "No matching flights found."
                
            # Format the response
            return format_flight_schedule(data["flights"])
            
    except Exception as e:
        return f"[Schedule Tool Error] {str(e)}"

def parse_schedule_query(query: str) -> Dict[str, Any]:
    """Parse natural language query into schedule service parameters"""
    # This is a simplified parser - in production, you might want to use NLP here
    params = {"limit": 5}  # Default limit
    
    # Simple keyword matching (can be enhanced with more sophisticated NLP)
    if "from" in query.lower() and "to" in query.lower():
        parts = query.lower().split()
        from_idx = parts.index("from") + 1
        to_idx = parts.index("to")
        params["from_city"] = " ".join(parts[from_idx:to_idx]).strip(",. ")
        params["to_city"] = " ".join(parts[to_idx+1:]).strip(",. ")
    
    return params

def format_flight_schedule(flights: list) -> str:
    """Format flight schedule data into a human-readable string"""
    if not flights:
        return "No flights found."
        
    result = ["Here are the available flights:", ""]
    
    for i, flight in enumerate(flights, 1):
        result.append(
            f"{i}. Flight {flight.get('flight_id', 'N/A')}: "
            f"{flight.get('from_airport_code', '')} → {flight.get('to_airport_code', '')}\n"
            f"   Departure: {flight.get('departure_time', 'N/A')} | "
            f"Arrival: {flight.get('arrival_time', 'N/A')}\n"
            f"   Duration: {flight.get('flight_duration', 'N/A')} hours | "
            f"Status: {flight.get('status', 'N/A')}"
        )
    
    return "\n".join(result)

# Tools wrapped in LangChain Tool interface
tools = [
    Tool(
        name="ReservationTool",
        func=lambda x: sql_tool_fn(x),
        description="Useful for flight reservation queries like bookings, cancellations, status, and refunds."
    ),
    Tool(
        name="PolicyTool",
        func=lambda x: rag_tool_fn(x),
        description="Useful for airline policy questions, general queries, and information about baggage, check-in, and other policies."
    ),
    Tool(
        name="ScheduleTool",
        func=lambda x: schedule_tool_fn(x),
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
