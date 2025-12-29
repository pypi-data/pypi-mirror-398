# Base image
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1

# Opt out of PEP 668 for all pip runs
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# Base packages
RUN apt-get update -qy \
 && apt-get install -y --no-install-recommends \
    curl \
    zip \ 
    git \
    graphviz \
    pandoc \
    python3 \
    python3-dev \
    python3-pip \
 && apt-get autoremove --purge -y \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade \
    pip \
    setuptools \
    setuptools-scm \
    wheel \
    build

RUN pip install --no-cache-dir \
    coverage \
    flake8 \
    nbmake \
    pytest \
    twine \
    xdoctest

RUN pip install --no-cache-dir \
    sphinx \
    sphinx_autodoc_typehints \
    sphinx-rtd-theme \
    sphinx_sitemap \
    sphinxcontrib-bibtex \
    nbsphinx \
    ipywidgets

RUN pip install --no-cache-dir \
    colorcet \
    colorspacious \
    h5py \
    matplotlib \
    cuda-bindings \
    cuda-core \
    numba-cuda \
    numpy \
    scipy \
    scikit-image \
    tqdm \
    cython

CMD /bin/bash
