FROM python:3.14-alpine

WORKDIR /app

# Non-root runtime user.
RUN addgroup -S app && adduser -S app -G app

COPY requirements/base.txt requirements/base.txt
# Install the dependencies, then drop pip itself. A runtime container has no
# need for a package manager, and keeping one costs us a false security
# finding: pip bundles its own vendored copies of msgpack and setuptools plus
# a CycloneDX manifest (pip/_vendor/bom.cdx.json) declaring them. Scanners read
# that manifest and report those versions as installed packages even though
# nothing in the app imports them and no .dist-info for them exists. Removing
# pip removes both the vendored code and the manifest.
RUN pip install --no-cache-dir -r requirements/base.txt \
    && python -m pip uninstall -y pip \
    && rm -rf /usr/local/lib/python*/ensurepip

COPY aleonard_mcp ./aleonard_mcp

USER app

# Liveness probe: this is a stdio server with no port, so verify the server
# package still imports cleanly. Resolves Trivy DS-0026 (no HEALTHCHECK).
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import aleonard_mcp" || exit 1

# MCP servers communicate over stdio.
ENTRYPOINT ["python", "-m", "aleonard_mcp.server"]
