FROM python:3.11-slim
RUN pip install --no-cache-dir mcp[cli] fastmcp
COPY server.py .
CMD ["python", "server.py"]
