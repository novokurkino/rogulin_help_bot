from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import datetime
import json
import os
import sys

# Получаем токен из переменных окружения
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ TOKEN не задан! Проверь переменные окружения на Railway.")
    sys.exit(1)

DATA_FILE = "data.json"
DEFAULT_GOAL = 100  # цель по отжиманиям


# Загрузка данных
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


# Сохранение данных
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# Сегодняшняя дата
def get_today():
    return str(datetime.date.today())


# Получение или создание данных пользователя
def get_user(data, user_id):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "goal": DEFAULT_GOAL,
            "pushups": {},
            "habits": {}
        }
    return data[uid]


# Обработка отжиманий
async def handle_pushups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        return

    user_id = update.effective_user.id
    data = load_data()
    user = get_user(data, user_id)

    today = get_today()
    user["pushups"].setdefault(today, 0)
    user["pushups"][today] += int(text)

    save_data(data)

    done = user["pushups"][today]
    left = user["goal"] - done

    if done >= user["goal"]:
        await update.message.reply_text(f"🔥 Цель по отжиманиям выполнена: {done}")
    else:
        await update.message.reply_text(f"Отжимания сегодня: {done}\nОсталось: {left}")


# Добавление привычки
async def add_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    user = get_user(data, user_id)

    try:
        name = context.args[0]
        time_str = context.args[1]
    except IndexError:
        await update.message.reply_text("Пример: /add Душ 08:30")
        return

    user["habits"][name] = {"time": time_str, "days": {}}
    save_data(data)

    await update.message.reply_text(f"Привычка '{name}' добавлена на {time_str}")


# Отметка выполнения привычки
async def done_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    user = get_user(data, user_id)

    name = " ".join(context.args)
    today = get_today()

    if name not in user["habits"]:
        await update.message.reply_text("Нет такой привычки")
        return

    user["habits"][name]["days"][today] = True
    save_data(data)

    await update.message.reply_text(f"✅ Отмечено: {name}")


# Список привычек
async def list_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    user = get_user(data, user_id)

    if not user["habits"]:
        await update.message.reply_text("У тебя пока нет привычек. Добавь командой /add")
        return

    text = "Твои привычки:\n"
    for h, info in user["habits"].items():
        text += f"{h} — {info['time']}\n"

    await update.message.reply_text(text)


# Стартовое сообщение
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для отжиманий и привычек.\n\n"
        "Отжимания — просто отправь число.\n"
        "Привычки:\n"
        "/add <Имя> <Время> — добавить привычку (пример: /add Душ 08:30)\n"
        "/done <Имя> — отметить выполнение привычки сегодня\n"
        "/habits — показать список привычек"
    )


# Настройка бота
app = ApplicationBuilder().token(TOKEN).build()

# Обработчики команд
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add_habit))
app.add_handler(CommandHandler("done", done_habit))
app.add_handler(CommandHandler("habits", list_habits))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pushups))

# Запуск бота
app.run_polling()
