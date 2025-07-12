#!/usr/bin/env python3
"""
ReAct RAG Agent with Gradio Interface

This script provides a Gradio-based web interface for interacting with a ReAct RAG agent.
It allows users to ask questions about documents using natural language.
"""
import os
import logging
from typing import Optional

import gradio as gr
from rag_react_agent import ReActRAGAgent
from config import Config

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rag_react_app.log')
    ]
)
logger = logging.getLogger(__name__)
logger.info("Starting RAG React Application")

def initialize_rag_agent() -> ReActRAGAgent:
    """
    Initialize the ReAct RAG agent with the existing ChromaDB.
    
    Returns:
        ReActRAGAgent: Initialized agent
        
    Raises:
        RuntimeError: If agent initialization fails
    """
    # Initialize the agent
    logger.info("Initializing ReAct RAG agent...")
    logger.info(f"Using model: {Config.MODEL_NAME} with temperature: {Config.TEMPERATURE}")
    
    agent = ReActRAGAgent()
    if not agent.initialize():
        raise RuntimeError(
            "Failed to initialize the ReAct RAG agent. "
            "Please ensure the ChromaDB vector store is properly set up. "
            "Check the logs for more details."
        )
    
    return agent

def create_gradio_interface(agent: ReActRAGAgent):
    """Create and return a Gradio chat interface for the RAG agent."""
    # System message to set the behavior of the assistant
    system_msg = "You are a helpful AI assistant that answers questions " \
    "based on the provided inputs. Be concise and accurate in your responses."
    
    def add_text(history, text):
        """Add user message to chat history."""
        history = history + [(text, None)]
        return history, ""
    
    def bot(history):
        """Generate bot response and update chat history."""
        if not history:
            return history
        
        user_message = history[-1][0]
        try:
            # Get response from the agent
            response = agent.query(user_message)
             # Modification start : By Madhu
            response = response.get("output", "No response generated.")
            # modification end  : By Madhu
            history[-1] = (user_message, response)
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            history[-1] = (user_message, f"An error occurred: {str(e)}")
        
        return history
    
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("# ReAct RAG Chatbot")
        gr.Markdown("Ask questions about your document using the chat interface below.")
        
        chatbot = gr.Chatbot(
            [],
            elem_id="chatbot",
            bubble_full_width=False,
            height=500
        )
        
        with gr.Row():
            txt = gr.Textbox(
                scale=4,
                show_label=False,
                placeholder="Type your question here...",
                container=False,
            )
            btn = gr.Button("Send", variant="primary")
        
        # Clear button
        clear_btn = gr.Button("Clear Chat")
        
        # Event handlers
        txt.submit(
            add_text, 
            [chatbot, txt], 
            [chatbot, txt]
        ).then(
            bot, 
            chatbot, 
            chatbot
        )
        
        btn.click(
            add_text, 
            [chatbot, txt], 
            [chatbot, txt]
        ).then(
            bot, 
            chatbot, 
            chatbot
        )
        
        clear_btn.click(lambda: None, None, chatbot, queue=False)
    
    return demo

def main():
    """Main function to run the ReAct RAG Gradio app."""
    try:
        logger.info("Starting main function")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"CHROMA_DB_DIR from config: {Config.CHROMA_DB_DIR}")
        
        # Check if vector store exists
        if not os.path.exists(Config.CHROMA_DB_DIR):
            logger.error(f"ChromaDB directory does not exist: {Config.CHROMA_DB_DIR}")
            return 1
            
        # List files in the ChromaDB directory for debugging
        try:
            files = os.listdir(Config.CHROMA_DB_DIR)
            logger.info(f"Files in ChromaDB directory: {files}")
        except Exception as e:
            logger.error(f"Error listing ChromaDB directory: {str(e)}")
        
        # Initialize the RAG agent with existing ChromaDB
        logger.info("Initializing RAG agent...")
        agent = initialize_rag_agent()
        
        if not agent:
            logger.error("Failed to initialize RAG agent")
            print("Error: Failed to initialize RAG agent. Check the logs for details.")
            return 1
            
        logger.info("RAG agent initialized successfully")
        
        # Create and launch the Gradio interface
        logger.info("Creating Gradio interface...")
        demo = create_gradio_interface(agent)
        
        logger.info("Launching Gradio interface...")
        #demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
        demo.launch()
    except Exception as e:
        logger.exception("Error in main function:")
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting tips:")
        print(f"1. Check the log file: {os.path.abspath('rag_react_app.log')}")
        print("2. Ensure you have set up the ChromaDB vector store first")
        print(f"3. Verify that {Config.CHROMA_DB_DIR} contains the vector store files")
        print("4. Make sure all required environment variables are set (e.g., OPENAI_API_KEY)")
        return 1
    
    return 0

if __name__ == "__main__":
    main()
