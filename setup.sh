#!/bin/bash

# playAgent Simple Setup Script
set -e

echo "🚀 Setting up playAgent..."

# Check if .env exists, if not create it
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. You can edit it if needed."
else
    echo "✅ .env file already exists"
fi

# Download models (optional)
echo "🤖 Downloading AI models (this may take a while)..."
if [ -f "setup-models.sh" ]; then
    ./setup-models.sh
else
    echo "⚠️  setup-models.sh not found, skipping model download"
fi

# Start services
echo "🐳 Starting Docker services..."
docker compose up --build -d

echo ""
echo "🎉 playAgent is ready!"
echo ""
echo "Access URLs:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:2024"
echo "  LangGraph: http://localhost:2924"
echo "  Neo4j:     http://localhost:7474"
echo "  NeoDash:   http://localhost:5005"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop:      docker compose down"
