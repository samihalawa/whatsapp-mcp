FROM golang:alpine AS go-builder

WORKDIR /app/whatsapp-bridge
COPY whatsapp-bridge/go.mod whatsapp-bridge/go.sum ./
RUN go mod download

COPY whatsapp-bridge/ ./
RUN go build -o whatsapp-bridge main.go

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install
COPY whatsapp-mcp-server/pyproject.toml whatsapp-mcp-server/uv.lock ./
RUN pip install uv && uv sync --frozen

# Copy Go binary
COPY --from=go-builder /app/whatsapp-bridge/whatsapp-bridge ./

# Copy Python source
COPY whatsapp-mcp-server/ ./

# Create directories
RUN mkdir -p store

# Create non-root user
RUN useradd -m -u 1001 whatsapp
RUN chown -R whatsapp:whatsapp /app
USER whatsapp

# Set environment
ENV PYTHONUNBUFFERED=1

# Start script
COPY start-whatsapp-mcp.sh ./
RUN chmod +x start-whatsapp-mcp.sh

CMD ["./start-whatsapp-mcp.sh"]
