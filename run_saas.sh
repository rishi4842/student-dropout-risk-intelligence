#!/usr/bin/env bash
# Start RetainAI SaaS: FastAPI Backend + Next.js Frontend

echo "Starting RetainAI FastAPI Backend on http://127.0.0.1:8000..."
./venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

echo "Starting RetainAI Next.js Frontend on http://localhost:3000..."
cd frontend && npm run start &
FRONTEND_PID=$!

echo "Platform running!"
echo "• Frontend: http://localhost:3000"
echo "• Backend Docs: http://127.0.0.1:8000/docs"
echo "Press Ctrl+C to terminate both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
