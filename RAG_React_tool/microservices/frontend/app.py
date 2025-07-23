import gradio as gr
import httpx
import asyncio
from typing import List, Tuple
import os

AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8004/react-agent")

async def query_agent(question: str, conversation_id: str = None) -> dict:
    """
    Send query to the agent service and return the response.
    """
    try:
        payload = {
            "question": question,
            "conversation_id": conversation_id
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                AGENT_SERVICE_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            #print("Response from react_agent: ", response)
            response.raise_for_status()
            result = response.json()
            #result = json.dumps(response)
            #print("Result from react_agent ", result)

            return {
                "answer": result.get("answer", "No response from agent"),
                "conversation_id": result.get("conversation_id"),
                "status": "success"
            }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "error": f"HTTP error occurred: {str(e)}",
            "answer": "I'm having trouble connecting to the agent service. Please try again later."
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"An error occurred: {str(e)}",
            "answer": "I encountered an unexpected error. Please try again."
        }

def create_interface():
    with gr.Blocks(title="Flight Assistant") as demo:
        gr.Markdown("""
        # ✈️ Flight Assistant  
        Ask me anything about flights, reservations, or travel policies.
        """)

        chatbot = gr.Chatbot(label="Conversation")
        state = gr.State(value=[])
        msg = gr.Textbox(placeholder="Type your question here and press Enter...", show_label=False)
        clear = gr.Button("Clear Conversation")
        conversation_id = gr.State(value=None)

        async def respond(message: str, chat_history: List[Tuple[str, str]], current_conversation_id: str):
            if not message.strip():
                return "", chat_history, current_conversation_id, chat_history

            response = await query_agent(
                question=message,
                conversation_id=current_conversation_id
            )

            new_conversation_id = response.get('conversation_id', current_conversation_id)
            bot_reply = response.get('answer', 'I apologize, but I encountered an error processing your request.')

            return "", [(message, bot_reply)], new_conversation_id, [(message, bot_reply)]

        msg.submit(respond, [msg, state, conversation_id], [msg, chatbot, conversation_id, state])
        clear.click(lambda: ([], [], None), None, [chatbot, state, conversation_id], queue=False)

    return demo

if __name__ == "__main__":
    demo = create_interface()
    try:
        demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
    except OSError:
        demo.launch(server_name="0.0.0.0", server_port=0, share=False)
