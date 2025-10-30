#!/bin/bash

# playAgent Model Setup Script
set -e

echo "🤖 Downloading AI models..."

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create models directory
mkdir -p ollama-custom/.ollama

# Start temporary Ollama container
echo "📦 Starting Ollama container..."
docker run -d \
    --name ollama-temp \
    -v "$(pwd)/ollama-custom/.ollama:/root/.ollama" \
    -p 11434:11434 \
    ollama/ollama:latest

# Wait for Ollama to start
echo "⏳ Waiting for Ollama to start..."
sleep 10

# Download models
echo "📥 Downloading models..."
docker exec ollama-temp ollama pull gpt-oss:20b
docker exec ollama-temp ollama pull nomic-embed-text

# Cleanup
echo "🧹 Cleaning up..."
docker stop ollama-temp
docker rm ollama-temp

echo "✅ Model setup completed!"
