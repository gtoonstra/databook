# DESCRIPTION: Databook docker file

FROM python:3.4-slim
MAINTAINER GT

# Never prompts the user for choices on installation/configuration of packages
ENV DEBIAN_FRONTEND noninteractive
ENV TERM linux

# Databook
ARG DATABOOK_VERSION=0.1.0
ARG DATABOOK_HOME=/usr/local/databook

# Define en_US.
ENV LANGUAGE en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV LC_CTYPE en_US.UTF-8
ENV LC_MESSAGES en_US.UTF-8
ENV LC_ALL en_US.UTF-8

RUN set -ex \
    && buildDeps=' \
        libkrb5-dev \
        libsasl2-dev \
        libssl-dev \
        libffi-dev \
        build-essential \
        libpq-dev \
        git \
    ' \
    && apt-get update -yqq \
    && apt-get install -yqq --no-install-recommends \
        $buildDeps \
        apt-utils \
        curl \
        netcat \
        locales \
    && sed -i 's/^# en_US.UTF-8 UTF-8$/en_US.UTF-8 UTF-8/g' /etc/locale.gen \
    && locale-gen \
    && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
    && useradd -ms /bin/bash -d ${DATABOOK_HOME} databook \
    && pip install Cython \
       ndg-httpsclient \
       ldap3 \
    && apt-get remove --purge -yqq $buildDeps \
    && apt-get clean \
    && rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/man \
        /usr/share/doc \
        /usr/share/doc-base

COPY docker/databook/script/entrypoint.sh /entrypoint.sh

ADD . /tmp/
WORKDIR /tmp/
RUN pip install /tmp/

# COPY config/databook.cfg ${DATABOOK_HOME}/databook.cfg

RUN chown -R databook: ${DATABOOK_HOME} \
    && chmod +x /entrypoint.sh

EXPOSE 5000

USER databook
WORKDIR ${DATABOOK_HOME}
ENTRYPOINT ["/entrypoint.sh"]
