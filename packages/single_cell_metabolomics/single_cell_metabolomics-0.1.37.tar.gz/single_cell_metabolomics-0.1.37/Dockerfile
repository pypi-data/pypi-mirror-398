# docker build -t archerkuo/scmap-python:1.0.0 .
# docker push archerkuo/scmap-python:1.0.0

FROM astral/uv:python3.13-bookworm

RUN apt-get update && \
    apt-get install -y \
    procps \
    graphviz && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY src/single_cell_metabolome /workspace/single_cell_metabolome

RUN uv init workspace && \
    cd workspace && \
    uv add typer \
    numpy \
    pandas \
    scipy \
    scikit-learn \
    pyopenms \
    matplotlib \
    seaborn \
    plotly \
    pathlib \
    dotenv \
    loguru \
    tqdm \
    psycopg[binary] && \
    uv pip install -e .

WORKDIR /workspace

ENV PATH="/workspace/.venv/bin:$PATH"

CMD ["uv", "run"]