#!/bin/bash
set -e

decode_file() {
  if [ -f "$1" ]; then
    cat "$1" | base64 -d
  fi
}

echo "╔══════════════════════════════════════╗"
echo "║   🦞 OpenClaw AI Agent Setup          ║"
echo "╚══════════════════════════════════════╝"

DEEPSEEK_KEY=$(decode_file /workspaces/openclaw-agent/.encoded-key)
BOT_TOKEN=$(decode_file /workspaces/openclaw-agent/.encoded-bot-token)

if [ -z "$DEEPSEEK_KEY" ]; then
  echo "❌ No DeepSeek key!"
  exit 1
fi

echo "[1/4] Installing OpenClaw..."
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

# Workspace
mkdir -p /workspaces/openclaw-agent/workspace/memory

cat > /workspaces/openclaw-agent/workspace/AGENTS.md << 'AGENTSEOF'
# AGENTS.md
## Persian+English, privacy first, write everything to files
AGENTSEOF

cat > /workspaces/openclaw-agent/workspace/SOUL.md << 'SOULEOF'
# SOUL.md
- Persian (فارسی), English in parentheses
- Direct, professional, trader+dev mindset
- Your personal AI agent — loyal to عباس
SOULEOF

cat > /workspaces/openclaw-agent/workspace/USER.md << 'USEREOF'
# USER.md
- Name: عباس (Abbas) | Istanbul | GMT+3
- Crypto trader, developer, server admin
USEREOF

echo "[2/4] Configuring OpenClaw..."
mkdir -p /root/.openclaw

cat > /root/.openclaw/openclaw.json << CONFIGEOF
{
  "gateway": {"mode": "local"},
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "${BOT_TOKEN}",
      "dmPolicy": "open"
    }
  },
  "plugins": {
    "entries": {
      "telegram": {"enabled": true}
    }
  },
  "agents": {
    "defaults": {
      "workspace": "/workspaces/openclaw-agent/workspace",
      "model": {"primary": "deepseek/deepseek-chat"},
      "heartbeat": {"every": "2h"}
    },
    "list": [{
      "id": "main",
      "name": "main",
      "workspace": "/workspaces/openclaw-agent/workspace",
      "default": true
    }]
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

echo "[3/4] Installing Telegram plugin deps..."
cd /tmp/openclaw
if [ -d extensions/telegram ]; then
  cd extensions/telegram
  npm install --legacy-peer-deps 2>&1 | tail -2 || true
  cd /tmp/openclaw
fi

echo "[4/4] Starting OpenClaw with Telegram..."
if [ -f dist/openclaw.mjs ]; then
  node dist/openclaw.mjs gateway > /tmp/openclaw.log 2>&1 &
  sleep 6
  
  echo ""
  echo "╔══════════════════════════════════════╗"
  echo "║ ✅ AI Agent IS LIVE! 🦞              ║"
  echo "║                                      ║"
  echo "║ 🌐 Web: http://localhost:18789       ║"
  echo "║ 📱 Telegram: @YOUR_BOT              ║"
  echo "║                                      ║"
  echo "║ Go to Telegram → start chatting!     ║"
  echo "╚══════════════════════════════════════╝"
  
  echo ""
  echo "Agent running..."
  tail -f /tmp/openclaw.log 2>/dev/null || sleep infinity
else
  echo "❌ Build failed"
fi
