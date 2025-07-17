

docker build -t agent-service .

docker run -e OPENAI_API_KEY -p 8000:8000 agent-service