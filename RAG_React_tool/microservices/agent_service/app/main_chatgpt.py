# react-agent/main.py
import traceback
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import httpx
import os
import json
from typing import Dict, Any
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
import sys
import logging 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv  
load_dotenv()

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

app = FastAPI()

# Service URLs from config map/env vars
SQL_TOOL_URL = os.getenv("SQL_TOOL_URL").format(PORT=os.getenv('SQL_TOOL_PORT'))
RAG_TOOL_URL = os.getenv("RAG_TOOL_URL").format(PORT=os.getenv('RAG_TOOL_PORT'))
SCHEDULE_SERVICE_URL = os.getenv("SCHEDULE_SERVICE_URL").format(PORT=os.getenv('SCHEDULE_SERVICE_PORT'))
BOOKING_TOOL_URL = os.getenv("BOOKING_TOOL_URL").format(PORT=os.getenv('BOOKING_TOOL_PORT'))
# ---- LangChain ReAct Agent Setup ---- #
llm = ChatOpenAI(
                model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-4o"), 
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0")), 
                openai_api_key=os.getenv("OPENAI_API_KEY")
                )

react_prompt = PromptTemplate.from_template("""
You are a helpful AI agent that assists users with flight reservations, policies, cancellations, and schedules.

You have access to the following tools:
{tools}

Tool names: {tool_names}

## Rules to Follow ##
- You must reason through each step and decide whether to use a tool.
- You should always use a tool if information is needed to answer the user.
- Only return the **Final Answer** if you have all the information and don't need to use a tool.
- NEVER combine both an Action and Final Answer in the same response.
- NEVER make up data. Use tools to retrieve accurate results.
- If the user asks for a **cancellation**, first:
  1. Use `PolicyTool` to check the refund/cancellation policy.
  2. Then, ask the user for confirmation before proceeding.
  3. Only after confirmation, use `CancelTool` to cancel the flight.
- Keep your responses short and informative.

## Format to Use ##

--- TOOL USAGE ---
Thought: I need to use a tool to proceed.
Action: <tool name>
Action Input: <your input to the tool>

--- FINAL ANSWER ---
Thought: I now know the final answer.
Final Answer: <your final answer to the user>

## Example: Booking Cancellation with Confirmation ##

User: Please cancel my flight booking with PNR AF1234.

Thought: I need to check the cancellation policy before proceeding.
Action: PolicyTool
Action Input: What is the refund policy for cancellations?

-- tool returns refund policy --

Thought: I now know the refund policy. I should confirm with the user.
Final Answer: Cancelling this flight will incur a 20 fee and refund will take 5–7 days. Would you like to proceed with the cancellation?

User: Yes, go ahead.

Thought: The user has confirmed. I will now cancel the booking.
Action: CancelTool
Action Input: Cancel flight with PNR AF1234.

-- tool returns confirmation message --

Thought: The booking has been cancelled.
Final Answer: Your flight with PNR AF1234 has been successfully cancelled. A refund of ₹8,000 will be processed in 5–7 business days.

---

Begin!

Question: {input}
{agent_scratchpad}

""")

prompt = react_prompt

async def sql_tool_fn(input: str) -> str:
    """Handle flight reservation related queries"""
    async with httpx.AsyncClient() as client:
        response = await client.post(SQL_TOOL_URL, json={"question": input}, timeout=30.0)
        logger.info(f"Response: {response.json()}")
        return response.json().get("response", "[SQL Tool Error]")

async def rag_tool_fn(input: str) -> str:
    """Handle general knowledge and policy queries"""
    async with httpx.AsyncClient() as client:
        response = await client.post(RAG_TOOL_URL, json={"question": input}, timeout=30.0)
        logger.info(f"Response: {response.json()}")
        return response.json().get("response", "[RAG Tool Error]")

async def schedule_tool_fn(input: str) -> str:
    print("schedule_tool_fn")
    try:
        print(f"Query: {input}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SCHEDULE_SERVICE_URL,
                json={"question": input}
            )

            if response.status_code != 200:
                return f"[Schedule Service Error] {response.text}"
            logger.info(f"Response: {response.json()}")
            return json.dumps(response.json(), indent=2)

    except Exception as e:
        print(str(e))
        return f"[Schedule Tool Error] {str(e)}"
    
async def flight_booking_fn(input: str) -> str:
    print("flight_booking_fn")
    async with httpx.AsyncClient() as client:
        print(f"Query: {input}")
        response = await client.post(BOOKING_TOOL_URL, json={"question": input}, timeout=30.0)
        logger.info(f"Response: {response.json()}")
        #print(response.json().get("response", "[Booking Tool Error]"))
        return response.json().get("response", "[Booking Tool Error]")
        
# Tools wrapped in LangChain Tool interface
tools = [
    Tool(
        name="CancelTool",
        func=sql_tool_fn,
        coroutine=sql_tool_fn,
        description="Useful for flight reservation queries like bookings, cancellations, booking status, and refunds."
    ),
    Tool(
        name="PolicyTool",
        func=rag_tool_fn,
        coroutine=rag_tool_fn,
        description="Useful for airline policy questions, general queries, and information about baggage, check-in, and other policies."
    ),
    Tool(
        name="BookingTool",
        func=flight_booking_fn,
        coroutine=flight_booking_fn,
        description="Useful for flight bookings."
    ),
    Tool(
        name="ScheduleTool",
        func=schedule_tool_fn,
        coroutine=schedule_tool_fn,
        description="""Useful for checking flight schedules, flight status availability, and timings. 
        Example inputs: 
        - 'Show flights from Delhi to Mumbai'
        - 'What are the available flights from Bangalore to Delhi tomorrow?'
        - 'Is there a morning flight from Mumbai to Delhi?'"""
    )
]


agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors = True)

class QueryInput(BaseModel):
    question: str

@app.post("/react-agent")
async def react_agent(input: QueryInput):
    try:
        print("caling agent service...")
        result = await agent_executor.ainvoke({"input": input.question})
        print(f"react_agent result: {result}")
        return {"answer": result.get("output")}
    except Exception as e:
        #traceback.print_stack()
        print(traceback.format_exc())
        print(f"Exception in react agent: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv('AGENT_SERVICE_PORT')))