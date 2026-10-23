FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY frontend/ frontend/

# Connects to the "ollama" service defined in docker-compose.yml
ENV OLLAMA_HOST=http://ollama:11434 \
    OLLAMA_MODEL=qwen2.5vl:3b

EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
