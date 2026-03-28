FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn python-multipart pydantic tweepy anthropic python-dotenv solana solders anchorpy schedule
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "dashboard.server:app", "--host", "0.0.0.0", "--port", "8000"]
