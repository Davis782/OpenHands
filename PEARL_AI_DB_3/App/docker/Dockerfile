FROM python:3.11-slim

WORKDIR /app

COPY src/ ./src/
COPY config/ ./config/
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

CMD ["python", "-m", "agent"]