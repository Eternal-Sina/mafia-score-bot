import os
import json
from collections import defaultdict
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

DATA_FILE = "medals.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text("فرمت: /register name1 name2 name3")
        return

    names = context.args
    medals = ["gold", "silver", "bronze"]

    for i in range(3):
        name = names[i]
        if name not in data:
            data[name] = {"gold": 0, "silver": 0, "bronze": 0}
        data[name][medals[i]] += 1

    save_data(data)
    await update.message.reply_text("مدال‌ها ثبت شدند.")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = []
    for name, medals in data.items():
        line = f"{name}: 🥇({medals['gold']}) 🥈({medals['silver']}) 🥉({medals['bronze']})"
        lines.append(line)
    await update.message.reply_text("\n".join(lines))

# اجرای مستقیم
TOKEN = os.getenv("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("register", register))
app.add_handler(CommandHandler("leaderboard", leaderboard))

app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 8443)),
    webhook_url=f"{RENDER_EXTERNAL_URL}/"
)
