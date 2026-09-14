import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ============================================================
# НАСТРОЙКИ
# ============================================================

TOKEN = os.getenv("8587201858:AAH8D0ORbyVjJ7A_fRNm_9c3LZUXYhQRr5A")

if not TOKEN:
    raise RuntimeError("Переменная BOT_TOKEN не задана в Railway Variables")

DATA_FILE = "data.json"

# Москва
TIMEZONE = ZoneInfo("Europe/Moscow")

DAILY_GOAL = 100


# ============================================================
# РАБОТА С ДАННЫМИ
# ============================================================

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


data = load_data()


def today():
    return datetime.now(TIMEZONE).date().isoformat()


def yesterday():
    return (
        datetime.now(TIMEZONE).date() - timedelta(days=1)
    ).isoformat()


# ============================================================
# СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ
# ============================================================

def create_user():
    return {
        "shower": {
            "streak": 0,
            "last": None
        },
        "reading": {
            "streak": 0,
            "last": None
        },
        "vitamins": {
            "streak": 0,
            "last": None
        },
        "pushups": {
            "streak": 0,
            "last": None,
            "done": 0,
            "started_date": None
        },
        "waiting_pushups": False
    }


def get_user(user_id):
    user_id = str(user_id)

    if user_id not in data:
        data[user_id] = create_user()
        save_data()

    return data[user_id]


# ============================================================
# КЛАВИАТУРА
# ============================================================

def keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🚿 Контрастный душ",
                callback_data="shower"
            )
        ],
        [
            InlineKeyboardButton(
                "📖 Чтение",
                callback_data="reading"
            )
        ],
        [
            InlineKeyboardButton(
                "💊 Витамины",
                callback_data="vitamins"
            )
        ],
        [
            InlineKeyboardButton(
                "💪 100 отжиманий",
                callback_data="pushups"
            )
        ],
    ])


# ============================================================
# ОБНОВЛЕНИЕ СЕРИИ
# ============================================================

def update_streak(habit):
    current_day = today()

    if habit["last"] == current_day:
        return

    if habit["last"] == yesterday():
        habit["streak"] += 1
    else:
        habit["streak"] = 1

    habit["last"] = current_day


# ============================================================
# /START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    get_user(user_id)

    # Запоминаем пользователя для ежедневных напоминаний
    context.application.bot_data.setdefault(
        "users",
        set()
    )

    context.application.bot_data["users"].add(user_id)

    save_data()

    await update.message.reply_text(
        "👋 Трекер привычек\n\n"
        "Выбери, что хочешь отметить:",
        reply_markup=keyboard()
    )


# ============================================================
# ОБРАБОТКА КНОПОК
# ============================================================

async def habit_click(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    user_id = str(query.from_user.id)
    user = get_user(user_id)

    context.application.bot_data.setdefault(
        "users",
        set()
    )

    context.application.bot_data["users"].add(user_id)

    habit = query.data

    # --------------------------------------------------------
    # ОТЖИМАНИЯ
    # --------------------------------------------------------

    if habit == "pushups":

        current_day = today()

        # Если начался новый день — начинаем заново
        if user["pushups"]["started_date"] != current_day:
            user["pushups"]["done"] = 0
            user["pushups"]["started_date"] = current_day

        user["waiting_pushups"] = True

        save_data()

        left = DAILY_GOAL - user["pushups"]["done"]

        await query.message.reply_text(
            f"💪 Осталось сделать: {left}\n\n"
            "Сколько отжиманий сделал за подход?"
        )

        return

    # --------------------------------------------------------
    # ОБЫЧНЫЕ ПРИВЫЧКИ
    # --------------------------------------------------------

    if user[habit]["last"] == today():
        await query.message.reply_text(
            "✅ Уже отмечено сегодня.",
            reply_markup=keyboard()
        )
        return

    update_streak(user[habit])

    save_data()

    names = {
        "shower": "🚿 Контрастный душ",
        "reading": "📖 Чтение",
        "vitamins": "💊 Витамины"
    }

    name = names[habit]

    await query.message.reply_text(
        f"✅ {name} выполнено!\n\n"
        f"🔥 Дней подряд: {user[habit]['streak']}",
        reply_markup=keyboard()
    )


# ============================================================
# ВВОД КОЛИЧЕСТВА ОТЖИМАНИЙ
# ============================================================

async def pushups_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)

    if not user["waiting_pushups"]:
        return

    current_day = today()

    # Новый день
    if user["pushups"]["started_date"] != current_day:
        user["pushups"]["done"] = 0
        user["pushups"]["started_date"] = current_day

    # Проверяем число
    try:
        count = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Введи количество цифрами.\n\n"
            "Например: 20"
        )
        return

    # Нельзя вводить 0 или отрицательное число
    if count <= 0:
        await update.message.reply_text(
            "❌ Нужно ввести число больше нуля."
        )
        return

    # Если цель уже выполнена
    if user["pushups"]["done"] >= DAILY_GOAL:
        user["waiting_pushups"] = False
        save_data()

        await update.message.reply_text(
            "🎉 Сегодня 100 отжиманий уже выполнены!",
            reply_markup=keyboard()
        )
        return

    user["pushups"]["done"] += count

    # Не позволяем показывать отрицательный остаток
    if user["pushups"]["done"] >= DAILY_GOAL:

        user["pushups"]["done"] = DAILY_GOAL
        user["waiting_pushups"] = False

        update_streak(user["pushups"])

        save_data()

        await update.message.reply_text(
            f"🎉 100 отжиманий выполнены!\n\n"
            f"🔥 Дней подряд: {user['pushups']['streak']}",
            reply_markup=keyboard()
        )

        return

    # Осталось сделать
    left = DAILY_GOAL - user["pushups"]["done"]

    save_data()

    await update.message.reply_text(
        f"💪 Сделано: {user['pushups']['done']}\n"
        f"⏳ Осталось: {left}"
    )


# ============================================================
# ЕЖЕДНЕВНЫЕ НАПОМИНАНИЯ
# ============================================================

async def morning_status(
    context: ContextTypes.DEFAULT_TYPE
):
    users = data.keys()

    for user_id in list(users):

        try:
            user = get_user(user_id)

            pushups_done = user["pushups"]["done"]

            # Если вчера не выполняли привычку —
            # серия фактически уже прервана
            message = (
                "🌅 Доброе утро!\n\n"
                "Сегодня новый день.\n\n"
                f"💪 Отжимания: {pushups_done}/{DAILY_GOAL}\n\n"
                "Не забудь про свои привычки!"
            )

            await context.bot.send_message(
                chat_id=int(user_id),
                text=message,
                reply_markup=keyboard()
            )

        except Exception as error:
            print(
                f"Ошибка отправки утреннего сообщения "
                f"{user_id}: {error}"
            )


async def reminder(
    context: ContextTypes.DEFAULT_TYPE
):
    users = data.keys()

    for user_id in list(users):

        try:
            user = get_user(user_id)

            done = user["pushups"]["done"]
            left = max(0, DAILY_GOAL - done)

            await context.bot.send_message(
                chat_id=int(user_id),
                text=(
                    "⏰ Напоминание!\n\n"
                    f"💪 Отжимания: {done}/{DAILY_GOAL}\n"
                    f"Осталось: {left}\n\n"
                    "Вперёд! 💪"
                ),
                reply_markup=keyboard()
            )

        except Exception as error:
            print(
                f"Ошибка отправки напоминания "
                f"{user_id}: {error}"
            )


# ============================================================
# ЗАПУСК
# ============================================================

def main():

    print("================================")
    print("BOT STARTING")
    print("================================")

    application = Application.builder().token(TOKEN).build()

    # Команда /start
    application.add_handler(
        CommandHandler("start", start)
    )

    # Нажатия кнопок
    application.add_handler(
        CallbackQueryHandler(habit_click)
    )

    # Сообщения с количеством отжиманий
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            pushups_input
        )
    )

    # --------------------------------------------------------
    # Напоминания
    # --------------------------------------------------------

    job_queue = application.job_queue

    # 07:00 — утренний статус
    job_queue.run_daily(
        morning_status,
        time=datetime.strptime(
            "07:00",
            "%H:%M"
        ).time(),
        name="morning_status"
    )

    # 08:00 — напоминание
    job_queue.run_daily(
        reminder,
        time=datetime.strptime(
            "08:00",
            "%H:%M"
        ).time(),
        name="reminder_08"
    )

    # 15:00 — напоминание
    job_queue.run_daily(
        reminder,
        time=datetime.strptime(
            "15:00",
            "%H:%M"
        ).time(),
        name="reminder_15"
    )

    print("BOT STARTED")

    application.run_polling()


if __name__ == "__main__":
    main()
