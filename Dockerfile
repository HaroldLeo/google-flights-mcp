FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

ENV MCP_TRANSPORT=sse
ENV HOST=0.0.0.0
ENV PORT=7860

EXPOSE 7860

CMD ["python", "src/mcp_server_google_flights/server.py"]
