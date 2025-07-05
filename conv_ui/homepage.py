
import gradio as gr
#import FirstOpenAI as first
import chat_api

def generate_response(message, history):
    return chat_api.chat_api(message, history)

def vote(data: gr.LikeData):
    if data.liked:
        print("upvoted: ", data.value, data.index)
    else:
        print("downvoted: ", data.value)

with gr.Blocks() as demo:
    chatbot = gr.Chatbot(placeholder="<strong>Airline customer support chatbot</strong><br>How can I help you?")
    chatbot.like(vote, None, None)
    gr.ChatInterface(fn=generate_response, type="messages", chatbot=chatbot, title="ConvAgent", save_history=False)

if __name__ == "__main__":
    demo.launch()