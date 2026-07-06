#!/bin/bash
set -e

echo "=== Wisconsin Overlay Map Deployment ==="

# Load environment
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "Starting PostgreSQL + PostGIS..."
docker-compose up -d db

echo "Waiting for database to be ready..."
sleep 8

echo "Running database setup..."
docker-compose run --rm app python db/db_setup.py

echo "Starting full pipeline..."
docker-compose up app

echo "Deployment complete."