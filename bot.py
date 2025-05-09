import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

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
    if len(context.args) != 3:
        await update.message.reply_text("فرمت: /register name1 name2 name3")
        return

    names = context.args
    medals = ["gold", "silver", "bronze"]

    # ایجاد جلسه برای تعامل با پایگاه داده
    session = Session()
    try:
        for i in range(3):
            name = names[i]
            # بررسی وجود بازیکن
            player = session.query(Player).filter_by(name=name).first()
            if not player:
                # ایجاد بازیکن جدید
                player = Player(name=name, gold=0, silver=0, bronze=0)
                session.add(player)
            # افزایش تعداد مدال
            setattr(player, medals[i], getattr(player, medals[i]) + 1)
        
        session.commit()
        await update.message.reply_text("مدال‌ها ثبت شدند.")
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f"خطا در ثبت مدال‌ها: {str(e)}")
    finally:
        session.close()

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    try:
        # دریافت همه بازیکنان
        players = session.query(Player).all()
        player_list = []
        for player in players:
            g = player.gold
            s = player.silver
            b = player.bronze
            # محاسبه طلای فرضی
            fake_golds = (s // 2) + (b // 4)
            real_plus_fake_gold = g + fake_golds
            player_list.append((player.name, real_plus_fake_gold, s, b, g, s, b))

        # مرتب‌سازی بر اساس طلا (واقعی + فرضی) → نقره → برنز
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
                output.append(f"رتبه {current_rank}:")
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
