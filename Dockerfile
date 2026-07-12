FROM python:3.11-slim
RUN pip install --no-cache-dir fastapi uvicorn mcp[cli] fastmcp
COPY server.py .
CMD ["python", "server.py"]
