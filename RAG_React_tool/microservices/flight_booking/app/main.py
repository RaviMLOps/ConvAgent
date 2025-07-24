from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
#from pypdf import PdfReader
import gradio as gr


import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
parent_dir = os.path.abspath(os.path.join(parent_dir, os.pardir))
parent_dir = os.path.abspath(os.path.join(parent_dir, os.pardir))
print(parent_dir)
sys.path.append(parent_dir)
from config import Config

load_dotenv(override=True)


def book_flight(Customer_Name,From_City,To_City):
    #book_flight_to_db(Customer_Name,From_City,To_City)
    print("The tool is called here....")
    return {"booked":"OK"}


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
        "required": ["Customer_Name","From_City","To_City","Travel_Date","Fight_ID"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": book_flight_json}]

class Me:

    def __init__(self):
        self.openai= OpenAI(api_key=Config.OPENAI_API_KEY)

    def system_prompt(self):
        system_prompt = f"You are acting as Custoomer support from an arline company.\
        You are answering questions on flight availability, flight booking or others. \
        Your responsibility is to represent airline orgniazation for interactions with the traveller as faithfully as possible. \
        You are provided with schema used for flight booking. Please steer the user to get required information book flight\
        and store in database. \
        Once you have received all desired information to book a flight based on schema, please use the book_flight tool.\
        create table tiket_reservation (\
            PNR_Number VARCHAR(10),\
            Customer_Name VARCHAR(50),\
            Flight_ID VARCHAR(50),\
            Airline VARCHAR(50),\
            From_City VARCHAR(50),\
            To_City VARCHAR(50),\
            Departure_Time DATE,\
            Arrival_Time DATE,\
            Travel_Date DATE,\
            Booking_Date DATE,\
            Booking_Status VARCHAR(20),\
            Refund_Status VARCHAR(20)\
        );"

        return system_prompt


    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results


    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model=Config.MODEL_NAME, messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content


if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()