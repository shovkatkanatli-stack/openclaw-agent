#!/bin/bash
set -e

echo "╔══════════════════════════════════════╗"
echo "║   🦞 OpenClaw AI Agent Setup          ║"
echo "╚══════════════════════════════════════╝"

# Install OpenClaw
echo "[1/4] Installing OpenClaw..."
cd /tmp
git clone https://github.com/openclaw/openclaw.git 2>/dev/null || true
cd openclaw

# Install dependencies
npm install --legacy-peer-deps 2>&1 | tail -1

# Create workspace for the agent
mkdir -p /workspaces/openclaw-agent/workspace/memory

# Create AGENTS.md
cat > /workspaces/openclaw-agent/workspace/AGENTS.md << 'AGENTSEOF'
# AGENTS.md

## First Run
Follow BOOTSTRAP.md if it exists.

## Memory
- Daily notes: memory/YYYY-MM-DD.md
- Long-term: MEMORY.md

## Red Lines
- Don't exfiltrate private data
- Don't run destructive commands without asking
- trash > rm

## Tools
Skills provide your tools. Check SKILL.md when needed.

## External vs Internal
Safe: read files, explore, organize, search web, work in workspace
Ask first: send emails, tweets, public posts, anything that leaves the machine
AGENTSEOF

# Create SOUL.md
cat > /workspaces/openclaw-agent/workspace/SOUL.md << 'SOULEOF'
# SOUL.md

## Core
- Professional, direct, helpful assistant
- Persian + English bilingual
- Proactive, not passive
- Think like a developer and trader

## Boundaries  
- Privacy is absolute
- No financial actions without approval
- Never send incomplete work
SOULEOF

# Create USER.md
cat > /workspaces/openclaw-agent/workspace/USER.md << 'USEREOF'
# USER.md

- Name: عباس (Abbas)
- Languages: فارسی primary, English secondary
- Location: Istanbul, Turkey (GMT+3)
- Roles: Crypto trader, developer, server admin
- Preferences: Ubuntu/Linux, Python & Bash, free/low-cost tools
USEREOF

# Build OpenClaw
echo "[2/4] Building OpenClaw..."
pnpm build 2>&1 | tail -1 || npm run build 2>&1 | tail -1

# Create config
mkdir -p /root/.openclaw
cat > /root/.openclaw/config.json << 'CONFIGEOF'
{
  "gateway": {"mode": "local"},
  "channels": {
    "polling": {"enabled": true, "intervalMs": 30000}
  },
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
        "apiKey": "YOUR_DEEPSEEK_API_KEY",
        "api": "openai-completions",
        "models": [{
          "id": "deepseek-chat",
          "name": "DeepSeek Chat",
          "contextWindow": 131072,
          "maxTokens": 8192,
          "input": ["text"]
        }]
      }
    }
  }
}
CONFIGEOF

echo "[3/4] Configuration created"
echo ""
echo "⚠️ IMPORTANT: Add your DeepSeek API key!"
echo "   1. Get FREE key: https://platform.deepseek.com/api_keys"
echo "   2. Edit: /root/.openclaw/config.json"
echo "   3. Replace YOUR_DEEPSEEK_API_KEY"
echo ""

# Start OpenClaw
echo "[4/4] Starting OpenClaw Gateway..."
cd /tmp/openclaw
node openclaw.mjs gateway > /tmp/openclaw.log 2>&1 &
sleep 3

echo ""
echo "✅ OpenClaw Agent is running!"
echo "🌐 Gateway: http://localhost:18789"
echo "💬 Start chatting: node openclaw.mjs chat"
echo ""
echo "╔══════════════════════════════════════╗"
echo "║   🦞 Agent Ready!                      ║"
echo "╚══════════════════════════════════════╝"
