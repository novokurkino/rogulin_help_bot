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

# Получаем токен из переменной окружения
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("TOKEN не задан! Проверь переменные окружения на Railway.")

DATA_FILE = "data.json"
DEFAULT_GOAL = 100


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    retu
