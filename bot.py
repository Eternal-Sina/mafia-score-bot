import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

# توکن ربات شما
BOT_TOKEN = os.getenv('BOT_TOKEN')

# آدرس URL سرور شما (برای Webhook)
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # به این آدرس اشاره کنید، مثلاً https://yourdomain.com/webhook

# لیست کاربران مجاز برای ثبت مدال
AUTHORIZED_USERNAMES = ["sinamsv", "admin1", "admin2", "admin3", "admin4"]

# تنظیمات logging برای دیباگ کردن
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# داده‌های رده بندی مدال‌ها
leaderboard = {}

# فرمان /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    username = user.username

    if username in AUTHORIZED_USERNAMES:
        await update.message.reply_text("سلام! شما می‌توانید مدال‌ها را ثبت کنید.")
    else:
        await update.message.reply_text("سلام! شما اجازه ثبت مدال ندارید.")

# فرمان /leaderboard
async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # مرتب کردن رده بندی بر اساس مدال‌های طلا، نقره، برنز
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda item: (
        item[1].get('gold', 0), item[1].get('silver', 0), item[1].get('bronze', 0)), reverse=True)
    
    response = "رده بندی مدال‌ها:\n"
    for idx, (user, medals) in enumerate(sorted_leaderboard, start=1):
        gold = medals.get('gold', 0)
        silver = medals.get('silver', 0)
        bronze = medals.get('bronze', 0)
        response += f"{idx}. {user} - 🥇({gold}) 🥈({silver}) 🥉({bronze})\n"
    
    await update.message.reply_text(response)

# فرمان برای ثبت مدال
async def add_medal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    username = user.username

    if username not in AUTHORIZED_USERNAMES:
        await update.message.reply_text("شما اجازه ثبت مدال ندارید.")
        return

    # بررسی تعداد آرگومان‌ها
    if len(context.args) < 3:
        await update.message.reply_text("لطفا تعداد مدال‌ها را وارد کنید. به صورت: /addmedal <username> <gold> <silver> <bronze>")
        return

    target_user = context.args[0]
    gold = int(context.args[1])
    silver = int(context.args[2])
    bronze = int(context.args[3])

    # اضافه کردن یا بروزرسانی مدال‌ها
    if target_user not in leaderboard:
        leaderboard[target_user] = {'gold': 0, 'silver': 0, 'bronze': 0}

    leaderboard[target_user]['gold'] += gold
    leaderboard[target_user]['silver'] += silver
    leaderboard[target_user]['bronze'] += bronze

    await update.message.reply_text(f"مدال‌ها برای {target_user} ثبت شد.")

# تنظیمات اپلیکیشن
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # تعریف فرمان‌ها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))
    application.add_handler(CommandHandler("addmedal", add_medal))

    # راه‌اندازی Webhook
    await application.run_webhook(
        listen="0.0.0.0",  # IP که به درخواست‌ها گوش می‌دهد
        port=int(os.getenv('PORT', 5000)),  # پورت برای پذیرش درخواست‌ها (مثلاً 5000)
        url_path='webhook',  # URL برای Webhook (این باید با Telegram همخوانی داشته باشد)
        webhook_url=WEBHOOK_URL,  # آدرس Webhook شما که به Telegram اطلاع داده می‌شود
        secret_token=None,  # اگر نیاز به توکن امنیتی دارید، اینجا قرار دهید
    )

# اجرای اپلیکیشن بدون استفاده از asyncio.run
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
