import os
import json
from collections import defaultdict
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# مسیر فایل داده‌ها
DATA_FILE = "medals.json"

# تابع برای بارگذاری داده‌ها از فایل
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            print(f"Data loaded: {data}")  # نمایش داده‌های بارگذاری شده
            return data
    except FileNotFoundError:
        return {}

# تابع برای ذخیره داده‌ها به فایل
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# بارگذاری داده‌ها از فایل
data = load_data()

# تابع ثبت مدال‌ها
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

    # ذخیره داده‌ها به فایل
    save_data(data)
    await update.message.reply_text("مدال‌ها ثبت شدند.")

# تابع برای نمایش لیدربورد
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score_map = defaultdict(list)

    # پردازش داده‌ها و محاسبه امتیاز
    for name, medals in data.items():
        g = medals["gold"]
        s = medals["silver"]
        b = medals["bronze"]
        
        # محاسبه امتیاز با تبدیل نقره و برنز به طلای فرضی
        score = g + s // 2 + b // 4  # تبدیل نقره و برنز به طلای فرضی
        score_map[score].append(name)

    # مرتب کردن امتیازات
    sorted_scores = sorted(score_map.keys(), reverse=True)

    output = []
    rank = 1
    for score in sorted_scores:
        names = score_map[score]
        output.append(f"🏅 رتبه {rank}:")
        for name in names:
            m = data[name]
            output.append(f"{name}: 🥇({m['gold']}) 🥈({m['silver']}) 🥉({m['bronze']})")
        rank += len(names)

    # چاپ اطلاعات در کنسول برای دیباگ
    print("\n\n".join(output))  # اینجا داده‌ها را در کنسول نمایش می‌دهیم

    # ارسال به تلگرام
    await update.message.reply_text("\n\n".join(output))

# تنظیمات وبهوک و دپلوی در Render
TOKEN = os.getenv("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

# ساخت اپلیکیشن تلگرام
app = ApplicationBuilder().token(TOKEN).build()

# اضافه کردن هندلرهای دستور
app.add_handler(CommandHandler("register", register))
app.add_handler(CommandHandler("leaderboard", leaderboard))

# اجرای وب
