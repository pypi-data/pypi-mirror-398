#!/bin/bash

# Exit on error
set -e

# Load configuration from .env file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.env"

# Use environment variables from .env
CONTAINER_NAME="$POSTGRES_CONTAINER_NAME"
HOST_PORT="$POSTGRES_HOST_PORT"

# Pull the official PostgreSQL image
docker pull postgres:$POSTGRES_VERSION

# Stop and remove any existing container with the same name
docker rm -f $CONTAINER_NAME 2>/dev/null || true

# Run PostgreSQL container
docker run -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
    -e POSTGRES_USER=$POSTGRES_USER \
    -e POSTGRES_DB=$POSTGRES_DB \
    -p $HOST_PORT:5432 \
    --name $CONTAINER_NAME \
    -d postgres:$POSTGRES_VERSION

echo "Waiting for PostgreSQL to start..."
sleep 10

echo "Test PostgreSQL is running."
echo "Connect with:"
echo "  Host: localhost"
echo "  Port: $HOST_PORT"
echo "  User: $POSTGRES_USER"
echo "  Password: $POSTGRES_PASSWORD"
echo "  Database: $POSTGRES_DB"
echo "  Version: $POSTGRES_VERSION"