FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY config ./config
COPY taximetro ./taximetro

EXPOSE 8000

CMD ["python", "main.py", "--api"]
