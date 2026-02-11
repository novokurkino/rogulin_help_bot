import os
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from aiogram.filters import Text
from aiogram import F
from aiogram import types
from aiogram.utils import executor

# ---------- Получение токена ----------
API_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not API_TOKEN:
    raise ValueError("Переменная окружения TELEGRAM_TOKEN не задана!")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ---------- Хранение данных (в памяти, для простоты) ----------
users_data = {}

# ---------- CallbackData для кнопок ----------
class HabitCallback(CallbackData, prefix="habit"):
    name: str

# ---------- Клавиатура ----------
def main_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Контрастный душ", callback_data=HabitCallback(name="Контрастный душ"))
    kb.button(text="Чтение", callback_data=HabitCallback(name="Чтение"))
    kb.button(text="Витамины", callback_data=HabitCallback(name="Витамины"))
    kb.button(text="100 отжиманий", callback_data=HabitCallback(name="Отжимания"))
    kb.adjust(2)
    return kb.as_markup()

# ---------- Помощь с отжиманиями ----------
def get_pushups_status(user_id):
    data = users_data.get(user_id, {})
    today = datetime.date.today()
    pushups_data = data.get("Отжимания", {"done": 0, "last_date": None, "streak": 0})
    
    # Сброс если день новый
    if pushups_data["last_date"] != today:
        pushups_data["done"] = 0
        pushups_data["last_date"] = today
        if pushups_data.get("completed_yesterday"):
            pushups_data["streak"] += 1
        else:
            pushups_data["streak"] = 0
        pushups_data["completed_yesterday"] = False
    return pushups_data

# ---------- Старт ----------
@dp.message(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_data:
        users_data[user_id] = {"Контрастный душ": 0, "Чтение": 0, "Витамины": 0, "Отжимания": {"done": 0, "last_date": None, "streak": 0, "completed_yesterday": False}}
    await message.answer(
        "Привет! Выбирай привычку и отмечай её:",
        reply_markup=main_keyboard()
    )

# ---------- Обработка нажатий ----------
@dp.callback_query(HabitCallback.filter())
async def habit_callback(call: types.CallbackQuery, callback_data: HabitCallback):
    user_id = call.from_user.id
    habit = callback_data.name
    user = users_data[user_id]

    if habit in ["Контрастный душ", "Чтение", "Витамины"]:
        user[habit] += 1
        await call.message.answer(f"{habit} выполнено! Всего раз: {user[habit]}")
    elif habit == "Отжимания":
        pushups_data = get_pushups_status(user_id)
        users_data[user_id]["Отжимания"] = pushups_data
        await call.message.answer(
            f"Сколько отжиманий сделал сегодня? Уже сделано: {pushups_data['done']} / 100"
        )
        await PushupsWaiting.waiting.set()

    await call.answer()

# ---------- Машина состояний для отжиманий ----------
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

class PushupsWaiting(StatesGroup):
    waiting = State()

@dp.message(FSMContext)
async def handle_pushups(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = users_data[user_id]
    pushups_data = get_pushups_status(user_id)

    try:
        count = int(message.text)
    except ValueError:
        await message.answer("Введите число отжиманий цифрами!")
        return

    pushups_data["done"] += count
    if pushups_data["done"] >= 100:
        pushups_data["done"] = 100
        pushups_data["completed_yesterday"] = True
        await message.answer(f"Поздравляю! Дневной план выполнен! 🔥\nТекущий стрик дней: {pushups_data['streak'] + 1}")
    else:
        await message.answer(f"Сделано {pushups_data['done']} из 100. Осталось {100 - pushups_data['done']}")

    users_data[user_id]["Отжимания"] = pushups_data
    await state.clear()
    await message.answer("Выбирай следующую привычку:", reply_markup=main_keyboard())

# ---------- Запуск ----------
if __name__ == "__main__":
    from aiogram import asyncio
    asyncio.run(dp.start_polling(bot))
