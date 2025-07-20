import gradio as gr
import httpx
import asyncio
from typing import List, Tuple

# Configuration
import os
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8004/react-agent")

async def query_agent(question: str) -> str:
    """Send query to the agent service and return the response."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                AGENT_SERVICE_URL,
                json={"question": question},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
        
            #return response
            try:
                print(type(response))
                print(response.text)
                result = response.json()                
                return result.get("answer", response.text)
            except ValueError:
                print("ValueError: ", response.text)
                return response.text
            
    except Exception as e:
        return f"Error querying agent service: {str(e)}"

def create_interface():
    with gr.Blocks(title="Flight Assistant") as demo:
        gr.Markdown("""
        # ✈️ Flight Assistant  
        Ask me anything about flights, reservations, or travel policies.
        """)

        chatbot = gr.Chatbot(label="Conversation")
        state = gr.State(value=[])  # will hold List[Tuple[str, str]]

        msg = gr.Textbox(
            placeholder="Type your question here and press Enter...",
            show_label=False
        )
        clear = gr.Button("Clear Conversation")

        # async handler so we can await query_agent()
        async def respond(message: str, chat_history: List[Tuple[str, str]]):
            if not message.strip():
                return "", chat_history, chat_history  # no-op

            bot_reply = await query_agent(message)
            updated_history = chat_history + [(message, bot_reply)]
            return "", updated_history, updated_history

        msg.submit(respond, [msg, state], [msg, chatbot, state])
        clear.click(lambda: ([], []), None, [chatbot, state], queue=False)

    return demo

if __name__ == "__main__":
    demo = create_interface()
    try:
        demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
    except OSError:
        demo.launch(server_name="0.0.0.0", server_port=0, share=False)
