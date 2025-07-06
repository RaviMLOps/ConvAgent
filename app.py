from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr

from tools.tools import Tools, Tools_description

load_dotenv(override=True)

tools = []
for description in Tools_description().get_tools_descriptions():
    tools.append({"type": "function", "function": description})

class ConvAgent:

    def __init__(self):
        self.openai = OpenAI()

    def sentiment_prompt(self):
        print("sentiment promt is caleld....")
        sentiment_prompt = f"You are acting as Customer support agent from an arline company.\
         Your job is to identify the sentiment of the message. You have to categorize the message into\
         any one of the following sentiments. Respond the sentiment in one word.\
         among the following list.\
         - Neutral\
         - Positive\
         - Rant\
         - Anger\
         - Frustration\
        );"
        return sentiment_prompt


    def system_prompt(self,sentiment):
        system_prompt = f"""You are acting as Customer support from an arline company.\
        The sentiment of user is {sentiment}. So please understand the {sentiment} and respond accoringly.
        Don't be impolite or use any bad words. Try to sympathise with user if required. \
        Your responsibility is to represent airline orgniazation for interactions with the traveller as faithfully as possible. \
        If the intent of the message includes is greeting or farewell or goodbye then please respond accordingly. 
        
        You are supplied with all intents and respective tool name. Based on the intent please seelct appripriate tool.
        
        You must steer to gather all required information from user based on parameters defined for that tool. You must only
        ask for required parameters in tool description. 

        );"""

        return system_prompt

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"arguments is {arguments} and funaction name is {tool_name}")
            tool = getattr(Tools, tool_name, None)
           # print("tool "+ tool)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results

    def get_sentiment(self, message):
        sentiment_message = self.sentiment_prompt() + message
        response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": sentiment_message}])
        print(f"sentiment response :{response.choices[0].message.content}")
        return response.choices[0].message.content

    def chat(self, message, history):
        sentiment = self.get_sentiment(message) 

        messages = [{"role": "system", "content": self.system_prompt(sentiment=sentiment)}]+history+[{"role": "user", "content": message}]
        done = False
        while not done:

            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
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
    convAgent = ConvAgent()
    gr.ChatInterface(convAgent.chat, type="messages").launch()