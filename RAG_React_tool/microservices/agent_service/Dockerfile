
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main_chatgpt.py .
# (Optional: copy test.py only if you want to run tests inside the container)
COPY test.py .

EXPOSE 8004

CMD ["uvicorn", "app.main_chatgpt:app", "--host", "0.0.0.0", "--port", "8004"]

