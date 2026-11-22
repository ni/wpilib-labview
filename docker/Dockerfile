# Build environment for the add-on packages (see scripts/build-in-docker.sh).
# strip for both x86-64 and aarch64 removes debug info from the Linux libraries.
# Pinned by digest; Dependabot updates it.
FROM ubuntu:24.04@sha256:9c7f200c07e3d4a03e7249d2c16bf66a51120fb876aa2242cf31451412543289

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        binutils \
        binutils-aarch64-linux-gnu \
        ca-certificates \
        git \
        python3 \
    && rm -rf /var/lib/apt/lists/*
