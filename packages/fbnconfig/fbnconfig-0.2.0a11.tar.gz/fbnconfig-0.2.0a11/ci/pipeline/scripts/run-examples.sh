#!/bin/sh

# this runs on an alpine image, so needs to be sh instead of bash
set -eu pipefail

echo "Starting docker daemon"

 nohup sh -c "/usr/local/bin/dockerd-entrypoint.sh" > /dev/null 2>&1 &

MAX_TRIES=10
TRIES=0

check_docker_status() {
    docker info >/dev/null 2>&1
    return $?
}

while [ $TRIES -lt $MAX_TRIES ] && ! check_docker_status ; do
      TRIES=$((TRIES + 1))
      echo "Attempt $TRIES: Docker daemon is not running, retrying in 5 seconds..."
      sleep 5
done

if [  -$TRIES -eq $MAX_TRIES ]; then
        echo "Docker daemon could not be started after $MAX_TRIES attempts. Exiting."
        exit 1
else
        echo "Docker daemon is now running."
fi
echo "Login to harbor"

docker login harbor.finbourne.com --username "$HARBOR_USERNAME" --password "$HARBOR_PASSWORD"

echo "Running install..."
uv sync
echo "Running tests..."
# auto option creates workers based on number of cpus available
uv run pytest tests/integration -n auto --dist loadfile -v -s


