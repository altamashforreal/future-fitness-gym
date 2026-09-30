#!/bin/bash
# This script runs on Render before starting the server.
# It seeds the database with default plans and admin account.

echo "Running database seed..."
python seed.py

echo "Starting server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT
