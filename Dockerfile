# Build stage for Go application
FROM golang:1.21-alpine AS go-builder

# Install build dependencies
RUN apk add --no-cache gcc musl-dev sqlite-dev

WORKDIR /app/whatsapp-bridge

# Copy Go modules and download dependencies
COPY whatsapp-bridge/go.mod whatsapp-bridge/go.sum ./
RUN go mod download

# Copy source code and build
COPY whatsapp-bridge/ ./
RUN CGO_ENABLED=1 go build -o whatsapp-bridge main.go

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including SQLite
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    libsqlite3-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install UV globally for all users
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx

# Copy and install Python dependencies
COPY whatsapp-mcp-server/pyproject.toml whatsapp-mcp-server/uv.lock ./whatsapp-mcp-server/
WORKDIR /app/whatsapp-mcp-server
RUN uv sync --frozen

# Go back to app root
WORKDIR /app

# Copy Go binary from builder
COPY --from=go-builder /app/whatsapp-bridge/whatsapp-bridge ./

# Copy Python source
COPY whatsapp-mcp-server/ ./whatsapp-mcp-server/

# Copy startup script
COPY start-container.sh ./
RUN chmod +x start-container.sh

# Create necessary directories
RUN mkdir -p store/media

# Create non-root user
RUN useradd -m -u 1001 whatsapp && \
    chown -R whatsapp:whatsapp /app

USER whatsapp

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/home/whatsapp/.local/bin:$PATH"

# Expose any necessary ports (if needed)
# EXPOSE 8080

# Health check to ensure both services are running
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD ps aux | grep -q "[w]hatsapp-bridge" && ps aux | grep -q "[p]ython.*main.py" || exit 1

# Start both services
CMD ["./start-container.sh"]