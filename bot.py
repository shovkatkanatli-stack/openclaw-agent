import os, json, base64, sys, traceback
from datetime import datetime
from pathlib import Path
from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

WS_DIR = Path(__file__).parent.resolve()

def decode_file(name):
    path = WS_DIR / name
    if not path.exists(): return ""
    try:
        data = path.read_text().strip()
        return base64.b64decode(data).decode()
    except Exception as e:
        print(f"Decode error {name}: {e}")
        return ""

GEMINI_KEY = decode_file(".dk")
BOT_TOKEN = decode_file(".bt")

if not GEMINI_KEY or not BOT_TOKEN:
    print("❌ Missing keys!")
    sys.exit(1)

# Gemini OpenAI-compatible endpoint (FREE)
client = AsyncOpenAI(
    api_key=GEMINI_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

WS = WS_DIR / "workspace"
WS.mkdir(parents=True, exist_ok=True)
(WS / "memory").mkdir(exist_ok=True)

SYSTEM_PROMPT = """You are جلیل (Jalil), a Persian-speaking AI assistant. Rules:
1. Always respond in Persian (فارسی)
2. Put English technical terms in parentheses: (Python), (API)
3. Be direct, professional, and helpful
4. Your user is عباس (Abbas) - crypto trader, developer, server admin"""

async def chat_with_ai(user_msg: str, user_id: str) -> str:
    history_file = WS / "memory" / f"chat_{user_id}.json"
    history = []
    if history_file.exists():
        try: history = json.loads(history_file.read_text())[-15:]
        except: pass
    
    history.append({"role": "user", "content": user_msg})
    
    try:
        resp = await client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
            max_tokens=2048,
            temperature=0.7
        )
        reply = resp.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        history_file.write_text(json.dumps(history[-30:], ensure_ascii=False, indent=2))
        return reply
    except Exception as e:
        return f"❌ خطا: {str(e)[:150]}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🦞 سلام عباس جان! من جلیل هستم، دستیار تو با هوش مصنوعی رایگان Google Gemini.\n\nهر کاری داری بگو.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    if not msg: return
    
    user = update.effective_user
    print(f"📩 {user.first_name}: {msg[:80]}")
    
    await update.message.chat.send_action(action="typing")
    
    try:
        reply = await chat_with_ai(msg, str(user.id))
    except Exception as e:
        reply = f"❌ خطا: {str(e)[:200]}"
    
    if len(reply) > 4000:
        for i in range(0, len(reply), 4000):
            await update.message.reply_text(reply[i:i+4000])
    else:
        await update.message.reply_text(reply)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦞 **جلیل — دستیار هوش مصنوعی عباس**\n\n"
        "/start — شروع\n"
        "/remember <متن> — ذخیره یادداشت\n"
        "/help — راهنما\n\n"
        "💡 با Google Gemini — کاملاً رایگان",
        parse_mode="Markdown"
    )

async def remember(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else ""
    if text:
        today = datetime.now().strftime("%Y-%m-%d")
        mem = WS / "memory" / f"{today}.md"
        with open(mem, "a") as f: f.write(f"- {text}\n")
        await update.message.reply_text("✅ ذخیره شد.")
    else:
        await update.message.reply_text("📝 /remember <متن>")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"❌ {context.error}")

if __name__ == "__main__":
    print(f"🦞 Starting @jaliabibot with Gemini...")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Model: gemini-2.0-flash (FREE)")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("remember", remember))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    print("✅ Running! Telegram → @jaliabibot")
    app.run_polling(drop_pending_updates=True)
