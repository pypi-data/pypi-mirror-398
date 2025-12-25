# Choose base system, use slim version to control size
FROM python:3.11-slim

# Set environment variables
ENV OPT /opt
ENV WORKDIR /tmp
ENV PATH $OPT:$PATH
ENV AUTHOR "Kathryn Kelley, Chen Chen, Contextualize LLC"

# Append image metadata
LABEL description="Dockfile for application" maintainer=$AUTHOR

# Manage packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends git tk-dev tcl-dev libgtk-3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install python packages and change permissions
WORKDIR $OPT
COPY . $OPT

#RUN pip install git+https://__token__:glpat-85e3-cF88H4YwSfARZej@gitlab.com/contextualize/pycarta.git
#RUN pip install git+https://__token__:glpat-85e3-cF88H4YwSfARZej@gitlab.com/contextualize-public/aimpf/aimpf.git@chen-dev
RUN pip install pycarta
RUN pip install git+https://__token__:glpat-85e3-cF88H4YwSfARZej@gitlab.com/contextualize-public/aimpf/aimpf.git@develop

# Set ENTRYPOINT
WORKDIR $WORKDIR
ENTRYPOINT ["db38pulling"]
CMD []
