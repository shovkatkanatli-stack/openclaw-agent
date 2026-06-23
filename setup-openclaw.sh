#!/bin/bash
set -e

decode_key() {
  if [ -f /workspaces/openclaw-agent/.encoded-key ]; then
    cat /workspaces/openclaw-agent/.encoded-key | base64 -d
  fi
}

echo "╔══════════════════════════════════════╗"
echo "║   🦞 OpenClaw AI Agent Setup          ║"
echo "╚══════════════════════════════════════╝"

DEEPSEEK_KEY=$(decode_key)
if [ -z "$DEEPSEEK_KEY" ]; then
  echo "❌ No key found!"
  exit 1
fi

echo "[1/3] Installing OpenClaw..."
cd /tmp
if [ ! -d openclaw ]; then
  git clone --depth 1 https://github.com/openclaw/openclaw.git 2>/dev/null
fi
cd openclaw
npm install --legacy-peer-deps 2>&1 | tail -2

if [ ! -f dist/openclaw.mjs ]; then
  echo "  Building..."
  npm run build 2>&1 | tail -2 || true
fi

mkdir -p /workspaces/openclaw-agent/workspace/memory

cat > /workspaces/openclaw-agent/workspace/AGENTS.md << 'AGENTSEOF'
# AGENTS.md
## Memory: memory/YYYY-MM-DD.md (daily), MEMORY.md (long-term)
## Persian+English, privacy first, write everything down
AGENTSEOF

cat > /workspaces/openclaw-agent/workspace/SOUL.md << 'SOULEOF'
# SOUL.md
- Persian (فارسی), English in parentheses
- Direct, professional, trader mindset
- AI agent for Abbas — crypto trader & dev
SOULEOF

cat > /workspaces/openclaw-agent/workspace/USER.md << 'USEREOF'
# USER.md  
- عباس (Abbas) | Istanbul | GMT+3
- Crypto trader, dev, server admin
- Python, Bash, Binance, Bybit, n8n
USEREOF

echo "[2/3] Configuring..."
mkdir -p /root/.openclaw

cat > /root/.openclaw/openclaw.json << CONFIGEOF
{
  "gateway": {"mode": "local"},
  "agents": {
    "defaults": {
      "workspace": "/workspaces/openclaw-agent/workspace",
      "model": {"primary": "deepseek/deepseek-chat"}
    }
  },
  "models": {
    "providers": {
      "deepseek": {
        "baseUrl": "https://api.deepseek.com/v1",
        "apiKey": "${DEEPSEEK_KEY}",
        "api": "openai-completions",
        "models": [{
          "id": "deepseek-chat",
          "name": "DeepSeek Chat",
          "contextWindow": 131072,
          "maxTokens": 8192,
          "cost": {"input": 0.14, "output": 0.28, "cacheRead": 0.014},
          "input": ["text"]
        }]
      }
    }
  }
}
CONFIGEOF

echo "[3/3] Starting OpenClaw..."
cd /tmp/openclaw

if [ -f dist/openclaw.mjs ]; then
  node dist/openclaw.mjs gateway > /tmp/openclaw.log 2>&1 &
  sleep 5
  echo ""
  echo "╔══════════════════════════════════════╗"
  echo "║ ✅ AI Agent IS LIVE! 🦞              ║"
  echo "║ Gateway: http://localhost:18789       ║"
  echo "║ Chat: cd /tmp/openclaw && \\           ║"
  echo "║   node dist/openclaw.mjs chat        ║"
  echo "╚══════════════════════════════════════╝"
  tail -f /tmp/openclaw.log 2>/dev/null || sleep infinity
else
  echo "❌ Build failed"
fi
