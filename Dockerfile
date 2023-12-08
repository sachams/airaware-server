# https://hub.docker.com/_/python
FROM python:3.10-slim-bullseye

ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
WORKDIR $APP_HOME

###### Install utils ###########

RUN apt-get -qqy update && apt-get install -qqy --no-install-recommends \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

###### Install supercronic #####

# Latest releases available at https://github.com/aptible/supercronic/releases
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.26/supercronic-linux-amd64 \
    SUPERCRONIC=supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=7a79496cf8ad899b99a719355d4db27422396735

RUN curl -fsSLO "$SUPERCRONIC_URL" \
    && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
    && chmod +x "$SUPERCRONIC" \
    && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
    && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

####### dev stuff

# Copy pdb config file to home directory to set default PDBPP behaviour
# Uncomment lines below when building for dev
# TODO: add separate dev Docker build target
# COPY ./.pdbrc.py /root
# COPY dev_requirements.txt ./
# RUN pip install --no-cache-dir -r dev_requirements.txt

COPY . ./

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
