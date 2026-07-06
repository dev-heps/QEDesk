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
        git \
        graphviz \
        latexmk \
        libgmp-dev \
        libgraphviz-dev \
        python3 \
        python3-pip \
        python3-pygments \
        python3-venv \
        texlive-latex-extra \
        texlive-science \
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
        openai \
        sympy \
        uv

WORKDIR /workspace

CMD ["sleep", "infinity"]
