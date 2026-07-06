FROM ubuntu:24.04

ARG LEAN_TOOLCHAIN=leanprover/lean4:v4.31.0

ENV DEBIAN_FRONTEND=noninteractive
ENV ELAN_HOME=/root/.elan
ENV PATH=/root/.elan/bin:/opt/venv/bin:$PATH

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        dvisvgm \
        git \
        ghostscript \
        graphviz \
        latexmk \
        libgmp-dev \
        libgraphviz-dev \
        nodejs \
        npm \
        python3 \
        python3-pip \
        python3-pygments \
        python3-venv \
        ripgrep \
        texlive-latex-extra \
        texlive-science \
        unzip \
        zstd \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh \
    | sh -s -- -y --default-toolchain "$LEAN_TOOLCHAIN"

RUN lean --version && lake --version

RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --upgrade pip setuptools wheel \
    && /opt/venv/bin/pip install --no-cache-dir \
        lean-lsp-mcp \
        leanblueprint \
        leanclient \
        jsonschema \
        openai \
        plasTeX \
        pylatexenc \
        sympy \
        uv

# The workspace is a host bind mount, often from WSL/Windows. Allow Git-based
# Lake dependencies inside this single-purpose development container.
RUN git config --global --add safe.directory '*'

WORKDIR /workspace

CMD ["sleep", "infinity"]
