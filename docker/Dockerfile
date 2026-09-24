FROM ghcr.io/foundry-rs/foundry:latest

RUN apk add --no-cache python3 py3-pip \
    && pip install --no-cache-dir slither-analyzer
WORKDIR /workspace
ENTRYPOINT ["forge"]
