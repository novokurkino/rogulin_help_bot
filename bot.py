from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import datetime
import json

# Вставьте свой токен от BotFather сюда
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
    user_id = update.effective_user.id
    data = load_data()
    user = get_user(data, user_id)

    if len(context.args) < 2:
        await update.message.reply_text("Пример: /add Душ 08:30")
        return

    name = context.args[0]
    time_str = context.args[1]

    user["habits"][name] = {"time": time_str, "days": {}}
    save_data(data)
    await update.message.reply_text(f"Привычка '{name}' добавлена на {time_str}")

async def done_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    user = get_user(data, user_id)

    name = " ".
