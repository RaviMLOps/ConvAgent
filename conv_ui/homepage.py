import random
import gradio as gr
import FirstOpenAI as first
import sys

# adding Folder_2 to the system path
#sys.path.insert(0, '/Users/madhu/Documents/Cohut4_project/projects/ConvAgent/ConvAgent/convagent')


def generate_response(message, history):

    return first.myfunc(message=message)

demo = gr.ChatInterface(generate_response, type="messages", autofocus=False)

if __name__ == "__main__":
    demo.launch()