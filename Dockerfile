FROM jekyll/jekyll:4

WORKDIR /srv/content

# Install Python + bash for your scripts
USER root
ENV BUNDLE_PATH=/srv/bundle

RUN apk add --no-cache python3 py3-pip bash \
    && pip install pyyaml && \
    mkdir -p /srv/bundle && \
    chmod -R 777 /srv/bundle

USER root
RUN

# Keep container running root for gem installation and avoid permission issues
# Scripts will handle gem install automatically