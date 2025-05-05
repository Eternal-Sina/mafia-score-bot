from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json
import os

DATA_FILE = 'scores.json'

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def add_medal(data, username, medal_type):
    if username not in data:
        data[username] = {'gold': 0, 'silver': 0, 'bronze': 0}
    data[username][medal_type] += 1

async def add_winners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text("فرمت درست: /add username1 username2 username3")
        return

    usernames = context.args
    data = load_data()
    medals = ['gold', 'silver', 'bronze']

    for username, medal in zip(usernames, medals):
        add_medal(data, username, medal)

    save_data(data)
    await update.message.reply_text("مدال‌ها ثبت شدند.")

async def show_scores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("هنوز هیچ مدالی ثبت نشده.")
        return

    result = "🏆 رتبه‌بندی بازیکنان:\n"
    sorted_data = sorted(data.items(), key=lambda x: (x[1]['gold'], x[1]['silver'], x[1]['bronze']), reverse=True)

    for username, scores in sorted_data:
        result += f"{username} — 🥇({scores['gold']}) 🥈({scores['silver']}) 🥉({scores['bronze']})\n"

    await update.message.reply_text(result)

if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    app.add_handler(CommandHandler("add", add_winners))
    app.add_handler(CommandHandler("scores", show_scores))

    print("ربات در حال اجراست...")
    app.run_polling()
