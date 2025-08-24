# Multi-stage build for WhatsApp Bridge + MCP Server
FROM golang:1.23-alpine AS go-builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache gcc musl-dev sqlite-dev

# Copy and build Go WhatsApp bridge
COPY whatsapp-bridge/ ./
RUN go mod download
RUN CGO_ENABLED=1 GOOS=linux go build -a -installsuffix cgo -o whatsapp-bridge .

# Final stage - Python with Go binary
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    supervisor \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    'mcp[cli]>=1.6.0' \
    'httpx>=0.28.1' \
    'requests>=2.32.3' \
    'qrcode[pil]>=7.4.2' \
    'Pillow>=10.0.0'

# Copy Go binary from builder
COPY --from=go-builder /build/whatsapp-bridge /app/whatsapp-bridge

# Copy MCP server code
COPY whatsapp-mcp-server/ ./whatsapp-mcp-server/

# Create store directory for WhatsApp data
RUN mkdir -p /app/store && chmod 755 /app/store

# Copy supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy startup script
COPY start-services.sh /app/start-services.sh
RUN chmod +x /app/start-services.sh

# Environment
ENV PYTHONUNBUFFERED=1
ENV WHATSAPP_BRIDGE_PORT=8080

# Expose bridge port (internal)
EXPOSE 8080

# Run both services via supervisor
CMD ["/app/start-services.sh"]