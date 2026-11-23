# Build environment for the add-on archives (see scripts/build-in-docker.sh).
# strip for both x86-64 and aarch64 removes debug info from the Linux libraries.
# Pinned by digest; Dependabot updates it.
FROM ubuntu:26.04@sha256:d66b366dac61b575bee2aef07e9c26e8070096fbe84a3d4d3eb0da069b5d76db

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        binutils \
        binutils-aarch64-linux-gnu \
        ca-certificates \
        git \
        python3 \
    && rm -rf /var/lib/apt/lists/*
