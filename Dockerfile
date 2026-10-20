FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY docker/*.txt docker/
RUN python -m venv /opt/build \
    && /opt/build/bin/pip install --require-hashes --only-binary :all: -r docker/build-requirements.txt \
    && python -m venv /opt/venv \
    && /opt/venv/bin/pip install --require-hashes --only-binary :all: -r docker/requirements.txt
COPY pyproject.toml hatch_build.py README.md LICENSE ./
COPY src src
COPY skills skills
RUN /opt/build/bin/pip wheel --no-deps --no-build-isolation --wheel-dir dist . \
    && /opt/venv/bin/pip install --no-deps dist/*.whl

FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f

RUN useradd --create-home --uid 10001 scanner
COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH PYTHONDONTWRITEBYTECODE=1
USER 10001
WORKDIR /src
ENTRYPOINT ["agentic-owasp"]
CMD ["scan", "."]
