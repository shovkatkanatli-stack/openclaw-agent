import os, json, asyncio, base64, subprocess
from datetime import datetime
from pathlib import Path
from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Decode keys from files
WS_DIR = Path("/workspaces/openclaw-agent")

def decode_file(name):
    path = WS_DIR / name
    if path.exists():
        return base64.b64decode(path.read_text().strip()).decode()
    return ""

DEEPSEEK_KEY = decode_file(".dk")
BOT_TOKEN = decode_file(".bt")

if not DEEPSEEK_KEY or not BOT_TOKEN:
    print("❌ Missing keys! Check .dk and .bt files")
    exit(1)

client = AsyncOpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com/v1")

WS = WS_DIR / "workspace"
WS.mkdir(parents=True, exist_ok=True)
(WS / "memory").mkdir(exist_ok=True)

SYSTEM_PROMPT = """You are a Persian-speaking AI agent for عباس. Rules:
1. Speak Persian (فارسی), put English terms in parentheses like this: (Python)
2. Be direct and professional - no fluff  
3. You are عباس's personal assistant - crypto trader, developer, server admin
4. Help with code, trading, server management, and everything else"""

async def chat_with_ai(user_msg: str, user_id: str) -> str:
    history_file = WS / "memory" / f"chat_{user_id}.json"
    history = []
    if history_file.exists():
        try: history = json.loads(history_file.read_text())[-20:]
        except: pass
    
    history.append({"role": "user", "content": user_msg})
    
    try:
        resp = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
            max_tokens=4096,
            temperature=0.7
        )
        reply = resp.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        history_file.write_text(json.dumps(history[-40:], ensure_ascii=False, indent=2))
        return reply
    except Exception as e:
        return f"❌ خطا: {str(e)[:200]}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦞 سلام عباس جان! من دستیار هوش مصنوعی تو هستم. هر کاری داری بگو.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message.text
    if not msg: return
    await update.message.chat.send_action(action="typing")
    reply = await chat_with_ai(msg, str(user.id))
    if len(reply) > 4000:
        for i in range(0, len(reply), 4000):
            await update.message.reply_text(reply[i:i+4000])
    else:
        await update.message.reply_text(reply)

async def remember(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if text:
        today = datetime.now().strftime("%Y-%m-%d")
        mem = WS / "memory" / f"{today}.md"
        mem.parent.mkdir(exist_ok=True)
        with open(mem, "a") as f: f.write(f"- {text}\n")
        await update.message.reply_text("✅ یادداشت شد.")
    else:
        await update.message.reply_text("📝 /remember <متن>")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        import psutil
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        await update.message.reply_text(
            f"📊 وضعیت:\n"
            f"رم: {mem.percent}% | {mem.used//1024**2}/{mem.total//1024**2} MB\n"
            f"دیسک: {disk.percent}% | {disk.free//1024**3} GB آزاد"
        )
    except:
        await update.message.reply_text("📊 وضعیت: فعال ✅")

async def run_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = " ".join(context.args) if context.args else ""
    if not cmd:
        await update.message.reply_text("📝 /run <دستور>")
        return
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, cwd=str(WS))
        output = result.stdout[:3500] or result.stderr[:3500] or "(بدون خروجی)"
        await update.message.reply_text(f"```\n{output}\n```", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)[:200]}")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦞 **دستیار هوش مصنوعی عباس**\n\n"
        "/start - شروع\n"
        "/remember <متن> - ذخیره یادداشت\n"
        "/status - وضعیت سرور\n"
        "/run <دستور> - اجرای دستور\n"
        "/help - راهنما",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("🦞 Starting AI Bot...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("remember", remember))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("run", run_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot running!")
    app.run_polling()
