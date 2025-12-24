FROM #{artifactory-python-image}# as base
LABEL maintainer="ia@bancolombia.onmicrosoft.com" description="Microservicio MCP Server scaffold"
RUN apt-get update && apt-get install -y build-essential

FROM base as with_deps
ARG ALLOW_ORIGINS
ENV ALLOW_ORIGINS=$ALLOW_ORIGINS
COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt -i https://artifactory.apps.bancolombia.com/api/pypi/pypi-bancolombia/simple --trusted-host artifactory.apps.bancolombia.com

RUN apt-get remove --purge cups* -y && apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN python -m pip uninstall pip -y
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN #{python-run-post-commands}#


FROM with_deps
EXPOSE #{container-port}#



USER appuser

WORKDIR /app

COPY src src
COPY main.py main.py

ENV PYTHONPATH=/app/src
# ENV SSL_CERT_FILE=#{docker-certificates-path}#

CMD #{worker-params}#


HEALTHCHECK NONE