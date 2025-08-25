FROM golang:1.21-alpine AS go-builder

WORKDIR /build
RUN apk add --no-cache gcc musl-dev sqlite-dev

COPY whatsapp-bridge/go.mod whatsapp-bridge/go.sum ./
RUN go mod download

COPY whatsapp-bridge/main.go ./
RUN CGO_ENABLED=1 GOOS=linux go build -a -installsuffix cgo -o whatsapp-bridge main.go

FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser

WORKDIR /app

COPY --from=go-builder /build/whatsapp-bridge /app/whatsapp-bridge
COPY whatsapp-mcp-server/ /app/whatsapp-mcp-server/
COPY start.sh /app/start.sh

RUN pip install --no-cache-dir \
    mcp \
    httpx \
    requests

RUN chmod +x /app/whatsapp-bridge /app/start.sh && \
    mkdir -p /app/store && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/start.sh"]