import os
import json
import aiohttp
from collections import defaultdict
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# تنظیمات GitHub
GITHUB_REPO = os.getenv("GITHUB_REPO")  # مثلا username/repo
GITHUB_FILE = "medals.json"
GITHUB_BRANCH = "main"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

async def load_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(GITHUB_API_URL, headers=headers) as res:
            if res.status == 200:
                response = await res.json()
                content = response["content"]
                import base64
                decoded = base64.b64decode(content).decode()
                return json.loads(decoded), response["sha"]
            return {}, None

async def save_data(data, sha=None):
    async with aiohttp.ClientSession() as session:
        payload = {
            "message": "Update medals",
            "content": json.dumps(data, ensure_ascii=False).encode("utf-8").decode("utf-8"),
            "branch": GITHUB_BRANCH
        }
        if sha:
            payload["sha"] = sha

        import base64
        payload["content"] = base64.b64encode(payload["content"].encode()).decode()

        async with session.put(GITHUB_API_URL, headers=headers, json=payload) as res:
            return res.status == 200 or res.status == 201

data = {}
data_sha = None

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global data, data_sha
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

    await save_data(data, data_sha)
    await update.message.reply_text("مدال‌ها ثبت شدند.")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global data, data_sha
    data, data_sha = await load_data()

    # ساخت لیست برای رتبه‌بندی دقیق
    participants = []
    for name, m in data.items():
        bonus_gold = (m["silver"] // 2) + (m["bronze"] // 4)
        participants.append((name, m["gold"] + bonus_gold, m["silver"], m["bronze"], m))

    # مرتب‌سازی بر اساس: طلا فرضی + واقعی > نقره > برنز
    participants.sort(key=lambda x: (-x[1], -x[2], -x[3]))

    output = []
    rank = 1
    prev_values = None
    count_same = 0

    for i, (name, gold_total, silver, bronze, medals) in enumerate(participants):
        values = (gold_total, silver, bronze)
        if values != prev_values:
            rank += count_same
            count_same = 1
            output.append(f"رتبه {rank}:")
        else:
            count_same += 1
        output.append(f"{name}: 🥇({medals['gold']}) 🥈({medals['silver']}) 🥉({medals['bronze']})")
        prev_values = values

    await update.message.reply_text("\n\n".join(output))

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
