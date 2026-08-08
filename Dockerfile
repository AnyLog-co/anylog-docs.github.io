FROM jekyll/jekyll:4

WORKDIR /srv/content

# Install Python + bash for your scripts
USER root
ENV BUNDLE_PATH=/srv/bundle

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 bash \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /srv/bundle \
    && chmod -R 777 /srv/bundle

# Keep container running root for gem installation and avoid permission issues
# Scripts will handle gem install automatically