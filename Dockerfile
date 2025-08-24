# Simple Python-only MCP server
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    'mcp[cli]>=1.6.0' \
    'httpx>=0.28.1' \
    'requests>=2.32.3'

# Copy MCP server code
COPY whatsapp-mcp-server/ ./

# Set environment
ENV PYTHONUNBUFFERED=1

# Run the MCP server
CMD ["python", "main.py"]