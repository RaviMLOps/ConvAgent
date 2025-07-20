# Use a slim Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install ChromaDB and other necessary libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script to add documents
COPY app/main_chatgpt.py .

EXPOSE 8000

CMD ["python", "main_chatgpt.py"]