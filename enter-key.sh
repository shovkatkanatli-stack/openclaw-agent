#!/bin/bash
echo "Paste your DeepSeek API key:"
read -s API_KEY
echo "export OPENCLAW_DEEPSEEK_KEY=${API_KEY}" >> /root/.bashrc
echo "✅ Key saved! Now run: bash /workspaces/openclaw-agent/setup-openclaw.sh"
