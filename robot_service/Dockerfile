FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir grpcio grpcio-tools protobuf pyzmq flatbuffers

COPY protos/ /app/protos/
COPY flatbuf/ /app/flatbuf/
COPY robot_service/ /app/robot_service/

CMD ["python", "robot_service/robot.py", "bread"]
