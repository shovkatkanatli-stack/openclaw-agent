#!/bin/bash
set -e

echo "╔══════════════════════════════════════╗"
echo "║   🦞 OpenClaw AI Agent Setup          ║"
echo "╚══════════════════════════════════════╝"

# Get key from env or fallback
DEEPSEEK_KEY="${OPENCLAW_DEEPSEEK_KEY:-}"
if [ -z "$DEEPSEEK_KEY" ]; then
  # Read from secret file if exists
  if [ -f /workspaces/openclaw-agent/.key ]; then
    DEEPSEEK_KEY=$(cat /workspaces/openclaw-agent/.key)
  fi
fi

if [ -z "$DEEPSEEK_KEY" ]; then
  echo ""
  echo "⚠️  Need DeepSeek API key!"
  echo ""
  echo "Quick fix: run this in terminal:"
  echo "  echo 'export OPENCLAW_DEEPSEEK_KEY=sk-xxx' >> ~/.bashrc"
  echo "  source ~/.bashrc"
  echo "  bash /workspaces/openclaw-agent/setup-openclaw.sh"
  echo ""
  exit 1
fi

echo "[1/3] Installing OpenClaw..."
cd /tmp
if [ ! -d openclaw ]; then
  git clone --depth 1 https://github.com/openclaw/openclaw.git 2>/dev/null
fi
cd openclaw
npm install --legacy-peer-deps 2>&1 | tail -3

# Build
if [ ! -f dist/openclaw.mjs ]; then
  echo "  Building..."
  npm run build 2>&1 | tail -3 || true
fi

# Workspace
mkdir -p /workspaces/openclaw-agent/workspace/memory

cat > /workspaces/openclaw-agent/workspace/AGENTS.md << 'AGENTSEOF'
# AGENTS.md
## Memory: memory/YYYY-MM-DD.md (daily), MEMORY.md (long-term)
## Rules: Direct, Persian+English, privacy first, write everything down
## Safe: read, explore, search, code in workspace | Ask: financial, external
AGENTSEOF

cat > /workspaces/openclaw-agent/workspace/SOUL.md << 'SOULEOF'
# SOUL.md
- Speak Persian (فارسی), English terms in parentheses
- Direct, professional, trader mindset
- Data > opinions
- Proactive helper for Abbas
SOULEOF

cat > /workspaces/openclaw-agent/workspace/USER.md << 'USEREOF'
# USER.md
- Name: عباس (Abbas) | Istanbul | GMT+3
- Roles: Crypto trader, dev, server admin
USEREOF

echo "[2/3] Configuring OpenClaw..."
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
  echo "║ ✅ Agent LIVE! 🦞                     ║"
  echo "║ Gateway: http://localhost:18789       ║"
  echo "║ Chat: cd /tmp/openclaw && \\           ║"
  echo "║   node dist/openclaw.mjs chat        ║"
  echo "╚══════════════════════════════════════╝"
  tail -f /tmp/openclaw.log 2>/dev/null || sleep infinity
else
  echo "❌ Build failed. Check logs."
fi
