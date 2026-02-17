FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir grpcio grpcio-tools protobuf pyzmq flatbuffers

COPY protos/ /app/protos/
COPY flatbuf/ /app/flatbuf/
COPY inventory_service/ /app/inventory_service/

EXPOSE 50051 5556

CMD ["python", "inventory_service/server.py"]
