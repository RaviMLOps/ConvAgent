

docker build -t agent-service .

docker run -e OPENAI_API_KEY -p 8000:8000 agent-service

curl -X POST -H "Content-Type: application/json" -d '{"question":"I need to cancel my flight booking"}' http://localhost:8000/react-agent