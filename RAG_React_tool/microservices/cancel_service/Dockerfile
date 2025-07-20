# reservation_service/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Expose the port the app runs on
EXPOSE 8003

# Command to run the application
CMD ["uvicorn", "app.main_chatgpt:app", "--host", "0.0.0.0", "--port", "8003"]