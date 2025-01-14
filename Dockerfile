FROM ghcr.io/astral-sh/uv:0.5.1-python3.12-bookworm-slim AS builder

WORKDIR /app

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching

ADD pyproject.toml /app
ADD t.py /app/t.py
ADD .env /app/.env
ADD README.md /app/README.md
ADD Makefile /app/Makefile

RUN uv add browser-use
RUN uv run playwright install --with-deps
CMD ["uv", "run", "t.py"]