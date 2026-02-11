from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8587201858:AAEnYwf8wO7N3DqvxMsmwnLXfD3jp-CjijY"

# Простое хранилище привычек для пользователей
user_habits = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_habits:
        user_habits[user_id] = {
            "pushups": 0,
            "habit1": 0,
            "habit2": 0,
        }
    await update.message.reply_text(
        "Привет! Отслеживаю твои привычки.\n"
        "Отправь сообщение в формате: habit_name число\n"
        "Например: pushups 20"
    )

# Команда /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_habits:
        await update.message.reply_text("Сначала введи /start")
        return
    habits = user_habits[user_id]
    text = "\n".join(f"{k}: {v}" for k, v in habits.items())
    await update.message.reply_text(f"Твои привычки:\n{text}")

# Обработка сообщений с привычками
async def handle_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_habits:
        await update.message.reply_text("Сначала введи /start")
        return

    try:
        habit_name, count_str = update.message.text.strip().split()
        count = int(count_str)
        habit_name = habit_name.lower()

        if habit_name in user_habits[user_id]:
            user_habits[user_id][habit_name] += count
            await update.message.reply_text(
                f"{habit_name} обновлено! Сейчас: {user_habits[user_id][habit_name]}"
            )
        else:
            await update.message.reply_text(
                f"Привычка '{habit_name}' не найдена. Доступные: {', '.join(user_habits[user_id].keys())}"
            )
    except Exception:
        await update.message.reply_text(
            "Ошибка формата. Используй: habit_name число, например: pushups 20"
        )

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем команды и обработчик сообщений
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_habit))

    # Запуск бота
    app.run_polling()

if __name__ == "__main__":
    main()
