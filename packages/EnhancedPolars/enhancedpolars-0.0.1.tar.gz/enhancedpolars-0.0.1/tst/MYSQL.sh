#!/bin/bash

# Load configuration from .env file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.env"

# Use environment variables from .env
CONTAINER_NAME="$MYSQL_CONTAINER_NAME"
HOST_PORT="$MYSQL_HOST_PORT"
CONTAINER_PORT="$MYSQL_CONTAINER_PORT"

# ---- Remove any existing container with the same name ----
if docker ps -a | grep -w "$CONTAINER_NAME" > /dev/null; then
    echo "Removing existing container: $CONTAINER_NAME"
    docker rm -f $CONTAINER_NAME
fi

# ---- Run the MySQL container ----
echo "Starting MySQL container: $CONTAINER_NAME"
docker run -d \
    --name $CONTAINER_NAME \
    -e MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD \
    -e MYSQL_DATABASE=$MYSQL_DATABASE \
    -e MYSQL_USER=$MYSQL_USER \
    -e MYSQL_PASSWORD=$MYSQL_PASSWORD \
    -p $HOST_PORT:$CONTAINER_PORT \
    $MYSQL_IMAGE

echo "MySQL Docker container '$CONTAINER_NAME' is up."
echo "Connect: docker exec -it $CONTAINER_NAME mysql -u root -p"