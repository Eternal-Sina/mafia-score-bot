import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# تنظیمات پایگاه داده
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()

# تعریف مدل بازیکن
class Player(Base):
    __tablename__ = "players"
    name = Column(String, primary_key=True)
    gold = Column(Integer, default=0)
    silver = Column(Integer, default=0)
    bronze = Column(Integer, default=0)

# ایجاد جدول‌ها در پایگاه داده
Base.metadata.create_all(engine)

# تنظیم جلسه برای تعامل با پایگاه داده
Session = sessionmaker(bind=engine)

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # بررسی دسترسی ادمین
    ADMIN_IDS = [66625527]  # آیدی عددی شما
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(f"فقط ادمین‌ها می‌تونن مدال ثبت کنن! آیدی شما: {user_id}")
        return

    if len(context.args) != 3:
        await update.message.reply_text("فرمت: /register name1 name2 name3")
        return

    # ذخیره موقت اسامی واردشده
    context.user_data["pending_names"] = context.args
    context.user_data["confirmed_names"] = []
    context.user_data["current_index"] = 0

    # شروع فرآیند تأیید اسامی
    await check_name(update, context)

async def check_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    try:
        if "current_index" not in context.user_data or "pending_names" not in context.user_data:
            await update.message.reply_text("خطا: داده‌های موقت از دست رفته. لطفاً دوباره /register رو اجرا کنید.")
            return

        current_index = context.user_data["current_index"]
        pending_names = context.user_data["pending_names"]
        if current_index >= len(pending_names):
            # همه اسامی تأیید شدن، ثبت مدال‌ها
            await finalize_registration(update, context)
            return

        name = pending_names[current_index].strip()
        # جستجوی اسامی مشابه
        all_players = session.query(Player).all()
        similar_names = [
            player.name for player in all_players
            if name.lower() in player.name.lower() or player.name.lower() in name.lower()
        ]

        if similar_names:
            # نمایش پیشنهادات با دکمه‌های اینلاین
            keyboard = [
                [InlineKeyboardButton(s_name, callback_data=f"select_name:{s_name}")]
                for s_name in similar_names
            ]
            keyboard.append([InlineKeyboardButton(f"استفاده از '{name}' به‌عنوان اسم جدید", callback_data=f"new_name:{name}")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"اسم '{name}' مشابه این اسامی موجوده. لطفاً انتخاب کنید یا اسم جدید رو تأیید کنید:",
                reply_markup=reply_markup
            )
        else:
            # هیچ مشابهتی پیدا نشد، مستقیم تأیید می‌شه
            context.user_data["confirmed_names"].append(name)
            context.user_data["current_index"] += 1
            await check_name(update, context)
    finally:
        session.close()

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # چک کردن وجود داده‌های موقت
    if "confirmed_names" not in context.user_data or "current_index" not in context.user_data:
        await query.message.reply_text("خطا: جلسه منقضی شده. لطفاً دوباره /register رو اجرا کنید.")
        return

    data = query.data
    if data.startswith("select_name:") or data.startswith("new_name:"):
        selected_name = data.split(":", 1)[1]
        context.user_data["confirmed_names"].append(selected_name)
        context.user_data["current_index"] += 1
        await check_name(query, context)

async def finalize_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "confirmed_names" not in context.user_data or len(context.user_data["confirmed_names"]) != 3:
        await update.message.reply_text("خطا: اسامی تأییدشده کامل نیستن. لطفاً دوباره /register رو اجرا کنید.")
        return

    confirmed_names = context.user_data["confirmed_names"]
    medals = ["gold", "silver", "bronze"]

    session = Session()
    try:
        for i in range(3):
            name = confirmed_names[i]
            player = session.query(Player).filter_by(name=name).first()
            if not player:
                player = Player(name=name, gold=0, silver=0, bronze=0)
                session.add(player)
            setattr(player, medals[i], getattr(player, medals[i]) + 1)
        
        session.commit()
        await update.message.reply_text("مدال‌ها با موفقیت ثبت شدند!")
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f"خطا در ثبت مدال‌ها: {str(e)}")
    finally:
        session.close()
        # پاک کردن داده‌های موقت
        context.user_data.clear()

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    try:
        players = session.query(Player).all()
        player_list = []
        for player in players:
            g = player.gold
            s = player.silver
            b = player.bronze
            fake_golds = (s // 2) + (b // 4)
            real_plus_fake_gold = g + fake_golds
            player_list.append((player.name, real_plus_fake_gold, s, b, g, s, b))

        player_list.sort(key=lambda x: (-x[1], -x[2], -x[3]))

        output = []
        current_rank = 1
        prev = None
        same_rank_count = 0

        for idx, player in enumerate(player_list):
            name, _, _, _, g, s, b = player
            key = (player[1], player[2], player[3])

            if key != prev:
                if idx != 0:
                    output.append("")
                output.append(f"🏅 رتبه {current_rank}:")
                same_rank_count = 1
            else:
                same_rank_count += 1

            output.append(f"{name}: 🥇({g}) 🥈({s}) 🥉({b})")
            prev = key
            if idx + 1 < len(player_list):
                next_player = player_list[idx + 1]
                next_key = (next_player[1], next_player[2], next_player[3])
                if next_key != key:
                    current_rank += same_rank_count

        await update.message.reply_text("\n".join(output) or "هیچ بازیکنی ثبت نشده است.")
    finally:
        session.close()

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # لیست آیدی‌های عددی ادمین‌ها
    ADMIN_IDS = [66625527]  # آیدی عددی شما
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(f"خطا: شما (آیدی: {user_id}) ادمین نیستید! فقط ادمین‌ها می‌تونن لیدربورد رو ریست کنن.")
        return

    session = Session()
    try:
        session.query(Player).delete()
        session.commit()
        await update.message.reply_text("لیدربورد با موفقیت ریست شد! همه نام‌ها و امتیازات پاک شدند.")
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f"خطا در ریست لیدربورد: {str(e)}")
    finally:
        session.close()

# اجرای مستقیم در Render با Webhook
TOKEN = os.getenv("BOT_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("register", register))
app.add_handler(CommandHandler("leaderboard", leaderboard))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(CallbackQueryHandler(button_callback))

# تنظیم منوی دستورات قبل از راه‌اندازی وب‌هوک
commands = [
    BotCommand("register", "ثبت مدال برای ۳ بازیکن (فقط ادمین‌ها)"),
    BotCommand("leaderboard", "نمایش لیدربورد بازیکنان"),
    BotCommand("reset", "ریست کامل لیدربورد (فقط ادمین‌ها)")
]

# راه‌اندازی ربات و تنظیم دستورات به‌صورت ناهمگام
import asyncio
loop = asyncio.get_event_loop()
loop.run_until_complete(app.initialize())
loop.run_until_complete(app.bot.set_my_commands(commands=commands))

app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 8443)),
    webhook_url=f"{RENDER_EXTERNAL_URL}/"
)
