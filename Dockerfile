FROM python:3.11.7-slim

WORKDIR /app

COPY . /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .



CMD uvicorn app.main:app --port=8000 --host=0.0.0.0
