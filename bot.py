from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import datetime
import json
import os

TOKEN = "8587201858:AAEnYwf8wO7N3DqvxMsmwnLXfD3jp-CjijY"
GOAL_PUSHUPS = 100
HABITS = ["Контрастный душ", "Чтение", "Витамины", "100 отжиманий"]
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

# ----------------- Подсчет серии дней подряд -----------------
def calculate_streak(data, habit):
    streak = 0
    today = datetime.date.today()
    for i in range(1, 365):
        day = str(today - datetime.timedelta(days=i))
        if day in data and habit in data[day]:
            # Для отжиманий проверяем, что сделано >= GOAL
            if habit == "100 отжиманий":
                if data[day][habit] >= GOAL_PUSHUPS:
                    streak += 1
                else:
                    break
            else:
                if data[day][habit]:
                    streak += 1
                else:
                    break
        else:
            break
    return streak

# ----------------- Отправка клавиатуры -----------------
def get_habits_keyboard():
    keyboard = [[InlineKeyboardButton(habit, callback_data=habit)] for habit in HABITS]
    return InlineKeyboardMarkup(keyboard)

# ----------------- Команда /start -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я буду помогать отслеживать твои привычки.\n"
        "Нажми на кнопку, чтобы отметить привычку или сделать отжимания.",
        reply_markup=get_habits_keyboard()
    )

# ----------------- Команда /status -----------------
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    today = get_today()
    message = "Сегодня выполнено:\n"
    for habit in HABITS:
        if habit == "100 отжиманий":
            done = data.get(today, {}).get(habit, 0)
            message += f"{habit}: {done}/{GOAL_PUSHUPS}\n"
        else:
            done = data.get(today, {}).get(habit, False)
            message += f"{habit}: {'✅' if done else '❌'}\n"
    await update.message.reply_text(message)

# ----------------- Обработка нажатий кнопок -----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    habit = query.data
    data = load_data()
    today = get_today()
    if today not in data:
        data[today] = {}

    if habit == "100 отжиманий":
        await query.message.reply_text("Сколько отжиманий сделал сейчас? Отправь число.")
        # Сохраняем, что пользователь сейчас вводит отжимания
        context.user_data["awaiting_pushups"] = True
    else:
        data[today][habit] = True
        save_data(data)
        streak = calculate_streak(data, habit)
        await query.message.reply_text(f"✅ Привычка '{habit}' отмечена!\nСерий подряд: {streak} дней")

# ----------------- Обработка сообщений -----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    today = get_today()
    data = load_data()
    if today not in data:
        data[today] = {}

    # Если пользователь вводит отжимания
    if context.user_data.get("awaiting_pushups"):
        if not text.isdigit():
            await update.message.reply_text("Пришли просто число отжиманий 🙂")
            return
        pushups_done = int(text)
        data[today]["100 отжиманий"] = data[today].get("100 отжиманий", 0) + pushups_done
        save_data(data)
        done = data[today]["100 отжиманий"]
        left = max(0, GOAL_PUSHUPS - done)
        if done >= GOAL_PUSHUPS:
            await update.message.reply_text(f"✅ Дневной план отжиманий выполнен! Сделано: {done}")
        else:
            await update.message.reply_text(f"Сделано сегодня: {done}\nОсталось до цели: {left}")
        # Сбрасываем флаг ожидания числа
        context.user_data["awaiting_pushups"] = False
        return

    await update.message.reply_text("Нажми на кнопку привычки или отправь число отжиманий после нажатия кнопки.")

# ----------------- Основная функция -----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
