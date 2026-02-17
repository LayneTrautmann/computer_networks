FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir streamlit requests

COPY client/ /app/client/

EXPOSE 8501

CMD ["streamlit", "run", "client/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
