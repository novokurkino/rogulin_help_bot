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

# Вставь сюда токен от BotFather
TOKEN = "8587201858:AAEnYwf8wO7N3DqvxMsmwnLXfD3jp-CjijY"  # <-- замените на ваш токен

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
        data[uid] = {
            "goal": DEFAULT_GOAL,
            "pushups": {},
            "habits": {}
        }
    return data[uid]


async def handle_pushups(update: Update, context: Co_
