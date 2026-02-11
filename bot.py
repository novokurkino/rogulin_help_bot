import json
import datetime
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

API_TOKEN = "8587201858:AAEnYwf8wO7N3DqvxMsmwnLXfD3jp-CjijY"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

DATA_FILE = "users_data.json"

# ================== Загрузка данных ==================
try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        users_data = json.load(f)
except FileNotFoundError:
    users_data = {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users_data, f, ensure_ascii=False, indent=4)

# ================== Клавиатура ==================
def main_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Контрастный душ", callback_data="habit_shower"),
        InlineKeyboardButton("Чтение", callback_data="habit_reading"),
        InlineKeyboardButton("Витамины", callback_data="habit_vitamins"),
        InlineKeyboardButton("100 отжиманий", callback_data="habit_pushups")
    )
    return keyboard

# ================== /start ==================
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in users_data:
        users_data[user_id] = {
            "habits": {
                "shower": {"streak": 0, "last_date": None},
                "reading": {"streak": 0, "last_date": None},
                "vitamins": {"streak": 0, "last_date": None},
                "pushups": {"streak": 0, "last_date": None, "done": 0}
            }
        }
        save_data()
    await message.answer(
        "Привет! Это твой трекер привычек.\nВыбирай привычку для отметки сегодня:",
        reply_markup=main_keyboard()
    )

# ================== Callback для привычек ==================
@dp.callback_query()
async def habit_callback(call: types.CallbackQuery):
    user_id = str(call.from_user.id)
    today = datetime.date.today().isoformat()
    await call.answer()

    if user_id not in users_data:
        await call.message.answer("Сначала напиши /start")
        return

    habits = users_data[user_id]["habits"]

    # ================== Простые привычки ==================
    if call.data in ["habit_shower", "habit_reading", "habit_vitamins"]:
        key_map = {
            "habit_shower": "shower",
            "habit_reading": "reading",
            "habit_vitamins": "vitamins"
        }
        key = key_map[call.data]
        name = key.capitalize()

        last_date = habits[key]["last_date"]
        if last_date == today:
            await call.message.answer(f"✅ {name} уже отмечена сегодня")
            return

        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        if last_date == yesterday:
            habits[key]["streak"] += 1
        else:
            habits[key]["streak"] = 1

        habits[key]["last_date"] = today
        save_data()
        await call.message.answer(f"✅ {name} отмечена!\nДней подряд: {habits[key]['streak']}")

    # ================== 100 отжиманий ==================
    elif call.data == "habit_pushups":
        last_date = habits["pushups"]["last_date"]
        if last_date != today:
            habits["pushups"]["done"] = 0
        habits["pushups"]["done"] += 100  # Отмечаем полный день
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        if last_date == yesterday:
            habits["pushups"]["streak"] += 1
        else:
            habits["pushups"]["streak"] = 1
        habits["pushups"]["last_date"] = today
        save_data()
        await call.message.answer(
            f"💪 100 отжиманий отмечены!\nДней подряд: {habits['pushups']['streak']}"
        )

    await call.message.answer("Выбирай следующую привычку:", reply_markup=main_keyboard())

# ================== Запуск ==================
async def main():
    try:
        print("Бот запущен...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
