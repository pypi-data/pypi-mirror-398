FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

ADD . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# allow writing files for this particular job
RUN chmod -R 700 ./* && \
    find . -type f -exec chmod -x {} \; && \
    chmod 700 src/main.py

RUN groupadd -r -g 10100 service && \
    useradd --no-log-init -r -m -u 10100 -g service service

FROM debian:12-slim AS base

RUN apt-get update
RUN apt-get install python3 -y

FROM gcr.io/distroless/cc-debian12 AS temp
COPY --from=base /usr/bin/c_rehash /usr/bin/openssl /usr/bin/pdb3 /usr/bin/pdb3.11 /usr/bin/py3clean /usr/bin/py3compile /usr/bin/py3versions /usr/bin/pydoc3 /usr/bin/pydoc3.11 /usr/bin/pygettext3 /usr/bin/pygettext3.11 /usr/bin/python3 /usr/bin/python3.11 /usr/bin/
COPY --from=base /usr/lib/binfmt.d /usr/lib/ssl /usr/lib/valgrind /usr/lib/ /usr/lib/
COPY --from=base /usr/share/applications/ /usr/share/zoneinfo/ /usr/share/lintian/ /usr/share/binfmts/ /usr/share/python3 /usr/share/readline/ /usr/share/

FROM temp AS final
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group
COPY --from=builder --chown=service:service /app /app
WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

USER service
ENTRYPOINT ["python3", "src/main.py"]

