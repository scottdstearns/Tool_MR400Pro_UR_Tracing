#!/bin/bash
# Rebuild script for MR400 Pro UR Tracing tool
# Run this after git pull to ensure Docker uses the latest code

set -e

echo "📦 Rebuilding MR400 Pro UR Tracing tool..."
echo ""

# Stop existing container
echo "🛑 Stopping existing container..."
docker compose down

# Rebuild image (no cache to ensure fresh build)
echo "🔨 Building fresh Docker image..."
docker compose build --no-cache

# Start container
echo "🚀 Starting container..."
docker compose up -d

# Show logs
echo ""
echo "📋 Container logs (Ctrl+C to exit):"
docker compose logs -f


