FROM python:3.14-alpine

WORKDIR /app

# Non-root runtime user.
RUN addgroup -S app && adduser -S app -G app

COPY requirements/base.txt requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt

COPY aleonard_mcp ./aleonard_mcp

USER app

# MCP servers communicate over stdio.
ENTRYPOINT ["python", "-m", "aleonard_mcp.server"]
