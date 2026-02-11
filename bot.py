from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, JobQueue
import datetime
import json
import os

TOKEN = "8587201858:AAEnYwf8wO7N3DqvxMsmwnLXfD3jp-CjijY"

# Список привычек
habits = ["Контрастный душ 🚿", "Чтение 📚", "Прием витаминов 💊"]

# Файл для хранения прогресса
DATA_FILE = "habit_data.json"

# Загрузка данных или создание пустого словаря
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        habit_data = json.load(f)
else:
    habit_data = {}  # {user_id: {habit: count}}

# Сохраняем прогресс
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(habit_data, f, ensure_ascii=False, indent=2)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я буду помогать тебе следить за твоими привычками.\n"
        "Команды:\n"
        "/habits — показать привычки и отметить выполнение"
    )

# Отправка привычек с кнопками
async def show_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id not in habit_data:
        habit_data[user_id] = {h: 0 for h in habits}

    keyboard = [
        [InlineKeyboardButton(f"✔ {h}", callback_data=h)] for h in habits
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Отметьте, что вы сделали сегодня:", reply_markup=reply_markup)

# Обработка нажатий на кнопки
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    habit = query.data

    # Увеличиваем счетчик на 1
    if user_id not in habit_data:
        habit_data[user_id] = {h: 0 for h in habits}

    habit_data[user_id][habit] += 1
    save_data()
    await query.edit_message_text(
        f"Отмечено ✅\n\n{habit} выполнено {habit_data[user_id][habit]} дней"
    )

# Напоминание
async def remind(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in habit_data.keys():
        keyboard = [
            [InlineKeyboardButton(f"✔ {h}", callback_data=h)] for h in habits
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await context.bot.send_message(chat_id=int(chat_id), text="Время сделать привычки!", reply_markup=reply_markup)
        except Exception as e:
            print(f"Не удалось отправить сообщение {chat_id}: {e}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("habits", show_habits))
    app.add_handler(CallbackQueryHandler(button))

    # Настройка ежедневных напоминаний 9:00 и 20:00
    job_queue: JobQueue = app.job_queue
    job_queue.run_daily(remind, time=datetime.time(hour=9, minute=0))
    job_queue.run_daily(remind, time=datetime.time(hour=20, minute=0))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
