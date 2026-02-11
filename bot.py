import os
import asyncio
from datetime import datetime, date
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Берём токен из переменной окружения Railway
API_TOKEN = "8587201858:AAEnYwf8wO7N3DqvxMsmwnLXfD3jp-CjijY"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Данные пользователей в памяти (для простоты)
user_data = {}

# Список привычек
habits = ["Контрастный душ", "Чтение", "Витамины", "100 отжиманий"]

def get_user(user_id):
    """Создаёт структуру данных для нового пользователя, если ещё нет"""
    if user_id not in user_data:
        user_data[user_id] = {
            "habits_done": {"Контрастный душ": False, "Чтение": False, "Витамины": False},
            "pushups_done": 0,
            "pushups_streak": 0,
            "last_pushups_date": None,
            "today": date.today()
        }
    # Сбрасываем ежедневные привычки при смене дня
    if user_data[user_id]["today"] != date.today():
        user_data[user_id]["habits_done"] = {h: False for h in ["Контрастный душ","Чтение","Витамины"]}
        user_data[user_id]["pushups_done"] = 0
        user_data[user_id]["today"] = date.today()
    return user_data[user_id]

def build_keyboard():
    kb = InlineKeyboardBuilder()
    for h in habits:
        kb.add(InlineKeyboardButton(text=h, callback_data=h))
    return kb.as_markup()

@dp.message(Command(commands=["start"]))
async def start(message: types.Message):
    get_user(message.from_user.id)
    await message.answer(
        "Привет! Я твой трекер привычек.\nВыбери привычку:",
        reply_markup=build_keyboard()
    )

@dp.callback_query()
async def handle_habit(call: types.CallbackQuery):
    user_id = call.from_user.id
    data = call.data
    user = get_user(user_id)

    # Если это одна из трёх обычных привычек
    if data in ["Контрастный душ", "Чтение", "Витамины"]:
        if user["habits_done"][data]:
            await call.message.answer(f"Привычка '{data}' уже выполнена сегодня ✅")
        else:
            user["habits_done"][data] = True
            await call.message.answer(f"Привычка '{data}' засчитана ✅")
        await call.answer()
        return

    # Отжимания
    if data == "100 отжиманий":
        await call.message.answer(f"Сколько отжиманий сделал сегодня? Уже сделано: {user['pushups_done']}")
        await call.answer()
        return

@dp.message()
async def handle_pushups(message: types.Message):
    user_id = message.from_user.id
    user = get_user(user_id)

    # Проверяем, что сообщение — число
    if message.text.isdigit():
        reps = int(message.text)
        user["pushups_done"] += reps

        remaining = 100 - user["pushups_done"]
        if remaining <= 0:
            # Завершили 100 отжиманий
            await message.answer("Поздравляю! Дневной план отжиманий выполнен 💪")
            # Обновляем серию
            today = date.today()
            if user["last_pushups_date"] == today - timedelta(days=1):
                user["pushups_streak"] += 1
            else:
                user["pushups_streak"] = 1
            user["last_pushups_date"] = today
            user["pushups_done"] = 100
        else:
            await message.answer(f"Сделано {user['pushups_done']}, осталось {remaining} отжиманий")

        await message.answer(f"Выполнял дней подряд: {user['pushups_streak']}")
    else:
        # Если не число — игнорируем
        await message.answer("Введи количество отжиманий цифрой!")

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
