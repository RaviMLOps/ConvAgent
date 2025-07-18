from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import json
import os, sys
import requests
import gradio as gr
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging

try:
    from config import Config
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from RAG_React_tool.Booking_tool.booking_sql_tool import get_sql_tool
except:
    sys.path.append((os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
    from Booking_tool.booking_sql_tool import get_sql_tool

app = FastAPI()

def book_flight(request):
    sql_tool_func = get_sql_tool()["func"]
    response = sql_tool_func(request)
    return {"response": response}


book_flight_json = {
    "name": "book_flight",
    "description": "Use this tool to book a flight for a user who has provided required parameters",
    "parameters": {
        "type": "object",
        "properties": {
            "Customer_Name": {
                "type": "string",
                "description": "This is the name of this user or traveller"
            },
            "From_City": {
                "type": "string",
                "description": "This is the source city from where the flight takes off"
            },
            "To_City": {
                "type": "string",
                "description":  "This is the destination city to where the flight lands "
            },
            "Travel_Date": {
                "type": "string",
                "description":  "This is the preferred travel date of the user or traveller "
            },
            "Fight_ID": {
                "type": "string",
                "description":  "This is the preferred flight of the user or traveller  "
            }

        },
        "required": ["Customer_Name", "Flight_ID", "From_City","To_City", "Travel_Date"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": book_flight_json}]

class BookingTool:
    def __init__(self, model_name: str = None, temperature: float = 0.0):
        self.openai= OpenAI(api_key=Config.OPENAI_API_KEY)
             

    def system_prompt(self):
        system_prompt = """You are acting as Customer support from an arline company.\
        You are answering questions on flight booking. \
        Your responsibility is to represent airline orgniazation for \
        interactions with the traveller as faithfully as possible. \
        please steer the user to get the mandatory information like Customer_Name, \
        From_City, To_City, Flight_ID and Travel_Date to book flight.

        Once you receive all necessary information, please go ahead 
        and book the flight ticket. 

        please use the book_flight tool.
        
        Example input: 
            My name is Arjun Deshpande, I need to travel on 4th Sep in SG948 from chennai to Dellhi
        Answer:
            I received all necessary information. So I should go ahead and book flight ticket.
                - Customer_Name : Arjun Deshpande
                - Travel_Date : 4th September 2025
                - From_City : Chennai
                - To_City : Delhi
                - Flight_ID : sG948
        
        Example input:
            My name is Amarnath. I need to book ticket from Delhi to Pune.
        Answer:
            Travel_Date and Flight_ID are missing. So I should steer the user to provide the same.
        """
        return system_prompt

booking_tool = BookingTool()

class QueryInput(BaseModel):
    question: str

@app.post("/chat")
async def chat(input: QueryInput):
    messages = [{"role": "system", "content": booking_tool.system_prompt()}] + [{"role": "user", "content": input.question}]
    response = booking_tool.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
        
    if response.choices[0].finish_reason=="tool_calls":
        message = response.choices[0].message
        tool_call = message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)
        sql_tool_func = get_sql_tool()["func"]
        results = sql_tool_func(message.content)
        messages.append(message)
        messages.extend(results)
        return {"response": results}
        
    else:
        return response.choices[0].message.content
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

