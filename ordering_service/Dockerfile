FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask grpcio grpcio-tools protobuf pyzmq

COPY protos/ /app/protos/
COPY ordering_service/ /app/ordering_service/

EXPOSE 5000

CMD ["python", "ordering_service/app.py"]
