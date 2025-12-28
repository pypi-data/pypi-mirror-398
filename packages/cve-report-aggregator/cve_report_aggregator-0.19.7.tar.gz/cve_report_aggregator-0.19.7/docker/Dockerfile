# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.14.0
ARG GRYPE_VERSION=v0.104.2
ARG SYFT_VERSION=v1.38.2
ARG TRIVY_VERSION=0.68.2
ARG UDS_VERSION=v0.27.20
ARG TARGETARCH=amd64
ARG REGISTRY_URL="registry.defenseunicorns.com"
ARG SKIP_UPDATE_VULNDB_DB="false"

# ============================================================================
# Scanner tool stages - extract binaries from upstream images
# ============================================================================
FROM anchore/grype:${GRYPE_VERSION}-nonroot AS grype
FROM anchore/syft:${SYFT_VERSION}-nonroot AS syft
FROM aquasec/trivy:${TRIVY_VERSION} AS trivy

# ============================================================================
# UDS CLI downloader stage - downloads and configures authentication
# ============================================================================
FROM alpine:3.22.2 AS uds-downloader

ARG UDS_VERSION
ARG TARGETARCH

RUN apk add --no-cache \
        curl=8.14.1-r2 \
        ca-certificates=20250911-r0 \
        jq && \
    set -ex && \
    case "${TARGETARCH}" in \
        amd64) UDS_ARCH="amd64" ;; \
        arm64) UDS_ARCH="arm64" ;; \
        *) echo "Unsupported architecture: ${TARGETARCH}" && exit 1 ;; \
    esac && \
    UDS_URL="https://github.com/defenseunicorns/uds-cli/releases/download/${UDS_VERSION}/uds-cli_${UDS_VERSION}_Linux_${UDS_ARCH}" && \
    echo "Downloading UDS CLI from: ${UDS_URL}" && \
    curl -fsSL --retry 3 --retry-delay 2 "${UDS_URL}" -o /usr/local/bin/uds && \
    if [ ! -s /usr/local/bin/uds ]; then \
        echo "ERROR: Failed to download UDS CLI or file is empty" && \
        echo "Attempted URL: ${UDS_URL}" && \
        exit 1; \
    fi && \
    chmod +x /usr/local/bin/uds && \
    /usr/local/bin/uds version

RUN --mount=type=secret,id=credentials,target=/run/secrets/credentials,required=false \
    if [ -f /run/secrets/credentials ]; then \
        echo "Using credentials from secret mount" && \
        creds=$(cat /run/secrets/credentials) && \
        user=$(echo "$creds" | jq -r .username) && \
        pass=$(echo "$creds" | jq -r .password) && \
        registry=$(echo "$creds" | jq -r .registry) && \
        auth=$(printf '%s' "$user:$pass" | base64 -w0) && \
        jq -n --arg auth "$auth" --arg registry "$registry" '{auths: {($registry): {"auth": $auth}}}' > /root/config.json; \
    else \
        echo "No credentials provided, creating empty Docker config" && \
        echo '{}' > /root/config.json; \
    fi

# ============================================================================
# Build stage - installs Python dependencies and builds the application
# ============================================================================
FROM python:${PYTHON_VERSION}-alpine AS builder

# Install build dependencies for Python packages with native extensions
RUN apk add --no-cache \
        gcc \
        musl-dev \
        libffi-dev \
        ca-certificates=20250911-r0

# Install uv for fast Python package installation
RUN python -m pip install --no-cache-dir --upgrade pip==25.2 uv==0.5.11

# Copy only build-time files
WORKDIR /build
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY utils/ ./utils/

# Build and install Python packages into isolated venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python .

# ============================================================================
# Final runtime stage - minimal image with only necessary runtime components
# ============================================================================
FROM python:${PYTHON_VERSION}-alpine

WORKDIR /home/cve-aggregator

# Accept build-time metadata arguments (injected by docker/metadata-action)
ARG BUILD_DATE
ARG VERSION
ARG REVISION
ARG SKIP_UPDATE_VULNDB_DB

# OCI image labels
LABEL org.opencontainers.image.title="CVE Report Aggregator" \
    org.opencontainers.image.description="Scans SBOM files contained in Zarf packages using Grype and/or Trivy, deduplicates findings, and saves results." \
    org.opencontainers.image.authors="Mitchell Murphy <mitchell.murphy@defenseunicorns.com>" \
    org.opencontainers.image.source="https://github.com/mkm29/cve-report-aggregator" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.created="${BUILD_DATE}" \
    org.opencontainers.image.version="${VERSION}" \
    org.opencontainers.image.revision="${REVISION}"

ARG GRYPE_VERSION
ARG SYFT_VERSION
ARG TRIVY_VERSION
ARG UDS_VERSION
ARG REGISTRY_URL

ENV GRYPE_VERSION=${GRYPE_VERSION} \
    SYFT_VERSION=${SYFT_VERSION} \
    TRIVY_VERSION=${TRIVY_VERSION} \
    UDS_VERSION=${UDS_VERSION}

# Install only runtime dependencies (no build tools)
RUN apk add --no-cache \
        ca-certificates=20250911-r0 \
        curl=8.14.1-r2 \
        git=2.49.1-r0 \
        bash=5.2.37-r0 \
        libgcc=14.2.0-r6 \
        libstdc++=14.2.0-r6 \
        busybox=1.37.0-r19 && \
    addgroup -g 1001 cve-aggregator && \
    adduser -D -u 1001 -G cve-aggregator cve-aggregator

# Copy scanner binaries from respective stages
COPY --from=grype /grype /usr/local/bin/grype
COPY --from=syft /syft /usr/local/bin/syft
COPY --from=trivy /usr/local/bin/trivy /usr/local/bin/trivy
COPY --from=uds-downloader /usr/local/bin/uds /usr/local/bin/uds
COPY --from=uds-downloader /root/config.json /tmp/config.json

# Copy Python virtual environment from builder (contains installed package)
COPY --from=builder /opt/venv /opt/venv

# Copy entrypoint script
ADD docker/entrypoint.sh /usr/local/bin/entrypoint.sh

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Remove system pip and create workspace directories
RUN rm -rf /usr/local/lib/python3.12/site-packages/pip* \
           /usr/local/lib/python3.12/ensurepip \
           /usr/local/bin/pip* && \
    mkdir -p /home/cve-aggregator/.docker \
             /home/cve-aggregator/reports \
             /home/cve-aggregator/output \
             /home/cve-aggregator/archive && \
    mv /tmp/config.json /home/cve-aggregator/.docker/config.json && \
    chown -R cve-aggregator:cve-aggregator /home/cve-aggregator && \
    chmod -R 755 /home/cve-aggregator && \
    chmod +x /usr/local/bin/entrypoint.sh

USER cve-aggregator

# Verify all tools are installed and working
RUN echo "=== Tool Versions ===" && \
    python --version && \
    grype version && \
    syft version && \
    trivy --version && \
    uds version && \
    cve-report-aggregator --version && \
    echo "=== All tools installed successfully ==="

ENV REGISTRY_URL=${REGISTRY_URL} \
    DOCKER_CONFIG="/home/cve-aggregator/.docker" \
    SKIP_UPDATE_VULNDB_DB=${SKIP_UPDATE_VULNDB_DB}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
