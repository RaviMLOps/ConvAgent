# Flight Assistant Frontend

A Gradio-based web interface for interacting with the Flight Assistant agent service.

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure the agent service is running on port 8000.

## Running the Frontend

Start the Gradio interface with:

```bash
python app.py
```

The interface will be available at `http://localhost:7860`

## Features

- Simple chat interface for asking questions about flights and travel
- Real-time responses from the agent service
- Clean, responsive design
- Conversation history in the chat window

## Configuration

You can modify the following in `app.py`:
- `AGENT_SERVICE_URL`: The URL of the agent service (default: `http://localhost:8000/chat`)
