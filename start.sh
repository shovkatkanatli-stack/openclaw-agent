#!/bin/bash
set -e

echo "╔══════════════════════════════╗"
echo "║   🦞 Jalil AI Bot Setup      ║"
echo "╚══════════════════════════════╝"
echo ""

echo "[1/3] Python: $(python3 --version)"
echo "[2/3] Installing dependencies..."
pip install -q python-telegram-bot openai 2>&1 | tail -1

echo "[3/3] Testing imports..."
python3 -c "
from telegram import Update; print('  ✅ telegram')
from openai import AsyncOpenAI; print('  ✅ openai')
import base64; print('  ✅ base64')
"

echo ""
echo "Starting bot..."
cd /workspaces/openclaw-agent
exec python3 -u bot.py
