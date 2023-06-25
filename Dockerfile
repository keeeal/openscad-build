FROM python:latest AS base

RUN apt update && apt install -y \
    openscad

RUN pip --no-cache-dir install --upgrade pip && \
    pip --no-cache-dir install --upgrade \
    fire \
    pydantic \
    pyyaml

COPY src /usr/bin
RUN for f in /usr/bin/*.py; do chmod u+x $f && mv $f $(dirname $f)/$(basename $f .py); done

FROM base AS dev

RUN pip --no-cache-dir install --upgrade \
    black \
    isort \
    pytest
