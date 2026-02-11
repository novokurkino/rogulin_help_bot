import json
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

TOKEN = "8587201858:AAEnYwf8wO7N3DqvxMsmwnLXfD3jp-CjijY"

DATA_FILE = "data.json"


# ---------- Работа с данными ----------
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


data = load_data()


def today():
    return datetime.now().date().isoformat()


def yesterday():
    return (datetime.now().date() - timedelta(days=1)).isoformat()


# ---------- Клавиатура ----------
def keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Контрастный душ", callback_data="shower")],
        [InlineKeyboardButton("Чтение", callback_data="reading")],
        [InlineKeyboardButton("Витамины", callback_data="vitamins")],
        [InlineKeyboardButton("100 отжиманий", callback_data="pushups")],
    ])


# ---------- /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in data:
        data[user_id] = {
            "shower": {"streak": 0, "last": None},
            "reading": {"streak": 0, "last": None},
            "vitamins": {"streak": 0, "last": None},
            "pushups": {"streak": 0, "last": None, "done": 0},
            "waiting_pushups": False
        }
        save_data(data)

    await update.message.reply_text(
        "Трекер привычек. Выбери действие:",
        reply_markup=keyboard()
    )


# ---------- Обработка привычек ----------
def update_streak(habit):
    if habit["last"] == yesterday():
        habit["streak"] += 1
    else:
        habit["streak"] = 1
    habit["last"] = today()


async def habit_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    user = data[user_id]

    habit = query.data

    if habit != "pushups":
        if user[habit]["last"] == today():
            await query.message.reply_text("Уже отмечено сегодня.")
            return

        update_streak(user[habit])
        save_data(data)
        await query.message.reply_text(
            f"Готово! Дней подряд: {user[habit]['streak']}",
            reply_markup=keyboard()
        )
    else:
        user["waiting_pushups"] = True
        user["pushups"]["done"] = 0
        save_data(data)
        await query.message.reply_text("Сколько отжиманий сделал?")


# ---------- Ввод числа отжиманий ----------
async def pushups_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = data[user_id]

    if not user["waiting_pushups"]:
        return

    try:
        count = int(update.message.text)
    except:
        await update.message.reply_text("Введи число.")
        return

    user["pushups"]["done"] += count
    left = 100 - user["pushups"]["done"]

    if left > 0:
        save_data(data)
        await update.message.reply_text(f"Осталось {left} отжиманий.")
    else:
        user["waiting_pushups"] = False
        update_streak(user["pushups"])
        save_data(data)
        await update.message.reply_text(
            f"100 выполнены! Дней подряд: {user['pushups']['streak']}",
            reply_markup=keyboard()
        )


# ---------- Запуск ----------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(habit_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, pushups_input))

    print("BOT STARTED")
    app.run_polling()


if __name__ == "__main__":
    main()
