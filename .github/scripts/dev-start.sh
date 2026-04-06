#!/bin/bash
set -e

echo "Running docs validation..."
python3 /srv/content/.github/scripts/validate_docs.py

# Ensure PATH includes Jekyll binaries
export PATH=/usr/jekyll/bin:$PATH

# Use Docker volume for gems
bundle config set path '/srv/bundle'

# Install gems if missing
if [ ! -d "/srv/bundle" ] || [ -z "$(ls -A /srv/bundle 2>/dev/null)" ]; then
    echo "Installing Ruby gems..."
    # Ensure bundle cache volume is writable
    mkdir -p /srv/bundle
    chmod -R 777 /srv/bundle
    bundle install --jobs 4 --retry 3
fi

echo "Starting Jekyll server..."
bundle exec jekyll serve --host 0.0.0.0 --livereload --watch