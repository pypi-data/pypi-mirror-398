#!/bin/bash

set -e

# Load configuration from .env file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.env"

# Use environment variables from .env
CONTAINER_NAME="$ORACLE_CONTAINER_NAME"
HOST_PORT="$ORACLE_HOST_PORT"

# Pull Oracle XE image (latest 21.3.0)
docker pull gvenzl/oracle-xe:21.3.0

# Stop and remove existing container
docker rm -f $CONTAINER_NAME 2>/dev/null || true

# Run the Oracle XE container
docker run -d \
  --name $CONTAINER_NAME \
  -e ORACLE_PASSWORD="$ORACLE_PASSWORD" \
  -e APP_USER="$ORACLE_USER" \
  -e APP_USER_PASSWORD="$ORACLE_PASSWORD" \
  -p $HOST_PORT:1521 \
  gvenzl/oracle-xe:21.3.0

echo "Waiting for Oracle XE to start (about 1 minute)..."
sleep 60

echo "Test Oracle XE is running."
echo "Connect with:"
echo "  Host: localhost"
echo "  Port: $HOST_PORT"
echo "  User: $ORACLE_USER"
echo "  Password: $ORACLE_PASSWORD"
echo "  Database/SID: $ORACLE_DATABASE (or XE for default SID)"