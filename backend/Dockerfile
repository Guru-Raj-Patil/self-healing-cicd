FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Since we might run fix scripts that use git or run shell commands:
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
