# syntax=docker/dockerfile:1

FROM --platform=linux/amd64 python:3.11-slim

ARG EXTRA
ENV EXTRA=${EXTRA}

RUN pip install --upgrade pip && \
    pip install castor-extractor[${EXTRA}]

ENV CASTOR_OUTPUT_DIRECTORY=/data

VOLUME [ "/data" ]

ENTRYPOINT castor-extract-${EXTRA}
CMD [ "--log-to-stdout" ]
