from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import datetime
import json
import os

TOKEN = "8587201858:AAEnYwf8wO7N3DqvxMsmwnLXfD3jp-CjijY"

GOAL_PUSHUPS = 100  # цель отжиманий
HABITS = ["Контрастный душ", "Чтение", "Витамины", "Отжимания"]
DATA_FILE = "data.json"

# ----------------- Работа с файлом -----------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def get_today():
    return str(datetime.date.today())

# ----------------- Подсчет прогресса -----------------
def calculate_streak(data, habit):
    streak = 0
    today = datetime.date.today()

    for i in range(1, 365):
        day = str(today - datetime.timedelta(days=i))
        if day in data and habit in data[day] and data[day][habit]:
            streak += 1
        else:
            break
    return streak

# ----------------- Обработчик сообщений -----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    data = load_data()
    today = get_today()

    if today not in data:
        data[today] = {}

    # Если пользователь вводит число → считаем как отжимания
    if text.isdigit():
        pushups_done = int(text)
        data[today]["Отжимания"] = data[today].get("Отжимания", 0) + pushups_done
        save_data(data)
        done = data[today]["Отжимания"]
        left = max(0, GOAL_PUSHUPS - done)
        if done >= GOAL_PUSHUPS:
            await update.message.reply_text(f"✅ Дневная цель отжиманий выполнена!\nСделано: {done}")
        else:
            await update.message.reply_text(f"Сделано сегодня: {done}\nОсталось до цели: {left}")
        return

    # Если сообщение совпадает с привычкой
    if text in HABITS:
        data[today][text] = True
        save_data(data)
        streak = calculate_streak(data, text)
        await update.message.reply_text(f"✅ Привычка '{text}' отмечена!\nСерий подряд: {streak} дней")
    else:
        await update.message.reply_text("Просто отправь название привычки или число отжиманий 🙂")

# ----------------- Команды -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    habits_text = "\n".join(HABITS)
    await update.message.reply_text(
        f"Привет! Я буду помогать отслеживать твои привычки.\n"
        f"Вот что можно отмечать:\n{habits_text}\n\n"
        f"Для отжиманий просто пришли число, сколько сделал сегодня."
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    today = get_today()
    message = "Сегодня выполнено:\n"
    for habit in HABITS:
        if habit == "Отжимания":
            done = data.get(today, {}).get(habit, 0)
            message += f"{habit}: {done}/{GOAL_PUSHUPS}\n"
        else:
            done = data.get(today, {}).get(habit, False)
            message += f"{habit}: {'✅' if done else '❌'}\n"
    await update.message.reply_text(message)

# ----------------- Основная функция -----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
