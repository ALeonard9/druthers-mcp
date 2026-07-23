FROM python:3.14-alpine

WORKDIR /app

# Non-root runtime user.
RUN addgroup -S app && adduser -S app -G app

COPY requirements/base.txt requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt

COPY aleonard_mcp ./aleonard_mcp

USER app

# Liveness probe: this is a stdio server with no port, so verify the server
# package still imports cleanly. Resolves Trivy DS-0026 (no HEALTHCHECK).
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import aleonard_mcp" || exit 1

# MCP servers communicate over stdio.
ENTRYPOINT ["python", "-m", "aleonard_mcp.server"]
