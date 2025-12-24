#!/bin/bash

# Database Test Environment Manager
# Usage: ./db_test.sh {start|stop|status}
# This script manages all database containers for testing

set -e

# Get the directory where this script is located and load .env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.env"

# Container names from the individual scripts
CONTAINERS=(
    "my-mysql-db"
    "postgres-test"
    "oracle-xe-test"
    "sqlserver-test"
)

# Database scripts in this directory
DB_SCRIPTS=(
    "MYSQL.sh"
    "PostgreSQL.sh"
    "ORACLE.sh"
    "SQLSERVER.sh"
)

# Function to start all database containers
start_databases() {
    echo "Starting all database containers..."
    echo "=================================="

    for script in "${DB_SCRIPTS[@]}"; do
        script_path="$SCRIPT_DIR/$script"
        if [[ -f "$script_path" && -x "$script_path" ]]; then
            echo
            echo "Running $script..."
            echo "-------------------"
            bash "$script_path"
        else
            echo "Warning: $script not found or not executable"
        fi
    done
    
    echo
    echo "=================================="
    echo "All database startup scripts completed!"
    echo "Use 'docker ps' to verify running containers"
}

# Function to stop all database containers
stop_databases() {
    echo "Stopping all database containers..."
    echo "==================================="
    
    for container in "${CONTAINERS[@]}"; do
        if docker ps -q -f name="$container" | grep -q .; then
            echo "Stopping container: $container"
            docker stop "$container"
            docker rm "$container"
        else
            echo "Container $container is not running"
        fi
    done
    
    echo
    echo "==================================="
    echo "All database containers stopped and removed!"
}

# Function to test MySQL connection
test_mysql_connection() {
    docker exec "$MYSQL_CONTAINER_NAME" mysql \
        -u"$MYSQL_USER" \
        -p"$MYSQL_PASSWORD" \
        -D"$MYSQL_DATABASE" \
        -e "SELECT 1;" > /dev/null 2>&1
}

# Function to test PostgreSQL connection
test_postgres_connection() {
    docker exec "$POSTGRES_CONTAINER_NAME" psql \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        -c "SELECT 1;" > /dev/null 2>&1
}

# Function to test Oracle connection
test_oracle_connection() {
    docker exec "$ORACLE_CONTAINER_NAME" bash -c \
        "echo 'SELECT 1 FROM DUAL;' | sqlplus -S $ORACLE_USER/$ORACLE_PASSWORD@localhost:1521/XE" > /dev/null 2>&1
}

# Function to test SQL Server connection
test_sqlserver_connection() {
    docker exec "$SQLSERVER_CONTAINER_NAME" /opt/mssql-tools18/bin/sqlcmd \
        -S localhost \
        -U "$SQLSERVER_USER" \
        -P "$SQLSERVER_PASSWORD" \
        -C \
        -Q "SELECT 1;" > /dev/null 2>&1
}

# Function to test BigQuery connection (checks for credentials file)
# test_bigquery_connection() {
#     [[ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]] && [[ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]]
# }


# Function to test database connection based on container name
test_connection() {
    local container=$1
    case $container in
        "$MYSQL_CONTAINER_NAME")
            test_mysql_connection
            ;;
        "$POSTGRES_CONTAINER_NAME")
            test_postgres_connection
            ;;
        "$ORACLE_CONTAINER_NAME")
            test_oracle_connection
            ;;
        "$SQLSERVER_CONTAINER_NAME")
            test_sqlserver_connection
            ;;
        # "bigquery")
        #     test_bigquery_connection
        #     ;;
        *)
            return 1
            ;;
    esac
}

# Function to show status of all containers
status_databases() {
    echo "Database Container Status"
    echo "========================"
    echo

    for container in "${CONTAINERS[@]}"; do
        if docker ps -q -f name="$container" | grep -q .; then
            # Container is running, test connection
            if test_connection "$container" 2>/dev/null; then
                echo "✓ $container - RUNNING & CONNECTED"
            else
                echo "⚠ $container - RUNNING (connection failed)"
            fi
        else
            echo "✗ $container - STOPPED"
        fi
    done

    # BigQuery (credential-based, not a container)
    if test_connection "bigquery" 2>/dev/null; then
        echo "✓ bigquery - CREDENTIALS CONFIGURED"
    else
        echo "✗ bigquery - NO CREDENTIALS"
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 {start|stop|status}"
    echo
    echo "Commands:"
    echo "  start   - Start all database containers"
    echo "  stop    - Stop and remove all database containers"
    echo "  status  - Show status of all database containers"
    echo
    echo "Managed databases:"
    for i in "${!CONTAINERS[@]}"; do
        echo "  - ${CONTAINERS[$i]} (${DB_SCRIPTS[$i]})"
    done
    exit 1
}

# Main script logic
case "${1:-}" in
    start)
        start_databases
        ;;
    stop)
        stop_databases
        ;;
    status)
        status_databases
        ;;
    *)
        show_usage
        ;;
esac