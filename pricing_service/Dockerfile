FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir grpcio grpcio-tools protobuf

COPY protos/ /app/protos/
COPY pricing_service/ /app/pricing_service/

EXPOSE 50053

CMD ["python", "pricing_service/server.py"]
