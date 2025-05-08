import os
import json
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
    # آماده‌سازی لیست رتبه‌بندی بر اساس طلای واقعی + فرضی، بعد نقره، بعد برنز
    players = []
    for name, medals in data.items():
        g = medals["gold"]
        s = medals["silver"]
        b = medals["bronze"]

        # فقط هر ۲ نقره = ۱ طلای فرضی، بقیه نادیده گرفته میشه
        fake_golds = (s // 2) + (b // 4)
        real_plus_fake_gold = g + fake_golds
        players.append((name, real_plus_fake_gold, s, b, g, s, b))  # tuple برای مرتب‌سازی

    # مرتب‌سازی: طلا (واقعی + فرضی) → نقره → برنز
    players.sort(key=lambda x: (-x[1], -x[2], -x[3]))

    output = []
    current_rank = 1
    prev = None
    same_rank_count = 0

    for idx, player in enumerate(players):
        name, _, _, _, g, s, b = player
        key = (player[1], player[2], player[3])  # برای مقایسه رتبه

        if key != prev:
            if idx != 0:
                output.append("")  # فاصله بین رتبه‌ها
            output.append(f"رتبه {current_rank}:")
            same_rank_count = 1
        else:
            same_rank_count += 1

        output.append(f"{name}: 🥇({g}) 🥈({s}) 🥉({b})")
        prev = key
        if idx + 1 < len(players):
            next_player = players[idx + 1]
            next_key = (next_player[1], next_player[2], next_player[3])
            if next_key != key:
                current_rank += same_rank_count

    await update.message.reply_text("\n".join(output))

# اجرای مستقیم در Render با Webhook
TOKEN = os.getenv("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("register", register))
app.add_handler(CommandHandler("leaderboard", leaderboard))

app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ["PORT"]),
    webhook_url=f"{RENDER_EXTERNAL_URL}/"
)
