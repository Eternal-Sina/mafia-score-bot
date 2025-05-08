import os
import json
from collections import defaultdict
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

# دستور ثبت مدال‌ها
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

# دستور نمایش لیدربورد
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score_map = defaultdict(list)

    # محاسبه امتیاز
    for name, medals in data.items():
        g = medals["gold"]
        s = medals["silver"]
        b = medals["bronze"]
        # به ازای هر 2 مدال نقره یک طلا و به ازای هر 4 مدال برنز یک طلا فرض می‌کنیم
        score = g + s // 2 + b // 4
        score_map[score].append(name)

    # مرتب‌سازی بر اساس امتیاز
    sorted_scores = sorted(score_map.keys(), reverse=True)

    # نمایش رتبه‌ها
    output = []
    rank = 1
    for score in sorted_scores:
        names = score_map[score]
        output.append(f" رتبه {rank}:")
        for name in names:
            m = data[name]
            output.append(f"{name}: 🥇({m['gold']}) 🥈({m['silver']}) 🥉({m['bronze']})")
        rank += len(names)

    await update.message.reply_text("\n".join(output))

# تنظیمات Bot
TOKEN = os.getenv("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("register", register))
app.add_handler(CommandHandler("leaderboard", leaderboard))

# اجرای Webhook
app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ["PORT"]),
    webhook_url=f"{RENDER_EXTERNAL_URL}/"
)
