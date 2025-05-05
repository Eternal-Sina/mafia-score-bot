import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio

# لیست نام‌های کاربری مجاز برای ثبت مدال (username های تلگرام)
AUTHORIZED_USERNAMES = ["sinamsv", "admin2", "admin3", "admin4", "admin5"]

DATA_FILE = "medals.json"

def load_data():
    """ داده‌ها را از فایل بارگذاری می‌کند. """
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    """ داده‌ها را در فایل ذخیره می‌کند. """
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ دستور start برای خوش‌آمدگویی. """
    await update.message.reply_text("سلام! برای دیدن رده‌بندی از دستور /leaderboard استفاده کن.")

async def register_medals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ ثبت مدال‌ها برای افراد مجاز """
    username = update.effective_user.username
    if username not in AUTHORIZED_USERNAMES:
        await update.message.reply_text("❌ شما اجازه ثبت مدال ندارید.")
        return

    if len(context.args) != 3:
        await update.message.reply_text("❗ فرمت درست: /register اسم1 اسم2 اسم3")
        return

    gold, silver, bronze = context.args

    # بارگذاری داده‌ها
    data = load_data()
    for name, medal in zip([gold, silver, bronze], ["gold", "silver", "bronze"]):
        if name not in data:
            data[name] = {"gold": 0, "silver": 0, "bronze": 0}
        data[name][medal] += 1

    # ذخیره داده‌ها
    save_data(data)
    await update.message.reply_text("✅ مدال‌ها ثبت شدند!")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ نمایش رده‌بندی افراد """
    data = load_data()
    if not data:
        await update.message.reply_text("هیچ مدالی ثبت نشده.")
        return

    # محاسبه امتیاز کل
    scores = []
    for name, medals in data.items():
        score = medals["gold"] * 3 + medals["silver"] * 2 + medals["bronze"]
        scores.append((score, medals["gold"], medals["silver"], medals["bronze"], name))

    # مرتب‌سازی بر اساس امتیاز و مدال‌ها
    scores.sort(reverse=True)

    result = "🏆 رده‌بندی:\n"
    last_score = None
    rank = 0
    real_rank = 0

    for i, (score, g, s, b, name) in enumerate(scores):
        real_rank += 1
        if (score, g, s, b) != last_score:
            rank = real_rank
            last_score = (score, g, s, b)

        result += f"{rank}. {name}: 🥇({g}) 🥈({s}) 🥉({b})\n"

    await update.message.reply_text(result)

async def main():
    """ راه‌اندازی و شروع ربات """
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("❌ BOT_TOKEN تعریف نشده!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register_medals))
    app.add_handler(CommandHandler("leaderboard", leaderboard))

    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=os.environ.get("WEBHOOK_URL")
    )

if __name__ == "__main__":
    asyncio.run(main())
