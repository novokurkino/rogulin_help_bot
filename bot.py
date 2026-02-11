# bot.py
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from datetime import datetime, date
import json
import os

API_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

DATA_FILE = "habit_data.json"

HABITS = ["Контрастный душ", "Чтение", "Витамины", "100 отжиманий"]

# Класс для callback кнопок
class HabitCallback(CallbackData, prefix="habit"):
    name: str

# Загрузка и сохранение данных
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Создаем клавиатуру для привычек
def habit_keyboard():
    kb = InlineKeyboardBuilder()
    for habit in HABITS:
        kb.button(text=habit, callback_data=HabitCallback(name=habit).pack())
    kb.adjust(2)
    return kb.as_markup()

# Проверка нового дня для сброса привычек
def reset_daily_habits(user_data):
    today_str = str(date.today())
    if user_data.get("last_date") != today_str:
        user_data["last_date"] = today_str
        # Сброс простых привычек
        for habit in HABITS[:-1]:  # кроме отжиманий
            user_data["habits_done"][habit] = False
        # Сброс отжиманий
        user_data["pushups_done"] = 0
        if user_data.get("missed_day"):
            user_data["streak"] = 0
        user_data["missed_day"] = True  # пока не выполнено
    return user_data

# /start команда
@dp.message(commands=["start"])
async def cmd_start(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data:
        data[user_id] = {
            "habits_done": {habit: False for habit in HABITS[:-1]},
            "pushups_done": 0,
            "streak": 0,
            "last_date": str(date.today()),
            "missed_day": True
        }
        save_data(data)
    await message.answer(
        "Привет! Вот твои привычки на сегодня:", 
        reply_markup=habit_keyboard()
    )

# Обработка нажатий кнопок
@dp.callback_query(HabitCallback.filter())
async def habit_callback(call: types.CallbackQuery, callback_data: HabitCallback):
    user_id = str(call.from_user.id)
    data = load_data()
    user_data = data.get(user_id)
    user_data = reset_daily_habits(user_data)

    habit = callback_data.name

    if habit == "100 отжиманий":
        await call.message.answer("Сколько отжиманий сделал?")
        # ждем ввод числа
        await PushupState.waiting_for_number.set()
        data[user_id] = user_data
        save_data(data)
        await call.answer()
        return

    # Простые привычки
    user_data["habits_done"][habit] = True
    data[user_id] = user_data
    save_data(data)
    await call.message.answer(f"Привычка '{habit}' засчитана ✅")
    await call.answer()

# Состояния для отжиманий
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

class PushupState(StatesGroup):
    waiting_for_number = State()

# Обработка ввода числа отжиманий
@dp.message(PushupState.waiting_for_number)
async def pushup_input(message: types.Message, state: FSMContext):
    try:
        count = int(message.text)
        if count < 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введи корректное число отжиманий.")
        return

    user_id = str(message.from_user.id)
    data = load_data()
    user_data = data[user_id]
    user_data = reset_daily_habits(user_data)

    user_data["pushups_done"] += count
    remaining = 100 - user_data["pushups_done"]

    if remaining <= 0:
        await message.answer("🎉 Дневной план отжиманий выполнен!")
        if user_data.get("missed_day"):
            user_data["streak"] += 1
            user_data["missed_day"] = False
        user_data["pushups_done"] = 100
    else:
        await message.answer(f"Сделано {user_data['pushups_done']} отжиманий. Осталось {remaining}.")

    data[user_id] = user_data
    save_data(data)
    await state.clear()
    await message.answer("Выбери привычку:", reply_markup=habit_keyboard())

# Команда /status
@dp.message(commands=["status"])
async def cmd_status(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()
    user_data = data.get(user_id)
    if not user_data:
        await message.answer("Сначала начни с /start")
        return
    user_data = reset_daily_habits(user_data)
    status = ""
    for habit in HABITS[:-1]:
        status += f"{habit}: {'✅' if user_data['habits_done'][habit] else '❌'}\n"
    status += f"100 отжиманий: {user_data['pushups_done']} / 100\n"
    status += f"Серий без пропуска: {user_data.get('streak',0)} дней"
    await message.answer(status, reply_markup=habit_keyboard())

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    from aiogram import F
    from aiogram.fsm.storage.memory import MemoryStorage
    dp.fsm.storage = MemoryStorage()
    asyncio.run(dp.start_polling(bot))
