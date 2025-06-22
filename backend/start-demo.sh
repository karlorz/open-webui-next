#!/usr/bin/env bash

# Demo/Guest Mode Startup Script
# This script starts Open WebUI in demo mode where authentication is bypassed
# and users can create chats without logging in.

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR" || exit

echo "Starting Open WebUI in Demo/Guest Mode..."

# Set demo mode environment variables
# export WEBUI_AUTH=False
# export WEBUI_NAME="Open WebUI Demo"
# export DEFAULT_USER_ROLE="admin"

# Add conditional Playwright browser installation
if [[ "${WEB_LOADER_ENGINE,,}" == "playwright" ]]; then
    if [[ -z "${PLAYWRIGHT_WS_URL}" ]]; then
        echo "Installing Playwright browsers..."
        playwright install chromium
        playwright install-deps chromium
    fi

    python -c "import nltk; nltk.download('punkt_tab')"
fi

KEY_FILE=.webui_secret_key

PORT="${PORT:-8080}"
HOST="${HOST:-0.0.0.0}"

# Handle secret key generation
if test "$WEBUI_SECRET_KEY $WEBUI_JWT_SECRET_KEY" = " "; then
  echo "Loading WEBUI_SECRET_KEY from file, not provided as an environment variable."

  if ! [ -e "$KEY_FILE" ]; then
    echo "Generating WEBUI_SECRET_KEY"
    # Generate a random value to use as a WEBUI_SECRET_KEY in case the user didn't provide one.
    echo $(head -c 12 /dev/random | base64) > "$KEY_FILE"
  fi

  echo "Loading WEBUI_SECRET_KEY from $KEY_FILE"
  WEBUI_SECRET_KEY=$(cat "$KEY_FILE")
fi

# Remove existing users database to ensure fresh demo state
echo "Preparing demo environment..."
DATA_DIR="${DATA_DIR:-./data}"
# DB_FILE="${DATA_DIR}/webui.db"

if [ -f "$DB_FILE" ]; then
    echo "Removing existing user database for demo mode..."
    rm -f "$DB_FILE"
fi

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"

if [[ "${USE_OLLAMA_DOCKER,,}" == "true" ]]; then
    echo "USE_OLLAMA is set to true, starting ollama serve."
    ollama serve &
fi

if [[ "${USE_CUDA_DOCKER,,}" == "true" ]]; then
  echo "CUDA is enabled, appending LD_LIBRARY_PATH to include torch/cudnn & cublas libraries."
  export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/local/lib/python3.11/site-packages/torch/lib:/usr/local/lib/python3.11/site-packages/nvidia/cudnn/lib"
fi

# Check if SPACE_ID is set, if so, configure for space
if [ -n "$SPACE_ID" ]; then
  echo "Configuring for HuggingFace Space deployment in demo mode"
  export WEBUI_URL=${SPACE_HOST}
fi

PYTHON_CMD=$(command -v python3 || command -v python)

echo "Demo mode enabled - authentication is disabled and anonymous access is allowed"
echo "Starting Open WebUI server on $HOST:$PORT"

# Start the server with demo mode environment variables
WEBUI_SECRET_KEY="$WEBUI_SECRET_KEY" exec uv run uvicorn open_webui.main:app --host "$HOST" --port "$PORT" --forwarded-allow-ips '*' --workers "${UVICORN_WORKERS:-1}"
