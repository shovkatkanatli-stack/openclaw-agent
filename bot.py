import os, json, base64, sys, time
from datetime import datetime
from pathlib import Path
from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

WS_DIR = Path("/opt/jalil-bot")

def load_keys():
    kf = WS_DIR / ".keys"
    if not kf.exists(): return []
    keys = []
    for line in kf.read_text().strip().split('\n'):
        d = base64.b64decode(line)
        keys.append(bytes([b ^ 42 for b in d]).decode())
    return keys

keys = load_keys()
OR_KEY = keys[0] if len(keys) > 0 else ""
BOT_TOKEN = keys[1] if len(keys) > 1 else ""

START_TIME = time.time()

# OpenRouter free models — short name → full model ID
MODELS = {
    "nemotron-120b": "nvidia/nemotron-3-super-120b-a12b:free",
    "gpt-oss-120b":  "openai/gpt-oss-120b:free",
    "gpt-oss-20b":   "openai/gpt-oss-20b:free",
    "nemotron-30b":  "nvidia/nemotron-3-nano-30b-a3b:free",
    "nemotron-9b":   "nvidia/nemotron-nano-9b-v2:free",
    "north-code":    "cohere/north-mini-code:free",
    "liquid-1b":     "liquid/lfm-2.5-1.2b-instruct:free",
}

DEFAULT_MODEL = "nemotron-120b"
MODEL_FILE = WS_DIR / ".model"

def get_model():
    if MODEL_FILE.exists():
        name = MODEL_FILE.read_text().strip()
        return MODELS.get(name, MODELS[DEFAULT_MODEL])
    return MODELS[DEFAULT_MODEL]

client = AsyncOpenAI(
    api_key=OR_KEY,
    base_url="https://openrouter.ai/api/v1",
    default_headers={"HTTP-Referer": "https://github.com/shovkatkanatli-stack"}
)

WS = WS_DIR / "workspace"
WS.mkdir(parents=True, exist_ok=True)
(WS / "memory").mkdir(exist_ok=True)

SYSTEM_PROMPT = """You are جلیل (Jalil), Persian AI assistant for عباس (Abbas) from Istanbul - crypto trader & developer.
ALWAYS respond in Persian (فارسی). Put English technical terms in parentheses: (Python).
Be direct, helpful, concise."""

async def chat(msgs):
    model = get_model()
    try:
        resp = await client.chat.completions.create(
            model=model, messages=msgs, max_tokens=2048, temperature=0.7
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"❌ {str(e)[:150]}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cur = [k for k,v in MODELS.items() if v == get_model()][0]
    await update.message.reply_text(
        f"🦞 سلام عباس جان! من جلیل هستم.\n"
        f"🌐 OpenRouter | 🧠 {cur}\n"
        f"/model برای تغییر | /status وضعیت"
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    if not msg: return
    uid = str(update.effective_user.id)
    hf = WS / "memory" / f"chat_{uid}.json"
    history = []
    if hf.exists():
        try: history = json.loads(hf.read_text())[-8:]
        except: pass
    history.append({"role": "user", "content": msg})
    await update.message.chat.send_action(action="typing")
    reply = await chat([{"role": "system", "content": SYSTEM_PROMPT}] + history)
    history.append({"role": "assistant", "content": reply})
    hf.write_text(json.dumps(history[-16:], ensure_ascii=False, indent=2))
    if len(reply) > 4000:
        for i in range(0, len(reply), 4000):
            await update.message.reply_text(reply[i:i+4000])
    else:
        await update.message.reply_text(reply)

async def model_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = context.args[0].lower() if context.args else ""
    current = get_model()
    cur_name = [k for k,v in MODELS.items() if v == current][0] if current in MODELS.values() else "?"
    
    if not choice:
        lines = ["🎯 **مدل‌های OpenRouter:**\n"]
        for key in MODELS:
            mark = " ⭐" if MODELS[key] == current else ""
            lines.append(f"/model {key}{mark}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return
    
    if choice in MODELS:
        MODEL_FILE.write_text(choice)
        await update.message.reply_text(f"✅ مدل: {choice}\n🗿 {MODELS[choice]}")
    else:
        await update.message.reply_text("❌ مدل نامعتبر. /model برای لیست")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = time.time() - START_TIME
    h, m = int(uptime // 3600), int((uptime % 3600) // 60)
    cur = [k for k,v in MODELS.items() if v == get_model()][0]
    
    # Test API
    try:
        resp = await client.chat.completions.create(
            model=get_model(), messages=[{"role": "user", "content": "."}],
            max_tokens=1, temperature=0
        )
        api_status = "✅ فعال"
    except Exception as e:
        api_status = f"❌ {str(e)[:50]}"
    
    await update.message.reply_text(
        f"🦞 **جلیل**\n"
        f"🌐 OpenRouter | 🧠 {cur}\n"
        f"⏱ {h}h {m}m | {api_status}",
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦞 /start /help /remember /status /model")

async def remember(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if text:
        today = datetime.now().strftime("%Y-%m-%d")
        mem = WS / "memory" / f"{today}.md"
        old = mem.read_text() if mem.exists() else ""
        mem.write_text(old + f"- {text}\n")
        await update.message.reply_text("✅ ذخیره شد.")
    else:
        await update.message.reply_text("/remember <text>")

if __name__ == "__main__":
    cur = [k for k,v in MODELS.items() if v == get_model()][0]
    print(f"🦞 @jaliabibot | OpenRouter | {cur}")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("remember", remember))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("model", model_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("✅ RUNNING!")
    app.run_polling(drop_pending_updates=True)
