# Build stage for Go application
FROM golang:1.21-alpine AS go-builder

# Install build dependencies
RUN apk add --no-cache gcc musl-dev sqlite-dev

WORKDIR /app

# Copy Go modules and download dependencies
COPY whatsapp-bridge/go.mod whatsapp-bridge/go.sum ./whatsapp-bridge/
WORKDIR /app/whatsapp-bridge
RUN go mod download

# Copy source code and build
COPY whatsapp-bridge/ ./
RUN CGO_ENABLED=1 go build -o whatsapp-bridge main.go

# Final stage - using Python base
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    libsqlite3-dev \
    ffmpeg \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install pip packages directly (simpler than UV for container)
RUN pip install --no-cache-dir \
    'mcp[cli]>=1.6.0' \
    'httpx>=0.28.1' \
    'requests>=2.32.3'

# Copy Go binary from builder
COPY --from=go-builder /app/whatsapp-bridge/whatsapp-bridge ./whatsapp-bridge

# Copy Python source
COPY whatsapp-mcp-server/ ./whatsapp-mcp-server/

# Copy startup script
COPY start-container.sh ./
RUN chmod +x start-container.sh

# Create necessary directories and set permissions
RUN mkdir -p store/media && \
    chmod -R 777 store

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/whatsapp-mcp-server

# Remove healthcheck for now to avoid deployment issues
# HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
#   CMD ps aux | grep -q "[w]hatsapp-bridge" || exit 1

# Start both services
CMD ["./start-container.sh"]