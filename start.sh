#!/bin/bash
# FinSight - Clean Launcher

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Cleanup function on Ctrl+C or script exit
cleanup() {
    echo ""
    echo "🛑 Shutting down FinSight..."
    lsof -ti:8000,3000 | xargs kill -9 2>/dev/null || true
    pkill -f "cloudflared" 2>/dev/null || true
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true
    rm -f "/tmp/cloudflared_$$.log" 2>/dev/null || true
    echo "✅ All services stopped."
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Kill old processes
lsof -ti:8000,3000 | xargs kill -9 2>/dev/null || true
pkill -f "cloudflared" 2>/dev/null || true

echo "🚀 Starting FinSight servers..."

# 1. Start Backend
cd "$DIR/backend"
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload > "$DIR/backend.log" 2>&1 &

# 2. Start Frontend
cd "$DIR/frontend"
npm run dev > "$DIR/frontend.log" 2>&1 &

# 3. Start Cloudflare Tunnel and capture URL
echo "🌐 Connecting phone tunnel..."
TMP_LOG="/tmp/cloudflared_$$.log"
cloudflared tunnel --url http://localhost:3000 > "$TMP_LOG" 2>&1 &
TUNNEL_PID=$!

# Wait for tunnel URL
URL=""
for i in {1..30}; do
    URL=$(grep -o 'https://[a-zA-Z0-9-]*\.trycloudflare\.com' "$TMP_LOG" 2>/dev/null | head -n 1)
    if [ -n "$URL" ]; then
        break
    fi
    sleep 0.5
done

clear

if [ -n "$URL" ]; then
    echo "================================================================"
    echo "             🎉 FinSight IS READY & LIVE!                     "
    echo "================================================================"
    echo ""
    echo "  📱 PHONE LINK:  $URL"
    echo "  💻 LAPTOP LINK: http://localhost:3000"
    echo ""
    echo "================================================================"
    echo "👉 Open the PHONE LINK above in your mobile browser."
    echo "👉 Press Ctrl+C in this terminal when you want to stop."
    echo "================================================================"
else
    echo "⚠️ Tunnel starting... check $TMP_LOG"
fi

# Keep script running until user presses Ctrl+C
wait $TUNNEL_PID
