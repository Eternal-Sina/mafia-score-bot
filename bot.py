import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

DATA_FILE = "medals.json"

# بارگذاری داده‌ها از فایل
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# ذخیره داده‌ها در فایل
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# داده‌های اولیه
data = load_data()

# دستور برای ثبت نتایج
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

# دستور برای نمایش رده‌بندی
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # مرتب‌سازی لیست بر اساس مدال‌های طلا، نقره، و برنز
    sorted_leaderboard = sorted(data.items(), key=lambda item: (
        -item[1]["gold"],   # اول طلا (نزولی)
        -item[1]["silver"], # بعد نقره (نزولی)
        -item[1]["bronze"]  # بعد برنز (نزولی)
    ))

    # تعیین رتبه‌ها و شناسایی افراد هم‌رتبه
    ranks = []
    last_rank = 1
    for i, (name, medals) in enumerate(sorted_leaderboard):
        if i > 0:
            prev_name, prev_medals = sorted_leaderboard[i - 1]
            # اگر نفر قبلی هم مدال‌های مشابه داشته باشه، هم‌رتبه خواهند بود
            if medals == prev_medals:
                ranks[-1][0].append(name)  # اضافه کردن به رتبه قبلی
                continue
            else:
                last_rank = i + 1  # تنظیم رتبه جدید

        ranks.append(([name], last_rank, medals))

    # ساختن پیام برای رده‌بندی
    lines = []
    for rank in ranks:
        names_in_rank = ', '.join(rank[0])
        medals = rank[2]
        line = f"{rank[1]}. {names_in_rank}: 🥇({medals['gold']}) 🥈({medals['silver']}) 🥉({medals['bronze']})"
        lines.append(line)

    await update.message.reply_text("\n".join(lines))

# اجرای ربات
TOKEN = os.getenv("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

app = ApplicationBuilder().token(TOKEN).build()

# ثبت دستورات
app.add_handler(CommandHandler("register", register))
app.add_handler(CommandHandler("leaderboard", leaderboard))

# راه‌اندازی Webhook
app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ["PORT"]),
    webhook_url=f"{RENDER_EXTERNAL_URL}/"
)
