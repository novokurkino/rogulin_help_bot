from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import json
import datetime

TOKEN = "8587201858:AAEnYwf8wO7N3DqvxMsmwnLXfD3jp-CjijY"
DATA_FILE = "data.json"
DEFAULT_GOAL = 100

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_today():
    return str(datetime.date.today())

def get_user(data, user_id):
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"goal": DEFAULT_GOAL, "pushups": {}, "habits": {}}
    return data[uid]

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

async def add_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Пример: /add Душ 08:30")
        return
    user_id = update.effective_user.id
    data = load_data()
    user = get_user(data, user_id)
    name = context.args[0]
    time_str = context.args[1]
    user["habits"][name] = {"time": time_str, "days": {}}
    save_data(data)
    await update.message.reply_text(f"Привычка '{name}' добавлена на {time_str}")

async def done_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пример: /done Душ")
        return
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

async def list_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    user = get_user(data, user_id)
    if not user["habits"]:
        await update.message.reply_text("У тебя нет привычек.")
        return
    text = "Твои привычки:\n"
    for h, info in user["habits"].items():
        text += f"{h} — {info['time']}\n"
    await update.message.reply_text(text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Отжимания — просто число.\n"
        "/add Душ 08:30\n"
        "/done Душ\n"
        "/habits"
    )

# Создаем приложение
app = Application.builder().token(TOKEN).build()

# Добавляем обработчики
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add_habit))
app.add_handler(CommandHandler("done", done_habit))
app.add_handler(CommandHandler("habits", list_habits))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pushups))

# Запуск бота
app.run_polling()
