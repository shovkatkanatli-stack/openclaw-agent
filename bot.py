import os, json, base64, sys, time
from datetime import datetime
from pathlib import Path
from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

WS_DIR = Path(__file__).parent.resolve()

def load_keys():
    kf = WS_DIR / ".keys"
    if not kf.exists(): return []
    keys = []
    for line in kf.read_text().strip().split('\n'):
        d = base64.b64decode(line)
        keys.append(bytes([b ^ 42 for b in d]).decode())
    return keys

keys = load_keys()
GEMINI_KEY = keys[0] if len(keys) > 0 else ""
GROQ_KEY = keys[1] if len(keys) > 1 else ""
BOT_TOKEN = keys[2] if len(keys) > 2 else ""

START_TIME = time.time()

PROVIDERS = []
if GROQ_KEY:
    PROVIDERS.append({
        "name": "Groq",
        "client": AsyncOpenAI(api_key=GROQ_KEY, base_url="https://api.groq.com/openai/v1"),
        "model": "llama-3.3-70b-versatile"
    })
if GEMINI_KEY:
    PROVIDERS.append({
        "name": "Gemini",
        "client": AsyncOpenAI(api_key=GEMINI_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/"),
        "model": "gemini-2.0-flash"
    })

WS = WS_DIR / "workspace"
WS.mkdir(parents=True, exist_ok=True)
(WS / "memory").mkdir(exist_ok=True)

SYSTEM_PROMPT = """You are جلیل (Jalil), Persian AI assistant for عباس (Abbas) from Istanbul - crypto trader & developer.
ALWAYS respond in Persian (فارسی). Put English technical terms in parentheses: (Python).
Be direct, helpful, concise."""

async def try_chat(msgs):
    last_error = "همه سرویس‌ها در دسترس نیستن"
    for p in PROVIDERS:
        try:
            resp = await p["client"].chat.completions.create(
                model=p["model"], messages=msgs, max_tokens=2048, temperature=0.7
            )
            reply = resp.choices[0].message.content
            # Mark which provider responded
            return f"{reply}"
        except Exception as e:
            err = str(e)[:100]
            if '429' in err or 'quota' in err.lower():
                continue
            last_error = err
            continue
    return f"❌ {last_error}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    providers = " + ".join(p["name"] for p in PROVIDERS)
    await update.message.reply_text(
        f"🦞 سلام عباس جان! من جلیل هستم.\n"
        f"🧠 {providers}\nهر کاری داری بگو."
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
    reply = await try_chat([{"role": "system", "content": SYSTEM_PROMPT}] + history)
    history.append({"role": "assistant", "content": reply})
    hf.write_text(json.dumps(history[-16:], ensure_ascii=False, indent=2))
    if len(reply) > 4000:
        for i in range(0, len(reply), 4000):
            await update.message.reply_text(reply[i:i+4000])
    else:
        await update.message.reply_text(reply)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦞 /start /help /remember /status")

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

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = time.time() - START_TIME
    h, m = int(uptime // 3600), int((uptime % 3600) // 60)
    
    # Test each provider
    prov_status = []
    for p in PROVIDERS:
        try:
            resp = await p["client"].chat.completions.create(
                model=p["model"],
                messages=[{"role": "user", "content": "."}],
                max_tokens=1,
                temperature=0
            )
            prov_status.append(f"✅ {p['name']} ({p['model']})")
        except Exception as e:
            err = str(e)
            if '429' in err or 'quota' in err.lower():
                prov_status.append(f"⚠️ {p['name']} - محدودیت")
            elif '403' in err:
                prov_status.append(f"🚫 {p['name']} - مسدود")
            else:
                prov_status.append(f"❌ {p['name']} - {err[:40]}")
    
    await update.message.reply_text(
        f"🦞 **جلیل**\n"
        f"⏱ زمان: {h}h {m}m\n\n"
        + "\n".join(prov_status),
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print(f"🦞 @jaliabibot with {len(PROVIDERS)} providers: {[p['name'] for p in PROVIDERS]}")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("remember", remember))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("✅ RUNNING!")
    app.run_polling(drop_pending_updates=True)
