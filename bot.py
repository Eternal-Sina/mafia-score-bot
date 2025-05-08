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
    score_map = defaultdict(list)

    for name, medals in data.items():
        g = medals["gold"]
        s = medals["silver"]
        b = medals["bronze"]
        score = g + s // 2 + b // 4  # تبدیل نقره و برنز به طلای فرضی
        score_map[score].append(name)

    sorted_scores = sorted(score_map.keys(), reverse=True)

    output = []
    rank = 1
    for score in sorted_scores:
        names = score_map[score]
        output.append(f"🏅 رتبه {rank}:")
        for na
