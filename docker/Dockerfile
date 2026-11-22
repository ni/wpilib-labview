# Build environment for the add-on packages (see scripts/build-in-docker.sh).
# strip for both x86-64 and aarch64 removes debug info from the Linux libraries.
FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        binutils \
        binutils-aarch64-linux-gnu \
        ca-certificates \
        git \
        python3 \
    && rm -rf /var/lib/apt/lists/*
