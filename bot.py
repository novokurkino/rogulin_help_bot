import json
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio

API_TOKEN = "8587201858:AAEnYwf8wO7N3DqvxMsmwnLXfD3jp-CjijY"  # <-- вставьте сюда свой токен

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

DATA_FILE = "users_data.json"

# Загрузка данных
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

# ================== Callback ==================
@dp.callback_query()
async def habit_callback(call: types.CallbackQuery):
    user_id = str(call.from_user.id)
    today = datetime.date.today().isoformat()
    await call.answer()  # обязательно

    if user_id not in users_data:
        await call.message.answer("Сначала напиши /start")
        return

    habits = users_data[user_id]["habits"]

    # ---------------- Отжимания ----------------
    if call.data == "habit_pushups":
        await call.message.answer("Сколько отжиманий ты сделал сегодня?")
        # ждем ввода числа
        @dp.message()
        async def pushups_count(msg: types.Message):
            if msg.from_user.id != call.from_user.id:
                return  # игнорируем других пользователей
            try:
                count = int(msg.text)
                if count < 0:
                    raise ValueError
            except ValueError:
                await msg.reply("Введи корректное число!")
                return

            # Обновляем прогресс
            if habits["pushups"]["last_date"] != today:
                habits["pushups"]["done"] = 0
            habits["pushups"]["done"] += count

            remaining = max(0, 100 - habits["pushups"]["done"])
            if remaining == 0:
                await msg.answer("🎉 Дневной план по 100 отжиманиям выполнен!")
                # обновляем streak
                last_date = habits["pushups"]["last_date"]
                if last_date == (datetime.date.today() - datetime.timedelta(days=1)).isoformat():
                    habits["pushups"]["streak"] += 1
                else:
                    habits["pushups"]["streak"] = 1
            else:
                await msg.answer(f"Осталось сделать {remaining} отжиманий")

            habits["pushups"]["last_date"] = today
            save_data()
            await msg.answer(f"Текущий рекорд дней подряд: {habits['pushups']['streak']}")
            await msg.answer("Выбирай следующую привычку:", reply_markup=main_keyboard())

    # ---------------- Простые привычки ----------------
    elif call.data == "habit_shower":
        await mark_habit(call, "shower", "Контрастный душ")
    elif call.data == "habit_reading":
        await mark_habit(call, "reading", "Чтение")
    elif call.data == "habit_vitamins":
        await mark_habit(call, "vitamins", "Витамины")

# ================== Функция для простых привычек ==================
async def mark_habit(call, key, name):
    user_id = str(call.from_user.id)
    habits = users_data[user_id]["habits"]
    today = datetime.date.today().isoformat()

    last_date = habits[key]["last_date"]
    if last_date == today:
        await call.message.answer(f"✅ {name} уже отмечена сегодня")
        return

    # проверка на предыдущий день для streak
    if last_date == (datetime.date.today() - datetime.timedelta(days=1)).isoformat():
        habits[key]["streak"] += 1
    else:
        habits[key]["streak"] = 1

    habits[key]["last_date"] = today
    save_data()
    await call.message.answer(f"✅ {name} отмечена!\nДней подряд: {habits[key]['streak']}")
    await call.message.answer("Выбирай следующую привычку:", reply_markup=main_keyboard())

# ================== Запуск бота ==================
async def main():
    try:
        print("Бот запущен...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
