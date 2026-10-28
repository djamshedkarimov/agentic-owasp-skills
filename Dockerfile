FROM cgr.dev/chainguard/wolfi-base@sha256:360896efb0753a5701c48f860e17130c205eae5a264797aa3e7ea126ee2923a7 AS python
RUN apk add --no-cache python-3.13

FROM python AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY docker/*.txt docker/
RUN python3.13 -m venv /opt/build \
    && /opt/build/bin/pip install --require-hashes --only-binary :all: -r docker/build-requirements.txt \
    && python3.13 -m venv /opt/venv \
    && /opt/venv/bin/pip install --require-hashes --only-binary :all: -r docker/requirements.txt
COPY pyproject.toml hatch_build.py README.md LICENSE ./
COPY src src
COPY skills skills
RUN /opt/build/bin/pip wheel --no-deps --no-build-isolation --wheel-dir dist . \
    && /opt/venv/bin/pip install --no-deps dist/*.whl

FROM python

COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH PYTHONDONTWRITEBYTECODE=1
# wolfi-base's built-in nonroot user.
USER 65532
WORKDIR /src
ENTRYPOINT ["agentic-owasp"]
CMD ["scan", "."]
