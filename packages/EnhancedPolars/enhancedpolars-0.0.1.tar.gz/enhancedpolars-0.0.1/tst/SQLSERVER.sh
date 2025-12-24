#!/bin/bash

# Exit if any command fails
set -e

# Load configuration from .env file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.env"

# Use environment variables from .env
CONTAINER_NAME="$SQLSERVER_CONTAINER_NAME"
SA_PASSWORD="$SQLSERVER_PASSWORD"
HOST_PORT="$SQLSERVER_HOST_PORT"
DB_NAME="$SQLSERVER_DB_NAME"

# Pull latest SQL Server 2022 image
# docker pull mcr.microsoft.com/mssql/server:2022-latest

# Stop and remove any existing container with the same name
docker rm -f $CONTAINER_NAME 2>/dev/null || true

# Run SQL Server container
docker run -e "ACCEPT_EULA=Y" \
    -e "MSSQL_SA_PASSWORD=$SA_PASSWORD" \
    -p $HOST_PORT:1433 \
    --name $CONTAINER_NAME \
    -d mcr.microsoft.com/mssql/server:2022-latest

echo "Waiting for SQL Server to start..."

# Wait for SQL Server to be ready (up to 60 seconds)
MAX_TRIES=30
TRIES=0
while [ $TRIES -lt $MAX_TRIES ]; do
    if docker exec $CONTAINER_NAME /opt/mssql-tools18/bin/sqlcmd \
        -S localhost -U SA -P "$SA_PASSWORD" -C -Q "SELECT 1" > /dev/null 2>&1; then
        echo "SQL Server is ready!"
        break
    fi
    TRIES=$((TRIES + 1))
    echo "Waiting for SQL Server to be ready... (attempt $TRIES/$MAX_TRIES)"
    sleep 2
done

if [ $TRIES -eq $MAX_TRIES ]; then
    echo "ERROR: SQL Server did not start within the expected time"
    exit 1
fi

# Create test database using sqlcmd inside the container
# In SQL Server 2022, sqlcmd is located at /opt/mssql-tools18/bin/sqlcmd
echo "Creating database $DB_NAME..."
docker exec $CONTAINER_NAME /opt/mssql-tools18/bin/sqlcmd \
    -S localhost -U SA -P "$SA_PASSWORD" -C -Q "IF DB_ID('$DB_NAME') IS NULL CREATE DATABASE [$DB_NAME];"

echo "Test SQL Server is running."
echo "Connect with:"
echo "  Host: localhost"
echo "  Port: $HOST_PORT"
echo "  User: SA"
echo "  Password: $SA_PASSWORD"
echo "  Database: $DB_NAME"