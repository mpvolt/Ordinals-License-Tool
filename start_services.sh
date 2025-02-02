#!/bin/bash

# Define paths
PROJECT_ROOT="$(pwd)"
FLASK_APP_DIR="$PROJECT_ROOT/flask-app"
BITCOIN_PROXY_DIR="$PROJECT_ROOT/bitcoin-proxy"

# Function to install dependencies for the Flask app
setup_flask_app() {
    echo "Setting up Flask app..."
    echo "Installing Flask dependencies..."
    pip install --upgrade pip
    pip install flask flask_cors requests
    pip install --upgrade requests urllib3

    echo "Flask setup complete."
}

# Install Node.js dependencies
echo "Running npm install in project root..."
(cd "$PROJECT_ROOT" && npm install) || { echo "npm install failed"; exit 1; }

# Setup the Flask app environment
setup_flask_app

# Start React app
echo "Starting React App..."
(cd "$PROJECT_ROOT" && npm start) &

# Start Flask app
echo "Starting Flask App..."
(cd "$FLASK_APP_DIR" && source .venv/bin/activate && python3 app.py) &

# Start Bitcoin Proxy server
echo "Starting Bitcoin Proxy Server..."
(cd "$BITCOIN_PROXY_DIR" && node server.js) &

# Wait for processes to run in the background
wait
