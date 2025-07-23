#!/bin/bash

# Load local environment config if it exists
CONFIG_FILE="./.env.local"
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    echo "Warning: Config file $CONFIG_FILE not found."
fi

echo "OLLAMA_MODELS:" $OLLAMA_MODELS
echo "OLLAMA_KEEP_ALIVE:" $OLLAMA_KEEP_ALIVE
ollama serve