# import gradio as gr
# from typing import Callable

# class GradioApp:
#     def __init__(self, query_function: Callable):
#         """
#         Initialize the Gradio application.
        
#         Args:
#             query_function: A function that takes a question and returns an answer
#         """
#         self.query_function = query_function
    
#     def answer_question(self, question: str) -> str:
#         """Wrapper function to handle the query."""
#         try:
#             return self.query_function(question)
#         except Exception as e:
#             return f"An error occurred: {str(e)}"
    
#     def launch(self):
#         """Launch the Gradio interface."""
#         iface = gr.Interface(
#             fn=self.answer_question,
#             inputs=gr.Textbox(label="Enter your question"),
#             outputs=gr.Textbox(label="AI Answer"),
#             title="RAG Chatbot with ChromaDB & OpenAI",
#             description="Ask any question, and the AI will retrieve relevant documents and generate an answer."
#         )
        
#         return iface.launch()
