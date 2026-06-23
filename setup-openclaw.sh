#!/bin/bash
set -e

echo "╔══════════════════════════════════════╗"
echo "║   🦞 OpenClaw AI Agent Setup          ║"
echo "╚══════════════════════════════════════╝"

# Get API key from env var (set in Codespace secrets)
DEEPSEEK_KEY="${DEEPSEEK_API_KEY:-}"
if [ -z "$DEEPSEEK_KEY" ]; then
  echo ""
  echo "⚠️  No DEEPSEEK_API_KEY found!"
  echo "   Set it in Codespace secrets or paste below:"
  echo ""
  read -p "Paste your DeepSeek API key: " DEEPSEEK_KEY
fi

echo "[1/3] Installing OpenClaw..."
cd /tmp
if [ ! -d openclaw ]; then
  git clone --depth 1 https://github.com/openclaw/openclaw.git 2>/dev/null
fi
cd openclaw
npm install --legacy-peer-deps 2>&1 | tail -2

# Create workspace with standard files
mkdir -p /workspaces/openclaw-agent/workspace/memory

# AGENTS.md
cat > /workspaces/openclaw-agent/workspace/AGENTS.md << 'AGENTSEOF'
# AGENTS.md
## Memory: memory/YYYY-MM-DD.md (daily), MEMORY.md (long-term)
## Rules: Direct, Persian+English, privacy first, write everything down
## Safe: read, explore, search, code in workspace
## Ask first: financial, external actions
AGENTSEOF

# SOUL.md
cat > /workspaces/openclaw-agent/workspace/SOUL.md << 'SOULEOF'
# SOUL.md
- Speak Persian (فارسی), English terms in parentheses
- Direct, professional, trader mindset
- Data > opinions, logs > guesses
- Proactive helper for Abbas
SOULEOF

# USER.md
cat > /workspaces/openclaw-agent/workspace/USER.md << 'USEREOF'
# USER.md
- Name: عباس (Abbas) | Location: Istanbul | GMT+3
- Roles: Crypto trader, developer, server admin
- Tools: Python, Bash, Linux, Binance, Bybit, n8n
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
node dist/openclaw.mjs gateway > /tmp/openclaw.log 2>&1 &
sleep 5

# Quick test
if curl -s http://localhost:18789/ > /dev/null 2>&1; then
  echo ""
  echo "╔══════════════════════════════════════╗"
  echo "║ ✅ OpenClaw Agent IS LIVE! 🦞        ║"
  echo "║                                      ║"
  echo "║ 🌐 Gateway: http://localhost:18789   ║"
  echo "║ 💬 Chat: cd /tmp/openclaw && \\       ║"
  echo "║    node dist/openclaw.mjs chat       ║"
  echo "║                                      ║"
  echo "║ Your personal AI agent — ready!      ║"
  echo "╚══════════════════════════════════════╝"
else
  echo ""
  echo "⚠️  Gateway may need manual start:"
  echo "   cd /tmp/openclaw"
  echo "   node dist/openclaw.mjs gateway"
fi
