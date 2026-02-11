from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Токен вашего бота
TOKEN = "8587201858:AAEnYwf8wO7N3DqvxMsmwnLXfD3jp-CjijY"

# Простое хранилище привычек для каждого пользователя
user_habits = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_habits:
        # Создаём словарь привычек для нового пользователя
        user_habits[user_id] = {
            "pushups": 0,
            "new_habit_1": 0,
            "new_habit_2": 0,
            # Добавьте свои новые привычки здесь
        }
    await update.message.reply_text(
        "Привет! Я буду отслеживать твои привычки.\n"
        "Отправь мне сообщение с названием привычки и количеством, например:\n"
        "`pushups 20`", parse_mode="Markdown"
    )

# Обработка сообщений с привычками
async def handle_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_habits:
        # Если пользователь не запускал /start
        await update.message.reply_text("Сначала введи /start")
        return

    try:
        # Ожидаем формат: habit_name number
        text = update.message.text.strip().split()
        habit_name = text[0].lower()
        count = int(text[1])

        if habit_name in user_habits[user_id]:
            user_habits[user_id][habit_name] += count
            await update.message.reply_text(
                f"{habit_name} обновлено! Сейчас у тебя: {user_habits[user_id][habit_name]}"
            )
        else:
            await update.message.reply_text(
                f"Привычка '{habit_name}' не найдена. Используй: {', '.join(user_habits[user_id].keys())}"
            )
    except (IndexError, ValueError):
        await update.message.reply_text(
            "Неправильный формат. Используй: habit_name число, например:\npushups 20"
        )

# Команда /status — показать текущие привычки
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_habits:
        await update.message.reply_text("Сначала введи /start")
        return

    habits = user_habits[user_id]
    status_text = "\n".join(f"{k}: {v}" for k, v in habits.items())
    await update.message.reply_text(f"Твои привычки:\n{status_text}")

# Основная часть бота
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
