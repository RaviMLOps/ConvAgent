FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application code
COPY app.py .

# Expose Gradio's default port
EXPOSE 7860

# Start the Gradio app
CMD ["python", "app.py"]
