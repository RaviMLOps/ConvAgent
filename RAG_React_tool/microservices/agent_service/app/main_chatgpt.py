# react-agent/main.py
from fastapi import FastAPI, Request, HTTPException, Depends
from pydantic import BaseModel, Field
import httpx
import os
import json
from typing import Dict, Any, List, Optional
from langchain.agents import Tool, AgentExecutor, initialize_agent
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate, MessagesPlaceholder, ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema import SystemMessage, HumanMessage, AIMessage
import sys
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv  
load_dotenv()

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory conversation store (in production, use a database)
conversation_store = {}

# Service URLs from config map/env vars
SQL_TOOL_URL = os.getenv("SQL_TOOL_URL", "http://localhost:8003/query")
RAG_TOOL_URL = os.getenv("RAG_TOOL_URL", "http://localhost:8002/search")
SCHEDULE_SERVICE_URL = os.getenv("SCHEDULE_SERVICE_URL", "http://localhost:8001/query")
BOOKING_SERVICE_URL = os.getenv("BOOKING_SERVICE_URL", "http://localhost:8005/query")

# ---- LangChain ReAct Agent Setup ---- #
llm = ChatOpenAI(
                model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-4o"), 
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0")), 
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                )

# Define the system message template
system_message = """You are a helpful travel assistant that helps users with flight information, bookings, and cancellations. You have access to tools that can retrieve flight details, check booking status, and process cancellations.

Tool names: {tool_names}
For policy related questions , just understand query and get response from rag tool.We have policy for baggage, refund, cancellation, web-checkin and more.
Pay attention to complete conversation history provided by user to get context of conversation.If you are able to retreive context from previous conversaton than use it to answer user query.
If you are not able to retreive context from previous conversaton than ask user to provide context.
## Rules to Follow ##
1. Always verify if you have complete information before using tools:
   - For flight status: Require Flight ID or PNR number
   - For booking details: Require PNR number
   - For cancellations: Require PNR number and confirmation
   - For schedule: Require origin , destination , date
   
2. If information is missing, ask specific questions to get the required details.
   Example: "Could you please provide the PNR number for your booking?"

3. NEVER query for all flights or bookings at once. Always require specific identifiers.
   - For general flight queries, ask for specific details like:
     * Source and destination cities
     * Travel dates
     * Preferred airlines or flight times
     * Number of passengers
   - For booking-related queries, always ask for the PNR number first

4. When using tools:
   - Be specific in your queries
   - Only request necessary information
   - Use exact identifiers when available
   - If a query is too broad, ask targeted questions to narrow down the search

5. Response Guidelines:
   - Keep responses concise and helpful
   - Format tool responses for better readability
   - Always confirm actions that modify bookings
   - Never expose sensitive information

## Required Information for Common Queries ##
- Flight Status: Flight ID or Flight Number + Date
- Flight Search: Source City, Destination City, Travel Date
- Booking Details: PNR Number
- Flight Timings: Flight Number or Route + Date
- Fare Information: Route + Travel Date + Class
- Booking Details: PNR Number
- Cancellation: PNR Number + Confirmation
- Refund Status: PNR Number
- Flight Schedule: Origin, Destination, and Date

## Format to Use ##

When using a tool:
```
Thought: I need to use a tool to proceed.
Action: tool_name
Action Input: input_to_the_tool
```

When asking for more information:
```
Final Answer: To help you better, I need some additional information: [specific information needed]. Could you please provide [specific details]?
```

When giving the final answer:
```
Final Answer: [Your response here]
```


## Example: Booking Cancellation with Confirmation ##

User: Please cancel my flight booking with PNR AF1234.
Thought: I need to check the cancellation policy before proceeding.
Action: RagTool
Action Input: What is the refund policy for flight cancellations?
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
"""

# We'll use a simple string prompt since initialize_agent will handle the chat format
## Example: Policy Query ##

# User: What is the baggage allowance for economy class on international flights?
# Thought: This is a policy-related question that requires checking airline policies.
# Action: RagTool
# Action Input: What is the baggage allowance for economy class on international flights?
# -- tool returns baggage policy --
# Thought: I have the baggage policy information. I should present it clearly to the user.
# Final Answer: For international economy class flights, the standard baggage allowance is typically 1 piece of cabin baggage up to 7 kg (15 lbs) with maximum dimensions of 115 cm (45 inches), and 1 piece of check-in baggage up to 23 kg (50 lbs). However, this may vary by airline and route. Would you like me to check the specific policy for your airline?


async def sql_tool_fn(input: str, conversation_history: list = None) -> str:
    """Handle flight reservation related queries with conversation context"""
    payload = {
        "question": input,
        "conversation_history": conversation_history or []
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(SQL_TOOL_URL, json=payload)
        return response.json().get("response", "[SQL Tool Error]")

async def rag_tool_fn(input: str, conversation_history: list = None) -> str:
    """Handle general knowledge and policy queries with conversation context"""
    try:
        payload = {
            "question": input,
            "conversation_history": conversation_history or []
        }
        print("Payload to rag tool: ", payload)

        async with httpx.AsyncClient() as client:
            response = await client.post(RAG_TOOL_URL, json=payload, timeout=30.0)
            response_data = response.json()
            print("Response from rag tool: ", response_data)
            
            # Handle different response formats
            if isinstance(response_data, dict):
                if "response" in response_data:
                    return response_data["response"]
                elif "answer" in response_data:  # Handle alternative response format
                    return response_data["answer"]
                elif "text" in response_data:  # Handle another alternative format
                    return response_data["text"]
                else:
                    # If no recognized key, return the entire response as string
                    return str(response_data)
            elif isinstance(response_data, str):
                return response_data
            else:
                return str(response_data)
                
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error occurred: {str(e)}"
        print(error_msg)
        return f"[RAG Tool Error] {error_msg}"
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse RAG service response: {str(e)}"
        print(error_msg)
        return "[RAG Tool Error] Could not process the response from the knowledge base."
    except Exception as e:
        error_msg = f"Unexpected error in RAG tool: {str(e)}"
        print(error_msg)
        return f"[RAG Tool Error] {error_msg}"

async def schedule_tool_fn(input: str, conversation_history: list = None) -> str:
    """Handle flight schedule queries with conversation context"""
    try:
        payload = {
            "question": input,
            "conversation_history": conversation_history or []
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SCHEDULE_SERVICE_URL,
                json=payload
            )
            if response.status_code != 200:
                return f"[Schedule Service Error] {response.text}"
            return json.dumps(response.json(), indent=2)
    except Exception as e:
        return f"[Schedule Tool Error] {str(e)}"

async def booking_tool_fn(input: str, conversation_history: list = None) -> str:
    """Handle flight booking queries with conversation context"""
    try:
        payload = {
            "question": input,
            "conversation_history": conversation_history or []
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                BOOKING_SERVICE_URL,
                json=payload
            )
            if response.status_code != 200:
                return f"[Booking Service Error] {response.text}"
            return json.dumps(response.json(), indent=2)
    except Exception as e:
        return f"[Booking Tool Error] {str(e)}"


def create_tool_callable(tool_fn):
    """Create a callable that passes conversation history to the tool function"""
    async def wrapper(input_str: str, **kwargs) -> str:
        # Extract conversation history from kwargs
        conversation_history = kwargs.get('conversation_history', [])
        return await tool_fn(input_str, conversation_history)
    return wrapper

# Tools wrapped in LangChain Tool interface with conversation context
tools = [
    Tool(
        name="CancelTool",
        func=create_tool_callable(sql_tool_fn),
        coroutine=sql_tool_fn,  # The coroutine will be called directly with conversation_history
        description=
            "Useful for flight reservation queries customers who have already booked the tickets. "
            "It can be used to:\n"
            "- Check flight details by PNR\n"
            "- View booking status\n"
            "- Cancel flights and update refund status\n"
            "- Get information about the booked flights like departure time and arrival time\n\n"
            "For cancellations, the tool will automatically update the booking and refund status. "
            "Requires PNR number for specific bookings."
    ),
    Tool(
        name="RagTool",
        func=create_tool_callable(rag_tool_fn),
        coroutine=rag_tool_fn,
        description="Use this tool to answer questions about airline policies, including:\n"
                   "- Baggage allowance and restrictions\n"
                   "- Check-in procedures and requirements\n"
                   "- Flight change and cancellation policies\n"
                   "- Special assistance services\n"
                   "- General airline policies and procedures\n\n"
                   "Input should be a clear question about any of these topics. "
                   "For policy-related questions, this is the tool to use."
    ),
    Tool(
        name="ScheduleTool",
        func=create_tool_callable(schedule_tool_fn),
        coroutine=schedule_tool_fn,  # The coroutine will be called directly with conversation_history
        description=
            "Useful for general enquiry about flight schedules, flight status availability, "
            "flight timings and available seats.\n"
            "Example inputs:\n"
            "- 'Show flights from Delhi to Mumbai'\n"
            "- 'What are the available flights from Bangalore to Delhi tomorrow?'\n"
            "- 'Is there a morning flight from Mumbai to Delhi?'"
    ),
    Tool(
        name="BookingTool",
        func=create_tool_callable(booking_tool_fn),
        coroutine=booking_tool_fn,  # The coroutine will be called directly with conversation_history
        description=
            "Useful for flight reservation for customers who need to book the tickets. "
            "It can be used to:\n"
            "- Book flights\n"
            "- View booking status\n"
    )
]

# from langchain.agents import AgentOutputParser
# from langchain.agents.conversational_chat.output_parser import ConvoOutputParser
# from langchain.schema import AgentAction, AgentFinish

# class CustomOutputParser(AgentOutputParser):
#     def parse(self, text: str) -> AgentAction | AgentFinish:
#         # Check for tool usage pattern
#         if "Action:" in text and "Action Input:" in text:
#             action = text.split("Action:")[1].split("Action Input:")[0].strip()
#             action_input = text.split("Action Input:")[1].strip()
#             return AgentAction(action.strip(), action_input.strip(), text)
        
#         # Check for final answer pattern
#         if "Final Answer:" in text:
#             answer = text.split("Final Answer:")[-1].strip()
#             return AgentFinish({"output": answer}, answer)
        
#         # If no specific pattern found, treat as final answer
#         return AgentFinish({"output": text.strip()}, text.strip())

# Create the agent with the chat prompt
# Initialize the agent with a simpler configuration

prompt = ChatPromptTemplate.from_messages([
    ("system", system_message),
    ("user", "{input}")
])

agent = initialize_agent(
    tools=tools,
    llm=llm,
    #agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    max_iterations=5,
    handle_parsing_errors=True,
    prompt=prompt
)

# Initialize agent executor with error handling and memory
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    return_intermediate_steps=False,
    max_iterations=5,
    memory_key="chat_history",
    include_run_info=True
)

class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class Conversation(BaseModel):
    id: str
    messages: List[Message] = []
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class QueryInput(BaseModel):
    question: str
    conversation_id: Optional[str] = None

def get_or_create_conversation(conversation_id: Optional[str] = None) -> Conversation:
    if conversation_id and conversation_id in conversation_store:
        return conversation_store[conversation_id]
    
    new_id = conversation_id or str(len(conversation_store) + 1)
    conversation = Conversation(id=new_id)
    conversation_store[new_id] = conversation
    return conversation

def format_chat_history(messages: List[Message]) -> List[tuple]:
    formatted = []
    for msg in messages:
        if msg.role == 'user':
            formatted.append(("human", msg.content))
        else:
            formatted.append(("ai", msg.content))
    return formatted


print("AgentType available:", list(AgentType))

@app.post("/react-agent")
async def react_agent(input: QueryInput):
    try:
        

        print("Inside react agent with conversation_id:", input.conversation_id)
        # Get or create conversation
        conversation = get_or_create_conversation(input.conversation_id)
        #print("conversation for react agent:", conversation)
        # Add user message to conversation
        conversation.messages.append(Message(role='user', content=input.question))
        
        # Format chat history for the prompt
        chat_history = format_chat_history(conversation.messages[:-1])  # Exclude current message
        
        # Prepare the input for the agent
        from langchain.schema.messages import HumanMessage, AIMessage
        
        # Convert chat history to message objects
        messages = []
        for msg in conversation.messages[:-1]:  # Exclude current message
            if msg.role == 'user':
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))
        
        # Add current user message
        messages.append(HumanMessage(content=input.question))
        
        # Convert messages to the format expected by the agent
        chat_history = [
            ("user" if msg.role == 'user' else 'assistant', msg.content)
            for msg in conversation.messages
        ]

        print("Chat history for react agent:", chat_history)
        
        # Prepare the input with conversation history for tools
        # agent_input = {
        #     "input": input.question,
        #     "chat_history": chat_history,
        #     "conversation_history": [
        #         {"role": msg.role, "content": msg.content}
        #         for msg in conversation.messages[-10:]  # Last 10 messages for context
        #     ]
        # }

        agent_input = {
            "input": input.question,
            "chat_history": chat_history,
            "conversation_history": [
                {"role": msg.role, "content": msg.content}
                for msg in conversation.messages[-10:]  # Last 10 messages for context
            ]
        }
        
        # Invoke the agent with the input and chat history
        result = await agent.ainvoke(agent_input)
        
        print("Agent response:", result)
        print("Agent response type:", type(result))
        print("Agent response keys:", result.keys())
        print("Agent response values:", result.values())
        print("Agent response items:", result.items())
        
        # Add assistant's response to conversation
        assistant_response = result.get("output", "I'm sorry, I couldn't process that request.")
        conversation.messages.append(Message(role='assistant', content=assistant_response))
        
        print("Assistant response:", assistant_response)
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow().isoformat()
        
        print("Agent response:", assistant_response)
        return {
            "answer": assistant_response,
            "conversation_id": conversation.id
        }
        
    except Exception as e:
        error_msg = f"Error in react agent: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
