# Use the official UV image for Python as base
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS uv-base

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

# Final stage using UV base
FROM uv-base

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    sqlite \
    sqlite-dev \
    ffmpeg \
    bash \
    procps

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Copy Python project files
COPY whatsapp-mcp-server/pyproject.toml whatsapp-mcp-server/uv.lock ./whatsapp-mcp-server/

# Install Python dependencies using UV with caching
WORKDIR /app/whatsapp-mcp-server
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=whatsapp-mcp-server/uv.lock,target=uv.lock \
    --mount=type=bind,source=whatsapp-mcp-server/pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy the rest of the Python source and install
COPY whatsapp-mcp-server/ ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Go back to app root
WORKDIR /app

# Copy Go binary from builder
COPY --from=go-builder /app/whatsapp-bridge/whatsapp-bridge ./whatsapp-bridge

# Copy startup script
COPY start-container.sh ./
RUN chmod +x start-container.sh

# Create necessary directories and set permissions
RUN mkdir -p store/media && \
    chmod -R 777 store

# Place executables in the environment at the front of the path
ENV PATH="/app/whatsapp-mcp-server/.venv/bin:$PATH"

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Start both services
CMD ["./start-container.sh"]