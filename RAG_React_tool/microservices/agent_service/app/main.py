# agent_service/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
from typing import Dict, Any, List, Optional
from enum import Enum
import json
from datetime import datetime
import logging
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI()

# Redis setup
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
redis_client = redis.from_url(REDIS_URL)

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class ToolName(str, Enum):
    RAG = "rag"
    RESERVATION = "reservation"
    TIME = "time"

class AgentResponse(BaseModel):
    response: str
    conversation_id: str
    tool_used: Optional[str] = None

# Service URLs
SERVICES = {
    "rag": os.getenv("RAG_SERVICE_URL", "http://rag-service:8000"),
    "reservation": os.getenv("RESERVATION_SERVICE_URL", "http://reservation-service:8002")
}

async def call_tool(tool_name: ToolName, query: str) -> Dict[str, Any]:
    """Call the appropriate tool based on the tool name."""
    try:
        if tool_name == ToolName.TIME:
            return {"result": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        service_url = SERVICES.get(tool_name.value)
        if not service_url:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{service_url}/query",
                json={"query": query}
            )
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {str(e)}")
        return {"error": str(e), "status": "error"}

def determine_tool(query: str) -> ToolName:
    """Determine which tool to use based on the query."""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ["time", "date", "current", "now", "today"]):
        return ToolName.TIME
    
    if any(word in query_lower for word in ["book", "reservation", "flight", "cancel", "pnr", "ticket"]):
        return ToolName.RESERVATION
    
    return ToolName.RAG

@app.get("/home")
def index():
    return "Welcome to the API!"
    
@app.post("/query", response_model=AgentResponse)
async def query(request: QueryRequest):
    """Handle incoming queries with ReAct agent logic."""
    try:
        # Generate or use provided conversation ID
        conversation_id = request.conversation_id or f"conv_{int(datetime.now().timestamp())}"
        
        # Get conversation history from Redis
        history = []
        try:
            history_data = await redis_client.get(f"conv:{conversation_id}")
            if history_data:
                history = json.loads(history_data)
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
        
        # Determine which tool to use
        tool_to_use = determine_tool(request.query)
        
        # Call the appropriate tool
        tool_response = await call_tool(tool_to_use, request.query)
        
        # Format the response
        response_text = "I'm not sure how to respond to that."
        if tool_to_use == ToolName.RAG:
            results = tool_response.get("results", [])
            response_text = results[0] if results else "I couldn't find relevant information."
        elif tool_to_use == ToolName.RESERVATION:
            response_text = tool_response.get("result", "I couldn't process your reservation request.")
        elif tool_to_use == ToolName.TIME:
            response_text = f"The current time is: {tool_response.get('result')}"
        
        # Update conversation history
        history.append({
            "query": request.query,
            "tool_used": tool_to_use.value,
            "response": response_text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Save updated history
        try:
            await redis_client.set(
                f"conv:{conversation_id}",
                json.dumps(history),
                ex=86400  # Expire after 24 hours
            )
        except Exception as e:
            logger.error(f"Error saving conversation history: {e}")
        
        return AgentResponse(
            response=response_text,
            conversation_id=conversation_id,
            tool_used=tool_to_use.value
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history."""
    try:
        history_data = await redis_client.get(f"conv:{conversation_id}")
        if not history_data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return json.loads(history_data)
    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        await redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        logger.error(f"Redis connection error: {e}")
        return {"status": "degraded", "redis": "disconnected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 8001)))