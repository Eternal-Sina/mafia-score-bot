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

    # محاسبه امتیاز و ذخیره داده‌ها
    for name, medals in data.items():
        g = medals["gold"]
        s = medals["silver"]
        b = medals["bronze"]
        score = g + s // 2 + b // 4  # تبدیل نقره و برنز به طلای فرضی
        score_map[score].append((name, g, s, b))  # ذخیره نام و تعداد مدال‌ها

    # مرتب‌سازی بر اساس امتیاز، سپس طلا، نقره، برنز
    sorted_scores = sorted(score_map.keys(), reverse=True)

    output = []
    rank = 1
    for score in sorted_scores:
        names_and_medals = score_map[score]
        
        # مرتب‌سازی افراد با امتیاز مشابه بر اساس تعداد مدال‌های طلا، نقره و برنز
        names_and_medals.sort(key=lambda x: (-x[1], -x[2], -x[3]))  # اول طلا، سپس نقره و بعد برنز

        output.append(f" رتبه {rank}:")
        for name, g, s, b in names_and_medals:
            output.append(f"{name}: 🥇({g}) 🥈({s}) 🥉({b})")
        
        # تعداد نفرات هم رتبه را از rank بعدی کم می‌کنیم
        rank += len(names_and_medals)

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
