FROM docker.io/python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --root-user-action ignore -r requirements.txt

RUN useradd -r -m -d /home/appuser appuser

COPY src/ src/
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir --no-deps . && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN chown -R appuser:appuser /app

USER appuser
ENTRYPOINT ["searxng-mcp-server"]
