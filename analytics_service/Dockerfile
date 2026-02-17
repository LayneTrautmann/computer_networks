FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir pyzmq

COPY analytics_service/ /app/analytics_service/

EXPOSE 5557

CMD ["python", "analytics_service/server.py"]
