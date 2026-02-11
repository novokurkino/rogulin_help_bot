from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import datetime

# Твой токен от BotFather
TOKEN = "8587201858:AAEnYwf8wO7N3DqvxMsmwnLXfD3jp-CjijY"

# Список привычек
habits = [
    "Контрастный душ 🚿",
    "Чтение 📚",
    "Прием витаминов 💊"
]

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я буду помогать тебе следить за твоими привычками.\n"
        "Команды:\n"
        "/habits — показать привычки на сегодня"
    )

# Команда /habits
async def show_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.date.today().strftime("%d.%m.%Y")
    text = f"Привычки на {today}:\n" + "\n".join(f"- {h}" for h in habits)
    await update.message.reply_text(text)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("habits", show_habits))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
