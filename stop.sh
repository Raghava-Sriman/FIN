#!/bin/bash
# FinSight - Shutdown Script

echo "🛑 Stopping FinSight services..."
lsof -ti:8000,3000 | xargs kill -9 2>/dev/null || true
pkill -f "cloudflared tunnel" 2>/dev/null || true
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
echo "✅ All services stopped."
