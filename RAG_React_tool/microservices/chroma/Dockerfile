FROM python:3.10-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Optionally copy your code for CI/prod; will be overlaid by volume in dev
COPY container/ .

# Ensure necessary folders exist (in case they aren't mounted)
RUN mkdir -p /app/data /app/chroma-data

# Hot-reload for dev (remove --reload for prod)
CMD ["uvicorn", "chroma_server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]