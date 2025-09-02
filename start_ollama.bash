#!/bin/bash

# Load local environment config if it exists
export OLLAMA_KEEP_ALIVE=4000

echo "OLLAMA_MODELS:" $OLLAMA_MODELS
echo "OLLAMA_KEEP_ALIVE:" $OLLAMA_KEEP_ALIVE
ollama serve

# sudo systemctl stop ollama
# sudo systemctl status ollama
