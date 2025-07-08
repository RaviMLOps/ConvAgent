# RAG (Retrieval-Augmented Generation) Tool

A modular Python implementation of a RAG (Retrieval-Augmented Generation) system that allows you to chat with your PDF documents using ChromaDB and OpenAI.

## Features

- **Document Processing**: Automatically processes PDF documents from a specified directory
- **Vector Storage**: Uses ChromaDB for efficient document storage and retrieval
- **RAG Pipeline**: Implements a retrieval-augmented generation pipeline with customizable prompts
- **Gradio Interface**: User-friendly web interface for interacting with your documents
- **Modular Design**: Easy to extend and modify components

## Prerequisites

- Python 3.8+
- OpenAI API key
- Required Python packages (install via `pip install -r requirements.txt`)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd RAG_tool
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

1. **Prepare your documents**:
   - Place your PDF files in the `documents` directory
   - The system will automatically use the most recently added PDF

2. **Run the application**:
   ```bash
   python main.py
   ```
   This will:
   - Process the PDF documents
   - Create/load the vector store
   - Launch the Gradio web interface

3. **Using the interface**:
   - Open the URL shown in the terminal (usually http://localhost:7860)
   - Ask questions about your document
   - The system will retrieve relevant information and generate answers

## Advanced Usage

### Using a specific PDF file
```bash
python main.py --pdf path/to/your/document.pdf
```

### Customizing the model
You can modify the model settings in `config.py`:
```python
# Model configuration
MODEL_NAME = "gpt-4"  # or any other OpenAI model
TEMPERATURE = 0.7     # Adjust for more creative (higher) or focused (lower) responses

# Text processing
CHUNK_SIZE = 1000     # Size of document chunks
CHUNK_OVERLAP = 200   # Overlap between chunks
```

## Project Structure

```
RAG_tool/
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── config.py              # Configuration settings
├── main.py                # Main entry point
├── document_loader.py     # PDF loading and processing
├── embeddings.py          # Vector store management
├── rag_chain.py          # RAG pipeline implementation
└── app.py                # Gradio web interface
```

## Troubleshooting

- **Missing PDF files**: Ensure your PDF is in the `documents` directory or provide the full path
- **API key issues**: Verify your OpenAI API key is correctly set in the `.env` file
- **Vector store errors**: Delete the `db` directory to force recreation of the vector store

## License

This project is licensed under the MIT License - see the LICENSE file for details.
